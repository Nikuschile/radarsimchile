#!/usr/bin/env python3
"""SCEL ATC Radar — local HTTP server + ADS-B proxy.

Endpoints:
  GET /live/fr24                — Flightradar24 scraper (primary ~50-100 aircraft)
  GET /live/chile?lat=X&lon=Y  — adsb.lol fallback
  GET /proxy/<encoded-url>       — pass-through CORS proxy

Usage:
  python server.py
  → http://localhost:8000/SCEL_ATC_Radar.html
"""
import http.server, socketserver, urllib.request, urllib.error, urllib.parse
import json, os, sys, time, threading, re
import http.cookiejar

PORT = 8000
PROXY_PREFIX = '/proxy/'
LIVE_PREFIX = '/live/chile'
FR24_PREFIX = '/live/fr24'
OSKY_PREFIX = '/live/opensky'
AIRNAV_PREFIX = '/live/airnav'

# Chile bounding box (approx)
CL_LAT_MIN, CL_LAT_MAX = -56.0, -17.0
CL_LON_MIN, CL_LON_MAX = -76.0, -64.0

# Cache
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 40  # seconds

# Upstream timeout — MUST stay below the frontend fetch abort (15 s),
# otherwise the client closes the connection and the server throws
# ConnectionAbortedError when writing the response.
UPSTREAM_TIMEOUT = 12  # seconds

# adsb.lol free API
ADSB_LOL_BASE = 'https://api.adsb.lol/v2/point'

# ── FlightRadar24 (lazy init, never blocks server startup) ──
_fr_api = None
_fr_lock = threading.Lock()
def _get_fr():
    global _fr_api
    with _fr_lock:
        if _fr_api is None:
            try:
                from FlightRadarAPI import FlightRadar24API
                _fr_api = FlightRadar24API()
                print('[FR24] FlightRadarAPI loaded OK')
            except ImportError:
                print('[FR24] FlightRadarAPI not installed — pip install FlightRadarAPI')
                return None
            except Exception as e:
                print(f'[FR24] Init error: {e}')
                return None
    return _fr_api

def _filter_chile(flights):
    """Filter Flight objects to Chile bounding box, return adsb.lol-compatible dicts."""
    ac_list = []
    for f in flights:
        lat = f.latitude
        lon = f.longitude
        if lat is None or lon is None:
            continue
        if not (CL_LAT_MIN <= lat <= CL_LAT_MAX and CL_LON_MIN <= lon <= CL_LON_MAX):
            continue
        ac = {
            'hex': (f.icao_24bit or '').lower(),
            'flight': (f.callsign or '').strip(),
            'lat': lat, 'lon': lon,
            'alt_baro': f.altitude or 0, 'gs': f.ground_speed or 0,
            'track': f.heading or 0, 't': f.aircraft_code or '',
            'r': f.registration or '', 'squawk': f.squawk or '',
            'category': f.airline_icao or '', 'dbFlags': 0,
            'ownOp': f.airline_iata or '',
            'origin': f.origin_airport_iata or '',
            'destination': f.destination_airport_iata or '',
            'vs': f.vertical_speed or 0,
        }
        ac_list.append(ac)
    return ac_list

def _do_fr24_fetch():
    """Single FR24 fetch attempt. Returns (ac_list, error_str)."""
    fr = _get_fr()
    if fr is None:
        return [], 'FlightRadarAPI not available'
    try:
        flights = fr.get_flights()
        ac_list = _filter_chile(flights)
        return ac_list, None
    except Exception as e:
        return [], str(e)


# ── AirNav RadarBox live feed (gRPC-web GetFlights) ──
# The map widget on es.airnavradar.com calls live.airnavradar.com/Flights/GetFlights
# (protobuf over gRPC-web). A valid rb_token (parsed from the homepage <meta name="token">)
# must be sent in the auth field, otherwise the server answers grpc-status 13 (empty).
AIRNAV_HOME = 'https://es.airnavradar.com/'
AIRNAV_RPC = 'https://live.airnavradar.com/Flights/GetFlights'
AIRNAV_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             '(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36')
# Same source whitelist as the map (flight-2viILNQN.js)
AIRNAV_SOURCES = ['adsb', 'adsbsat', 'asdi', 'ocea', 'mlat', 'sate',
                  'uat', 'hfdl', 'esti', 'asdex', 'flarm', 'aust']
# Bounds format = [maxLat, maxLng, minLat, minLng] (the map's getBounds output)
AIRNAV_FILTERS = {'bounds': f'{CL_LAT_MAX},{CL_LON_MAX},{CL_LAT_MIN},{CL_LON_MIN}',
                  'zoom': '8', 'designator': 'iata', 'tz': 'local',
                  'os': 'web', 'projType': 'webmercator'}
AIRNAV_OPTIONS = ['showLastTrails', 'vehicles', 'ground', 'onair']
AIRNAV_SESSION_TTL = 600  # refresh homepage token+cookies every 10 min

_airnav_lock = threading.Lock()
_airnav_cj = http.cookiejar.CookieJar()
_airnav_token = None
_airnav_session_ts = 0

# ── minimal protobuf writers/readers ──
def _pb_varint(n):
    out = b''
    while n > 0x7F:
        out += bytes([(n & 0x7F) | 0x80]); n >>= 7
    return out + bytes([n])

def _pb_fld_str(tag, s):
    b = s.encode()
    return _pb_varint(tag << 3 | 2) + _pb_varint(len(b)) + b

def _pb_fld_bytes(tag, b):
    return _pb_varint(tag << 3 | 2) + _pb_varint(len(b)) + b

def _pb_kv(k, v):
    return _pb_fld_bytes(2, _pb_fld_str(1, k) + _pb_fld_str(2, v))

def _pb_rd_varint(buf, pos):
    result = 0; shift = 0
    while True:
        b = buf[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7

def _pb_rd_bytes(buf, pos):
    ln, pos = _pb_rd_varint(buf, pos)
    return buf[pos:pos + ln], pos + ln

def _airnav_build_query(token):
    """FlightsQuery message → gRPC-web frame (0x00 + uint32 BE len + message)."""
    body = b''
    for s in AIRNAV_SOURCES:
        body += _pb_fld_str(1, s)
    for k, v in AIRNAV_FILTERS.items():
        body += _pb_kv(k, v)
    for o in AIRNAV_OPTIONS:
        body += _pb_fld_str(3, o)
    if token:
        body += _pb_fld_bytes(4, _pb_fld_str(1, 'rb_token') + _pb_fld_str(2, token))
    return b'\x00' + len(body).to_bytes(4, 'big') + body

def _airnav_decode_flight(b):
    """Decode one LiveFlight message → dict with named fields (see buffer bundle proto)."""
    f = {}
    pos = 0; end = len(b)
    while pos < end:
        tag, pos = _pb_rd_varint(b, pos)
        field = tag >> 3; wire = tag & 7
        if wire == 2:
            s, pos = _pb_rd_bytes(b, pos)
            name = {2: 'fn', 7: 'act', 11: 'so', 12: 'acr', 13: 'ms', 14: 'org',
                    15: 'dst', 16: 'al', 20: 'sn', 21: 'th1', 23: 'arrIn', 24: 'fir',
                    25: 'tkot', 26: 'eta', 27: 'depa', 30: 'apprcint', 31: 'fplacint',
                    32: 'curint', 33: 'cs', 34: 'st', 36: 'estiso', 39: 'orgAlt',
                    40: 'dstAlt', 41: 'aporgci', 42: 'apdstci', 43: 'deprel',
                    44: 'arrrel', 45: 'div', 46: 'arra', 47: 'lngt', 48: 'atgate'}.get(field)
            if name:
                f[name] = s.decode('utf-8', 'replace')
        elif wire == 0:
            v, pos = _pb_rd_varint(b, pos)
            name = {1: 'fid', 5: 't', 6: 'alt', 8: 'gs', 9: 'hd', 10: 'estihd',
                    17: 'vs', 19: 'sq', 22: 'dist', 29: 'arrau', 35: 'pr'}.get(field)
            if name:
                if v > 0x7FFFFFFFFFFFFFFF:  # signed 64 (int64 fields)
                    v -= 1 << 64
                elif v > 0x7FFFFFFF:        # signed 32 (int32 fields, negative 64-bit varint)
                    v -= 1 << 64
                f[name] = v
        elif wire == 5:
            import struct
            v = struct.unpack('<f', b[pos:pos + 4])[0]; pos += 4
            name = {3: 'la', 4: 'lo', 37: 'nextposla', 38: 'nextposlo'}.get(field)
            if name:
                f[name] = v
        elif wire == 1:
            pos += 8
        else:
            break
    return f

def _airnav_parse(raw):
    """Parse gRPC-web response → (payload, trailer_dict)."""
    payload = b''; trailer = {}
    pos = 0
    while pos + 5 <= len(raw):
        flag = raw[pos]
        ln = int.from_bytes(raw[pos + 1:pos + 5], 'big')
        frame = raw[pos + 5:pos + 5 + ln]
        if flag & 0x80:
            p2 = 0
            while p2 < len(frame):
                t2, p2 = _pb_rd_varint(frame, p2)
                if (t2 >> 3) == 1:
                    kv, p2 = _pb_rd_bytes(frame, p2)
                    k, pk = _pb_rd_bytes(kv, 0)
                    v, _ = _pb_rd_bytes(kv, pk)
                    trailer[k.decode()] = v.decode('utf-8', 'replace')
                else:
                    break
        else:
            payload += frame
        pos += 5 + ln
    return payload, trailer

def _airnav_fetch():
    """Fetch AirNav live flights for Chile. Returns (ac_list, error_str)."""
    global _airnav_token, _airnav_session_ts
    now = time.time()
    try:
        with _airnav_lock:
            token = _airnav_token
            need_session = not token or now - _airnav_session_ts >= AIRNAV_SESSION_TTL
            if need_session:
                req = urllib.request.Request(AIRNAV_HOME, headers={'User-Agent': AIRNAV_UA})
                opener = urllib.request.build_opener(
                    urllib.request.HTTPCookieProcessor(_airnav_cj))
                with opener.open(req, timeout=UPSTREAM_TIMEOUT) as resp:
                    html = resp.read().decode('utf-8', 'replace')
                m = re.search(r'<meta name="token" content="([^"]+)"', html)
                token = m.group(1) if m else None
                if token:
                    _airnav_token = token
                    _airnav_session_ts = now
            body = _airnav_build_query(token)
            req = urllib.request.Request(AIRNAV_RPC, data=body, method='POST', headers={
                'User-Agent': AIRNAV_UA,
                'Content-Type': 'application/grpc-web+proto',
                'X-Grpc-Web': '1',
                'Referer': AIRNAV_HOME,
            })
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(_airnav_cj))
            with opener.open(req, timeout=UPSTREAM_TIMEOUT) as resp:
                raw = resp.read()
    except urllib.error.HTTPError as e:
        return [], f'http {e.code}'
    except Exception as e:
        return [], str(e)
    payload, trailer = _airnav_parse(raw)
    if trailer.get('grpc-status', '0') != '0':
        return [], f"grpc {trailer.get('grpc-status')} {trailer.get('grpc-message', '')}"
    # decode flights
    flights = []
    pos = 0
    while pos < len(payload):
        tag, pos = _pb_rd_varint(payload, pos)
        if (tag >> 3) == 1 and (tag & 7) == 2:
            inner, pos = _pb_rd_bytes(payload, pos)
            flights.append(_airnav_decode_flight(inner))
        elif (tag & 7) == 2:
            _, pos = _pb_rd_bytes(payload, pos)
        elif (tag & 7) == 0:
            _, pos = _pb_rd_varint(payload, pos)
        else:
            break
    ac_list = []
    for f in flights:
        la, lo = f.get('la'), f.get('lo')
        if la is None or lo is None:
            continue
        if not (CL_LAT_MIN <= la <= CL_LAT_MAX and CL_LON_MIN <= lo <= CL_LON_MAX):
            continue
        ac_list.append({
            'hex': (f.get('ms') or '').lower(),
            'flight': (f.get('fn') or f.get('cs') or '').strip(),
            'lat': la, 'lon': lo,
            'alt_baro': f.get('alt') or 0,
            'gs': f.get('gs') or 0,
            'track': f.get('hd') or 0,
            'squawk': str(f.get('sq') or ''),
            'r': f.get('acr') or '',
            't': f.get('act') or '',
            'category': f.get('al') or '',
            'vs': f.get('vs') or 0,
            'origin': f.get('org') or '',
            'destination': f.get('dst') or '',
            'ownOp': '', 'dbFlags': 0,
        })
    return ac_list, None


# ── HTTP Handler ──
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith(FR24_PREFIX):
            return self._handle_fr24()
        if self.path.startswith(OSKY_PREFIX):
            return self._handle_opensky()
        if self.path.startswith(AIRNAV_PREFIX):
            return self._handle_airnav()
        if self.path.startswith(LIVE_PREFIX):
            return self._handle_live_chile()
        if self.path.startswith(PROXY_PREFIX):
            return self._handle_proxy()
        return super().do_GET()

    def do_POST(self):
        """Guarda fraseologia_editada.json (panel FRASES) y datos_offline.json (sección OFFLINE)."""
        if self.path == '/save/fraseologia':
            try:
                ln = int(self.headers.get('Content-Length') or 0)
                raw = self.rfile.read(ln) if ln > 0 else b''
                data = json.loads(raw.decode('utf-8'))
                if not isinstance(data, dict) or 'readbacks' not in data:
                    self._send_json(json.dumps({'ok': False, 'error': 'JSON inválido: falta "readbacks"'}).encode(), 'ERR')
                    return
                target = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fraseologia_editada.json')
                tmp = target + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, target)
                self._send_json(json.dumps({'ok': True, 'archivo': 'fraseologia_editada.json',
                                            'readbacks': len(data.get('readbacks', []))}).encode(), 'OK')
                print(f'[FRASES] Guardado fraseologia_editada.json ({len(data.get("readbacks", []))} readbacks)')
            except Exception as e:
                self._send_json(json.dumps({'ok': False, 'error': str(e)}).encode(), 'ERR')
            return
        if self.path == '/save/datos_offline':
            try:
                ln = int(self.headers.get('Content-Length') or 0)
                raw = self.rfile.read(ln) if ln > 0 else b''
                data = json.loads(raw.decode('utf-8'))
                if not isinstance(data, dict):
                    self._send_json(json.dumps({'ok': False, 'error': 'JSON inválido'}).encode(), 'ERR')
                    return
                target = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datos_offline.json')
                tmp = target + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, target)
                total = sum(len(data.get(k, [])) for k in ('mrvac', 'zonas', 'sectores', 'awy', 'rwy', 'fixes', 'star'))
                self._send_json(json.dumps({'ok': True, 'archivo': 'datos_offline.json',
                                            'entradas': total}).encode(), 'OK')
                print(f'[OFFLINE] Guardado datos_offline.json ({total} entradas)')
            except Exception as e:
                self._send_json(json.dumps({'ok': False, 'error': str(e)}).encode(), 'ERR')
            return
        self._send_json(json.dumps({'ok': False, 'error': 'endpoint desconocido: ' + self.path}).encode(), 'ERR')

    def _handle_fr24(self):
        """Flightradar24 scraper — returns empty [] if rate-limited or still warming."""
        cache_key = 'fr24_chile'
        now = time.time()
        with _cache_lock:
            cached = _cache.get(cache_key)
            if cached and now - cached[1] < CACHE_TTL:
                self._send_json(cached[0], 'HIT')
                return
        # Fetch fresh (lazy init — first request triggers FR24 loading)
        ac_list, err = _do_fr24_fetch()
        if ac_list:
            result = json.dumps({'ac': ac_list, 'total': len(ac_list), 'source': 'flightradar24'}).encode()
            with _cache_lock:
                _cache[cache_key] = (result, now)
            self._send_json(result, 'MISS')
            print(f'[FR24] Served {len(ac_list)} Chile aircraft')
            return
        # Serve stale cache or empty
        with _cache_lock:
            stale = _cache.get(cache_key)
        if stale:
            self._send_json(stale[0], 'STALE')
        else:
            self._send_json(json.dumps({'ac': [], 'note': err or 'no_data', 'source': 'flightradar24'}).encode(), 'MISS')

    def _handle_live_chile(self):
        """adsb.lol endpoint — fast, reliable, no auth needed."""
        params = {}
        if '?' in self.path:
            qs = self.path.split('?', 1)[1]
            for kv in qs.split('&'):
                k, v = kv.split('=', 1) if '=' in kv else (kv, '')
                params[k] = v
        lat = float(params.get('lat', '-33.45'))
        lon = float(params.get('lon', '-70.66'))
        r = int(params.get('r', '750'))
        cache_key = f'adsb_{lat}_{lon}_{r}'
        now = time.time()
        with _cache_lock:
            c = _cache.get(cache_key)
            if c and now - c[1] < CACHE_TTL:
                self._send_json(c[0], 'HIT')
                return
        try:
            url = f'{ADSB_LOL_BASE}/{lat}/{lon}/{r}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT) as resp:
                raw = resp.read()
            raw_json = json.loads(raw)
            aircraft = raw_json.get('ac', [])
            # Return ALL aircraft in radius (no Chile filter — client filters by viewport)
            result = json.dumps({
                'ac': aircraft, 'total': len(aircraft), 'source': 'adsb.lol'
            }).encode()
            with _cache_lock:
                _cache[cache_key] = (result, now)
            self._send_json(result, 'MISS')
        except urllib.error.HTTPError as e:
            with _cache_lock:
                stale = _cache.get(cache_key)
            if stale:
                self._send_json(stale[0], 'STALE')
            else:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self._safe_write(json.dumps({'ac': [], 'error': str(e)}).encode())
        except Exception as e:
            with _cache_lock:
                stale = _cache.get(cache_key)
            if stale:
                self._send_json(stale[0], 'STALE')
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self._safe_write(json.dumps({'ac': [], 'error': str(e)}).encode())

    def _handle_opensky(self):
        """OpenSky Network — Chile bounding box, no auth needed (~10-50 aircraft)."""
        cache_key = 'opensky_chile'
        now = time.time()
        with _cache_lock:
            c = _cache.get(cache_key)
            if c and now - c[1] < CACHE_TTL:
                self._send_json(c[0], 'HIT')
                return
        try:
            # Chile bounding box
            url = f'https://opensky-network.org/api/states/all?lamin={CL_LAT_MIN}&lamax={CL_LAT_MAX}&lomin={CL_LON_MIN}&lomax={CL_LON_MAX}'
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT) as resp:
                raw = resp.read()
            raw_json = json.loads(raw)
            states = raw_json.get('states', [])
            # Convert OpenSky state vectors to adsb.lol-compatible format
            ac_list = []
            for sv in states:
                if not isinstance(sv, (list, tuple)) or len(sv) < 11:
                    continue
                ac_list.append({
                    'hex': (sv[0] or '').lower(),
                    'flight': (sv[1] or '').strip(),
                    'lat': sv[6], 'lon': sv[5],
                    'alt_baro': sv[7] or 0,
                    'gs': sv[9] or 0,
                    'track': sv[10] or 0,
                    'squawk': sv[14] or '',
                    'r': '', 't': '',
                })
            result = json.dumps({
                'ac': ac_list, 'total': len(ac_list), 'source': 'opensky'
            }).encode()
            with _cache_lock:
                _cache[cache_key] = (result, now)
            self._send_json(result, 'MISS')
            print(f'[OpenSky] Served {len(ac_list)} aircraft')
        except Exception as e:
            # Serve stale cache if we have it (keeps the map populated when
            # OpenSky is slow/rate-limited), otherwise a clean 502.
            with _cache_lock:
                stale = _cache.get(cache_key)
            if stale:
                self._send_json(stale[0], 'STALE')
                print(f'[OpenSky] Error {e} — serving stale cache')
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self._safe_write(json.dumps({'ac': [], 'error': str(e)}).encode())

    def _handle_airnav(self):
        """AirNav RadarBox — full Chile coverage via gRPC-web GetFlights."""
        cache_key = 'airnav_chile'
        now = time.time()
        with _cache_lock:
            c = _cache.get(cache_key)
            if c and now - c[1] < CACHE_TTL:
                self._send_json(c[0], 'HIT')
                return
        try:
            ac_list, err = _airnav_fetch()
            if ac_list:
                result = json.dumps({
                    'ac': ac_list, 'total': len(ac_list), 'source': 'airnav'
                }).encode()
                with _cache_lock:
                    _cache[cache_key] = (result, now)
                self._send_json(result, 'MISS')
                print(f'[AirNav] Served {len(ac_list)} Chile aircraft')
                return
            with _cache_lock:
                stale = _cache.get(cache_key)
            if stale:
                self._send_json(stale[0], 'STALE')
                print(f'[AirNav] No data ({err}) — serving stale cache')
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self._safe_write(json.dumps({'ac': [], 'error': err or 'no_data', 'source': 'airnav'}).encode())
        except Exception as e:
            with _cache_lock:
                stale = _cache.get(cache_key)
            if stale:
                self._send_json(stale[0], 'STALE')
            else:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self._safe_write(json.dumps({'ac': [], 'error': str(e)}).encode())

    def _handle_proxy(self):
        """Pass-through CORS proxy."""
        raw_path = self.path[len(PROXY_PREFIX):]
        if '?' in raw_path:
            target_url = urllib.parse.unquote(raw_path.split('?')[0]) + '?' + raw_path.split('?', 1)[1]
        else:
            target_url = urllib.parse.unquote(raw_path)
        if not target_url.startswith('http'):
            self.send_error(400, 'Bad proxy URL')
            return
        now = time.time()
        with _cache_lock:
            c = _cache.get(target_url)
            if c and now - c[1] < CACHE_TTL:
                self._send_json(c[0], 'HIT')
                return
        try:
            req = urllib.request.Request(target_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT) as resp:
                data = resp.read()
            with _cache_lock:
                _cache[target_url] = (data, now)
            self._send_json(data, 'MISS')
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, 'read') else b'{}'
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self._safe_write(body if body else json.dumps({'error': str(e)}).encode())
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self._safe_write(json.dumps({'error': str(e)}).encode())

    def _send_json(self, data, cache_status):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('X-Cache', cache_status)
        self.end_headers()
        self._safe_write(data)

    def _safe_write(self, data):
        """Write response bytes, tolerating clients that aborted the request
        (ConnectionAbortedError / BrokenPipeError are normal when the browser
        cancels a fetch — the upstream already timed out on its own)."""
        try:
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # client went away — nothing to send
        except OSError:
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, format, *args):
        msg = str(args[0]) if args else ''
        if '/proxy/' in msg or '/live/' in msg:
            return
        super().log_message(format, *args)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with ThreadedHTTPServer(('0.0.0.0', PORT), Handler) as httpd:
        print('  SCEL ATC Radar — Servidor activo')
        print(f'  http://localhost:{PORT}/SCEL_ATC_Radar.html')
        print(f'  FR24:  {PORT}/live/fr24')
        print(f'  ADSB:  {PORT}/live/chile')
        print(f'  AIRNAV:{PORT}/live/airnav')
        print(f'  Proxy: {PORT}/proxy/<url>')
        print(f'  Cache: {CACHE_TTL}s  |  Ctrl+C para detener')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n  Servidor detenido.')
