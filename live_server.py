#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor del simulador ATC SCEL con datos ADS-B en vivo (Chile).

Fuentes de vuelos:
  - api.adsb.lol  (primaria, sin key, rica: hex/flight/reg/tipo/alt/gs/track)
  - OpenSky Network (respaldo, sin key, latencia ~5s)
  - FlightRadar24 (intento de scraping del feed en vivo; en 2026 suele estar
    bloqueado sin cookies -> si no responde, devuelve adsb.lol Chile)

Uso:
  python live_server.py [puerto] [carpeta]
  Ejemplo: python live_server.py 8123 C:\\nikus\\simulador\\radarsave22

Endpoints (mismos que espera SCEL_ATC_Radar.html):
  /                        -> archivos estaticos (HTML, coast_xy_smooth.js...)
  /proxy/<url-percent-encoded>  -> proxy HTTP generico (cache 45s)
  /live/chile?lat=&lon=&r= -> api.adsb.lol point query      -> {"ac":[...]}
  /live/opensky            -> OpenSky Network (caja Chile)   -> {"ac":[...]}
  /live/fr24               -> FR24 feed.js; si vacio -> adsb -> {"ac":[...]}
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import http.cookiejar
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
ROOT = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# Puntos estrategicos de Chile (mismos que usa el cliente)
CHILE_POINTS = [
    (-33.45, -70.66, 750),   # Santiago + centro
    (-18.48, -70.30, 750),   # Arica / norte
    (-53.16, -70.91, 750),   # Punta Arenas / Magallanes
    (-33.00, -78.00, 600),   # Corredor oceánico (Isla de Pascua)
]

CACHE = {}
def cached(key, ttl):
    def deco(fn):
        def wrapper(*a, **kw):
            now = time.time()
            c = CACHE.get(key)
            if c and c[0] > now:
                return c[1]
            data = fn(*a, **kw)
            CACHE[key] = (now + ttl, data)
            return data
        return wrapper
    return deco

def http_get(url, timeout=12, max_bytes=4_000_000):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError('response too large')
        ctype = r.headers.get('Content-Type', '')
        return data, ctype

def norm_ac(a):
    """Normaliza un avion al formato que entiende el cliente (adsb.lol style)."""
    out = {}
    for k in ('hex', 'flight', 'r', 't', 'alt_baro', 'gs', 'track', 'squawk', 'lat', 'lon'):
        v = a.get(k)
        if v is not None:
            out[k] = v
    if not out.get('hex') or out.get('lat') is None or out.get('lon') is None:
        return None
    out['hex'] = str(out['hex']).lower()
    if 'flight' in out:
        out['flight'] = str(out['flight']).strip()
    return out

# ── Fuente 1: api.adsb.lol ────────────────────────────────────────────────
def _adsb_point(lat, lon, r):
    key = f"adsb:{lat}:{lon}:{r}"
    now = time.time()
    c = CACHE.get(key)
    if c and c[0] > now:
        return c[1]
    url = f"https://api.adsb.lol/v2/point/{lat}/{lon}/{r}"
    try:
        body, _ = http_get(url, 12)
        j = json.loads(body)
    except Exception as e:
        print('[adsb.lol]', url, '->', e)
        return {'ac': []}
    out = {}
    for a in j.get('ac', []):
        n = norm_ac(a)
        if n:
            out[n['hex']] = n
    data = {'ac': list(out.values())}
    CACHE[key] = (now + 45, data)
    return data

def fetch_adsb_chile():
    merged = {}
    for lat, lon, r in CHILE_POINTS:
        for a in _adsb_point(lat, lon, r)['ac']:
            merged[a['hex']] = a
    return {'ac': list(merged.values())}

# ── Fuente 2: OpenSky Network (respaldo) ──────────────────────────────────
@cached('opensky', 60)
def fetch_opensky():
    url = ("https://opensky-network.org/api/states/all"
           "?lamin=-57&lamax=-17&lomin=-78&lomax=-63")
    try:
        body, _ = http_get(url, 15)
        j = json.loads(body)
    except Exception as e:
        print('[opensky]', e)
        return {'ac': []}
    out = {}
    for sv in j.get('states', []):
        try:
            if len(sv) < 15 or sv[5] is None or sv[6] is None:
                continue
            n = {
                'hex': (sv[0] or '').lower(),
                'flight': (sv[1] or '').strip(),
                'lat': sv[6], 'lon': sv[5],
                'alt_baro': sv[7] or 0,
                'gs': sv[9] or 0,
                'track': sv[10] or 0,
                'squawk': sv[14] or '',
            }
            if n['hex']:
                out[n['hex']] = n
        except Exception:
            continue
    return {'ac': list(out.values())}

# ── Fuente 3: FlightRadar24 (scraping; en 2026 suele requerir cookies) ────
@cached('fr24', 60)
def fetch_fr24():
    url = ("https://data-live.flightradar24.com/zones/fcgi/feed.js"
           "?bounds=-57,-17,-78,-63&faa=1&satellite=1&mlat=1&flarm=1"
           "&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400"
           "&gliders=1&stats=1")
    try:
        body, _ = http_get(url, 10)
        j = json.loads(body)
        ac = j.get('aircraft') or {}
        if ac:
            out = {}
            for fid, arr in ac.items():
                try:
                    hexid, squawk, flight, lat, lon, alt, track, spd = (
                        arr[0], arr[1], arr[2] or '', arr[3], arr[4],
                        arr[5], arr[6], arr[7])
                except Exception:
                    continue
                if not lat or not lon or not hexid:
                    continue
                n = {'hex': str(hexid).lower(), 'flight': str(flight).strip(),
                     'lat': lat, 'lon': lon, 'alt_baro': alt,
                     'track': track, 'gs': spd, 'squawk': str(squawk)}
                out[n['hex']] = n
            if out:
                print(f'[fr24] feed OK -> {len(out)} aeronaves')
                return {'ac': list(out.values())}
        print('[fr24] feed vacio/bloqueado -> fallback adsb.lol Chile')
    except Exception as e:
        print('[fr24] feed fail:', e)
    return fetch_adsb_chile()

# ── Fuente 4: AirNav RadarBox (gRPC-web GetFlights, cobertura Chile completa) ─
# El mapa de es.airnavradar.com llama live.airnavradar.com/Flights/GetFlights
# (protobuf sobre gRPC-web). Sin rb_token (del <meta name="token"> del homepage)
# el servidor responde grpc-status 13 vacio.
AIRNAV_HOME = 'https://es.airnavradar.com/'
AIRNAV_RPC = 'https://live.airnavradar.com/Flights/GetFlights'
AIRNAV_SOURCES = ['adsb', 'adsbsat', 'asdi', 'ocea', 'mlat', 'sate',
                  'uat', 'hfdl', 'esti', 'asdex', 'flarm', 'aust']
# Bounds = [maxLat, maxLng, minLat, minLng] (formato getBounds del mapa)
AIRNAV_FILTERS = {'bounds': '-17,-64,-56,-76', 'zoom': '8',
                  'designator': 'iata', 'tz': 'local', 'os': 'web',
                  'projType': 'webmercator'}
AIRNAV_OPTIONS = ['showLastTrails', 'vehicles', 'ground', 'onair']
AIRNAV_SESSION_TTL = 600

_airnav_cj = http.cookiejar.CookieJar()
_airnav_token = None
_airnav_session_ts = 0
_airnav_lock = threading.Lock()

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
                if v > 0x7FFFFFFFFFFFFFFF:
                    v -= 1 << 64
                elif v > 0x7FFFFFFF:
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

@cached('airnav', 40)
def fetch_airnav():
    global _airnav_token, _airnav_session_ts
    now = time.time()
    try:
        with _airnav_lock:
            token = _airnav_token
            if not token or now - _airnav_session_ts >= AIRNAV_SESSION_TTL:
                req = urllib.request.Request(AIRNAV_HOME, headers={'User-Agent': UA})
                opener = urllib.request.build_opener(
                    urllib.request.HTTPCookieProcessor(_airnav_cj))
                with opener.open(req, timeout=12) as resp:
                    html = resp.read().decode('utf-8', 'replace')
                m = re.search(r'<meta name="token" content="([^"]+)"', html)
                token = m.group(1) if m else None
                if token:
                    _airnav_token = token
                    _airnav_session_ts = now
            body = _airnav_build_query(token)
            req = urllib.request.Request(AIRNAV_RPC, data=body, method='POST', headers={
                'User-Agent': UA,
                'Content-Type': 'application/grpc-web+proto',
                'X-Grpc-Web': '1',
                'Referer': AIRNAV_HOME,
            })
            opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(_airnav_cj))
            with opener.open(req, timeout=12) as resp:
                raw = resp.read()
    except Exception as e:
        print('[airnav]', e)
        return {'ac': []}
    payload, trailer = _airnav_parse(raw)
    if trailer.get('grpc-status', '0') != '0':
        print('[airnav] grpc', trailer.get('grpc-status'), trailer.get('grpc-message', ''))
        return {'ac': []}
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
    out = {}
    for f in flights:
        la, lo = f.get('la'), f.get('lo')
        if la is None or lo is None:
            continue
        if not (-56.0 <= la <= -17.0 and -76.0 <= lo <= -64.0):
            continue
        n = norm_ac({
            'hex': (f.get('ms') or '').lower(),
            'flight': (f.get('fn') or f.get('cs') or '').strip(),
            'lat': la, 'lon': lo,
            'alt_baro': f.get('alt') or 0,
            'gs': f.get('gs') or 0,
            'track': f.get('hd') or 0,
            'squawk': str(f.get('sq') or ''),
            'r': f.get('acr') or '',
            't': f.get('act') or '',
        })
        if n and n['hex']:
            out[n['hex']] = n
    print(f'[airnav] {len(out)} aeronaves Chile')
    return {'ac': list(out.values())}

# ── Proxy generico ────────────────────────────────────────────────────────
@cached('proxy', 45)
def proxy_fetch(url):
    body, ctype = http_get(url, 12)  # below frontend abort (15 s)
    return body, ctype

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def _safe_write(self, body):
        """Tolerate clients that aborted the fetch (normal when the frontend
        aborts at 15 s while an upstream is slow)."""
        try:
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except OSError:
            pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self._safe_write(body)

    def _send_bytes(self, body, ctype='application/octet-stream', status=200):
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self._safe_write(body)

    def do_GET(self):  # noqa: C901
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        try:
            if path == '/live/chile':
                q = urllib.parse.parse_qs(parsed.query)
                lat = q.get('lat', ['-33.45'])[0]
                lon = q.get('lon', ['-70.66'])[0]
                r = q.get('r', ['750'])[0]
                return self._send_json(_adsb_point(lat, lon, r))
            if path == '/live/opensky':
                return self._send_json(fetch_opensky())
            if path == '/live/fr24':
                return self._send_json(fetch_fr24())
            if path == '/live/airnav':
                return self._send_json(fetch_airnav())
            if path == '/live/status':
                return self._send_json({
                    'ok': True, 'time': time.time(),
                    'cache': {k: c[0] for k, c in list(CACHE.items())[:10]},
                })
            if path == '/proxy/' or path.startswith('/proxy/'):
                target = urllib.parse.unquote(path[len('/proxy/'):])
                if not target:
                    return self._send_bytes(b'proxy: missing url', 'text/plain', 400)
                body, ctype = proxy_fetch(target)
                return self._send_bytes(body, ctype or 'application/octet-stream')
        except Exception as e:
            return self._send_json({'ac': [], 'error': str(e)})
        return super().do_GET()

    def do_POST(self):  # noqa: C901
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        try:
            if path == '/save/fraseologia':
                ln = int(self.headers.get('Content-Length') or 0)
                raw = self.rfile.read(ln) if ln > 0 else b''
                data = json.loads(raw.decode('utf-8'))
                if not isinstance(data, dict) or 'readbacks' not in data:
                    return self._send_json({'ok': False, 'error': 'JSON inválido: falta "readbacks"'}, 400)
                target = os.path.join(ROOT, 'fraseologia_editada.json')
                tmp = target + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, target)
                return self._send_json({'ok': True, 'archivo': 'fraseologia_editada.json',
                                        'readbacks': len(data.get('readbacks', []))})
            if path == '/save/datos_offline':
                ln = int(self.headers.get('Content-Length') or 0)
                raw = self.rfile.read(ln) if ln > 0 else b''
                data = json.loads(raw.decode('utf-8'))
                if not isinstance(data, dict):
                    return self._send_json({'ok': False, 'error': 'JSON inválido'}, 400)
                target = os.path.join(ROOT, 'datos_offline.json')
                tmp = target + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, target)
                total = sum(len(data.get(k, [])) for k in ('mrvac', 'zonas', 'sectores', 'awy', 'rwy', 'fixes', 'star'))
                return self._send_json({'ok': True, 'archivo': 'datos_offline.json',
                                        'entradas': total})
            return self._send_json({'ok': False, 'error': 'endpoint desconocido: ' + path}, 404)
        except Exception as e:
            return self._send_json({'ok': False, 'error': str(e)}, 500)

    def log_message(self, fmt, *args):
        sys.stderr.write('[server] %s - %s\n' % (self.address_string(), fmt % args))

if __name__ == '__main__':
    os.chdir(ROOT)
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'[LIVE-SERVER] sirviendo {ROOT} en http://localhost:{PORT}')
    print('[LIVE-SERVER] endpoints: /proxy/, /live/fr24, /live/chile, /live/opensky, /live/airnav')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n[LIVE-SERVER] detenido')
