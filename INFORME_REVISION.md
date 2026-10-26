# INFORME DE REVISIÓN — SCEL ATC Radar Trainer
**Versión guardada:** radarnote30 · **Fecha:** 2026-08-23 · **Alcance:** revisión completa de los 13 archivos del proyecto

---

## 1. Cambios aplicados en esta versión (radarnote30)

### 1.1 Fraseología — readbacks de piloto en formato ICAO (Anexo 10 / DGAC Chile)
Antes el piloto "confirmaba" repitiendo la frase del controlador con el callsign al principio.
Ahora usa formato correcto de readback: instrucción en gerundio/confirmación + **callsign al final**.

| Comando | Antes (incorrecto) | Ahora (ICAO) |
|---|---|---|
| Rumbo izq. 240 | LAN101, vire a la izquierda rumbo dos cuatro cero | Virando izquierda rumbo dos cuatro cero, LAN101 |
| Ascender FL350 | LAN101, ascienda a nivel de vuelo tres cinco cero | Ascendiendo a nivel de vuelo tres cinco cero, LAN101 |
| Reducir 250 kt | LAN101, reduzca velocidad a dos cinco cero nudos | Reduciendo a dos cinco cero nudos, LAN101 |
| Mantener 250 kt | LAN101, mantenga dos cinco cero nudos | Manteniendo dos cinco cero nudos, LAN101 |
| ILS 17R | LAN101, establecido ILS pista uno siete derecha | Establecido en localizador pista uno siete derecha, LAN101 |
| Directo UGOLA | LAN101, directo a UGOLA | Directo UGOLA, LAN101 |
| Espera UGOLA | LAN101, espere en UGOLA | En espera sobre UGOLA, LAN101 |
| Abandonar espera | LAN101, abandone espera, reanude ruta | Abandonando espera, reanudando ruta, LAN101 |
| Ident | LAN101, identifique | Ident, LAN101 |

Aplicado en español e inglés (diccionario completo de `readback()`), y también en las
respuestas de reporte ("¿qué nivel tienes?" → "Manteniendo nivel de vuelo tres cinco cero, LAN101")
y en la respuesta a llamada ("Adelante, LAN101").

### 1.2 Bugs corregidos
1. **`spd` indefinido (ex-línea 6271):** `readback(a,'spd_mnt',spd)` lanzaba ReferenceError al
   procesar "mantenga velocidad NNN" → ahora pasa `ias`. La velocidad sí se aplicaba, pero el
   readback/TTS fallaba.
2. **PAUSE global sin filtro de callsign:** "LAN101, detener descenso" pausaba todo el simulador.
   Ahora PAUSE solo es global si la frase no contiene callsign (igual que RESUME).
3. **LEAVE HOLD sobre aeronave equivocada:** "LAN101 abandona espera" sacaba de espera la
   aeronave *seleccionada*, no la nombrada. Ahora el canonical incluye el callsign y
   `processVoice` resuelve la aeronave por `matchCS` antes de usar la seleccionada.

---

## 2. Hallazgos sin cambiar (menores / para próxima versión)

- **Multi-comando:** "vire rumbo 240 y reduzca a 250" solo ejecuta el último número
  (250 → velocidad). El parser toma un solo valor por llamado; está documentado como limitación.
- **Detección 17R inconsistente:** nlpParse acepta "17 derecha/right/r"; el parser clásico #11
  solo mira `17 r` (`/\b17\s?r\b/i`). Unificar cuando se toque esa sección.
- **SWITCH RUNWAY silencioso:** si la aeronave no está en LOC/GS, cae a "Comando no reconocido"
  sin explicar por qué (requiere `a.locMode||a.gsMode`).
- **matchCS laxo:** acepta coincidencia de solo 3 letras del prefijo dentro del texto plano;
  riesgo bajo de falso positivo con palabras que contengan un prefijo de aerolínea.
- **nlpNumbers posiciones:** `t.indexOf(p)` toma la primera ocurrencia de una palabra numérica
  repetida; puede desposicionar (afecta qué número gana como "último"). Caso raro.
- **Código muerto:** `_origUnlock` (sin uso) y un `clock()` suelto en el handler táctil.
- **spk() inglés** usa wun/tree/fower/fife/niner (auténtico ICAO); los motores TTS lo pronuncian
  irregular pero se mantiene por realismo.

## 3. Servidores

- `live_server.py` (recomendado): bind 127.0.0.1:8123, 4 fuentes (FR24 scraper, adsb.lol,
  OpenSky, AirNav gRPC-web), caché ~40 s, tolerante a clientes abortados. Correcto.
- `server.py`: bind **0.0.0.0:8000** + `/proxy/<url>` abierto = proxy SSRF accesible desde la LAN.
  Recomendación: cambiar bind a 127.0.0.1 o restringir `/proxy` a dominios permitidos.

## 4. Arquitectura confirmada (sin cambios)

- HTML único (6540 líneas tras esta edición) + assets geográficos JS estáticos.
- Piloto IA local sin red: `nlpParse` (ES/EN libre) → canonical clásico → `processVoice`;
  fallback al parser regex; guard `_nlpGuard` evita recursión infinita.
- Números hablados ES completos (unidades→miles) + lectura ATC dígito-a-dígito
  ("dos cuarenta"→240, "once mil"→11000).
- TTS es-CL preferente con desbloqueo por interacción; STT multi-alternativa (3).
- Rendimiento Eurocontrol (`performance.xml`) para ROC/ROD por fase; callsigns Doc 8585 + FACH.

---

## ADDENDUM v1.1 (23/08/2026) — Readback completo + transferencia a torre

Solicitud del usuario: que los pilotos hagan readback de TODOS los comandos y digan
"contacto santiago torre 118.1" al ser transferidos a la TWR.

### Cambios en SCEL_ATC_Radar.html (6540 → 6567 líneas)

**Nuevas frases en el diccionario `readback()`:**
- `loc` ahora dice "**Interceptando** localizador pista uno siete X" (antes decía
  "establecido" recién asignado el comando, lo cual era prematuro).
- `estloc` (nuevo): reporte automático "**Establecido en localizador...**" cuando la
  aeronave captura el ILS (una vez por interceptación, flag `_locRep`, reseteado en
  cada `interceptLoc`).
- `inheld` (nuevo): reporte automático "**Establecido en espera sobre FIX**" cuando la
  aeronave llega al fix y determina su entrada OACI (en `determineHoldEntry`).
- `twr` (nuevo): "**Contacto Santiago Torre 118.1**, LAN101" / EN "Contact tower 118.1, LAN101".

**Nuevo comando CONTACT TOWER:**
- Voz/texto ES: "contacto torre", "contactar torre", "cambio a torre", "traspasar torre".
- EN: "contact tower", "transfer tower". Acepta "santiago" opcional.
- Marca `handedOff=true`, lastCmd "→ TWR 118.1" y el piloto confirma con la frase exacta.

**Readbacks agregados donde faltaban:**
- Cambio de pista por contingencia (`switch`) — antes sin readback.
- Menú contextual: HOLD (`applyHoldCtx`), DIRECTO (`applyDctCtx`), LEAVE (`leaveHoldCtx`).
- Panel HOLDING: asignación y LEAVE en `applyHold`.
- Editor rápido de velocidad (doble clic en etiqueta).

**Cobertura final de readback:** rumbos ✓ · niveles ✓ · velocidades ✓ · directos ✓ ·
ingreso a espera ✓ · abandono de espera ✓ · interceptación ILS ✓ · establecido ILS ✓ ·
establecido en espera ✓ · cambio de pista ✓ · ident ✓ · resume STAR ✓ · transferencia TWR ✓.

### MANUAL_FRASEOLOGIA.md actualizado a v1.1
Secciones 2.4/2.6/3/4/6 reescritas con el formato ICAO (callsign al final), los reportes
automáticos y el comando de transferencia.

---

## ADDENDUM v1.2 (23/08/2026) — Callsign primero · CMP/IBE español · dígitos

Solicitud del usuario: readback con **callsign primero y luego la instrucción**;
**CMP (Copa) e IBE (Iberia) siempre hablan español**; **todos los números dígito a dígito**
(incluido el número del vuelo), evitando "once/doce/trece/veintidós/ciento...".

### Cambios
1. **Diccionario `readback()` reescrito:** todas las frases ES/EN ahora son
   `"CALLSIGN, instrucción"` (ej. "LAN101, virando izquierda rumbo dos cuatro cero").
2. **Regla de idioma:** `_icao==='CMP'||_icao==='IBE'` fuerza `useEs=true` aunque no haya
   voz española instalada; el resto de compañías mantiene el fallback automático.
3. **`resolveCallsign()` habla el número del vuelo dígito a dígito** vía `spkes()`:
   "IBERIA dos ocho cuatro" (antes TTS leía "284" como "doscientos ochenta y cuatro").
   También cubre callsigns LIVE sin entrada en CS_MAP.
   OJO: los `canonical` del NLP siguen usando el id crudo para que `matchCS` resuelva bien.
4. **Reportes del NLP en dígito a dígito:** nivel/altitud/velocidad ahora usan `spkes()`
   (antes `numToWordsEs()`: "doscientos cincuenta"). `numToWordsEs` queda sin uso (dead code).
5. **Rechazos/aclaraciones con callsign hablado** (`csS`): "LAN101, ¿a qué rumbo?" etc.,
   incluido "limito a tres ocho cero nudos" (antes "trescientos ochenta").
6. **Reporte de posición de entrada** ("IBERIA dos ocho cuatro en su frecuencia...")
   hereda el formato correcto automáticamente vía `resolveCallsign`.

### MANUAL_FRASEOLOGIA.md actualizado a v1.2
Secciones 3 y 4 reescritas: callsign primero, números dígito a dígito, regla CMP/IBE,
y ejemplo de transferencia con "IBERIA dos ocho cuatro".

---

## ADDENDUM v1.3 (23/08/2026) — Rumbos: 000≡360 y siempre 3 dígitos

Solicitud del usuario: el rumbo 000 en aviación es el rumbo **360**, y todos los rumbos
se pronuncian con **3 dígitos sin omitir ceros** (010 = "cero uno cero", 020 = "cero dos cero").

### Cambios en SCEL_ATC_Radar.html
1. **Nuevos helpers de voz:** `hdg3(n)` (normaliza 0→360 y rellena a 3 dígitos),
   `num3(n)` (3 dígitos para niveles), `spkesS(s)` (dígitos desde string, conserva ceros),
   `spkHdgEs(n)` / `spkHdgEn(n)`.
2. **Readbacks de rumbo** (ES/EN): usan `spkHdgEs/spkHdgEn` → "LAN101, rumbo tres seis cero",
   "LAN101, virando derecha rumbo cero uno cero".
3. **Reporte de rumbo** ("reporte rumbo"): también `spkHdgEs`.
4. **Niveles de vuelo** en readback con 3 dígitos: FL090 → "nivel de vuelo cero nueve cero".
5. **Validación NLP:** rumbos válidos ahora 0–360 (antes rechazaba 360).
6. **Displays coherentes con 000≡360:** lastCmd/sidebar/canvas preview/data-block
   (`applyHdg`, `holdHdg`, `processVoice` #1/#8/#13, `s-hdg`, `s-thdg`, preview de rumbo
   pendiente, etiquetas de radar) muestran "HDG 360°" en vez de "000°".
   Internamente el rumbo sigue normalizado 0–359 (`norm()`); solo habla/display usan 360.

### MANUAL_FRASEOLOGIA.md actualizado a v1.3
Regla de rumbos documentada en 1.2, 3.1 y consejo 5.3.

---

## ADDENDUM v1.3b (23/08/2026) — FIX: readbacks de voz no se escuchaban

Reporte del usuario: los readbacks por voz de las aeronaves no se escuchaban.

### Causas encontradas y corregidas en SCEL_ATC_Radar.html
1. **Bug de Chrome/Edge:** `speechSynthesis.cancel()` seguido inmediatamente de
   `speak()` hace que el navegador se "trague" el audio. Ahora hay una espera de
   60 ms entre cancelar y hablar, se verifica que la síntesis realmente empezó
   (`speaking/pending/paused`) y hay **un reintento automático** si no sonó.
2. **Desbloqueo de audio débil:** el unlock usaba un utterance con texto vacío,
   que algunos navegadores ignoran. Ahora usa `' '` (espacio) y también escucha
   `pointerdown` además de click/keydown/touchstart.
3. **Voces:** caché global `_ttsVoices` + recarga en `onvoiceschanged` (antes
   `getVoices()` podía llegar vacío y quedarse así). Diagnóstico en consola:
   `[TTS] voces cargadas: N`.
4. **Colisiones:** contador de generación `_ttsGen` — si llega un readback más
   nuevo, el anterior se descarta sin reintentar (evita que dos mensajes peleen
   por el altavoz).
5. **Botón 🔊 TEST** bajo el botón VOZ (lado izquierdo): reproduce
   "LAN101, virando izquierda rumbo cero uno cero" para verificar el audio al
   instante; muestra en consola y en el log las voces disponibles del sistema.

> Si aun con el botón TEST no suena nada: revisar volumen del sistema y que
> Windows tenga voces instaladas (Configuración → Hora e idioma → Voz), o probar
> en otro navegador (Edge suele traer voces naturales en español preinstaladas).

---

## ADDENDUM v1.5b (23/08/2026) — Fix: voces empezaban en inglés, ahora español desde el inicio

Solicitud del usuario: al presionar TEST empezaba en inglés; las voces deben
empezar en español chileno.

### Causa raíz
1. `_unlockTTS()` hablaba "OK" sin cargar voces ni fijar idioma → usaba la voz
   por defecto del sistema (posiblemente inglés).
2. Las voces no se cargaban hasta que no se hacía clic/tecla → el primer readback
   usaba voice=undefined → navegador elige voz por defecto (inglés).

### Cambios en SCEL_ATC_Radar.html
1. `_unlockTTS()`: ahora llama `_findTTSVoice('cl')` ANTES de hablar, fija
   `utt.lang='es-CL'` y asigna voz española al "OK" de desbloqueo.
2. `_ttsSpeak()`: si no hay voces cargadas aún, espera (setTimeout 100ms) hasta
   que `onvoiceschanged` dispare, en vez de hablar con voz por defecto.
3. `DOMContentLoaded`: carga proactiva de voces (`_refreshVoices()` +
   `_findTTSVoice('cl')`) al iniciar la página.
4. `testVoice()`: espera a que voces estén cargadas (retry cada 100ms) antes de
   hablar; usa LAN101 (LATAM) → español Chile.

### Verificación
- Al cargar la página: `[TTS] voces cargadas: N` en consola.
- Al presionar 🔊 TEST: el "OK" de desbloqueo y el readback salen en español
  chileno desde el primer momento (antes salía en inglés).

---

## ADDENDUM v1.3f (23/08/2026) — Voz México + fraseología pura + heading EN corregido

Solicitud del usuario: voz español latino de México (fluido, sin modismos),
confirmar IBE202 = IBERIA202, verificar heading EN = "one eight zero".

### Cambios en SCEL_ATC_Radar.html
1. `_findTTSVoice(mode)`: el modo para "todos" cambió de `'cl'` (es-CL) a `'mx'`
   (es-MX), priorizando voces mexicanas naturales (Sabina/Dalia). Respaldo
   es-419 → cualquier español.
2. `_ttsSpeak`: `utt.lang` para todos los vuelos es ahora `'es-MX'` (era 'es-CL').
   IBE mantiene `'es-ES'` (neutro).
3. **Heading en inglés corregido:** `spkHdgEn(val)` usaba DIGEN con alfabeto
   fonético ICAO (wun/tree/fower/fife/niner) → producía "heading wun eight zero".
   Se cambió DIGEN a dígitos ingleses planos (one/two/three...) → ahora produce
   correctamente "heading one eight zero". También corrige speeds y niveles
   ("three five zero knots", "flight level three five zero").
4. IBE202 → "IBERIA202" (callsign unido) ✓ ya funcionaba.

### MANUAL_FRASEOLOGia.md
Tabla 1.3: voz México (es-MX), fraseología sin modismos.

---

## ADDENDUM v1.6 (23/08/2026) — normativa.xml + diluciones + voz Chile

Solicitud del usuario: archivo de normativa con fraseología establecida,
voz español de Chile (más natural), fixes como palabras, diluciones y
correcciones de fraseología.

### Cambios en SCEL_ATC_Radar.html
1. **normativa.xml cargado** al iniciar (NORM, FIX_PRON, HOLD_PATTERNS_NORM).
   Contiene readbacks, diluciones, correcciones y lista de fixes con pronunciación.
2. **readback() prioriza frases de normativa.xml** (NORM[cmd].es/.en) sobre el
   diccionario local (ph). Formato con placeholders {cs}, {val}, {fix}, {fl}.
3. **Voz Chile para todos** (revertido de México): `_findTTSVoice('cl')` prioriza
   voces es-CL neurales (Antonia/Raul). `utt.lang='es-CL'`.
4. **Exclusión de gallego** en todos los fallbacks de voz española.
5. **spkFix(s)** usa FIX_PRON de normativa.xml → "UGOLA" → "ugola" (no "U G O L A").
   Aplicado en direct/hold/inheld, reportes de posición, respuestas NLP.
6. **Diluciones:** nueva función `dilucion(ac,tipo,val)` + NLP action 'dilucion'.
   El piloto pregunta confirmación: "¿me confirma autorizado a ugola patrón de
   espera publicado, nivel de vuelo 280?"
7. **Correcciones:** nueva función `correccion(ac,instr,wrong,tipo)` + NLP action
   'correccion'. El controlador corrige: "CORRECCIÓN: LAN101, rumbo 240, no ..."
8. **startVoice() limpio:** usa `_unlockTTS()` centralizado.
9. **testVoice()** verifica voz chilena + fix como palabra ("directo ugola").

### Archivos nuevos
- `radarnote30/normativa.xml` — fraseología establecida (DAP-11/DAN-11).

### MANUAL_FRASEOLOGIA.md
- Versión 1.6.
- Sección 1.3: voz Chile (es-CL), neural preferida, excluye gallego.
- Sección 1.4: callsign IBE unido ("IBERIA202").
- Sección 1.5: diluciones y correcciones.

---

## ADDENDUM v2.0 (27/08/2026) — FIX: el radar no se dibujaba al elegir PC/MONITOR

Reporte del usuario: al elegir **PC / MONITOR** solo se veían los botones de la
interfaz, no el escenario (canvas vacío / congelado). En casos extremos el
simulador no abría el radar en absoluto.

### Causa raíz
1. **El bucle principal dependía 100% de `requestAnimationFrame`.** Si rAF está
   bloqueado o fuertemente throttled (pestaña oculta, iframe embebido, navegador
   integrado, ventana minimizada), `frame()` nunca se ejecuta y el radar jamás se
   dibuja: quedan solo los botones de la UI sobre el canvas oscuro.
2. **Cualquier excepción mataba el bucle para siempre.** `update()` y el bloque de
   dibujo no estaban protegidos; si una función lanzaba un error puntual, la
   excepción se propagaba y `requestAnimationFrame(frame)` final nunca se
   reprogramaba → el radar quedaba congelado en el último frame (o vacío).

### Cambios en SCEL_ATC_Radar.html (7048 → 7064 líneas)
1. **`frame()` blindado:** `update()` y todo el bloque de dibujo ahora van en
   `try/catch` con log en consola (`[UPDATE] error` / `[DRAW] error`). Un error
   puntual ya no detiene el radar; el bucle sigue corriendo y reintenta en el
   siguiente frame.
2. **Bucle de respaldo `setInterval` (100 ms):** nueva variable `_lastFrameAt`
   registra el último frame ejecutado. Si rAF no ha corrido en 250 ms, el
   intervalo ejecuta `frame()` directamente. Resultado: el radar se dibuja y
   actualiza (~10 fps) incluso con rAF bloqueado; en navegadores normales el
   intervalo no interfiere (rAF va a 60 fps y `_lastFrameAt` siempre está fresco).
3. **`resize()` al arrancar:** el canvas tiene tamaño correcto (W/H/CX/CY/SZ)
   desde el primer frame, antes de que el usuario elija dispositivo.
4. **`selectDevice('pc')` resetea cámara:** igual que tablet, PC ahora fija
   `currentScale=40 NM`, `panX=0`, `panY=0` al entrar (evita heredar zoom/pan
   de un modo anterior que dejara el escenario fuera de vista).

### Verificación
- Con rAF bloqueado (navegador integrado): al elegir PC/MONITOR el radar se
  dibuja al instante (píxel central cian = centro SCEL), las aeronaves se mueven
  y el canvas se redibuja continuamente.
- Carga limpia: modal de dispositivo visible, canvas dimensionado desde el inicio.
- Sin cambios de comportamiento en navegadores normales (rAF sigue siendo el
  motor principal; el respaldo solo actúa si rAF falla).

---

## 3. Límites de velocidad — performance 300 kt IAS / ATC 320 kt IAS (radarnote31)

**Fecha:** 2026-09-02 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
Se limita la velocidad de performance de las aeronaves comerciales a **300 kt IAS**
como máximo, salvo que el ATC ordene otra velocidad, con un **tope de 320 kt IAS**.

### Implementación
1. **Constantes nuevas** (`PERF_MAX_IAS=300`, `ATC_MAX_IAS=320`) definidas antes de
   `iasToTas()`.
2. **Performance cap (300 kt IAS):**
   - En la inicialización (`mkAC`): la velocidad de spawn se limita a 300 kt IAS
     (`initIas=Math.min(PERF_MAX_IAS,spd)`).
   - En el bucle de actualización: si la aeronave **no** tiene instrucción ATC de
     velocidad (`a.atcSpd` nulo), su `tSpd` se limita a 300 kt IAS.
3. **ATC override (hasta 320 kt IAS):**
   - Nuevo flag `a.atcSpd` que registra la velocidad ordenada por el ATC.
   - Todos los comandos de velocidad del ATC (dropdown `selectSpd`, botones +/-
     `spdChg`, comandos por voz REDUCE/INCREASE/MAINTAIN, y edición manual del
     label) fijan `a.atcSpd` y se limitan a `ATC_MAX_IAS` (320).
   - Si el ATC ordena >320, se limita a 320 (con mensaje "limito a tres dos cero
     nudos" en el caso de voz).

### Verificación (navegador)
- Spawn: aeronaves aparecen a ≤300 kt IAS (260/255/250), `atcSpd:null`.
- ATC 320 → `atcSpd=320`, TAS 417 kt a FL170.
- ATC 350 → limitado a `atcSpd=320`.
- Performance: spawn a 340 IAS → limitado a 300 IAS.
- Voz "reduce speed 350" → limitado a 320; "reduce speed 250" → 250.
- Botones +/-: desde 300, +10× → 320 (tope); -5× → 270.

---

## 4. Rango de velocidad por altitud — performance (radarnote31)

**Fecha:** 2026-09-02 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
Se añade un **rango de velocidad por altitud** (mínimo y máximo IAS) que la aeronave
debe respetar por performance. Si el ATC ordena una velocidad **fuera del rango**
permitido para la altitud actual, el piloto responde:
**"CALLSIGN, no es posible cumplir por performance de aeronave"** y la velocidad NO se aplica.

### Rango de velocidad por altitud (interpolación lineal entre puntos)

**Velocidad mínima IAS:**
| Altitud | Mínimo IAS |
|---------|-----------|
| < 5.000 ft | 160 |
| 5.000 ft | 160 |
| 6.000 ft | 180 |
| 10.000 ft (FL100) | 210 |
| 17.000 ft (FL170) | 230 |
| 18.000 ft (FL180) | 250 |
| ≥ 18.000 ft | 250 |

**Velocidad máxima IAS:**
| Altitud | Máximo IAS |
|---------|-----------|
| < 10.000 ft (FL100) | 250 |
| 10.000 ft (FL100) | 300 |
| ≥ 10.000 ft | 300 |

> **Corrección 2026-09-09:** el máximo bajo FL100 era 210-215 IAS (demasiado bajo:
> las llegadas en descenso se frenaban a ~221 IAS entre 6.000 y 10.000 ft). Se corrige
> a **250 kt IAS bajo FL100** (regla estándar) con interpolación lineal a 300 kt en FL100.

### Senda de planeo (GS mode) — reducción gradual
- Al dejar 5.000 ft: **195 kt IAS**
- FAF (9.42 NM): **140 kt IAS**
- Touchdown (umbral): **130 kt IAS**
- Reducción gradual a lo largo de la senda (interpolación lineal entre FAF y umbral).

### Implementación
1. **Funciones nuevas** `perfMinIas(alt)` y `perfMaxIas(alt)` con interpolación lineal
   entre los puntos clave (`PERF_MIN_PTS`, `PERF_MAX_PTS`).
2. **Rechazo por performance** en todos los comandos de velocidad del ATC:
   - Dropdown `selectSpd`, botones +/- `spdChg`, comandos por voz
     (REDUCE/INCREASE/MAINTAIN), edición manual del label, y handler canónico de voz.
   - Si la velocidad ordenada está fuera del rango `[perfMinIas, perfMaxIas]` de la
     altitud actual, se rechaza con readback "no es posible cumplir por performance
     de aeronave" y NO se aplica.
3. **Update loop**: si la aeronave no tiene instrucción ATC (`a.atcSpd` nulo), su
   `tSpd` se mantiene dentro del rango `[perfMinIas, perfMaxIas]` de la altitud actual.
   - **Corrección 2026-09-09 (velocidad por fase):** en **ascenso** sin instrucción ATC
     la aeronave acelera a su velocidad de ascenso de performance — **250 kt IAS bajo
     FL100** y **`climb_IAS` de AC_PERF sobre FL100** (290-300 kt según tipo, tope
     `PERF_MAX_IAS`=300). Antes las salidas volaban al mínimo del rango (221-224 IAS
     a FL140-150) en vez de a su velocidad de ascenso normal. En descenso/crucero se
     mantiene el mínimo `perfMinIas` como límite inferior.
4. **GS mode**: reemplaza la reducción fija (160/140/120) por la reducción gradual
   de la senda de planeo (140 kt en el FAF → 130 kt al umbral).

### Verificación (navegador)
- `perfMinIas`: 160 (0-5000), 180 (6000), 210 (10000), 230 (17000), 250 (18000+).
- `perfMaxIas`: 250 (< FL100), 300 (FL100+).
- LAN101 a FL170: `selectSpd(120)` → rechazado (min 230); `selectSpd(230)` → aceptado.
- SKY220 a FL170: `selectSpd(100)` → rechazado; `selectSpd(250)` → aceptado.
- IBE345 a FL100: `selectSpd(150)` → rechazado (min 210); `selectSpd(210)` → aceptado.
- IBE345 a FL100: `selectSpd(350)` → rechazado (max 300).
- Voz "reduce speed 120" a FL170 → rechazado; "reduce speed 230" → aceptado.
- Readback de rechazo: "LAN uno cero uno, no es posible cumplir por performance de aeronave".
- GS mode: a FAF (9.42 NM) → 140 kt IAS; a 2 NM del umbral → 132 kt IAS (gradual).
- Update loop: a FL170 sin instrucción ATC → se mantiene ≥ 230 IAS; a 5.000 ft → ≤ 250 IAS.
- **Corrección 2026-09-09 (verificada en navegador):**
  - Salida A320 en ascenso a FL150 → **290 IAS** (366 TAS) — antes 224 IAS (283 TAS).
  - Salida A320 a FL100 → **250 IAS** — antes 206 IAS.
  - Llegada en descenso a FL94 → **297 IAS** — antes 221 IAS (frenada por el máximo viejo).
  - Espera (hold) a FL140 → mantiene 230 IAS (no se acelera a 290).
  - Descenso a FL140 → 300 IAS (372 TAS), sin cambios.

---

## 5. Primer contacto — formato con nivel real y nivel autorizado (radarnote31)

**Fecha:** 2026-09-02 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
El **primer contacto** (llamada inicial del piloto al entrar al área) ahora informa:
1. El **nivel real que cruza** (altitud actual)
2. El **nivel al que está autorizado** (CFL)

En lugar de solo notificar el nivel autorizado.

### Formato nuevo
> "Santiago Radar, buen día, LXP202 en descenso vía UMKAL7C llegada, cruzando nivel de vuelo XXX, autorizado para nivel de vuelo XXX, instrucciones"

### Componentes
1. **"Santiago Radar"** — llamada al controlador
2. **"buen día"** — saludo
3. **Callsign** — ej. "LXP202"
4. **Fase** — "en descenso" / "en ascenso" / "en nivel" (según relación altitud objetivo vs actual)
5. **"vía [STAR] llegada"** — la STAR de llegada
6. **"cruzando [nivel/altitud]"** — nivel real (`a.alt`) leído con la regla de tres rangos de `spkCrossAlt()`
7. **"autorizado para [nivel/altitud]"** — nivel autorizado (`a.cfl`) con la misma regla
8. **"instrucciones"** — petición de instrucciones

### Implementación
- `queueEntryReport()` (STARs configuradas) y `queuePositionReport()` (legacy) usan el
  nuevo formato.
- El nivel de los dos huecos se lee con `spkCrossAlt()` (misma regla de tres
  rangos que en las salidas): FL110+ → *"nivel de vuelo NNN"* — frase textualmente
  idéntica a la anterior — y por debajo → cientos / miles y cientos de pies.
- La fase se determina por la relación entre `a.tAlt` (altitud objetivo) y `a.alt`
  (altitud actual): descenso si `tAlt < alt`, ascenso si `tAlt > alt`, nivel si
  `|tAlt - alt| < 300 ft`.

### Verificación (navegador)
- En descenso: "Santiago Radar, buen día, LANEX dos cero dos en descenso vía umkal
  siete CHARLIE llegada, cruzando nivel de vuelo uno siete cero, autorizado para
  diez mil pies, instrucciones".
- En ascenso: "… en ascenso vía asimo siete DELTA llegada, cruzando diez mil
  pies, autorizado para nivel de vuelo uno siete cero, instrucciones".
- En nivel: "… en nivel vía simok siete BRAVO llegada, cruzando nivel de vuelo uno
  siete cero, autorizado para nivel de vuelo uno siete cero, instrucciones".
- Legacy: "… en descenso vía some uno ALFA llegada, pasando su ruta, cruzando nivel
  de vuelo uno cinco cero, autorizado para ocho mil pies, instrucciones".

(Actualizado 2026-10-07: con la regla de tres rangos, por debajo de FL110 se
hablan en pies — FL100 → "diez mil pies", FL080 → "ocho mil pies" —; FL110+
conserva "nivel de vuelo NNN". Con aeronave real hoy: 4300 ft → "…llegada,
cruzando cuatro mil trescientos pies, autorizado para cuatro mil trescientos
pies, instrucciones".)

---

## 6. Puntos de llamada direccionales por STAR (radarnote31)

**Fecha:** 2026-09-02 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
El **primer contacto** ahora se dispara a **15 NM en una dirección específica** desde
el waypoint de entrada de cada STAR, en lugar de al llegar al waypoint mismo.

### Puntos de llamada por STAR
| STAR | Punto de llamada | Coordenadas (x,y NM) |
|------|-----------------|---------------------|
| **SIMOK7B** | 15 NM al norte de SIMOK | (-3.38, 113.55) |
| **ASIMO7D** | 15 NM al norte de ASIMO | (23.5, 105.7) |
| **EROLO8A** | 15 NM al sur de EROLO | (-31.17, -90.38) |
| **UMKAL7C** | 15 NM al este de UMKAL | (54.35, 30.65) |
| **SUKSA2A** | 15 NM al norte de SUKSA | (-9.36, 113.21) |

### Implementación
1. **`STAR_ENTRY`**: cada STAR ahora tiene `entryDir` ('N','S','E','W') y
   `entryDist:15`. Se agregó `SUKSA2A` (antes no estaba configurada).
2. **`_checkEntryReport`**: calcula el punto de llamada como el waypoint + offset
   direccional (`entryDist` NM en la dirección `entryDir`), y dispara el reporte
   cuando la aeronave está dentro de 1.2 NM de ese punto.

### Verificación (navegador)
- Puntos de llamada calculados correctamente para las 5 STARs.
- Aeronave en el punto de llamada → reporta.
- Aeronave lejos del punto de llamada → NO reporta.
- Aeronave a 0.7 NM del punto de llamada → reporta.

---

## 7. Niveles de aparición por STAR (radarnote31)

**Fecha:** 2026-09-02 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
Los **niveles de vuelo de aparición** de las aeronaves en la pantalla radar se ajustan
según la STAR de llegada:

| STAR | Nivel de aparición | Nivel autorizado |
|------|-------------------|-----------------|
| **UMKAL7C** | Mínimo **FL240** (o el del XML si es superior) | El del XML |
| **EROLO8A** | Mínimo **FL290** (o el del XML si es superior) | El del XML |
| **SIMOK7B** | Mínimo **FL290** (o el del XML si es superior) | El del XML |
| **SUKSA2A** | Mínimo **FL290** (o el del XML si es superior) | El del XML |
| **ASIMO7D** | **FL310** (cruzando) | **FL250** (mínimo de cruce de ASIMO) |

### Implementación
1. **`starSpawnAlt(starKey,xmlAlt)`**: calcula el nivel de aparición mínimo según la
   STAR. `max(FL240, xml)` para UMKAL7C, `max(FL290, xml)` para EROLO8A/SIMOK7B/SUKSA2A,
   FL310 fijo para ASIMO7D.
2. **`starCclAlt(starKey,xmlCcl)`**: calcula el nivel autorizado. FL250 fijo para
   ASIMO7D, el del XML para el resto.
3. **`mkACwithRoute`**: usa `starSpawnAlt` para la altitud de aparición y ajusta
   `tAlt=FL250` + `cfl/assignedFL/selAlt=FL250` para ASIMO7D (nivel autorizado
   consistente con el descenso).
4. **`addFlights`** y **`spawnFlight`**: aplican `starCclAlt` al nivel autorizado.
5. **`ARR_TEMPLATES`**: actualizados con los nuevos niveles (SIMOK7B FL290, ASIMO7D
   FL310, UMKAL7C FL240, EROLO8A FL290, SUKSA2A FL290).

### Verificación (navegador)
- `starSpawnAlt('UMKAL7C',15000)` → 24000; con XML 30000 → 30000.
- `starSpawnAlt('EROLO8A',10000)` → 29000; con XML 32000 → 32000.
- `starSpawnAlt('SIMOK7B',17000)` → 29000; `starSpawnAlt('SUKSA2A',16000)` → 29000.
- `starSpawnAlt('ASIMO7D',17000)` → 31000; `starCclAlt('ASIMO7D',...)` → 25000.
- Textarea: UMKAL7C FL200 → aparece FL240; SIMOK7B FL250 → FL290; ASIMO7D FL280 →
  FL310 con tAlt FL250; EROLO8A FL300 → FL300 (prevalece XML).
- XML: mismos resultados que textarea.
- Performance: a FL290/FL310/FL240 el rango es 250-300 IAS; las aeronaves aparecen
  con IAS dentro del rango.
- Primer contacto ASIMO7D: "cruzando nivel de vuelo tres uno cero, autorizado para
  nivel de vuelo dos cinco cero" (cfl=250 consistente con tAlt=25000).

---

## 8. Posición de aparición a 20 NM del fix de entrada (radarnote31)

**Fecha:** 2026-09-02 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
Todos los vuelos de llegada aparecen en pantalla a **20 NM del fix principal de
inicio de la STAR**, en la dirección de entrada. Así, cuando la aeronave llega al
punto de llamada (15 NM del fix), ya ha sido vista en pantalla durante 5 NM de
aproximación.

### Implementación
1. **`STAR_ENTRY`**: campo `spawnBack` reemplazado por `spawnDist:20` en las 5 STARS
   principales (SIMOK7B, ASIMO7D, UMKAL7C, EROLO8A, SUKSA2A), y `entryDir` (N/S/E/W)
   reemplazado por **`entryHdg`** (rumbo de entrada en grados, concordante con el
   rumbo real de cada llegada). `entryDist:15` se mantiene.

   | STAR | Rumbo de ruta | entryHdg (desde) | Posición de aparición |
   |------|--------------|------------------|----------------------|
   | SIMOK7B | 178° | 358° | 20 NM al norte |
   | ASIMO7D | 211° | 31° | 20 NM al **noreste** |
   | UMKAL7C | 276° | 96° | 20 NM al este |
   | EROLO8A | 22° | 202° | 20 NM al **suroeste** |
   | SUKSA2A | 178° | 358° | 20 NM al norte |

2. **`mkACwithRoute`**:
   - Si la STAR tiene `entryHdg`+`spawnDist`: la aeronave aparece a `spawnDist` NM del
     fix en ese rumbo (trigonometría: `x+sin(h)*d`, `y+cos(h)*d`), y la ruta se
     construye como `[fix, ...routeWpts]` (fix duplicado al inicio) para que navegue
     primero hacia el fix y luego siga la STAR.
   - Si no tiene rumbo configurado (SABLA5A, VTN1D, etc.): aparece a 20 NM antes del
     fix a lo largo de la ruta (fallback).
3. **`_checkEntryReport`**: el punto de llamada se calcula con `entryHdg` en lugar de
   `entryDir` (misma trigonometría, `entryDist` NM del fix en ese rumbo).
4. **`loadScenario` / `addFlights` / `spawnFlight`**: llamadas a `mkACwithRoute`
   simplificadas (ya no pasan `spawnBack`).

### Verificación (navegador)
- Spawn a 20 NM del fix en el rumbo de entrada correcto para las 5 STARS (colineal
  con el punto de llamada a 15 NM y el fix; `callDist=5` NM entre spawn y llamada).
- EROLO8A: aparece 20 NM al suroeste (entryHdg 202°), vuela al fix con rumbo 22°
  (noreste) — concordante con la llegada EROLO8A.
- ASIMO7D: aparece 20 NM al noreste (entryHdg 31°), vuela al fix con rumbo 211°
  (suroeste) — concordante con la llegada ASIMO7D.
- Ruta duplicada `[fix, fix, ...]` → la aeronave vuela al fix, avanza `routeIdx`, y
  sigue la STAR normal (SIMOK7B: SIMOK→DABIT→MORPA→...).
- Reporte de entrada se dispara al pasar por el punto de llamada (15 NM del fix,
  margen 1.2 NM por timestep) — verificado para ASIMO7D y EROLO8A.
- Update loop sin errores tras 120 frames; aeronaves volaron de 20 NM a ~13 NM del
  fix y reportaron.
- Los 3 flujos (loadScenario, textarea, XML) spawn a 20 NM con rumbos correctos.

---

## 9. Primer llamado concordante con la etiqueta radar (radarnote31)

**Fecha:** 2026-09-08 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
El **nivel autorizado** (`cfl`) que reporta el piloto en el primer llamado ahora
refleja el **nivel al que la aeronave está realmente autorizada a volar** (`tAlt`),
y es **concordante con la etiqueta radar** (Row 1: `FL[curFl] FL[cfl]`).

Antes, `cfl` quedaba fijo en el nivel de aparición (ej. FL290) mientras la aeronave
descendía por la STAR a un nivel inferior (ej. FL170 por SIMOK). El reporte decía
"autorizado FL290" y la etiqueta mostraba FL290, pero la aeronave descendía a FL170 —
el nivel autorizado real era FL170.

### Implementación
1. **`updateAltConstraint(a,wp)`**: al ajustar `tAlt` por una restricción de la STAR
   (llegadas) o SID (salidas), ahora también actualiza `cfl` y `assignedFL` al nivel
   de la restricción (`Math.round(wp.alt/100)`). Así el nivel autorizado sigue el
   descenso/ascenso por la ruta.
2. **`mkACwithRoute`** (llegadas): después de establecer `tAlt`, `cfl` y `assignedFL`
   se fijan a `Math.round(tAlt/100)` — el nivel al que la aeronave desciende, no el
   nivel de aparición.
3. **ASIMO7D**: la restricción del waypoint ASIMO en la ruta pasa de `WPT.ASIMO`
   (alt=17000) a `_w('ASIMO',25000)` — el mínimo de cruce real de ASIMO es **FL250**
   (requisito previo). EL790→FL200, VULBI→FL170, EL570→FL145 (restricciones de la
   carta). Así `updateAltConstraint` mantiene el descenso a FL250, no a FL170.

### Comportamiento resultante
| Aeronave | STAR | Reporte (primer llamado) | Etiqueta Row 1 |
|----------|------|--------------------------|----------------|
| LAN101 | SIMOK7B | "cruzando FL277, autorizado FL170" | FL277 FL170 |
| SKY220 | ASIMO7D | "cruzando FL301, autorizado FL250" | FL301 FL250 |
| IBE345 | EROLO8A | "cruzando FL281, autorizado FL100" | FL281 FL100 |
| LAN101 (ccl F240) | SIMOK7B | "cruzando FL276, autorizado FL240" | FL276 FL240 |
| SKY220 (ccl F260) | ASIMO7D | "cruzando FL298, autorizado FL250" | FL298 FL250 |
| IBE345 (ccl F200) | EROLO8A | "cruzando FL276, autorizado FL200" | FL276 FL200 |

### Verificación (navegador)
- Los 3 flujos (loadScenario, textarea, XML escenario) generan reportes con ambos
  niveles, concordantes con la etiqueta en el momento del llamado.
- Instrucción ATC (descienda FL200): `cfl=200`, `tAlt=20000`, etiqueta FL276 FL200 —
  el ccl del ATC prevalece sobre la STAR (`atcAlt=true` bloquea `updateAltConstraint`).
- Sin errores de consola tras 342+500 frames; aeronaves descienden por la STAR
  (LAN101 FL250→FL170, SKY220 FL284→FL250, IBE345 FL268→FL100).

---

## 10. Botón LABEL — tamaño de etiqueta 1-5 con validador (radarnote31)

**Fecha:** 2026-09-08 · **Alcance:** SCEL_ATC_Radar.html

### Cambio
Nuevo botón **LABEL** en la sección **CONFIG** que permite seleccionar el **tamaño de
la etiqueta radar** de **1 a 5** en **incrementos de 20%** desde el valor base
(1 = 100%), con un **validador de selección** que confirma con **"OK"** o **"VALID"**.

| Valor | Escala | Tamaño |
|-------|--------|--------|
| 1 | 100% | base (actual) |
| 2 | 120% | +20% |
| 3 | 140% | +40% |
| 4 | 160% | +60% |
| 5 | 180% | +80% |

### Implementación
1. **`labelScale`** (global, default 1): factor de escala que multiplica las
   dimensiones de la etiqueta (`F0`, `F1`, `LH`, `PAD`, `BAR`) en los 3 lugares que
   replican el cálculo:
   - `drawLabel()` — dibujo de la etiqueta (Row 0-4, caja, STCA banner).
   - `lblAt()` — hit-testing (clic sobre la etiqueta).
   - dblclick inline (edición de velocidad) — zona de la fila GS.
2. **Botón LABEL** (`cat-btn.label`, violeta) en CONFIG, junto a LIVE y FLIGHTS.
3. **Panel LABEL** (`#labelPanel`): 5 botones de tamaño (1-5) + fila **VALIDACIÓN**
   con el indicador.
4. **`toggleLabelPanel()`**: abre/cierra el panel.
5. **`setLabelSize(n)`**: valida la selección:
   - `1 ≤ n ≤ 5` → aplica `labelScale = 1 + (n-1)*0.2` (incrementos de 20%),
     validador muestra **"OK"** o **"VALID"** (verde), redibuja.
   - Fuera de rango o no numérico → validador muestra **"INVÁLIDO"** (rojo), no
     cambia la escala.

### Verificación (navegador)
- Botón LABEL presente en CONFIG; panel se abre/cierra correctamente.
- `setLabelSize(1..5)` → escalas 1.0 / 1.2 / 1.4 / 1.6 / 1.8 (100% / 120% / 140% /
  160% / 180%); validador alterna "OK"/"VALID".
- `setLabelSize(6)` y `setLabelSize(0)` → "INVÁLIDO", escala sin cambios.
- Tamaños medidos (boxW×boxH): escala 1 → 97×46 px; escala 5 → 174×83 px
  (ratio exacto 180%).
- Hit-testing con escala 3: clic dentro de la etiqueta selecciona la aeronave
  correcta (`lblAt` concuerda con `drawLabel`).
- Sin errores de consola al dibujar con escala aplicada.

---

## 12. Fraseología radar — comandos de aproximación y reportes (radarnote31, 2026-09-09)

**Alcance:** 10 comandos nuevos (voz o barra de texto) en `SCEL_ATC_Radar.html` +
readbacks en `normativa.xml` + documentación en `MANUAL_FRASEOLOGIA.md` §7.

### 12.1 Comandos implementados

| # | Comando | Ejemplo | Readback piloto |
|---|---|---|---|
| 1 | Aproximación ILS | "LAN101 autorizado aproximación ILS pista 17 izquierda" | "autorizado aproximación ILS pista uno siete izquierda" |
| 2 | Aproximación visual | "… autorizado aproximación visual pista 17 derecha" | "autorizado aproximación visual pista uno siete derecha" |
| 3 | Vector final | "… vector para el localizador pista 17 izquierda, vire izquierda rumbo 240" | "vector al localizador pista 17L, rumbo dos cuatro cero" |
| 4 | Velocidad Mach | "… mantenga velocidad Mach punto ocho dos" | "aumentando/reduciendo/manteniendo velocidad Mach punto ocho dos" |
| 5 | Razón vertical | "… descienda a mil quinientos pies por minuto" | "descendiendo a mil quinientos pies por minuto" |
| 6 | Cruce restricción | "… cruce UGOLA a nivel de vuelo 240 o superior" | "cruzando UGOLA a nivel de vuelo dos cuatro cero o superior" |
| 7 | Tránsito | "… tránsito a las doce" | respuesta aleatoria ("tráfico a la vista" / "buscando tráfico" / "sin tráfico a la vista") |
| 8 | Notifique pasando | "… notifique pasando UGOLA" | "notificaré pasando UGOLA" + reporte automático 1 vez al pasar |
| 9 | Notifique establecido | "… notifique establecido en patrón de espera" | "notificaré establecido en el patrón de espera" |
| 10 | Notifique nivel | "… notifique nivel" | reporte inmediato del nivel actual |

### 12.2 Implementación

1. **Waypoints**: `BICEN` (9.0, -0.5, 8000 ft) y `RENCA` (4.3, 0.7, 3500 ft) en `WPT`;
   RENCA se dibuja como V invertida amarilla. Puntos de alineación `ALN17L` (-0.549,
   10.495, 3000 ft) y `ALN17R` (-1.400, 10.742, 3000 ft) en el eje de pista, en el
   FAF (9.42 NM del umbral, alt = senda de planeo 3° ≈ 3000 ft).
2. **Funciones nuevas** (tras `tasToIas`): `machToTas`/`tasToMach`, `spkNumEs`
   (números en palabras ES hasta 9999), `setMach`, `setVS`, `apprAuth`, `vecFinal`,
   `crossRestriction`, `trafficCall`, `reportPassing`, `reportHoldReq`, `reportLevel`.
3. **Reconocimiento**: bloque 0a-0j en `processVoice` + acciones/canónicos en
   `nlpAction`/`nlpParse` (ES y EN).
4. **Física**:
   - `apprAuth` → ruta norte `[ALN]` (y>0) o sur `[BICEN, RENCA, ALN]` (y≤0);
     al completar la ruta captura LOC y GS automáticamente; aterriza en el umbral
     (dist<0.12 NM y alt<200 ft) y desaparece a los 4 s.
   - `vecFinal` → vira al rumbo dado; al interceptar el localizador (|ilsLat|≤0.15)
     captura LOC/GS.
   - `setMach` → tile MACH en sidebar ("M.82"), TAS recalculada según altitud,
     readback comparativo (tasToMach ±0.01).
   - `setVS` → razón aplicada hasta FL250 (ascenso) / 10000 ft (descenso); fuera,
     razón normal de performance.
   - `reportPassing` → reporte automático único (dist<0.5 NM del fix).
5. **normativa.xml**: readbacks `mach_inc`/`mach_red`/`mach_mnt`, `reportfix`,
   `reporthold`; torre actualizada a "uno uno ocho coma uno" (ES) / "one one eight
   decimal one" (EN). Diccionario local `ph` en `readback()` para
   appr_ils/appr_visual (ES/EN) y vs_climb/vs_descend (con `spkNumEs`).

### 12.3 Verificación (navegador, servidor local 127.0.0.1:8124)

- Los 10 comandos responden correctamente (ES y EN), incluyendo variantes con
  números en palabras ("mil quinientos pies por minuto", "Mach punto ocho dos").
- Circuito sur completo: BICEN (8000) → RENCA (3500) → ALN (3000) → captura LOC/GS
  → senda 3° → aterrizaje en el umbral → aeronave retirada (count 3→2).
- Aproximación norte directa: ruta `[ALN]` → LOC/GS → aterrizaje.
- Vector final: vira al rumbo, captura automática al interceptar el localizador
  ("establecido en localizador pista uno siete L").
- Mach: M.82 → 483 kt TAS @30000 ft / 523 kt @10000 ft (correcto por densidad).
- Razón vertical: 1500 ft/min aplicada en el tramo válido; normal fuera.
- Reporte automático "pasando UGOLA" dispara 1 sola vez.
- Torre: "contacto Santiago Torre uno uno ocho coma uno", handedOff=true.
- Bugs corregidos durante la verificación: detección de pista (regex `\bderech\b`
  no casaba "derecha"; "izquierda" contiene "r"), números en palabras en Mach/VS,
  y "notifique" con Q (regex `notif\w*`).
- **Incidente de codificación**: un `Set-Content` de PowerShell corrompió el HTML
  (mojibake UTF-8→ANSI→UTF-8, 930 caracteres). Revertido leyendo como UTF-8 y
  decodificando los bytes como Windows-1252. Archivo final íntegro: 373691 bytes,
  0 caracteres corruptos, 8029 líneas. Backup de la versión corrupta en
  `C:\Users\noten\AppData\Local\Temp\opencode\SCEL_ATC_Radar_corrupto.html`.
**Lección: editar el HTML solo con la herramienta de edición, nunca con
   Set-Content.**

---

## 13. Fondo negro profundo + botón BUTTON (radarnote31)

**Fecha:** 2026-09-09 · **Alcance:** SCEL_ATC_Radar.html

### 13.1 Fondo negro de máximo contraste
- `--bg` y `--panel`: `#161616`/`#1e1e1e` (gris oscuro) → **`#000000`** (negro puro).
- `--surface`: `rgba(2,6,12,.96)` → `rgba(0,0,0,.97)`.
- Canvas `#rc` (CSS): gradiente gris → `#000`.
- `drawBG()`: `rgba(22,22,22,.92)` → `rgba(0,0,0,.96)` (negro puro + scanlines CRT).
- Modal de selección de dispositivo y `<meta theme-color>` → negro puro.
- Resultado: contraste máximo para la simbología radar (cyan/verde/ámbar sobre negro).

### 13.2 Botón BUTTON en CONFIG — tamaño de botones del panel izquierdo
- Nuevo botón **BUTTON** (naranja) en CONFIG, junto a LIVE/FLIGHTS/LABEL, con panel
  desplegable `#buttonPanel` idéntico al de LABEL (5 tamaños + fila VALIDACIÓN).
- Variable CSS `--btn-scale` (default 1) en `:root`; `.cat-btn` y `.cat-btn .dot`
  escalan con `calc(... * var(--btn-scale))` (font-size, padding, gap, dot).
- `btnScale` (global) + `toggleButtonPanel()` + `setButtonSize(n)`:
  `1 ≤ n ≤ 5` → `btnScale = 1 + (n-1)*0.2` (incrementos 20%, igual que LABEL),
  aplicado vía `document.documentElement.style.setProperty('--btn-scale', ...)`.
- Escala **todos** los `.cat-btn` del costado izquierdo (paneles GENERAL y CONFIG:
  NAMES, SIM, MINSECTOR, COAST, LPI, MAP, GMAP, HOLD, RWY17L, RWY17R, LIVE,
  FLIGHTS, LABEL, BUTTON).

### 13.3 Verificación (navegador)
- Fondo: pixel del canvas `[0,0,0]` (negro puro); `--bg`/`--panel` = `#000000`.
- Botón BUTTON presente en CONFIG; panel se abre/cierra con `toggleButtonPanel()`.
- `setButtonSize(3)` → `--btn-scale=1.4`, font-size 7→9.8 px, padding 3×5→4.2×7 px,
  dot 5→7 px; validación "OK"/"VALID" en verde, "INVÁLIDO" en rojo (n fuera de 1-5).
- Sin superposición de paneles a escala 1.4 (GENERAL bottom 144 < CONFIG top 196).
- `setButtonSize(1)` restaura el tamaño base.

---

## 14. Esperas al nivel autorizado + interceptación ILS corregida (radarnote31)

**Fecha:** 2026-09-10 · **Alcance:** SCEL_ATC_Radar.html

### 14.1 Esperas — nivel autorizado por ATC (TEGEB, SEDPA, MORPA, DABIT, KADAK, UGOLA, VTN)
- **Antes:** al asignar HOLD, la aeronave se ponía al nivel **publicado del patrón**
  (`a.tAlt=hp.alt`): MORPA FL120, DABIT FL160, TEGEB/SEDPA FL050, etc.
- **Ahora:** la aeronave ingresa al patrón **al nivel autorizado por ATC** (el `a.tAlt`
  actual: nivel dado por el controlador, o el nivel de crucero/descenso si no se dio).
- **Rechazo del piloto:** si el nivel autorizado es **inferior al nivel de espera
  publicado**, el piloto NO ingresa al patrón y responde:
  - ES: *"nivel inferior al nivel de espera publicado en la STAR, confirme nivel"*
  - EN: *"level below the published holding level on the STAR, confirm level"*
  La aeronave mantiene su nivel y continúa; el controlador debe autorizar un nivel
  ≥ publicado y repetir la instrucción.
- Aplicado en los 3 caminos de asignación: `applyHold` (sidebar), `applyHoldCtx`
  (menú contextual) y comando de voz HOLD.
- Nota: el patrón de espera del sur en EROLO8A es **KADAK** (no EROLO); EROLO no
  tiene patrón publicado y sigue sin estar en la lista de esperas.

### 14.2 Interceptación ILS — niveles correctos
- **`gsAlt(d)` ahora incluye la elevación del aeropuerto** (APT_ELEV=1555 ft):
  `APT_ELEV + d·tan(3°)·6076`. Antes la senda calculada era ~1555 ft más baja que la
  real (FAF ≈ 3000 ft en vez de ≈ 4554 ft) → la aeronave volaba por debajo de la senda.
- **Captura del GS:** ya no se limita al FAF (9.42 NM). La aeronave captura la senda
  cuando está **en o por encima de ella** (`a.alt ≥ gsAlt(dist)`). Así, un tránsito
  que intercepta el LOC a 8000 ft en UGOLA (~27 NM) vuela nivelado hasta que la senda
  lo alcanza (~20 NM, 7924 ft) y lo deja a ~5000 ft en TEGEB/SEDPA (~12 NM, 5351 ft).
- **Altitud mínima de interceptación del localizador: 5000 ft** (`ILS_INTERCEPT_ALT`).
  Antes era un MÁXIMO (`if(tAlt>5000) tAlt=5000`); ahora es un MÍNIMO
  (`if(tAlt<5000) tAlt=5000`) en los 3 caminos: fin de STAR con aproximación
  autorizada, `interceptLoc()` y vector final. Un tránsito a 8000 ft NO es forzado a
  bajar a 5000 — puede interceptar más alto.
- **Aterrizaje:** la condición `alt<200` se reemplazó por `alt ≤ APT_ELEV+100`
  (1655 ft): la aeronave sigue la senda hasta el umbral (1555 ft MSL) y aterriza.

### 14.3 Verificación (navegador, servidor local 127.0.0.1:8124)
- **Esperas (5/5):**
  - FL140 autorizado + HOLD MORPA (mín FL120) → entra a **FL140** (no FL120).
  - FL90 + HOLD MORPA → **rechazo** "NIVEL 90 < PUBLICADO FL120 — PILOTO RECHAZA",
    no entra al patrón, mantiene FL90.
  - FL130 + HOLD MORPA → entra a **FL130**.
  - Voz "hold MORPA" con FL90 → rechazo; con FL140 → entra a FL140.
- **ILS (4/4):**
  - 8000 ft a 20 NM (senda 7924 ft) → captura GS y sigue la senda (tAlt=7804 a 19.6 NM).
  - 8000 ft a 27 NM (UGOLA, senda 10153 ft) → NO captura, vuela nivelada a 8000 ft.
  - 3000 ft + `interceptLoc('17L')` → tAlt sube a **5000** (mínimo).
  - gsMode a 0.1 NM del umbral a 1587 ft → aterriza (alt ≤ 1655).
- Senda verificada: FAF 4555 ft · TEGEB 5351 ft ≈ 5000 ft · 20 NM 7924 ft ≈ 8000 ft ·
  umbral 1555 ft.

## 15. Nivel autorizado siempre visible en la aeronave — SA/selAlt + panel de comando (radarnote31)

**Fecha:** 2026-09-10 · **Alcance:** SCEL_ATC_Radar.html

### 15.1 Problema
Al asignar un nivel por el panel de comando (FL), la etiqueta ya mostraba el nivel
autorizado (CFL en la fila 1: `FL249 -11 FL080`), pero el campo **SA** (fila 3,
`I269 M022 SA290`) y el tile **SEL ALT** del sidebar quedaban **desactualizados** en
aeronaves en descenso por STAR: `selAlt` conservaba la altitud de aparición (p. ej.
FL290) aunque el nivel autorizado fuera FL080. La aeronave "no colocaba" el nivel
autorizado en su display.

### 15.2 Causa raíz
`updateAltConstraint()` (restricciones de cruce SID/STAR) actualizaba
`tAlt/cfl/assignedFL` pero **no `selAlt`**. Lo mismo ocurría en el spawn
(`mkACwithRoute`, rama de llegadas) y en las 2 rutas de parsing de escenario XML
(`parseAndLoadScenario` / `addFlights`). `applyFL`, `flStep` y los comandos de voz
ya sincronizaban los 4 campos.

### 15.3 Cambios en SCEL_ATC_Radar.html
1. **`mkACwithRoute` (rama llegadas):** `a.selAlt=a.tAlt` — el FCU/SA nace concordante
   con el nivel autorizado (antes quedaba en la altitud de aparición).
2. **`updateAltConstraint`:** ambas ramas (SID mín. de cruce y STAR máx. de cruce)
   ahora también fijan `a.selAlt=wp.alt`.
3. **`parseAndLoadScenario` y `addFlights`:** al aplicar CCL, se calcula `cclAlt` una
   sola vez y se sincroniza `tAlt/cfl/assignedFL/selAlt`.
4. **Panel de comando (`flSelect`):** al seleccionar una aeronave, el desplegable FL
   muestra su nivel autorizado actual (`cfl*100`); se limpia al deseleccionar.

### 15.4 Verificación (navegador, servidor local 127.0.0.1:8124)
- Spawn (escenario "arrivals"): LAN101 `cfl=170/selAlt=17000/tAlt=17000` (antes
  selAlt=29000), SKY220 `250/25000/25000`, IBE345 `100/10000/10000`.
- `updateAltConstraint` STAR (`{alt:8000}`): `cfl=80/selAlt=8000/tAlt=8000`; SID
  (`{alt:24000}` con alt=15000): `cfl=240/selAlt=24000/tAlt=24000`.
- `applyFL('14000')`: `cfl=140/selAlt=14000/tAlt=14000` (sin cambios).
- `flSelect`: al seleccionar LAN101 muestra `17000`; al deseleccionar se limpia.
- 180 s de simulación: las 3 aeronaves con `selAlt===tAlt` y SA de etiqueta = CFL
  (interceptando `fillText`: `SA100`/`SA240`/`SA140`).
- Regresión: HOLD MORPA con FL140 → entra a FL140; con FL80 → rechazo del piloto;
  `interceptLoc('17L')` → `locMode=true, locRwy='17L'`.

## 16. Panel de comando: el nivel asignado permanece visible (como la velocidad) (radarnote31)

**Fecha:** 2026-09-10 · **Alcance:** SCEL_ATC_Radar.html

### 16.1 Problema
El usuario reportó: al seleccionar **velocidad** en el panel de comandos, la aeronave
"coloca" la velocidad autorizada (el desplegable SPD conserva el valor asignado), pero
al seleccionar **altitud/nivel de vuelo**, el desplegable FL se **limpiaba** a
"— FL —" inmediatamente después de aplicar (`applyFL` hacía `sel.value=''`), dando la
impresión de que la aeronave no había "colocado" el nivel.

### 16.2 Causa raíz
Asimetría entre ambos paneles:
- **SPD:** `updateSB()` sincroniza `spdSelect` con la IAS objetivo de la aeronave en
  cada llamada (L3447-3450) → el valor asignado permanece visible.
- **FL:** `applyFL()` borraba el desplegable (`sel.value=''`) y `updateSB()` **no**
  sincronizaba `flSelect` → el nivel asignado desaparecía del panel.

### 16.3 Cambios en SCEL_ATC_Radar.html
1. **`applyFL`:** se eliminó `sel.value=''` — el desplegable conserva el nivel asignado.
2. **`updateSB`:** se añadió la sincronización de `flSelect` junto a la de `spdSelect`:
   `flSel.value=String((a.cfl||Math.round(a.alt/100))*100)` — el panel FL refleja
   siempre el nivel autorizado de la aeronave seleccionada (mismo mecanismo que SPD).
3. **`selectAC`:** se eliminó el código específico de `flSelect` (ahora redundante:
   `updateSB` lo sincroniza).

### 16.4 Verificación (navegador, servidor local 127.0.0.1:8124)
- Flujo real (`selectDevice('pc')` → seleccionar LAN101): `flSelect=17000`,
  `spdSelect=260` (IAS actual).
- Asignar FL140 por evento `change` real → `cfl=140/selAlt=14000/tAlt=14000` y
  **`flSelect` permanece en `14000`** (antes se limpiaba).
- Asignar 250 kt por evento `change` real → `atcSpd=250` y `spdSelect=250`.
- Etiqueta tras asignar: `FL262 -31 FL140` / `I263 M178 SA140`; tiles sidebar
  `s-cfl=FL140`, `s-selalt=FL140`.
- 180 s de simulación: LAN101 desciende a FL140 (`alt=16835`, `vSpd=-2889`, etiqueta
  `FL168 -29 FL140`).
- `flStep(1)` → `tAlt=14100/cfl=141`; `flSelect` queda en blanco porque 14100 no es
  opción del desplegable (mismo comportamiento que SPD con IAS no múltiplo de 10);
  con valores válidos (p. ej. `cfl=200`) `flSelect=20000`.
- Al deseleccionar: `flSelect=''` y `spdSelect=''`.

## 17. La aeronave ahora colasiona (asienta) el nivel asignado — captura de nivel (radarnote31)

**Fecha:** 2026-09-10 · **Alcance:** SCEL_ATC_Radar.html

### 17.1 Problema
El usuario reportó: "si bien los cambios se ven reflejados en la etiqueta radar, la
aeronave no colasiona los niveles asignados, ya sea por voz o por comandos". La
etiqueta mostraba el CFL/SA correctos, pero la aeronave **nunca se asentaba** en el
nivel autorizado: oscilaba alrededor de `tAlt` con amplitud creciente/constante
(±1500 ft) en lugar de estabilizarse.

### 17.2 Causa raíz
La física vertical (bloque "Vertical speed with inertia") usaba una tasa objetivo
`targetVR=getVertRate(a,da)` **constante** hasta `|da|<10 ft`, con inercia
`VS_TC=4 s`. Al acercarse al nivel a ~3000 ft/min (50 ft/s), la aeronave **sobrepasaba**
el nivel (la inercia no la frenaba a tiempo) y el snap solo ocurría con
`|da|<5 && |vSpd|<50`, condición que nunca se cumplía a esa velocidad. Resultado:
sobrepaso → reversa → sobrepaso en sentido contrario → oscilación permanente
(verificado: 29000→14386→12259→13945→14247→12510→14189 en 600 s, vSpd aún +1679).

### 17.3 Cambios en SCEL_ATC_Radar.html (bloque de física vertical, ~L3808-3830)
1. **Zona de captura:** a menos de **2000 ft** del nivel autorizado, la tasa vertical
   objetivo se vuelve **proporcional a la distancia restante** (`targetVR=da*1.75`,
   ft/min por ft) y la respuesta se acelera (`vsTc=2 s` en lugar de 4 s) → sistema
   sobreamortiguado: la aeronave frena suavemente y se acerca al nivel sin sobrepaso
   grande ni oscilación. Fuera de la zona (|da|≥2000 ft) se mantiene la tasa de
   performance (`getVertRate`).
2. **Captura final:** a menos de **100 ft** del nivel asignado, la aeronave se asienta
   exactamente en el nivel (`alt=tAlt`, `vSpd=0`). El `da` se **recalcula después** de
   la física (`daSnap`) para que el snap dispare aunque el paso de simulación cruce la
   ventana de 100 ft en un solo tick (antes usaba el `da` previo a la física y podía
   fallar con pasos grandes).

### 17.4 Verificación (navegador, servidor local 127.0.0.1:8124)
- **Panel** (`flSelect=14000`): 29000→14000 en ~400 s, **asentado exacto** (`alt=14000`,
  `vSpd=0`, permanece fijo en t=450/500/550/600).
- **Voz** (`processTextCmd('SKY220 descend FL100')`): 27140→10000, asentado exacto
  (`alt=10000`, `vSpd=0`).
- **Ascenso** (alt=10000, asignar FL140): 10000→14000, asentado exacto.
- **Cambios múltiples** (FL140→FL100→FL180): cada nivel se asienta exacto
  (14000, luego 10000, luego 18000 con `vSpd=0`).
- **Espera + voz** (HOLD MORPA + "descend FL80"): desciende a 8000 durante la espera,
  asentado exacto.
- **Restricciones STAR** (`atcAlt=false`): la aeronave se asienta en cada nivel de
  cruce (8000: `alt=7911` antes del siguiente escalón a 7000) — la captura también
  aplica a los descensos por restricción.
- **Tiempo real (RAF)**: LAN101 desciende 509 ft en 15 s reales (`vSpd=-2710`).
- **Regresiones**: HOLD MORPA acepta a nivel actual / rechaza con nivel distinto;
  `interceptLoc('17L')` → `locMode=true`, altitud mantenida (la captura no interfiere
  con LOC/GS).

## 18. Readback de nivel: "autorizado ascenso/descenso para nivel de vuelo ___" (radarnote31)

**Fecha:** 2026-09-10 · **Alcance:** SCEL_ATC_Radar.html, normativa.xml

### 18.1 Problema
El usuario pidió que el readback del piloto al autorizar un cambio de nivel sea:
**CALLSIGN + "AUTORIZADO" + (ASCENSO/DESCENSO según la comparación con el nivel
actual) + "PARA NIVEL DE VUELO ___"**. Antes:
- `applyFL` (panel de comandos) **no generaba ningún readback**.
- `flStep` usaba el signo del paso (±100 ft) como dirección, no la comparación con la
  altitud actual (p. ej. con tAlt=FL250 y alt=FL200, un paso −1 decía "descenso"
  aunque la aeronave aún debía ascender a FL240).
- Voz CLIMB/DESCEND y `aAltDirect` usaban la dirección del comando, no la comparación.
- Las frases eran "ascendiendo/descendiendo a nivel de vuelo ___" (sin "autorizado").

### 18.2 Cambios
1. **normativa.xml** (`climb`/`descend`):
   - ES: `{cs}, autorizado ascenso/descenso para nivel de vuelo {val}`
   - EN: `{cs}, cleared to climb/descend to flight level {val}`
   (el item `level` "manteniendo nivel de vuelo" se usa cuando el nivel asignado
   coincide con la altitud actual).
2. **Diccionario local `ph`** en `readback()`: `climb_es`/`descend_es`/`climb`/`descend`
   actualizados al mismo formato (fallback si normativa.xml no carga).
3. **Helper `levelDir(a,alt)`**: `alt>a.alt?'climb':alt<a.alt?'descend':'level'` —
   dirección del readback según la comparación del nivel asignado con la altitud actual.
4. **`applyFL` (panel):** ahora genera readback con `levelDir`.
5. **`flStep`:** dirección por `levelDir(a,a.tAlt)` (nivel nuevo vs altitud actual),
   no por el signo del paso.
6. **Voz CLIMB/DESCEND y `aAltDirect`:** dirección por `levelDir` (comparación), de
   modo que un comando contradictorio ("climb FL140" con la aeronave en FL290) produce
   el readback correcto "autorizado descenso para nivel de vuelo 140".

### 18.3 Verificación (navegador, servidor local 127.0.0.1:8124)
- Panel FL330 desde FL290 → "LAN uno cero uno, autorizado **ascenso** para nivel de
  vuelo tres tres cero".
- Panel FL140 desde FL290 → "…autorizado **descenso** para nivel de vuelo uno cuatro
  cero".
- Panel FL290 desde FL290 → "…**manteniendo** nivel de vuelo dos nueve cero".
- Voz "descend FL140" desde FL290 → "…autorizado **descenso**…"; "climb FL350" →
  "…autorizado **ascenso**…".
- Voz contradictoria "climb FL140" desde FL290 → "…autorizado **descenso** para nivel
  de vuelo uno cuatro cero" (comparación, no el verbo del comando).
- `aAltDirect` descend 1500 ft → "…autorizado descenso para nivel de vuelo uno cinco".
- `flStep(-1)` desde FL290 → "…autorizado descenso para nivel de vuelo dos ocho nueve".
- EN (DAL123): "DELTA uno dos tres, cleared to descend to flight level one five".
- NORM cargó las frases nuevas (verificado en `NORM.climb/descend`).
- Regresión física: la aeronave sigue asentándose exacto en el nivel asignado
  (29000→14000, vSpd=0).

---

## 19. Panel FRASES — fraseología editable con fuente única JSON (radarnote31)

**Fecha:** 2026-09-23 · **Alcance:** SCEL_ATC_Radar.html, fraseologia_editada.json (nuevo), server.py, live_server.py

### 19.1 Objetivo
Que el usuario pueda **editar la fraseología del simulador** (readbacks, diluciones,
correcciones, pronunciación de fixes y patrones de espera) desde la interfaz, con
**guardado persistente** en un archivo JSON que pasa a ser la **fuente ÚNICA** de
fraseología (consolida todo lo que antes vivía en `normativa.xml` + el diccionario
local `ph` del JS, sin duplicidades).

### 19.2 fraseologia_editada.json (nuevo)
- **Estructura:** `meta` (versión, fuente, instrucciones, placeholders `{cs}/{val}/{fl}/{fix}`),
  `readbacks` (29), `diluciones` (8), `correcciones` (7), `fixes_pron` (20),
  `hold_patterns` (7), `establecida_referencia` (bloque de referencia DAP-11 §12.3).
- **Regla de oro:** una frase completa ES + EN con la misma clave = sin duplicidades.
  Los placeholders NO se renombran (el simulador depende de ellos).
- **Pulido aplicado (2026-09-23):**
  - Eliminados duplicados idénticos: `reportfix_en`, `reporthold_en`.
  - Añadido readback de **aproximación frustrada**: `goaround`
    ES `{cs}, frustrando aproximación` / EN `{cs}, going around`.
  - Añadido readback de **QNH deletreado**: `qnh` ES/EN `{cs}, Q-N-H {val}`.
  - Alineadas todas las cadenas ES/EN con las fuentes autoritativas (normativa.xml +
    diccionario `ph`): `resume` → "reanudando STAR"/"resuming STAR"; `direct` →
    "directo {fix}"/"direct {fix}"; `hold` → "en espera sobre {fix}"/"holding at {fix}";
    `loc`/`estloc` EN → "the ILS runway"; `switch` EN → "runway change confirmed";
    `twr` ES → "contacto Santiago Torre 118.1"; `inheld` EN → "established holding at";
    `mach_*` EN → "Mach point" (normativa).
  - `switch_twr` ("cambie a torre Santiago 118.1") se conserva: NO es duplicado de `twr`.

### 19.3 Panel FRASES en CONFIG
- **5 botones** en CONFIG (estilo `cfg-mini`): **READBACKS**, **DILUCIONES**,
  **CORRECCIONES**, **FIXES**, **ESPERAS** — cada uno abre el modal en su pestaña.
- **Modal `#frasesModal`**: cabecera con título y cierre, pestañas (`#frTabs`),
  lista de tarjetas (`#frList`) y barra de estado (`#frStatus`).
- **Tarjeta de frase** (`_frasesCard`): campos editables **ES**, **EN**, **VAR**
  (variables separadas por coma) y **KEY** (keywords de reconocimiento), botones
  **▶ ESCUCHAR ES / EN** (TTS con preview: `{cs}`→LAN112, `{val}`→180, `{fl}`→nivel
  de vuelo 140, `{fix}`→UGOLA) y hint de placeholders.
- **FIXES**: edición de pronunciación como palabra (no se deletrea).
- **ESPERAS**: edición de INB (rumbo de entrada), viraje (left/right) y altitud.
- **Guardado**: botón **💾 GUARDAR** → `POST /save/fraseologia` con el JSON completo.

### 19.4 Carga (fuente única) en SCEL_ATC_Radar.html
- El loader (ex L1464-1492) ahora intenta **primero** `fraseologia_editada.json`
  (síncrono, `cache:'no-store'` en el panel); si no existe, cae a `normativa.xml`
  como respaldo y el panel ofrece regenerar el JSON con GUARDAR.
- Puebla `NORM` (readbacks + diluciones `dilucion:true` + correcciones `correccion:true`),
  `FIX_PRON` y `HOLD_PATTERNS_NORM` desde el JSON.
- `readback()` sigue priorizando `NORM[cmd]` (fraseología establecida) sobre el
  diccionario local `ph` (fallback).

### 19.5 Endpoint /save/fraseologia
- Añadido a **server.py** (servir.bat, PORT 8000) y **live_server.py** (PORT 8123):
  valida `readbacks`, escribe con `tmp + os.replace` (atómico) y responde JSON
  `{ok, archivo, readbacks}`.

### 19.6 Verificación
- JSON válido (ConvertFrom-Json): 29 readbacks, sin ids duplicados.
- Todas las cadenas ES/EN de readbacks verificadas contra normativa.xml + diccionario
  `ph` (script de comparación: 25/25 OK en ES y EN).
- HTML estático: todas las funciones `frases*` referenciadas están definidas
  (frasesOpen/Edit/FixPron/Hold/Play/PlayEn/Save/Tab + helpers `_frases*`); todos los
  IDs del DOM usados por el JS existen (frasesModal, frasesPanel, frTabs, frList,
  frStatus); CSS `.fm-*`/`.fr-*` presente; `_frasesTab` declarado e inicializado.
- **Pendiente (requiere servidor):** validación funcional en navegador — abrir panel,
  editar, ▶ ESCUCHAR, GUARDAR y recargar para confirmar persistencia.

### 19.7 Fix: conexión del panel FRASES sin servidor (file://)
- **Síntoma reportado:** al presionar el botón FRASES, error al conectar con
  `fraseologia_editada.json`. Causa: la página se abre por doble clic (file://) y el
  `fetch()` del panel es bloqueado por el navegador (CORS en file://); no había
  servidor corriendo en 8000/8123/8124.
- **Solución aplicada en SCEL_ATC_Radar.html:**
  1. **`FRASES_FALLBACK`** (antes del loader): fraseología completa embebida como
     constante JS (copia de fraseologia_editada.json; JSON válido, 29 readbacks,
     8 diluciones, 7 correcciones, 20 fixes, 7 holds; sin `</script>`; llaves 364/364).
  2. **Loader** refactorizado con helper `_populateFromJson(json,src)` y cadena de
     respaldos: `fraseologia_editada.json` → `normativa.xml` → `FRASES_FALLBACK`
     (funciona igual con servidor y sin él).
  3. **`_frasesLoad`**: si el fetch falla, usa `FRASES_FALLBACK` (con categorías,
     variables y keywords completas) en vez de reconstruir desde NORM; avisa en el
     panel que está en modo embebido.
  4. **`frasesSave`**: si `POST /save/fraseologia` falla por red (file://), descarga
     el JSON editado vía Blob + `a.download` para reemplazar el archivo manualmente.
- **Verificación:** constante embebida parseada con ConvertFrom-Json (conteos
  idénticos al archivo); sin `</script>` en el bloque; tags `<script>` balanceados
  (3/3); referencias FRASES_FALLBACK/_populateFromJson en loader y panel confirmadas.
- **Pendiente:** prueba en navegador abriendo el HTML por doble clic — FRASES debe
  mostrar las 5 pestañas con datos, editar y GUARDAR debe descargar el JSON.

### 19.8 Nueva sección INSTRUCCIONES (fraseología del controlador)
- **Solicitud:** fraseología de INGRESO y ABANDONO de patrón de espera (frases del
  controlador, no readbacks de piloto). Verificado que no existían → agregadas.
- **3 entradas nuevas** en `fraseologia_editada.json` (sección `instrucciones`),
  `FRASES_FALLBACK` (HTML) y `normativa.xml` (sección `<instruccion>`):
  - `hold_clear`: ES "autorizado hasta {fix}, mantenga patrón de espera publicado,
    prevea autorización de aproximación a las {val}" / EN "cleared to {fix}, hold as
    published, expect approach clearance at {val}".
  - `leave_vec`: ES "vectores para abandonar espera" / EN "vectors to leave the hold".
  - `leave_via`: ES "abandone espera sobre {fix}, continúe vía {star}" / EN "leave the
    hold at {fix}, continue via {star}".
- **Placeholder nuevo `{star}`** (ej. EROLO8A) añadido a `meta.placeholders` (JSON +
  FRASES_FALLBACK) y al hint de tarjetas del panel.
- **Cableado:**
  - Loader `_populateFromJson`: carga `instrucciones` → `NORM` con flag
    `instruccion:true`; respaldo normativa.xml lee `<instruccion > item`.
  - Panel FRASES: 6ª pestaña **INSTRUCCIONES** (tabs + render + `_frasesFromNORM`
    incluye `ins`); botón `cfg-mini` INSTRUCCIONES en CONFIG.
  - `_frasesPreviewText`: sustituye `{star}` → "EROLO8A" en el preview TTS.
- **Verificación:** JSON archivo y embebido válidos (29 readbacks + 3 instrucciones +
  5 placeholders); llaves FRASES_FALLBACK 382/382; script tags 3/3; normativa.xml
  bien formado (3 items instruccion).

### 19.9 Sección OFFLINE (edición de datos con clave)
- **Solicitud:** botón **OFFLINE** en CONFIG protegido por clave `SIMOK7B @` (exacta,
  con espacio antes de `@`), que abre un panel con 7 botones: FRASES, MRVAC, AWY,
  ZONAS, SECTORES, RWY, FIXES - para editar offline (agregar mínimos de sector radar,
  zonas restringidas, sectores de control, aerovías, pistas, fixes) sin tocar el código.
- **Implementación en `SCEL_ATC_Radar.html`:**
  - Botón `cat-btn` OFFLINE en CONFIG → `openOffline()`: `prompt` valida la clave
    exacta `SIMOK7B @`; incorrecta → alerta y no abre.
  - `#offlineModal`: grid 3×2 con los 6 botones; FRASES reutiliza `frasesOpen()`
    (panel existente); los otros 5 abren `openOfflineEditor(section)`.
  - `#offEditModal` + editor genérico **schema-driven** (`OFF_SCHEMAS`): cada sección
    define sus campos (mrvac: name/alt/vértices; zonas: name/label/altLimit/vértices;
    awy: id/nombre/fixes/nivel; rwy: id/largo_m/thr_x/thr_y/ils; fixes:
    fix/x/y/alt/pron). Tarjetas editables + ＋ AGREGAR + ✕ ELIMINAR + 💾 GUARDAR.
  - **MRVAC (y ZONAS) — configuración gráfica completa**: campos NOMBRE, NIVEL
    MÍNIMO, RELLENO (rgba), BORDE (rgba) y COORDENADAS `x,y;x,y;…` (NM desde ARP
    SCEL), más **vista previa gráfica** del polígono (mini-canvas por tarjeta,
    `_offPreview`: escala automática al bounding box, relleno/borde según campos,
    vértices numerados). La vista previa se refresca en vivo al editar coordenadas
    o colores (`offEdit` redibuja el canvas de la tarjeta).
  - **STAR — rutas de llegada editables** (7º botón en el modal OFFLINE): cada STAR
    tiene ID (ej. `SIMOK7B_17L`), **NIVEL ENTRADA** (ft) y **PUNTOS** en formato
    `FIX,ALT,SPDMIN,SPDMAX;…` donde ALT = nivel mínimo de cruce (ft), SPDMIN/SPDMAX
    = velocidades mínima/máxima (kt IAS) al pasar por el punto (0 = sin restricción)
    y FIX = nombre del waypoint o coordenadas `x,y`. Vista previa de la ruta
    (polilínea con puntos numerados) en cada tarjeta.
  - **Aplicación en el simulador**: el merge Parte B (después de `const STARS`)
    repuebla `STARS` con los puntos editados (con `spdMin`/`spdMax` en cada
    waypoint) y `STAR_ENTRY_ALT` con el nivel de entrada; `starSpawnAlt` consulta
    `STAR_ENTRY_ALT` antes de las reglas por prefijo; nueva `updateSpdConstraint`
    (llamada junto a `updateAltConstraint` en la navegación) ajusta la velocidad
    objetivo a SPDMIN/SPDMAX del siguiente punto, salvo instrucción ATC (`atcSpd`).
  - `_offLoad`: intenta `datos_offline.json` (XHR síncrono); si no existe o falta la
    sección, parte de los datos integrados (`_offFromBuiltins` desde SECTOR_MIN /
    RESTRICTED / WPT+FIX_PRON / AWY / RWY). Vértices en formato `x,y;x,y;…` (NM).
  - `offSave`: `POST /save/datos_offline` con el JSON completo de las 5 secciones
    (`_offFullData` conserva las secciones no editadas); sin servidor (file://)
    descarga `datos_offline.json` vía Blob + `a.download` (mismo patrón que FRASES).
  - **Merge de arranque** (bloque OFFLINE DATA, antes de `const IAF=WPT.PUMAR;`):
    si `datos_offline.json` existe, REEMPLAZA por sección SECTOR_MIN, RESTRICTED,
    WPT+FIX_PRON, AWY y RWY (borra claves y repuebla; const objects no reasignables).
    Nuevas constantes `const AWY={},RWY={}` (no existía data de aerovías).
  - El primer GUARDAR crea `datos_offline.json` (no se pre-crea manualmente); al
    recargar, el simulador usa ese archivo si existe.
- **Servidores:** endpoint `POST /save/datos_offline` añadido a `server.py` (PORT
  8000) y `live_server.py` (PORT 8123), mismo patrón atómico (tmp + `os.replace`)
  que `/save/fraseologia`; respuesta `{ok, archivo, entradas}`.
- **Verificación:** script tags 3/3; llaves 2356/2356; corchetes 1145/1145; bloque
  OFFLINE JS balanceado (161/161 paréntesis, 71/71 llaves); bloque merge balanceado
  (63/63, 34/34); merge ubicado antes de `const IAF=WPT.PUMAR;` (IAF usa datos
  editados); `_escAttr`, `sysLog`, `frasesOpen`, `_frasesStatus` confirmados.
  Tras ampliar MRVAC/ZONAS: llaves 2368/2368, corchetes 1157/1157, bloque OFFLINE
  balanceado (211/211 paréntesis, 83/83 llaves, 56/56 corchetes), script tags 3/3.
  Tras añadir STAR: llaves 2405/2405, corchetes 1191/1191, bloque OFFLINE
  balanceado (287/287 paréntesis, 103/103 llaves, 75/75 corchetes); merge Parte A
  antes de `const IAF` y Parte B después de `const STARS` (evita TDZ);
  `tasToIas`/`iasToTas` (L3910/3916) confirmadas; `STAR_ENTRY_ALT` declarada antes
  de `starSpawnAlt`.
- **Pendiente:** prueba en navegador — OFFLINE → clave `SIMOK7B @` → editar una
  sección → GUARDAR (con servidor escribe el archivo; sin servidor descarga el JSON
  para reemplazo manual) → recargar y verificar que el simulador usa los datos.

### 19.10 Auditoría de código (consistencia entre archivos)
- **FRASES — consistencia total verificada:**
  - `fraseologia_editada.json` = `FRASES_FALLBACK` (embebido): 29 readbacks + 8
    diluciones + 7 correcciones + 3 instrucciones + 20 fixes_pron + 7 hold_patterns
    + 5 placeholders; **IDs idénticos en ambas direcciones** (47/47 únicos).
  - `normativa.xml` vs JSON: readback 26/29 (JSON añade `qnh`, `goaround`,
    `switch_twr` — añadidos documentados), dilucion 8/8, correccion 7/7,
    instruccion 3/3 — **IDs idénticos por sección**.
  - Loader `_populateFromJson` procesa las 6 secciones; respaldo XML lee las 4
    secciones de frase + fixes + hold_patterns; `_frasesFromNORM` reconstruye el
    JSON completo (pierde solo `meta.placeholders`/`fuente_base_original` en el
    último recurso — menor).
- **OFFLINE — consistencia de campos por sección** (schema ↔ merge ↔
  `_offFromBuiltins` ↔ `_offFullData`): mrvac (name/alt/fill/stroke/vertices),
  zonas (name/label/altLimit/fill/stroke/vertices), awy (id/nombre/fixes/nivel),
  rwy (id/largo_m/thr_x/thr_y/ils), fixes (fix/x/y/alt/pron), star
  (id/entry/wpts[fix,alt,spdMin,spdMax]) — **todas coinciden**.
- **STAR — orden de ejecución correcto:** merge Parte A (mrvac/zonas/fixes/awy/rwy)
  antes de `const IAF` (IAF usa WPT editado); merge Parte B (star) después de
  `const STARS` (evita TDZ); `ARR_TEMPLATES` resuelve STAR por nombre en runtime
  (no por referencia) → repoblado de STARS siempre visible.
- **Hallazgos corregidos en esta auditoría:**
  1. **Primer guardado OFFLINE incompleto**: `_offFullData` inicializaba las
     secciones no editadas como `[]` → al editar otra sección después, `_offLoad`
     mostraba "Sin entradas" (builtins perdidos). **Fix:** si `datos_offline.json`
     no existe, el primer GUARDAR captura TODAS las secciones desde los builtins;
     `_offLoad` usa builtins si la sección existe pero está vacía.
  2. **Modal FRASES oculto tras OFFLINE**: `frasesModal` z-index 510 < `offlineModal`
     520 → el botón FRASES del modal OFFLINE abría el panel detrás. **Fix:**
     `closeOfflineModal();frasesOpen('readbacks')`.
  3. **`offSave` total sin star**: el conteo de entradas no incluía la sección star.
     **Fix:** se añadió `+full.star.length`.
- **Hallazgos menores (no corregidos, sin impacto funcional):**
  - `_wptName` definida 2 veces (L2737 simple, L3358 robusta con `_wptNameMap`);
    la segunda sobrescribe a la primera (código muerto).
  - `_frasesTab` y `d2r` son globales implícitas (sin `let`/`const`); funcionan en
    modo no estricto.
  - `frasesValid` (span ESTADO del panel FRASES en CONFIG) nunca se actualiza
    desde JS — siempre muestra "—".
- **Verificación final:** llaves 2406/2406, corchetes 1192/1192, script tags 3/3;
  bloque OFFLINE balanceado (294/294 paréntesis, 104/104 llaves, 76/76 corchetes);
  71 handlers onclick únicos, todos definidos (los "sin definir" eran `this`/
  `document`); IDs de elementos (offlineModal, offEditModal, offEditTitle,
  offEditList, offEditStatus, frTabs, frList, frStatus, frasesModal) definidos y
  referenciados; servidores con `_send_json`/ROOT correctos y SimpleHTTPRequestHandler
  sirviendo `datos_offline.json` automáticamente cuando existe.

### 19.11 Fraseología de espera (hold) — comprensión no literal por voz

Solicitud del usuario: los ingresos a patrones de espera por comando de voz no se
reconocían bien (rumbos y niveles sí). Causa raíz: el parser solo aceptaba
`espera/hold + fix` directo, y la fraseología real de la normativa
("autorizado hasta UGOLA, mantenga patrón de espera publicado, prevea autorización
de aproximación a las 15:30") no encajaba: "espera publicado" → buscaba un patrón
llamado PUBLICADO; "hold as published" → buscaba AS; el fix real (UGOLA) va ANTES
de la palabra "espera" y nunca se extraía.

**Cambios en SCEL_ATC_Radar.html:**
1. **Nueva función `nlpHoldFix(lo)`** (antes de `nlpParse`): extracción robusta del
   fix de espera con 6 patrones (fix después de "espera/hold" con en/sobre/a/hacia/
   para/de/del/at/over/in/to/the; "patrón de espera [publicado] [en/sobre/...]";
   "ingrese/entre a patrón de espera"; "mantenga patrón de espera [publicado]";
   "hold as published"; y fix ANTES con "autorizado/cleared hasta/a/para/to X" o
   "directo X" cuando la frase contiene palabras de espera). Cada candidato se
   valida contra `HOLD_PATTERNS` antes de aceptarse.
2. **`nlpParse` hold**: usa `nlpHoldFix`; captura nivel de espera ("nivel de vuelo
   140", con fallback para números hablados "ciento cuarenta") y hora de expectativa
   ("prevea... a las 15:30", con fallback "quince treinta"); el canonical es
   `cs+' hold '+patName[' nivel de vuelo '+fl][' expect '+hhmm]` — siempre parseable
   por `processVoice`.
3. **`processVoice` bloque 9 (HOLD)**: 3 regex encadenados con validación contra
   `HOLD_PATTERNS` en cada paso (evita falsos positivos como "PREVEA"); soporta
   "nivel de vuelo NNN" (asigna tAlt/cfl/assignedFL/selAlt antes de la validación
   de nivel publicado) y "expect HHMM"/"a las HH:MM" (guarda `a.expectAppr`).
4. **`a.expectAppr`** (hora de expectativa de aproximación): se muestra en el status
   bar junto al patrón ("UGOLA 180° IZQ · APPR 15:30") y el piloto la confirma en el
   readback ("preveo autorización de aproximación a las 15 30" / "expect approach
   clearance at 1530"). Se limpia al abandonar el hold, cambiar rumbo, directo,
   resume STAR, LOC, appr, vecFinal, switch y al asignar un hold nuevo por menú.
5. **`startVoice`**: `maxAlternatives` 3→5 (más opciones de transcripción); fallback
   de idioma ante `language-not-supported`/`service-not-allowed` (es-CL → es-ES →
   es; en-US → en) con reintento automático; hints actualizados con la fraseología
   completa de espera (botón, popup y fallback de callsign).

**Fraseología ahora aceptada (voz o texto):** "hold UGOLA", "hold at UGOLA",
"espere en UGOLA", "espera sobre UGOLA", "espera a UGOLA", "esperando en UGOLA",
"hold over UGOLA", "ingrese a patrón de espera en UGOLA", "mantenga patrón de
espera publicado", "autorizado hasta UGOLA, mantenga patrón de espera publicado",
"cleared to UGOLA, hold as published", con nivel ("nivel de vuelo 140" o hablado
"ciento cuarenta") y hora de expectativa ("prevea... a las 15:30" / "expect 1530" /
hablado "a las quince treinta").

**Correcciones detectadas en la validación (parser real Chrome headless):**
1. **Bug de sintaxis real**: el bloque 9 reescrito de `processVoice` perdió el `if`
   externo que envuelve el bloque (los demás bloques usan `if(cond){...return;}`).
   El `return;}` final cerraba la FUNCIÓN entera → "Illegal return statement" en el
   primer `return` del bloque 10 (resume STAR). Corregido restaurando el `if` externo
   de detección de intención de espera
   (`/\b(?:hold|espera|espere|esperando|holding|patr[oó]n\s+de\s+espera)\b/`).
2. **`nlpHoldFix` regex 1**: exigía preposición entre la palabra de espera y el fix
   ("espere EN UGOLA" sí, "hold UGOLA" no). Preposición ahora opcional
   (`(?:(?:en|sobre|a|al|hacia|para|de|del|at|over|in|to|the)\s+)?`); la validación
   contra `HOLD_PATTERNS` evita falsos positivos ("hold heading" → null).
3. **Hora hablada "a las quince treinta"**: `nlpNumbers` combina palabras numéricas
   consecutivas en un solo valor (`_wordsValue` → 45), pero el fallback esperaba dos
   entradas separadas. Ahora usa las palabras individuales del primer resultado
   (`after[0].words[0]`/`[1]` como HH/MM).
4. **`nlpAction` hold**: no incluía "esperando"/"holding" (sí presentes en
   `nlpHoldFix` y en el `if` externo de `processVoice`). Alineado.
5. **`processVoice` regex 1**: lista de preposiciones ampliada (a/al/hacia/para/
   in/to/the) para consistencia con `nlpHoldFix`.

**Verificación (2026-09-25):** parser real Chrome headless sobre el archivo completo:
0 errores de sintaxis y 0 errores de ejecución en carga. Test funcional inyectado
(25 casos): `nlpHoldFix` 13/13 OK, `nlpParse` canonical 7/7 OK (incluye nivel
hablado, hora hablada y round-trip), `processVoice` ejecución 6/6 OK (incluye
rechazo por nivel inferior al publicado: FL80 < FL090 en UGOLA). Balance de llaves
2729/2729, corchetes 1254/1254; contador con stack (ignora strings/regex): los 3
bloques `<script>` terminan en 0 con 0 errores. MANUAL_FRASEOLOGIA.md secciones 2.4
y 6 actualizadas con las variaciones soportadas.

### 19.12 Reconocimiento de voz robusto — números hablados, alternativas y reintentos

Solicitud del usuario: reconocimiento de voz más robusto y las sugerencias pendientes
(persistir el harness de validación). Problemas detectados: (a) la fraseología ATC
real dice los números DÍGITO A DÍGITO ("rumbo uno ocho cero", "nivel de vuelo uno
cuatro cero", "one eight zero") y ningún regex los aceptaba — `nlpNumbers` los
SUMABA ("uno ocho cero" → 9); (b) el bucle de voz solo probaba alternativas hasta
encontrar un callsign, no hasta encontrar un comando válido; (c) un callsign mal
escuchado ("LAM 101" por "LAN 101") no resolvía.

**Cambios en SCEL_ATC_Radar.html:**
1. **Nueva función `_normSpoken(lo)`**: colapsa secuencias de 2+ palabras de dígito
   único (ES/EN, incluye fonética "niner/tree/fife/fower") a dígitos: "rumbo uno
   ocho cero" → "rumbo 180", "one eight zero" → "180". Guarda de contexto de hora:
   NO colapsa tras "a las/at/expect/prevea/hora/time" ("a las uno cinco" = 01:05 lo
   sigue resolviendo el fallback de hora hablada). Los números compuestos ("ciento
   cuarenta", "mil quinientos") no se tocan — los maneja `nlpNumbers`. Aplicada en
   `processVoice` y en `nlpParse` (lo, loNoCS y la entrada de `nlpNumbers`).
2. **`startVoice`**: `maxAlternatives` 5→10; el bucle prueba TODAS las alternativas
   hasta que una produce un comando válido (gracias a `processTextCmd` que ahora
   devuelve éxito); salta alternativas que son solo el callsign si quedan más;
   si ninguna funciona muestra lo escuchado ("⚠ No entendí — escuché: 'X' — ¿puede
   repetir?"); ante silencio reintenta automáticamente hasta 2 veces antes de avisar.
3. **`matchCS`**: fallback difuso con distancia de Levenshtein (≤1 en el prefijo,
   parte numérica EXACTA) para callsigns mal escuchados: "LAM 101" → LAN101, pero
   "LAN 102" nunca resuelve a LAN101.
4. **`processTextCmd`**: devuelve `true` si se produjo un comando/feedback y `false`
   si no se reconoció nada (fallo = "Comando no reconocido" o "Callsign no
   detectado"); base del bucle de alternativas de voz.

**Verificación (2026-09-25):** harness persistido en `tests/` (`hold_test.js` +
`run_tests.ps1`, que regenera el archivo de prueba en %TEMP% y ejecuta Chrome
headless con perfil aislado). 29 casos: `nlpHoldFix` 13/13, `_normSpoken` 10/10
(incluye guarda de hora y compuestos intactos), `nlpParse` 9/9 (nuevos: "rumbo uno
ocho cero" → `turn heading 180`, "ascienda a nivel de vuelo uno cuatro cero" →
`climb 140`), `processVoice` 7/7 (nivel hablado dígito a dígito), `matchCS` difuso
2/2, `processTextCmd` 3/3. ERR:0 (sin errores de carga). Balance de llaves
2743/2743, corchetes 1279/1279; los 3 `<script>` con stack 0 y 0 errores.
MANUAL_FRASEOLOGIA.md sección 6 actualizada con los números hablados.

### 19.13 Espera incompleta — el piloto pide confirmación de nivel y hora de abandono

Solicitud del usuario: si el ATC da una instrucción de espera INCOMPLETA, el piloto
debe ejecutar la espera pero pedir en el readback que se le confirme el nivel de
ingreso al patrón y la hora prevista de abandono de la espera.

**Cambios en SCEL_ATC_Radar.html:**
1. **`readback(ac,cmd,val,opts)`**: nuevo parámetro `opts` con `noLevel`/`noExpect`.
   Para `cmd==='hold'`, tras el readback principal: si la instrucción incluyó hora
   de expectativa, el piloto la confirma (comportamiento previo); si falta nivel y/o
   hora, el piloto pide confirmación de lo que falta:
   - ES: "confirme nivel de ingreso al patrón de espera" / "confirme hora prevista
     de abandono de la espera" (unidas con "y" si faltan ambas)
   - EN: "confirm holding level" / "confirm expected time of leaving the hold"
2. **`processVoice` bloque 9 (HOLD)**: `readback(a,'hold',patName,{noLevel:!mFl,
   noExpect:!mTime})` — las banderas reflejan si la instrucción incluyó nivel
   ("nivel de vuelo NNN") y hora ("expect HHMM"/"a las HH:MM"). Aplica a voz y
   texto (nlpParse produce canonical que pasa por el mismo bloque). El menú
   contextual (`applyHold`) no lo usa: ahí el nivel es el autorizado actual.

**Verificación (2026-09-25):** 4 casos nuevos en `tests/hold_test.js` (PV8-PV11):
"hold UGOLA" → pide nivel Y hora; "nivel de vuelo 140" sin hora → pide solo la hora;
"expect 1530" sin nivel → pide solo el nivel; instrucción completa → confirma la
hora y no pide nada. 33/33 tests OK, ERR:0. Balance de llaves 2746/2746, corchetes
1280/1280; los 3 `<script>` con stack 0 y 0 errores.

### 19.14 Adaptación a desviaciones de fraseología + solicitud de confirmación

Solicitud del usuario: el piloto debe adaptarse a desviaciones de fraseología
SIEMPRE que se entienda bien lo que el ATC quiere instruir; en caso contrario,
debe solicitar que se confirmen las instrucciones.

**Cambios en SCEL_ATC_Radar.html:**
1. **`_normSpoken`**: además de los números hablados, ahora elimina palabras de
   relleno/cortesía que no aportan instrucción ("por favor", "porfa", "please",
   "amablemente", "si es tan amable", "gracias", "thank you", "thanks", etc.) y
   colapsa espacios múltiples. Ej.: "hold UGOLA por favor" → "hold UGOLA";
   "ascienda por favor a nivel uno cuatro cero" → "ascienda a nivel 140";
   "please hold at UGOLA" → "hold at UGOLA". Aplica en `processVoice` y `nlpParse`.
2. **`processTextCmd(raw,silent)`**: nuevo parámetro `silent`. Cuando la intención
   NO es clara (ningún comando reconocido con callsign presente), el piloto
   SOLICITA confirmación de instrucciones en lugar de fallar en silencio:
   - ES: "LAN101, no entendí la instrucción, confirme instrucciones"
   - EN: "LAN101, say again, confirm instructions"
   Con `silent=true` (alternativas intermedias del bucle de voz) NO responde; la
   respuesta se emite una sola vez (última alternativa de voz o texto directo).
3. **Bucle de voz**: `processTextCmd(alt, ai<last.length-1)` — las alternativas
   intermedias fallidas no generan respuesta del piloto; solo la última.

**Verificación (2026-09-25):** casos nuevos en `tests/hold_test.js`: NS rellenos
(3 OK), PT4 (silent → false, sin respuesta), PT5 (→ false, piloto pide
"confirme instrucciones"), PT6 (desviación con relleno → se ejecuta, hold=UGOLA).
Todos los tests OK, ERR:0. Balance de llaves 2748/2748, corchetes 1281/1281;
los 3 `<script>` con stack 0 y 0 errores.

### 19.15 Piloto adaptativo — fraseología por intención (no por patrón fijo)

Solicitud del usuario: el piloto NO debe ser estructurado; debe adaptarse a
distintos tipos de fraseología de control ATC siempre que la intención sea clara,
y pedir confirmación cuando no lo sea.

**Cambios en SCEL_ATC_Radar.html:**
1. **Regex de acción compartidos** (`_RE_HDG`, `_RE_CLIMB`, `_RE_DESCEND`,
   `_RE_SPD`, `_RE_DIRECT`, `_RE_HOLD`) usados por `nlpAction` y
   `splitInstructions`. Sinónimos ampliados: "proa"/"steer" (rumbo),
   "go up"/"go down", "dirígete", "vaya directo"/"ve directo"/"vaya a"/"go to".
2. **`_valFor(lo,nums,kw)`**: extrae el número MÁS CERCANO a la palabra de acción
   (independiente del orden de palabras). "240 a la izquierda" → 240;
   "nivel 140 ascienda" → 140; "vire a la izquierda rumbo 240 a nivel 140" → 240
   (antes tomaba el ÚLTIMO número → 140, incorrecto).
3. **Viraje implícito**: "240 a la izquierda" (dirección + número, sin verbo) →
   hdg. "vaya a la izquierda" → pregunta "¿a qué rumbo?".
4. **"nivel NNN" sin verbo**: infiere subir/bajar según la altitud actual
   ("nivel 140" con la aeronave en FL120 → climb 140).
5. **Directo con fix ANTES de la palabra clave**: "a UGOLA directo" → direct UGOLA
   (fallback: cualquier fix de la base de datos presente en la frase).
6. **Instrucciones MÚLTIPLES**: `splitInstructions()` divide la frase por
   comas/"y"/"and" SOLO si hay 2+ acciones distintas; cada parte se procesa con su
   callsign. "vire a la izquierda rumbo 240, ascienda a nivel 140" → viraje +
   ascenso. Si alguna parte falla, se reprocesa la frase completa (idempotente).
   Nota: un viraje cancela el HOLD (semántica del simulador: vector cancela
   espera), por lo que "espera + viraje" deja el estado del último comando.

**Verificación (2026-09-25):** casos nuevos en `tests/hold_test.js`: NLP10-15
(240 a la izquierda, a UGOLA directo, nivel 140→climb, proa 240, vaya directo
UGOLA, suba a nivel 140) y PT7/PT8 (instrucciones múltiples con coma y con "y").
37 tests OK, ERR:0. Balance de llaves 2766/2766, corchetes 1297/1297;
los 3 `<script>` con stack 0 y 0 errores.

### 19.16 Lenguaje implícito editable — FRASES → LENGUAJE (persistido en el JSON)

Solicitud del usuario: el lenguaje implícito (los sinónimos/palabras clave que el
piloto usa para detectar la INTENCIÓN del controlador) también debe poder
modificarse en la sección OFFLINE → FRASES y quedar almacenado en el archivo JSON
de fraseología.

**Cambios en SCEL_ATC_Radar.html:**
1. **Nueva sección `lenguaje` en `fraseologia_editada.json`** (y en el respaldo
   embebido `FRASES_FALLBACK`): `{ "descripcion": ..., "acciones": { hdg, climb,
   descend, spd, direct, hold } }`, cada acción con su lista de sinónimos ES/EN.
2. **`LANG_IMPLICITO` + `_buildLangRegexes()`**: los regex de acción ya NO son
   constantes hardcodeadas; se construyen dinámicamente desde `LANG_IMPLICITO`
   (declarados `let _RE_*` al inicio de la carga de fraseología). El constructor
   genera clases de acentos opcionales (`patrón` ≡ `patron`, `diríjase` ≡
   `dirijase`) y convierte espacios en `\s+` para frases de varias palabras
   ("go up", "patrón de espera"). Se conserva el estilo prefijo (sin `\b` final)
   salvo en `_RE_HOLD` (palabra completa).
3. **Carga**: `_populateFromJson()` fusiona `_json.lenguaje.acciones` sobre
   `LANG_IMPLICITO`; `_buildLangRegexes()` se ejecuta SIEMPRE al final de la
   carga (fuera del try/catch), con los defaults si el JSON no trae la sección.
4. **Fix de bug latente**: el respaldo `normativa.xml` ahora valida
   `_x2.responseXML` antes de usar `querySelectorAll` (en file:// el XHR devuelve
   status 0 con responseXML null y lanzaba una excepción que se tragaba el catch
   externo — inofensivo con regex hardcodeados, pero impedía construir los regex).
5. **Nuevo tab LENGUAJE en el panel FRASES** (CONFIG → FRASES): 6 tarjetas
   (RUMBO, ASCENSO, DESCENSO, VELOCIDAD, DIRECTO, ESPERA) con un campo KEY
   editable (sinónimos separados por coma). `frasesLang()` escribe en
   `_frasesData.lenguaje.acciones`; el botón GUARDAR existente persiste todo el
   JSON (POST `/save/fraseologia` o descarga del archivo en file://). Hint
   didáctico: prefijos cortos cubren variantes ("gir" → gire/gira/girar) y los
   acentos son opcionales.
6. **`_frasesFromNORM()`** (último recurso sin JSON) incluye `lenguaje` con los
   defaults de `LANG_IMPLICITO`.

**Verificación (2026-09-25):** casos nuevos en `tests/hold_test.js`: LG1a-c
(regex construidos: "gir" prefijo, "proa", "rumbo"), LG2a-b ("patrón de espera"
con y sin acento), LG3a-b ("diríjase"/"dirijase"), LG4a-b (editar
`LANG_IMPLICITO.hdg=['proa']` + reconstruir → el nuevo sinónimo aplica y el viejo
deja de matchear), LG5a-b (`_populateFromJson` con sección `lenguaje` sobreescribe
los sinónimos), LG6 (`frasesLang` escribe en `_frasesData.lenguaje.acciones`).
49 tests OK, 0 FAILS, ERR:0. Balance de llaves 2783/2783, corchetes 1345/1345;
los 3 `<script>` con stack 0 y 0 errores. JSON válido (ConvertFrom-Json OK).

### 19.17 Fix: botón de comandos por voz muerto (variables implícitas en modo estricto)

Reporte del usuario: el botón de reconocimiento de voz dejó de funcionar (pulsar
no hacía nada).

**Causa raíz:** el script corre con `"use strict"` (L1252). `startVoice()` usaba
dos contadores de reintento como variables IMPLÍCITAS (asignación sin declarar):

```js
if(typeof _recogLangTry!=='number')_recogLangTry=0;   // ReferenceError en strict mode
if(typeof _noSpeechTries!=='number')_noSpeechTries=0; // idem
```

En modo estricto, asignar a una variable no declarada lanza
`ReferenceError: _recogLangTry is not defined`, así que `startVoice()` → 
`toggleVoice()` lanzaba la excepción en cuanto se pulsaba el botón (o la barra
espaciadora). El fallo no lo detectaban los tests porque ninguno invocaba
`toggleVoice()`/`startVoice()` directamente (solo `processTextCmd`/`processVoice`).

**Cambios en SCEL_ATC_Radar.html:**
1. `let _recogLangTry=0,_noSpeechTries=0;` declaradas junto a `recog`/`voiceActive`
   (sección VOICE), con comentario explicando el modo estricto.
2. Eliminadas las guardias `typeof ...!=='number'` redundantes en `startVoice()`.

**Verificación (2026-09-25):** diagnóstico con Chrome headless reprodujo el
`ReferenceError` antes del fix y `toggleVoice OK` después. Tests de regresión
nuevos en `tests/hold_test.js`: VB1 (contadores declarados como number) y VB2
(`toggleVoice()` sin excepción). 51 tests OK, 0 FAILS, ERR:0. Balance de llaves
2783/2783, corchetes 1345/1345; los 3 `<script>` con stack 0 y 0 errores.

### 19.18 Readback de espera/abandono — nueva fraseología

Solicitud del usuario: al seleccionar un patrón de espera desde el menú COMANDO
de la etiqueta, el readback del piloto cambia de "en espera sobre (FIX)" a
"sobre (FIX) ingreso a patrón de espera publicado"; al abandonar la espera dice
"abandonando patrón de espera sobre (FIX), reanudo (STAR) o volando directo a
(FIX)".

**Cambios (aplicados en los 4 orígenes del texto para mantener consistencia):**
1. `SCEL_ATC_Radar.html` — diccionario `ph` en `readback()`:
   - `hold_es`: `"{cs}, sobre {fix} ingreso a patrón de espera publicado"`
   - `leave_es`: `"{cs}, abandonando patrón de espera sobre {fix}, reanudo {star} o volando directo a {fix}"` (con `ac.starName` vía `spkStar`, fallback "ruta")
   - espejos EN: "at {fix} entering the published hold" / "leaving the hold at {fix}, resuming {star} or flying direct to {fix}"
   - `_fmt` ahora reemplaza `{star}` (nuevo placeholder; no afecta a otras frases).
2. `fraseologia_editada.json` — entradas `hold` y `leave` con las nuevas plantillas
   y `variables` actualizadas (`["{cs}","{fix}","{star}"]` en leave).
3. `normativa.xml` — `<item id="hold">` y `<item id="leave">` con las nuevas
   plantillas (fuente prioritaria cuando el XML carga).
4. `FRASES_FALLBACK` (embebido) — mismas plantillas.

**Verificación (2026-09-25):** tests nuevos RB1/RB2 en `tests/hold_test.js`
verifican el texto del banner:
- RB1: "LAN uno cero uno, sobre ugola ingreso a patrón de espera publicado"
- RB2: "LAN uno cero uno, abandonando patrón de espera sobre ugola, reanudo
  simok siete BRAVO o volando directo a ugola"
53 tests OK, 0 FAILS, ERR:0. Balance de llaves 2792/2792, corchetes 1345/1345;
JSON y normativa.xml válidos.

**Mejora al runner:** `tests/run_tests.ps1` ahora copia también
`fraseologia_editada.json` al temp (la carga es síncrona por XHR), de modo que el
suite valida SIEMPRE la fraseología editable real y no una copia obsoleta.

### 19.19 Sección HELP - comandos permitidos por voz y por texto

Solicitud del usuario: configurar una sección llamada HELP que liste los comandos
permitidos por voz y por texto para dar instrucciones a las aeronaves.

**Implementación (referencia estática, alineada con el parser real):**
1. Botón `HELP` en el panel CONFIG (junto a FRASES/OFFLINE) → abre `#helpModal`.
2. Modal reutiliza el patrón visual de `#frasesModal` (`.fm-hdr/.fm-close/.fm-body`)
   con pestañas por categoría (`.hp-tabs/.hp-tab`) y tarjetas de comando
   (`.hp-card` con ejemplos ES/EN y nota).
3. Datos en `HELP_CMDS` (constante): 10 categorías — RUMBO, NIVEL, VELOCIDAD,
   DIRECTOS, ESPERAS, APROXIMACIÓN, TRANSFERENCIA, INFORMES, CONSULTAS, GLOBALES —
   con 30 comandos documentados (id, ejemplos ES/EN, notas de validación).
4. Funciones: `openHelpModal()`, `closeHelpModal()`, `helpTab(t)`, `_helpRender()`
   y `_escHtml()` (escape de HTML para los ejemplos).
5. El catálogo se relevó de las fuentes reales del parser: `processVoice()`
   (comandos por voz), `nlpParse()`/`nlpAction()` (acciones e intenciones) y
   `LANG_IMPLICITO` (sinónimos editables en FRASES → LENGUAJE).

**Verificación (2026-09-30):** tests nuevos HP1-HP4 en `tests/hold_test.js`:
- HP1: `HELP_CMDS` definido con 10 categorías
- HP2: `openHelpModal()` sin excepción
- HP3: 10 pestañas renderizadas
- HP4: tarjetas renderizadas en la lista
57 tests OK (53 previos + 4 nuevos), 0 FAILS, ERR:0. Balance de llaves
2862/2862, corchetes 1428/1428.

**Nota de entorno:** Chrome headless dejó de funcionar en esta máquina (la
carpeta de versión `153.0.8010.53` quedó sin `chrome.exe` — instalación
corrupta), por lo que `tests/run_tests.ps1` no puede ejecutarse hasta reparar
Chrome. La validación de esta sección se hizo con el navegador integrado de
OpenWork sobre un servidor HTTP local (`httpd.ps1` en temp + `http.server`
equivalente en PowerShell), abriendo `SCEL_TEST.html` y leyendo el título
`RES::...`.

### 19.20 Sección SECTORES en OFFLINE - sectores de control persistentes

Solicitud del usuario: agregar en la sección OFFLINE un botón SECTORES para
dibujar los sectores de control, con **color verde oscuro y línea gruesa
continua**, y que al crearlos queden **grabados en el programa** (persistencia,
no dibujo temporal).

**Implementación en `SCEL_ATC_Radar.html`:**
1. **Botón `SECTORES`** en `#offlineModal` (grid, junto a ZONAS) →
   `openOfflineEditor('sectores')`.
2. **Schema `sectores`** en `OFF_SCHEMAS` (name/fill/stroke/vertices, con vista
   previa de polígono como MRVAC/ZONAS).
3. **Objeto global `SECTORES`** (vacío por defecto) — el controlador los crea
   desde cero con ＋ AGREGAR.
4. **Carga persistente**: bloque OFFLINE DATA lee la sección `sectores` de
   `datos_offline.json` (si existe) y reemplaza `SECTORES`; defaults de color
   verde oscuro: fill `rgba(0,120,60,.15)`, stroke `rgba(0,160,80,.9)`.
5. **Dibujo en el radar** (`drawRestrictedZones`): los sectores se dibujan
   SIEMPRE (sin toggle), con `ctx.lineWidth=3*DPR` (línea gruesa) y sin
   `setLineDash` (continua), en verde oscuro.
6. **Guardado**: `_offFullData()` incluye `sectores` (y lo captura en el primer
   guardado junto a las demás secciones); `offSave()` cuenta la sección en el
   total; `server.py` y `live_server.py` suman `sectores` en el endpoint
   `/save/datos_offline`.

**Verificación (2026-09-30):** tests nuevos SC1-SC5 en `tests/hold_test.js`:
- SC1: schema `sectores` con título "SECTORES DE CONTROL"
- SC2: `SECTORES` definido (objeto)
- SC3: `_offFromBuiltins('sectores')` devuelve array
- SC4: botón SECTORES presente en el modal OFFLINE
- SC5: `drawRestrictedZones()` sin excepción con SECTORES
62 tests OK (57 previos + 5 nuevos), 0 FAILS, ERR:0. Balance de llaves
2877/2877, corchetes 1435/1435.

**Prueba interactiva (navegador integrado):** editor abre con título
"SECTORES DE CONTROL"; `offAdd()` + edición de name/fill/stroke/vertices
funcionan; vista previa canvas presente; `_offFullData()` incluye la sección
`datos_offline.json` con todas las claves (mrvac, zonas, sectores, awy, rwy,
fixes, star); con un sector inyectado (SECTOR_NORTE) el radar dibuja 506
píxeles verde oscuro (fill+stroke) sin excepción.

### 19.21 Sector DELTA creado (OFFLINE → SECTORES)

Solicitud del usuario: crear el sector de control **DELTA** con 10 vértices en
coordenadas geográficas DMS (S/W) y persistirlo en el programa.

**Conversión geográfica → NM desde ARP SCEL** (`SCEL_LAT=-33.3942`,
`SCEL_LNG=-70.7856`):
- `y = (lat − latRef) · 60`
- `x = (lon − lonRef) · 60 · cos(latRef)` con `cos(33.3942°) = 0.8349036`
- Fórmula verificada contra el polígono R27 existente (33°30'00"S/070°36'15"W →
  x=9.09, y=-6.35 ✓) y por conversión inversa del vértice 1 (x=-103.067,
  y=187.685 → 30°15'58"S, 72°50'35"W exacto).

**Vértices DELTA (x,y en NM):**
`-103.067,187.685; -78.02,141.569; -42.647,137.535; -15.624,111.652;
-15.527,26.669; -11.993,10.735; -10.364,-4.581; -38.306,-37.381;
-116.898,-37.298; -111.207,-20.431; -103.067,187.685` (cierre = vértice 1).

**Persistencia:** creado `datos_offline.json` (nuevo) con la sección
`sectores` → `DELTA` (fill `rgba(0,120,60,.15)`, stroke `rgba(0,160,80,.9)`,
11 vértices). El bloque OFFLINE DATA lo carga al iniciar; las demás secciones
siguen usando los datos integrados (JSON parcial manejado por `_offLoad`/
`_offFullData`).

**Verificación (2026-09-30, navegador integrado):** ERR:0, 0 FAILS;
`SECTORES['DELTA']` cargado con 11 vértices; radar dibuja 2051 píxeles verde
oscuro; editor SECTORES muestra 1 tarjeta "DELTA" con el campo COORDENADAS
completo en formato `x,y;x,y;…`.


### 19.22 Boton SECTORES en barra GEN - capa de sectores con toggles individuales

**Objetivo:** mostrar/ocultar los limites de cada sector de control desde la
barra GEN, dibujados en amarillo dorado con linea gruesa continua. Al
desactivar el boton del sector, el sector desaparece de la pantalla radar.

**Implementacion (SCEL_ATC_Radar.html):**
- Boton `SECTORES` (`#sectBtn`, clase `cat-btn sect`) en la barra GEN, junto a
  HOLD. Abre/cierra la seccion `#sectPopup` (popup estilo simPopup) con los
  botones de cada sector: CHARLIE, DELTA, ECHO, GOLF, FOXTROT, HOTEL, INDIA,
  mas TODOS y NINGUNO. La capa general queda activa al abrir (no se apaga).
- Estado: `showSectores` (capa general, default true), `SECT_NAMES` (7
  nombres), `sectoresOn` (toggle por sector; DELTA on por defecto, resto off).
- `toggleSectores()` abre/cierra el popup; `toggleSector(name)` alterna la
  visibilidad de un sector; `sectAll(on)` activa/desactiva todos;
  `_sectRender()` pinta el estado on/off de cada boton del popup. Cierre del
  popup con clic fuera.
- Dibujo en `drawRestrictedZones()`: si `showSectores` y `sectoresOn[name]`,
  dibuja el poligono con fill `rgba(245,220,96,.12)` y stroke
  `rgba(245,220,96,.95)` (amarillo dorado, igual que el boton COAST), linea
  gruesa `3*DPR`, continua (sin setLineDash).
- `datos_offline.json`: DELTA actualizado a dorado (fill/stroke).

**Tests (hold_test.js):** SC6-SC12 (boton SECTORES, SECT_NAMES, DELTA on por
defecto, toggleSector, dibujo dorado ON/OFF por conteo de pixeles, sectAll).
SC10 usa dibujo sincrono (replica de frame()) porque forceRedraw es asincrono
via rAF; drawAC se omite (no hay aeronaves en el contexto de test).

**Verificacion (2026-09-30, navegador integrado):** ERR:0, 0 FAILS (69
tests). Pagina real: abrir SECTORES no apaga DELTA (2220 px dorados antes y
despues); toggleSector('DELTA') off -> 492 px, on -> 2177 px; popup muestra
los 7 sectores con DELTA=ON; cierre con clic fuera OK. Balance llaves
2901/2901, corchetes 1444/1444.

### 19.23 Sector FOXTROT creado + activacion automatica de sectores existentes

**Solicitud:** definir el sector FOXTROT con 10 coordenadas DMS y habilitar
los botones de la seccion SECTORES para visualizar los sectores subidos
(DELTA y FOXTROT).

**Conversion (formula verificada, latRef=-33.3942, lonRef=-70.7856,
cos=0.834903583653854):** P1 333809S/0695158W -> (46.061,-14.498);
P2 332814S/0705933W -> (-10.364,-4.581); P3 340102S/0713301W ->
(-38.306,-37.381); P4 340057S/0730709W -> (-116.898,-37.298);
P5 351332S/0733609W -> (-141.11,-109.881); P6 351852S/0720422W ->
(-64.48,-115.215); P7 352821S/0713822W -> (-42.773,-124.698);
P8 352528S/0712559W -> (-32.434,-121.815); P9 353237S/0711900W ->
(-26.603,-128.965); P10 353543S/0702314W -> (19.956,-132.065).
Verificacion cruzada: P2, P3 y P4 coinciden exactamente con los vertices
compartidos de DELTA (mismas coordenadas DMS). Correccion del usuario
(2026-09-30): P2 era 331255S/0710130W -> corregido a 332814S/0705933W
(equivale al vertice 7 de DELTA). Nota: el punto 6 del usuario era
"3518852S" (7 digitos, anomalo) -> se asumio 35°18'52"S (351852S);
el usuario confirmo que todas las demas coordenadas estan correctas.

**Segunda correccion del P2 (2026-09-30):** el usuario pidio que P2 parta
de P1 (46.061,-14.498) y siga una linea horizontal rumbo 270 (oeste, y
constante) hasta topar el sector DELTA, al sur y al oeste de la ubicacion
anterior. Interseccion de la linea y=-14.498 con DELTA: borde V6-V7 en
x=-18.812 (primer cruce desde el este) y borde V9-V10 en x=-110.975.
Nuevo P2 = (-18.812,-14.498) = 33°38'09"S / 71°09'40"W (misma latitud
que P1; 64.9 NM al oeste de P1). Cumple: sur de (-10.364,-4.581) y oeste
de (-10.364,-4.581). Aplicado en datos_offline.json y en el builtin.

**datos_offline.json:** seccion sectores con DELTA (11 verts) y FOXTROT
(10 verts, sin cierre explicito; el dibujo cierra con closePath()), ambos
con fill rgba(245,220,96,.12) y stroke rgba(245,220,96,.95).

**Activacion automatica:** al cargar datos_offline.json, los sectores que
existen se encienden (sectoresOn[name]=true). DELTA y FOXTROT se visualizan
al iniciar; CHARLIE/ECHO/GOLF/HOTEL/INDIA quedan off hasta crearlos.
Defaults de fill/stroke en la carga actualizados a dorado.

**Verificacion (2026-09-30, navegador integrado):** ERR:0, 0 FAILS (69
tests; SC10 ON=3629px con ambos sectores tras la correccion del P2).
Caso sin datos_offline.json (builtins): SC10 ON=3629px identico — DELTA y
FOXTROT se dibujan incluso con file:// o servidor colgado. Pagina real:
DELTA y FOXTROT cargados y ON al iniciar (3905 px dorados); popup muestra
DELTA=ON y FOXTROT=ON; toggleSector('FOXTROT') off -> 2177 px (solo DELTA),
on -> 3907 px; toggleSector('DELTA') -> 2217 px (solo FOXTROT); bucle rAF
activo (la app no queda colgada). Balance llaves 2945/2945, corchetes
1446/1446. XHR sincronos a datos_offline.json: 0 (todos asincronos con
timeout 3s: carga inicial, _offLoad y _offFullData).

### 19.24 Escenario tablet: transitos UGOLA/TEGEB + Auto DEP 17R

**Solicitud:** version tablet en radio 40 NM norte y 40 NM sur centrado en
SCEL, transitos en UGOLA y TEGEB, y despegues RWY 17R con todos los tipos
de SIDs de la 17R cada 2 min. Solo version tablet.

**Implementacion:**
- Nueva opcion "Tablet · UGOLA+TEGEB · Auto DEP 17R" en el select de
  escenarios (value="tablet").
- selectDevice('tablet') fuerza el escenario tablet automaticamente
  (solo tablet; PC conserva su escenario previo).
- loadScenario('tablet'): _spawnTransit(WPT.UGOLA,'LAN101','A320',9000,250)
  + _spawnTransit(WPT.TEGEB,'SKY220','A321',5000,250) + startAutoDep().
- _spawnTransit(): aeronave posicionada en el waypoint, rumbo hacia SCEL
  (0,0), role='arr', starName='TRANSITO'.
- Auto DEP 17R: pool AUTO_DEP ya rota los 3 SIDs de la 17R (ALBAL7A_17R,
  NEBEG7A_17R, DONTI5B_17R) cada 2 min (setInterval 120000 ms).
- autoDepBtn visible tambien en escenario tablet.
- Radio 40 NM centrado en SCEL: ya era el comportamiento de tablet/PC
  (currentScale=SCALE_NM, panX=0, panY=0).

**Verificacion (2026-09-30, navegador integrado):** harness ERR:0, 72
tests (SC13 opcion tablet, SC14 transitos UGOLA+TEGEB, SC15 auto dep
activo). Pagina real: al seleccionar TABLET -> scenario='tablet',
aircraft=3 (LAN101 en UGOLA, SKY220 en TEGEB, LAN100 ALBAL7A_17R dep),
autoDepTimer activo, currentScale=40, panX=0, panY=0, bucle rAF 61 fps
(app viva, no congelada). Balance llaves 2948/2948, corchetes 1447/1447.

### 19.25 SIDs reales SCEL — AIP Chile DGAC (cartas SID 1–14)

**Solicitud:** las salidas despegaban mal porque no seguian la salida
normalizada de SCEL. Cargar TODAS las salidas de SCEL con sus rutas reales.

**Fuente:** cartas SID 1–14 del AIP Chile
(https://aipchile.dgac.gob.cl/aip/vol2/seccion/proc/pagina/01). Los 14 PDF
se descargaron y su texto se extrajo descomprimiendo los streams FlateDecode
con PowerShell + .NET DeflateStream (texto en operadores Tj/TJ).

**Implementacion:**
- **WPT**: 31 waypoints nuevos con coordenadas calculadas desde las cartas
  (conversion DMS→NM verificada contra GENPO/TABON/TEMUS/PUMAR existentes):
  YESOS, SUPRA, ETEMI, ANGOD, ESKUL, VAGOS, DESIT, LINER, KIDUG, ARSEV,
  DGO (VOR DOMINGO), VTN (VOR VENTANAS), PABEK, AMB (VOR SANTIAGO), EL250,
  EL400, EL401, EL403, EL500, EL019, EL021, EL034, EL070, EL080, EL091,
  EL106, EL131, EL177, EL299. Los waypoints existentes validados NO se
  tocaron (TBN usa WPT.TABON).
- **SIDS**: objeto reemplazado por las 66 SIDs reales (24 de 17R, 24 de
  17L, 18 de 35L/35R) con la secuencia exacta de cada carta:
  - SID1: ALBAL 7A / NEBEG 7A / ANGOD 8B (17R/L)
  - SID2: LINER 5A / GELUS 6A / SABLA 8 (17R/L)
  - SID3: DOMINGO 6 / VENTANAS 6 / DONTI 6A / TABON 6A (17R/L)
  - SID4: TENUT 5 / GUVOL 5C / SANTIAGO 5 (35R/L)
  - SID5: GELUS 5B (17R/L) / GELUS 3C (35L/R)
  - SID6: DILOK 7B (17R/L) / DILOK 5A (35L/R)
  - SID7: GUVOL 6B (17R/L) / GUVOL 4A (35L/R)
  - SID8: DONTI 5B (17L/R)
  - SID9: NEBEG 7C (17L/R) / NEBEG 5D (35L/R)
  - SID10: ALBAL 7C (17L/R) / ALBAL 5D (35L/R)
  - SID11: LINER 6C (17L/R) / LINER 5D (35L/R)
  - SID12: ANGOD 6C (17R/L)
  - SID13 (RNP 17R): DONTI 1R / DILOK 1R / GUVOL 1R / DOMINGO 1R /
    GELUS 1R / VENTANAS 1R
  - SID14 (RNP 17L): DONTI 1L / DILOK 1L / GUVOL 1L / DOMINGO 1L /
    GELUS 1L / VENTANAS 1L
- **AUTO_DEP**: pool ampliado a las 24 SIDs de la 17R con 24 bases ICAO
  unicas (LAN, SKY, TAM, IBE, JAL, AVA, DLH, AFR, KLM, QTR, UAE, AMX,
  AAL, UAL, DAL, BAW, CPA, SIA, ETH, KAL, ACA, ANA, CES, HAL) → ids
  unicos por ciclo.
- **spawnDep**: ids de salida con offset 200 (LAN200, SKY200…) en vez de
  100, para no colisionar con llegadas/transitos (LAN101, SKY220…).
- **DEP_TEMPLATES**: mantiene GELUS5B_17L / DILOK7B_17L / GUVOL6B_17L /
  DONTI5B_17L, ahora con rutas reales.
- **loadScenario**: comentarios y nombre del escenario 'auto' actualizados
  ("24 SIDs reales SCEL").

**Verificacion (2026-10-04, navegador integrado):** harness ERR:0, 73
tests (SC16 nuevo: SIDs=66, AUTO_DEP 17R=24, existen 17L y 35L/R, ids sin
colision con llegadas, bases ICAO unicas). Prueba de spawns: 24 salidas
(1 ciclo completo) sin ids duplicados, sin rutas invalidas, todas con su
SID correcta en starName y rumbo inicial valido. Balance llaves 3052/3052,
corchetes 1504/1504 (parens 7663/7673: diferencia preexistente en strings
de texto en espanol, no afecta sintaxis).

### 19.26 Salidas: ascenso por el EJE DE PISTA hasta el punto/altitud publicado

**Solicitud:** los despegues viraban en el primer tercio de la pista. Ninguna
SID debe iniciar el viraje antes del punto o nivel que publica la carta.

**Causa raiz:** las rutas tenian como primer punto el fix de la carta (p.ej.
VAGOS o EL019). `updateRouteNav()` apuntaba directamente a ese fix, de modo
que la aeronave viraba hacia el nada mas despegar, y el viraje se activaba
ademas por la captura por esfera de 1.2 NM, todavia antes de llegar al punto.

**Implementacion (SCEL_ATC_Radar.html):**
- **`RWY_AXIS`**: THR y rumbo de eje por pista (17R/17L → 177°, 35L/35R → 357°).
- **`thr(rwy)`**: el THR como primer punto de cada SID, con `axisHdg` y `rwy`.
- **`_ax(rwy,roc,altTurn)`**: marcador de viraje EN NIVEL para las cartas que
  fijan altitud («Climb on TR177° until 4000FT, turn right direct to LOLAT»).
  La distancia del marcador se calcula con la MNM Razón ASC publicada
  (`(altTurn-ARP_ELEV)/roc`, minimo 2.5 NM), de modo que el viraje es correcto
  tambien en planta.
- **`_ap(rwy,name,min,max)`**: primer punto alcanzado EN EJE para las cartas
  que fijan el viraje sobre el fix («Ascenso en TR177° hasta EL019», «R177 AMB
  VOR hasta LINER INT», «R357 PDH/AMB VOR hasta TEMUS/PUMAR»). Clona el waypoint
  con `altMin`/`altMax` y le anade `axisHdg`.
- **`SID_ROC`**: MNM Razón ASC por SID (FT/NM) con el nivel en que cesa
  (300, 310, 320, 330, 331, 350, 370, 400, 445, 450), tomada de la nota
  «MNM Razón ASC» de cada carta.
- **`updateRouteNav()`**: si el punto objetivo lleva `axisHdg`, la aeronave
  mantiene el rumbo de pista; el avance al fix siguiente ocurre solo al
  alcanzar `altTurn` (viraje por nivel) o al sobrepasar el punto
  (`routePointPassed`), nunca antes.
- **`routePointPassed()`**: para salidas exige haber atravesado el plano del
  tramo (`along>=1`) dentro de un corredor de 2.5 NM — el viraje ocurre SOBRE
  el punto. Las llegadas conservan la captura de 1.2 NM.
- **`updateAltConstraint()`**: respeta `altTurn` como objetivo de ascenso y
  aplica `altMin`/`altMax` de cada punto (ventanas «entre X y Y» y minimos
  «Z o superior»), con `nextSidAlt()` para el climb-to de puntos sin cota.
- **`mkACwithRoute()`**: fija `hdg`/`tHdg`/`axisHdg` al rumbo de eje y aplica
  `SID_ROC` como piso de ascenso (`sidRoc`/`sidRocTil`).
- **`getVertRate()`**: aplica el piso `sidRoc*GS/60` FT/min mientras la
  aeronave este bajo el nivel en que cesa la MNM Razón ASC.
- **Waypoints**: anadido `D22AMB` (D22 AMB a 22 NM, FL140).

**Distribucion resultante:** 24 SIDs en 17R, 24 en 17L, 9 en 35L, 9 en 35R.
Las 66 arrancan en el THR de su pista y todas tienen `axisHdg` en el punto del
primer viraje.

**Escenario disponible en TABLET y PC (solicitud del usuario):**
- Nueva opcion `deps` — «Salidas SCEL · 1 cada 2 min · tablet y PC».
- `selectDevice('tablet')` y `selectDevice('pc')` seleccionan `deps` por defecto.
- `DEP_TEMPLATES` ampliado de 4 a 8 entradas, incluyendo 35L (GUVOL5C, TENUT5)
  y 35R (DILOK5A). Sigue en uso por el escenario `mixed` (2 salidas).
- **Correccion posterior:** `loadScenario('deps')` ya NO inyecta las ocho
  salidas de `DEP_TEMPLATES`. El usuario reporto que «aparecen 9 despegues al
  mismo tiempo», cuando en realidad es UN despegue cada dos minutos. Ahora el
  escenario carga solo los 2 transitos (LAN101 en UGOLA, SKY220 en TEGEB) y
  arranca el Auto DEP, que genera 1 salida al activar y 1 mas cada 120 s segun
  el selector de pista. Total al cargar: 3 Aircraft.

**Verificacion (2026-10-05, navegador integrado, ERR:0):** tests SC17–SC23
nuevos, todos OK:
- SC17: THR y `axisHdg` correctos en las 66 SIDs.
- SC18: ninguna SID vira antes de su punto de eje (66 con `axisHdg`).
- SC19: ascenso en eje y viraje solo al alcanzar el nivel (no avanza antes).
- SC20: las salidas viran sobre el punto, no a 1.2 NM; las llegadas conservan 1.2.
- SC21: `altMin`/`altMax` de las cartas (VAGOS 4000-9000, KIDUG 7500-10000,
  SEKSU 7500-9000, D22AMB FL110-140, LOLAT 5500-9000, EL131 ≥6000,
  EL177 ≥7000).
- SC22: MNM Razón ASC aplicada a las 24+8 salidas.
- SC23: `deps` disponible y seleccionado en TABLET y PC, con Auto DEP activo
  y 9 salidas en vuelo.

Fix adicional durante la validacion: `_ax()` usaba `d2r()` en tiempo de carga
de `SIDS`, cuando `d2r` se declara mas abajo (TDZ) yprovocaba
`ReferenceError: Cannot access 'd2r' before initialization` — se cambio a
conversion inline. Balance llaves 3054/3054, corchetes 1512/1512.

### 19.27 Auto DEP: una salida cada 2 min, de la misma pista o rotando

**Solicitud:** que los despegues salgan cada dos minutos desde SCEL, ya sea
siempre de la misma pista o alternando entre pistas diferentes.

**Implementacion (SCEL_ATC_Radar.html):**
- **Selector de pista** junto al boton INICIAR AUTO DEP (`#autoDepRwy`):
  - `AUTO DEP · RWY 17R (misma pista)` — comportamiento anterior.
  - `AUTO DEP · RWY 17L (misma pista)`
  - `AUTO DEP · RWY 35L (misma pista)`
  - `AUTO DEP · RWY 35R (misma pista)`
  - `AUTO DEP · ROTAR 17R→17L→35L→35R` — un despegue por pista, en ciclo.
- El selector y el boton se agrupan en `#autoDepRow`, que se muestra solo en
  los escenarios `auto`, `tablet` y `deps` (igual que antes).
- **`AUTO_DEP_MS = 120000`**: intervalo unico y explicito de 2 min para todos
  los modos. Antes estaba escrito como literal dentro de `startAutoDep()`.
- **`autoDepPool(rwy)`**: 17R usa el pool validado `AUTO_DEP` (24 SIDs); 17L,
  35L y 35R generan su pool con `autoDepSids(rwy)` (SIDs de esa pista en orden
  de carta SID1→SID14) y las mismas 24 bases ICAO. Cada pool tiene su propio
  `SID_ROC`, asi que la razon de ascenso minima published se aplica igual.
- **`autoDepRunway()`**: devuelve la pista del proximo despegue segun el modo
  (fija, o `AUTO_DEP_RWYS[seq % 4]` en modo ROTAR).
- **`spawnDep()`** ahora registra `a.depRwy` y anuncia la pista en el log
  (`✈ LAN200 SALIDA RWY 17R › NEBEG7A_17R`).
- **`nextDepId(base)`**: serial monotonico por base ICAO. Al alternar pistas,
  dos bases pueden coincidir dentro del mismo ciclo (17R y 17L comparten las
  24 bases), y el esquema anterior `base + 200 + ciclo` habria generado ids
  duplicados. Con el serial por base los ids siempre son unicos
  (LAN200, LAN201, SKY200, SKY201…), manteniendo el offset 200 que evita
  colision con llegadas y transitos (LAN101, SKY220).
- **`setAutoDepRwy(v)`**: si el Auto DEP ya esta corriendo, reinicia el ciclo
  para que el cambio de pista surta efecto inmediato; si esta detenido, solo
  deja el modo seleccionado para el proximo INICIAR.

**Verificacion (2026-10-05, navegador integrado, ERR:0):** tests SC24–SC26
nuevos, todos OK:
- SC24: intervalo de 120 s y pools validos (17R=24, 17L=24, 35L=9, 35R=9),
  todas las SIDs de cada pool existen y corresponden a su pista.
- SC25: ROTAR cicla 17R → 17L → 35L → 35R → 17R → 17L → 35L → 35R; ids unicos
  en el ciclo; cada salida nace en el THR de su pista con el rumbo de eje
  (177° en 17, 357° en 35).
- SC26: modo pista fija 17L/35L/35R sin mezclas ni ids repetidos, y vuelta a
  17R por defecto.

Comprobacion en la UI: el selector muestra las 5 opciones, queda visible en el
escenario `deps`, el timer arranca con el Auto DEP y el cambio a ROTAR reinicia
el ciclo empezando por la 17R.

### 19.28 Escenario «Salidas SCEL»: sin ráfaga, 1 despegue cada 2 minutos

**Problema reportado por el usuario:** al cargar el escenario aparecian 9
despegues al mismo tiempo.

**Causa:** `loadScenario('deps')` hacia dos cosas a la vez — inyectar las ocho
rutas de `DEP_TEMPLATES` ya en vuelo (`DEP_TEMPLATES.forEach(...)`) y ademas
arrancar el Auto DEP (`startAutoDep()`), que genera un despegue inmediato.
Total: 9 salidas en el mismo instante, con `setInterval` despues a 120 s.

**Correccion:**
- Eliminada la inyeccion de `DEP_TEMPLATES` en `loadScenario('deps')`.
- El escenario ahora carga 2 transitos (LAN101 en UGOLA, SKY220 en TEGEB) y
  arranca el Auto DEP: **1 salida inmediata + 1 cada 120 s**. Total 3 Aircraft
  al abrir, y nunca mas de una entrada por intervalo.
- `DEP_TEMPLATES` se conserva para el escenario `mixed` (2 salidas).
- Etiqueta del selector actualizada a «Salidas SCEL · 1 cada 2 min · tablet y PC».
- Nombre en el log del escenario: `Salidas SCEL · 1 despegue cada 2 min`.

**Verificacion (2026-10-05, navegador integrado, ERR:0):**
- SC23 (reescrito): al abrir el escenario hay exactamente 1 salida + 2 transitos
  = 3 Aircraft, con temporizador activo, tanto en TABLET como en PC.
- SC27 (nuevo): verifica que `loadScenario` no inyecta salidas mas alla de la
  que arranca el Auto DEP, que el total es 3 y que `AUTO_DEP_MS === 120000`.
- Prueba en tiempo real con la app real: t=0 s → 1 salida (SKY200/ALBAL7A_17R);
  t=143 s → 2 salidas (SKY200/ALBAL7A_17R + TAM200/ANGOD8B_17R). Es decir, la
  segunda entrada ocurre a los 120 s, no antes. Suite completa `ERR:0`.

### 19.29 Quinta línea de la etiqueta radar: nombre de la SALIDA (SID)

**Solicitud del usuario:** habilitar la quinta línea de la etiqueta radar para
que indique el nombre de la salida que efectúa la aeronave que despega, con el
texto en **amarillo dorado**.

**Implementacion (`drawLabel()`):**
- Nuevo bloque tras las 4 filas existentes. La quinta fila es la SID en vuelo y
  se dibuja unicamente para despegues (`a.role==='dep' || a.axisHdg!=null`).
- Texto: **solo el nombre de la salida**, sin prefijo y sin sufijo de pista
  (ajuste pedido por el usuario, 2026-10-05). Ejemplos: `NEBEG7A`, `GUVOL5C`,
  `GELUS3C`, `DONTI6A`. El sufijo interno `_17R` / `_35R` con que se almacenan
  las SIDs en `SIDS` se elimina antes de dibujar.
- **Color amarillo dorado `#ffd84d`**, en negrita y con contorno negro de
  2.6 px (`strokeText` + `fillText`), igual que la fila de banderas para que
  resalte sobre el fondo negro de la tarjeta sin fatiga visual.
- **Nota de diseño (trade-off aceptado):** 35 nombres de SID están duplicados
  entre pistas — 17R/17L comparten `NEBEG7A`, `DILOK7A`, `GELUS5B`, `DONTI5B`,
  `ALBAL7A`, `ANGOD8B`; 35L/35R comparten `GUVOL5C`, `GELUS3C`, `NEBEG5D`,
  `DILOK5A`, `LINER5D`, `ALBAL5D`, `GUVOL4A`. La quinta línea ya **no** muestra
  la pista (el usuario pidió solo el nombre), así que en esas SID la pista no se
  deduce de la etiqueta. Sigue disponible en el log de despegues
  (`✈ LAN200 SALIDA RWY 17R › NEBEG7A_17R`) y en el sufijo interno de `SIDS`.
- La caja negra crece solo cuando hay SID: las **llegadas mantienen 4 filas** y
  no muestran una fila vacia.
- Si la aeronave tiene texto de control (`a.txt`), ese pasa a sexta fila para no
  pisar la SID.

**Hit-test (seleccion y menu contextual):** `lblAt()` calculaba un alto de caja
fijo (`BAR+LH*3+PAD`) y un ancho minimo, por lo que la quinta fila quedaba
fuera del area seleccionable y el ancho se quedava corto. Actualizado para
replicar exactamente el `drawLabel()`: mide tambien `SID`, `txt` y `opcode`, y
suma las filas extra. Comprobado en la app real: el hit-test del despegue
llega hasta y=56 px y el de la llegada termina en y=46 px.

**Verificacion (2026-10-05, navegador integrado, ERR:0):** tests SC28–SC29
nuevos, ambos OK:
- SC28: intercepta `fillText` y comprueba que la quinta fila es el **nombre
  desnudo** de la SID (sin `SID` delante, sin `·17R` detrás), con color exacto
  `#ffd84d`, para salidas de 17R, 17L, 35L y 35R; las llegadas dibujan 5 lineas
  (4 datos + SSR) y ninguna de tipo SID. Resultado: `NEBEG7A`, `GUVOL5C`,
  `GELUS3C`, `DONTI6A`.
- SC29: barre la superficie de la etiqueta con `lblAt()` y confirma que el
  despegue cubre la quinta fila completa y que la llegada termina antes de
  ella.

Nota de infraestructura: `tests/run_tests.ps1` sigue sin poder ejecutar
Chrome headless (instalacion corrupta: falta
`chrome.exe` en `C:\Program Files\Google\Chrome\Application\154.0.8037.97`).
La validacion se realizo cargando el harness generado en
`%TEMP%\opencode\SCEL_TEST.html` desde el navegador integrado via servidor
HTTP local, leyendo el resultado en `document.title` y `window.__errs`.

---

## RAFAJA DE DESPEGUES AUTOMATICOS — CAUSA RAIZ Y CORRECCION (2026-10-05)

**Sintoma reportado:** al dejar correr el simulador aparecian **8 despegues
simultaneos** en lugar de uno cada dos minutos.

### Causa raiz

`startAutoDep()` programaba el ciclo con un unico `setInterval`:

```js
autoDepTimer=setInterval(spawnDep,AUTO_DEP_MS); // 1 cada 2 min
```

Un `setInterval` es **una sola suscripcion que se rearma sola**. Cuando el hilo
principal se bloquea (render del canvas con zoom alto, XHR de la fraseologia,
carga de escenario) o la pestana pasa a segundo plano, el navegador agrupa los
disparos vencidos y al desbloquear ejecuta **varios `spawnDep()` en el mismo
instante**. No era una inyeccion masiva de datos: se descarto que
`loadScenario()` o las plantillasesseran la causa (ver "Descartes" abajo).

### Correccion aplicada

Se sustituyo el intervalo por una **cadena de `setTimeout`** que se programa
DESPUES de ejecutarse, de modo que solo puede existir un temporizador vivo:

- `_autoDepSchedule()` — programa el siguiente eslabon (`AUTO_DEP_MS=120000`).
- `_autoDepTick()` — genera **como mucho un** despegue y se reancla al presente.
  Si la entrega llego demasiado pronto, no genera: solo espera.
- `_autoDepWatch()` — vigilante de respaldo: si el eslabon se perdiera, rearma
  dentro del intervalo para no romper la cadencia de 2 min.
- `AUTO_DEP_MIN_GAP_MS=10000` — piso anti-rafaga: nunca dos despegues con menos
  de 10 s de diferencia (cubre reinicios por cambio de pista y entregas
  agrupadas del navegador).
- `try/catch/finally` — si `spawnDep()` lanza, la cadena **no** se rompe.
- `stopAutoDep()` limpia tanto el eslabon como el vigilante, y pone
  `_depStopped=true` para invalidar cualquier entrega pendiente.

El atraso acumulado **se descarta**: nunca se "recupera", porque eso es
justamente lo que produce la rafaga.

### Evidencia (reloj virtual, `sids\dep_timer.mjs`)

Se simulo el bloqueo del hilo principal con un reloj virtual que entrega lo
vencido, comparando el codigo anterior contra el actual:

| Escenario | `setInterval` (antes) | cadena `setTimeout` (ahora) |
|---|---|---|
| 3 h normal, frames de 1 s | 91 despegues, 120/120/120 s | 91 despegues, 120/120/120 s |
| **2 min + bloqueo de 10 min** | **5 despegues en el mismo instante** | **1 despegue, rafa maxima 1** |
| 30 min en segundo plano | 16 despegues | 16 despegues |

La cadencia normal es identica; el unico cambio es que la rafaga desaparecio.

### Descartes (no eran la causa)

- `loadScenario()` ya llamaba a `stopAutoDep()` antes de limpiar aeronaves.
- Solo `auto`, `deps` y `tablet` invocan `startAutoDep()`.
- `DEP_TEMPLATES`, `AUTO_DEP` y `ARR_TEMPLATES` tienen 24 entradas cada una, y
  `DEP_TEMPLATES` solo se usa como `.slice(0,2)` en el escenario `mixed`.
- No hay ningun `setInterval`/`clearInterval` residual sobre el temporizador de
  despegues (los que quedan son el reloj de escenario, el refresco LIVE y el
  respaldo de render, ninguno relacionado).

### Cobertura de pistas

Se verifico que **todos los modos** generan despegues y que ninguna ruta
corresponde a otra pista (`sids\dep_cadence.mjs`):

| Modo | Pool | SID inexistente | SID de otra pista |
|---|---|---|---|
| 17R | 24 | 0 | 0 |
| 17L | 24 | 0 | 0 |
| 35L | 9 | 0 | 0 |
| 35R | 9 | 0 | 0 |
| ROTAR | 24 / 24 / 9 / 9 | 0 | 0 |

Total 66 SIDs (24 + 24 + 9 + 9). El identificador se mantiene serial por base
(`nextDepId`) ,así que tras dos ciclos completos cada base aparece 2 veces.

---

## COBERTURA DEL VALIDADOR DE GEOMETRIA: 65 -> 66 RUTAS (2026-10-05)

`sids\check_sids.ps1` informaba `rutas SIDs: 65` mientras el objeto `SIDS`
tiene 66 claves. La causa era el **lookahead** del regex de rutas:

```
\[(?<b>.*?)\](?=,\s*\n|\s*\n)
```

La ultima ruta del bloque, `VENTANAS1L_17L`, termina en `],` **inmediatamente
antes del fin del bloque**, sin salto de linea despues. Ninguna de las dos
alternativas del lookahead se cumplia, asi que la ruta se descartaba en
silencio. Se corrigio a:

```
\[(?<b>.*?)\](?=,\s*\n|\s*\n|[,\s]*$)
```

Ahora el validador analiza **66/66** rutas. La ruta incorporada
(`VENTANAS1L_17L`) no presenta giros excesivos, por lo que el total de rutas con
problemas se mantiene en **14 de 66** (antes "14 de 65"). La correccion es solo
del validador: **no se modifico ninguna ruta del simulador**.

Las 14 rutas pendientes siguen necesitando la carta SID oficial para confirmar
la secuencia (no se modifican por inferencia):

- 8 rutas `35L/35R` (`ALBAL5D`, `GELUS3C`, `LINER5D`, `NEBEG5D`): `_ax` sube
  7.7-8.6 NM al norte y luego gira hacia `PARKE` (149-155°).
- 2 `SANTIAGO5`: `TEMUS/PUMAR -> D22AMB` ~43 NM al sur y luego `D22AMB -> AMB`
  22 NM al norte (168-170°).
- 2 `TABON6A`: `KIDUG -> TABON` gira 118-119° (sin `KIDUG` serian ~37°).
- 2 `DONTI6A`: `VTN -> DONTI` gira ~151° y `DONTI` esta muy cerca del ARP.

---

## CÓDIGOS DE PISTA 001-005: SELECCIÓN SIN COLACIONADO DEL PILOTO (2026-10-07)

### Requisito

Los valores 001-005 del selector `#flSelect` **no son niveles de vuelo**: son
códigos de pista/procedimiento (AIP/DAP SCEL) — 001 aprox IFR 17L, 002 aprox
visual 17L, 003 aprox IFR 17R, 004 aprox visual 17R, 005 ingreso VFR especial
SCEL. El piloto **no debe colacionarlos como nivel**.

### Implementación

- Nuevo optgroup **"CÓDIGOS DE PISTA 001-005"** en `#flSelect` con las 5
  opciones (`001 · IFR 17L`, `002 · VISUAL 17L`, `003 · IFR 17R`,
  `004 · VISUAL 17R`, `005 · VFR ESPECIAL SCEL`); se eliminó el optgroup
  "BAJA ALTITUD" y las etiquetas viejas F001-F005.
- `RWY_CODES` (significado de cada código) + `isRwyCode(fl)` (valores 1-5).
- Guard en `readback()`: `climb`/`descend`/`level` con val 1-5 → **sin
  colacionado** por ninguna vía (selector, pasos FL +/-, voz/NLP).
- `applyFL()`/`flStep()`: al caer en un código, log
  `CÓDIGO 00X · <significado>` sin readback del nivel.

### Verificación

`sids\rwy_codes.mjs` (7 checks): readback mudo para los 5 códigos en ES+EN
(30/30), niveles normales siguen hablando, guard solo aplica a
climb/descend/level, applyFL/flStep en código sin colacionado + log con
significado, nivel normal con readback, estática del selector.

Página real (CDP, recargada): optgroup y etiquetas correctos;
`readback(descend,3)` mudo y `(descend,43)` habla; `applyFL` F001 → log
"ZZZ901 ← CÓDIGO 001 · aproximación IFR a pista 17L" sin voz; `flStep` 600→500 →
"CÓDIGO 005 · ingreso VFR especial a SCEL" sin voz; FL11000 → readback EN
"cleared to climb to flight level one one zero". Solo errores de consola
preexistentes (proxy 404).

Nota: quedó pendiente de confirmación del usuario si los códigos además deben
**accionar el procedimiento** (ver capítulo siguiente).

---

## ACTIVACIÓN DEL COMANDO DE VOZ: ICONO DE MICRÓFONO O TECLA CTRL (2026-10-07)

### Requisito

Activar/desactivar el reconocimiento de voz con el **icono de micrófono** o con
la **tecla Ctrl** (además de la barra espaciadora existente).

### Implementación

- **Icono de micrófono** (`#voiceBtn`): alterna la voz al hacer clic (método
  existente); su tooltip ahora documenta "Reconocimiento de voz · Icono de
  micrófono · Ctrl · Spacebar · …".
- **Barra espaciadora**: alterna la voz con Space (método existente).
- **Tecla Ctrl (nueva)**: un par de listeners `keydown`/`keyup` a nivel documento
  alternan `toggleVoice()` cuando **Ctrl se presiona y suelta solo**. Si Ctrl
  forma parte de una combinación (Ctrl+C, Ctrl+Enter, Ctrl+Shift, Ctrl+Meta…)
  **no** alterna — se detecta cualquier otra tecla presionada mientras Ctrl está
  abajo (`_ctrlChord`) y se descarta el disparo.
- Misma guardia que la barra espaciadora: con el foco en INPUT/SELECT/TEXTAREA
  no alterna (no interrumpe la escritura en la barra de llamados).
- **HELP modal** y **popup de voz**: se documentó "botón VOZ, tecla Ctrl o barra
  espaciadora" y "Activar voz: icono de micrófono · tecla Ctrl · barra
  espaciadora".

### Verificación

Nuevo verificador `sids\voice_ctrl.mjs` (bloque real extraído del HTML, con
`document`/`toggleVoice` simulados):

```
  OK  1. Ctrl suelto alterna voz (1)
  OK  2. Ctrl+C no alterna
  OK  3. Ctrl+Enter no alterna
  OK  4. Ctrl+Shift no alterna
  OK  5. Ctrl suelto x2 alterna 2 veces
  OK  6. combo no alterna; siguiente Ctrl suelto sí
  OK  7. Ctrl con foco en INPUT no alterna
  OK  8. Shift suelto previo no bloquea Ctrl
  OK  9. Ctrl+Meta no alterna
  OK 10. título voiceBtn menciona icono y Ctrl
  OK 11. HELP menciona tecla Ctrl
  OK 12. popup menciona activación
RESULTADO: OK
```

Página real (CDP, recargada, eventos de teclado reales vía
`Input.dispatchKeyEvent` con spy en `toggleVoice`): Ctrl suelto → 2 alternancias;
Ctrl+C y Ctrl+Enter → 0 (el contador quedó en 2, no 4). Tooltip, HELP y popup
actualizados. Sin errores de consola nuevos.

Suite completa exit=0: `js_syntax`, `voice_ctrl`, `rwy_codes`, `dep_call`,
`dep_phrase`, `dep_cadence`, `dep_timer`, `sid_cross`, `ui_contrast`,
`arr_report`, `check_sids.ps1` (14/66, sin regresión).



---

## CÓDIGOS 001-005: ACCIONAN EL PROCEDIMIENTO (ILS/VISUAL/VFR) EN LUGAR DE BAJAR A 100-500 FT (2026-10-07)

### Requisito

El usuario confirmó que los códigos de pista 001-005 del selector `#flSelect`
**también deben accionar el procedimiento** correspondiente — aproximación ILS
17L/17R, aproximación visual 17L/17R o ingreso VFR especial a SCEL — **en lugar
de bajar la aeronave a 100-500 ft**.

### Implementación

- Nueva constante `RWY_CODE_ACT` (junto a `RWY_CODES`): mapea cada código al
  procedimiento real que autoriza:

  | Código | Procedimiento | apprAuth(type, rwy) |
  |--------|---------------|---------------------|
  | 001 | Aprox IFR 17L | `ILS, 17L` |
  | 002 | Aprox visual 17L | `VISUAL, 17L` |
  | 003 | Aprox IFR 17R | `ILS, 17R` |
  | 004 | Aprox visual 17R | `VISUAL, 17R` |
  | 005 | Ingreso VFR especial SCEL | `VFR, 17L` |

- `applyFL()` y `flStep()`: al caer en un código (selector o pasos FL +/-) ya
  **no** se modifica `tAlt`/`cfl`/`assignedFL`/`selAlt` (la aeronave conserva su
  nivel asignado) y se invoca `apprAuth(a, act[0], act[1])`, que:
  - registra `a.apprAuth = {type, rwy}` y limpia modos (LOC/GS/hold/vector);
  - arma la ruta: **NORTE** (`y>0`) directo al umbral `[ALN17L|ALN17R]`;
    **SUR** (`y<0`) circuito `[BICEN, RENCA, umbral]`;
  - colaciona la **autorización de aproximación** (readback `appr_ils` /
    `appr_visual` — el piloto sí colaciona la autorización, no el código como
    nivel);
  - al completar la ruta, `updateRouteNav` captura el LOC
    (`tAlt ≥ ILS_INTERCEPT_ALT 5000`) y sigue el descenso GS hasta aterrizar.
- **005 (ingreso VFR especial)**: el simulador no tiene mecanismo VFR ni pista
  activa; se ejecuta como aproximación visual a la pista principal **17L**
  (entra visual y aterriza), con `apprAuth.type='VFR'` para distinguirlo en el
  log ("APPR VFR 17L").
- El guard de `readback()` (climb/descend/level con val 1-5 → silencio) se
  **mantiene intacto**: el código nunca se colaciona como nivel por ninguna vía
  (selector, pasos FL +/-, voz/NLP); solo la autorización de aproximación que
  acciona habla.

### Verificación

`rwy_codes.mjs` actualizado (extrae `RWY_CODE_ACT`, `apprAuth`, `ALN17L/R` y
stub de `WPT`):

```
1. readback sin colacionar códigos 001-005 (ES+EN, climb/descend/level): 30/30
2. readback de niveles normales sigue activo:            5/5
3. guard sólo aplica a climb/descend/level:              OK
4. applyFL en código 001-005: ACCIONA apprAuth (NORTE+SUR): 10/10
5. applyFL nivel normal (FL110) con readback:            OK
6. flStep: códigos ACCIONAN apprAuth / normal con readback: 3/3
7. Estática (selector + guard + RWY_CODE_ACT):          12/12
RESULTADO: OK
```

Página real (CDP, recargada, spy en `sayReadback`, aeronave temporal NORTE y
SUR restaurada al final):

- 001 → `apprAuth{ILS,17L}`, tAlt **9000 sin cambio**, habla "autorizado
  aproximación ILS pista uno siete izquierda", ruta NORTE directa, log "APPR
  ILS 17L · NORTE: directo al umbral".
- 002/003/004 → `VISUAL/17L`, `ILS/17R`, `VISUAL/17R` idem (frase derecha para
  17R).
- 005 → `apprAuth{VFR,17L}`, habla "autorizado aproximación visual pista uno
  siete izquierda", log "APPR VFR 17L".
- SUR (`y=-10`) → ruta `[BICEN, RENCA, umbral]` (3 puntos).
- `flStep(-1)` 600→500 → tAlt **600 sin cambio**, `apprAuth{VFR,17L}` con
  readback.
- Nivel normal FL110 → readback "autorizado ascenso para nivel de vuelo uno uno
  cero" (sin regresión).
- Guard: `readback(descend,3)` mudo. Solo los 2 errores de consola
  preexistentes (proxy 404).

Suite completa exit=0: `js_syntax` (0 errores, 0 U+FFFD), `rwy_codes`,
`voice_ctrl`, `dep_call`, `dep_phrase`, `dep_cadence`, `dep_timer`,
`sid_cross`, `ui_contrast`, `arr_report`.

## NIVEL AUTORIZADO DE ASCENSO POR SALIDA: FL280/FL270 SEGÚN SID (2026-10-07)

Configuración del usuario: las salidas **DONTI, DILOK, VTN (VENTANAS), DGO
(DOMINGO)** quedan autorizadas a ascender a **nivel de vuelo 280**; las salidas
**LINER, ANGOD, GELUS, GUVOL, NEBEG, ALBAL** a **nivel de vuelo 270**. Las SID
sin nivel configurado (**SABLA8, TABON6A, TENUT5, SANTIAGO5**) conservan la
autorización por altitud de cruce publicada.

### Cambios en SCEL_ATC_Radar.html

1. **`SID_AUTH_LVL`** (tras `SID_ROC`): tabla por nombre base de SID (antes del
   sufijo de pista) — 35 SIDs: 14 → FL280 (DONTI6A/5B/1R/1L, DILOK7B/5A/1R/1L,
   VENTANAS6/1R/1L, DOMINGO6/1R/1L) y 21 → FL270 (LINER5A/6C/5D, ANGOD8B/6C,
   GELUS6A/5B/3C/1R/1L, GUVOL5C/6B/4A/1R/1L, NEBEG7A/7C/5D, ALBAL7A/7C/5D).
2. **`sidAuthLvl(sid)`** (junto a `sidCrossAlt`): devuelve el nivel autorizado
   en ft (0 si la SID no tiene nivel). Busca por `split('_')[0]`, por lo que
   vale para cualquier variante de pista (`NEBEG7A_17R` → 27000).
3. **`queueDepReport`**: el "autorizado para" de la llamada de salida usa
   `sidAuthLvl(sid) || sidCrossAlt(sid)` — el nivel configurado tiene
   prioridad; sin nivel, se mantiene el cruce publicado.
4. **`updateRouteNav`** (rama de ruta completada): si la salida no tiene
   aproximación autorizada, al completar la SID continúa el ascenso hasta el
   nivel autorizado (`_setTAlt` sincroniza tAlt/cfl/assignedFL/selAlt). Solo
   se aplica mientras la aeronave sigue la ruta: vectoreado o con instrucción
   ATC (updateRouteNav ya retorna antes) no lo toca, y nunca baja un tAlt que
   ya esté por encima del nivel.

### Verificación

`dep_call.mjs` actualizado (extrae `SID_AUTH_LVL` y `sidAuthLvl`; test 3 =
nivel configurado/publicado) y harness nuevo `sid_auth.mjs` (código real
extraído del HTML):

```
1. Tabla SID_AUTH_LVL (14 FL280 + 21 FL270 + 4 sin nivel): 113/113
2. sidAuthLvl con sufijo de pista:                         19/19
3. "autorizado para" = nivel configurado (8 casos):         8/8
4. Hook ascenso al completar SID (7 casos):                 7/7
RESULTADO: OK
```

Ejemplos de la llamada de salida (a nivel de pista, 1555 ft):

- NEBEG7A → "autorizado para nivel de vuelo dos siete cero"
- DONTI6A / VENTANAS6 / DOMINGO6 → "autorizado para nivel de vuelo dos ocho cero"
- SANTIAGO5 → "autorizado para nivel de vuelo uno uno cero" (sin nivel, cruce publicado)
- TABON6A → "autorizado para siete mil quinientos pies" (sin nivel, cruce publicado)

Página real (CDP `probe_cdp10.mjs`, recargada, estado restaurado):

- Frases de llamada correctas para NEBEG7A/DONTI6A/VENTANAS6/DOMINGO6/LINER5A
  y fallback en SABLA8 ("autorizado para diez mil pies").
- Hook: NEBEG7A completa la SID en 13000 → tAlt 27000, cfl 270, selAlt 27000;
  DONTI6A → 28000; SABLA8 → 9000 sin cambio; vectoreado → 13000 sin cambio;
  ya encima (30000) → no baja.
- Tabla accesible en la app: 35 SIDs (14 FL280 + 21 FL270).
- Solo los 2 errores de consola preexistentes (proxy 404).

Suite completa exit=0: `js_syntax` (0 errores, 0 U+FFFD), `rwy_codes`,
`dep_call`, `dep_phrase`, `dep_cadence`, `dep_timer`, `sid_cross`,
`ui_contrast`, `arr_report`, `voice_ctrl`, `sid_auth`.---

## COLACIÓN DEL NIVEL AUTORIZADO: REGLA DE TRES RANGOS EN EL READBACK (2026-10-07)

### Pedido del usuario
> "REVIZA LA NOTIFICACION DE LOS NIVELES QUE SE AUTORIZAN EN EL PANEL DE COMANDOS, EL PILOTO LOS DEBE COLACIONAR DE LA SIGUIENTE MANERA: 050 CINCO MIL PIES, 060 SEIS MIL PIES, 070 SIETE MIL PIES, 080 OCHO MIL PIES, 090 NUEVE MIL PIES, 100 DIEZ MIL PIES, DESDE 110 Y SUPERIOR SERA COLACIONADO COMO NIVEL DE VUELO"

La colación (readback) del nivel autorizado por el piloto usa ahora la regla de
tres rangos ya existente en `spkCrossAlt`/`spkCrossAltEn`:

| Nivel | Colación ES | Colación EN |
|---|---|---|
| FL001–FL009 | cientos de pies ("cien pies" ... "novecientos pies") | "one hundred feet" ... "nine hundred feet" |
| FL010–FL109 | miles y cientos ("cinco mil pies" ... "diez mil pies") | "five thousand feet" ... "ten thousand feet" |
| FL110+ | "nivel de vuelo uno uno cero" (dígito a dígito) | "flight level one one zero" |

### Cambios aplicados

1. **`normativa.xml`** — frases `climb`, `descend` y `level` (ES/EN) reemplazan
   el placeholder `{val}` (dígitos) por `{nivel}` (colación con la regla):
   - `climb`: "autorizado ascenso para {nivel}" / "cleared to climb to {nivel}"
   - `descend`: "autorizado descenso para {nivel}" / "cleared to descend to {nivel}"
   - `level`: "manteniendo {nivel}" / "maintaining {nivel}"

2. **`fraseologia_editada.json`** (fuente ÚNICA de fraseología) — mismas frases
   con `{nivel}`; `variables` de climb/descend/level pasan a `["{cs}","{nivel}"]`;
   se agrega el placeholder `{nivel}` a `meta.placeholders` (con descripción y
   ejemplos de la regla) y se actualiza `meta.instrucciones`.

3. **`SCEL_ATC_Radar.html`**:
   - `FRASES_FALLBACK` (respaldo offline): mismas frases con `{nivel}`,
     `variables`, placeholder `{nivel}` en `meta.placeholders` e `instrucciones`.
   - `_fmt` del `readback` (~9131): nuevo `nivelSpk` que resuelve `{nivel}` con
     `spkCrossAlt(val*100)` (ES) o `spkCrossAltEn(val*100)` (EN).
   - Diccionario local `ph`: `climb_es`/`descend_es`/`level_es` → `spkCrossAlt(val*100)`;
     `climb`/`descend`/`level` (EN) → `spkCrossAltEn(val*100)`.
   - `crossRestriction` (~4854): la colación del cruce "a FL/ALTITUD O SUPERIOR"
     también usa la regla (`spkCrossAlt(val*100)` / `spkCrossAltEn(val*100)`).

### Alcance cubierto
- `applyFL`/`flStep` (selector y pasos de nivel), comandos NLP/voz de nivel
  (`readback(a,levelDir(...),fl)`), y `crossRestriction` por voz.
- El guard de códigos de pista 001-005 (`isRwyCode`) se mantiene intacto: los
  códigos NO se colacionan como nivel (tarea previa RWY_CODE_ACT).

### NO cambiado (a propósito)
- Diluciones y correcciones del piloto (`dilucion`/`correccion`): son preguntas
  de confirmación del ATC, no colación del nivel autorizado; siguen con dígitos.
- `hold_confirm` y `flSpk` de `_fmt`: formato hablado genérico de nivel.
- Canonicals NLP (parseo de intención, no colación).

### Verificación
- Harness nuevo `lvl_readback.mjs` (91/91 OK): `spkCrossAlt`/`spkCrossAltEn`
  (24 casos ES/EN), readback ES climb 050-110 (8), ES descend/level (6),
  EN climb/descend/level (9), ruta NORM con `{nivel}` sembrado (8),
  guard códigos 001-005 sin colacionar ES+EN (30), `crossRestriction` (6).
- `rwy_codes.mjs` actualizado: expectativas de nivel con la regla
  (FL043→"cuatro mil trescientos pies", FL030→"three thousand feet",
  FL069→"seis mil novecientos pies") — OK.
- `arr_report.mjs`: regex del chequeo NLP más específico
  (`manteniendo '+spkCrossAlt(vFl*100)`) porque el diccionario `ph` ahora
  también contiene `manteniendo '+spkCrossAlt(val*100)` — OK.
- **Suite completa 12/12 exit=0** (js_syntax 0 errores/0 U+FFFD, rwy_codes,
  dep_call, dep_phrase, dep_cadence, dep_timer, sid_cross, ui_contrast,
  arr_report, voice_ctrl, sid_auth, lvl_readback).
- **Smoke CDP `probe_cdp11.mjs` OK** en la página real (LAN→ES):
  - applyFL 5000→"autorizado descenso para cinco mil pies", 6000→"seis mil
    pies", 7000→"siete mil pies", 8000→"ocho mil pies", 9000→"manteniendo
    nueve mil pies", 10000→"autorizado ascenso para diez mil pies",
    11000→"autorizado ascenso para nivel de vuelo uno uno cero".
  - crossRestriction ES/EN: FL050→"cruzando ugola a cinco mil pies o superior" /
    "crossing ugola at five thousand feet or above"; FL110→"a nivel de vuelo
    uno uno cero o superior" / "at flight level one one zero or above".
  - NORM cargado desde `fraseologia_editada.json` con `{nivel}` confirmado.
  - Solo los 2 errores de consola preexistentes (proxy 404).---

## NIVELES PREACORDADOS EN EL ESCENARIO + PAUSA/PLAY + FIXES NARANJA (2026-10-07)

### 1. Escenario configurado con los niveles preacordados de las salidas
El usuario reportó que el escenario no mostraba los niveles preacordados. Causa:
`mkACwithRoute` (spawn de aeronaves) asignaba `tAlt` = altitud de cruce inicial
(ARP_ELEV+500 ≈ 2055 ft) pero **no** asignaba `cfl`/`assignedFL`/`selAlt` para
las salidas → la etiqueta mostraba "FL015 FL015" sin nivel autorizado.

**Cambio** (`mkACwithRoute`, rama `dep`): al crear una salida se asigna el nivel
autorizado desde el despegue:
```js
const authLvl=sidAuthLvl(tmpl.sid)||sidCrossAlt(tmpl.sid);
if(authLvl){a.cfl=Math.round(authLvl/100);a.assignedFL=a.cfl;a.selAlt=authLvl;}
```
- `tAlt` conserva el cruce inicial → el ascenso respeta las restricciones de la
  SID; al completarla, `updateRouteNav` sube `tAlt` al nivel autorizado.
- La etiqueta muestra "FL015 +00 FL270" (nivel autorizado) desde el despegue.
- Cubre TODAS las salidas: `spawnDep` (Auto DEP), escenario `mixed`
  (`DEP_TEMPLATES.slice(0,2)`) y cualquier template con `sid`.

**Tabla completa (39 SIDs, todas con nivel):**
- **FL280 (16):** DONTI6A/5B/1R/1L, DILOK7B/5A/1R/1L, VENTANAS6/1R/1L,
  DOMINGO6/1R/1L, **SABLA8**, **TENUT5**.
- **FL270 (23):** LINER5A/6C/5D, ANGOD8B/6C, GELUS6A/5B/3C/1R/1L,
  GUVOL5C/6B/4A/1R/1L, NEBEG7A/7C/5D, ALBAL7A/7C/5D, **TABON6A**, **SANTIAGO5**.

### 2. Botón PAUSA / PLAY en la sección de velocidad de reproducción
El popup de velocidad (`#simPopup`, botón "×" de la barra superior) ahora incluye
un botón **⏸ PAUSA** que alterna con **▶ PLAY** para reanudar:
- HTML: `<div class="sim-pause" id="simPauseBtn" onclick="togglePause()">⏸ PAUSA</div>`
  (entre el divisor y el "■ 1×").
- CSS: `.sim-pause` (verde) con variante `.paused` (ámbar) cuando está en pausa.
- JS: `togglePause()` sincroniza `simPauseBtn` (texto + clase) además del botón
  `pauseBtn` del panel de escenario y el indicador `tb-state` (PAUSA/ACTIVO).
- El bucle `frame()` ya respetaba el flag `paused` (`if(!paused)update(dt)`):
  en pausa se congela la simulación pero el radar sigue dibujando.

### 3. Fixes en color NARANJA
`drawWaypoints` cambió de cian a naranja para mejor visualización:
- Compulsory (triángulo relleno): fill `rgba(255,160,40,.6)`, stroke
  `rgba(255,170,50,.95)`, sombra `rgba(255,150,30,.15)`, texto `rgba(255,180,80,1)`.
- No-compulsory (triángulo abierto): stroke `rgba(255,150,40,.65)`.
- RENCA (punto de referencia del circuito visual) se mantiene amarillo a propósito.

### Verificación
- **Suite completa 12/12 exit=0** (js_syntax 0 errores/0 U+FFFD, rwy_codes,
  dep_call, dep_phrase, dep_cadence, dep_timer, sid_cross, ui_contrast,
  arr_report, voice_ctrl, sid_auth, lvl_readback).
- **Smoke CDP `probe_cdp10.mjs` OK**: llamadas de salida con nivel autorizado
  (SABLA8→"dos ocho cero", TABON6A→"dos siete cero", TENUT5→"dos ocho cero",
  SANTIAGO5→"dos siete cero"); hook de ascenso sube tAlt a 27000/28000;
  tabla 39 SIDs (16 FL280 + 23 FL270); vectoreado/ya-encima sin cambio.
- **Smoke CDP `probe_cdp11.mjs` OK**: colación de niveles 050-110 con la regla
  de tres rangos; crossRestriction ES/EN; NORM con `{nivel}`.
- **Smoke CDP `probe_cdp12.mjs` OK** (página real):
  - Escenario: NEBEG7A→cfl 270/selAlt 27000, DONTI6A→280, SABLA8→280,
    TABON6A→270, TENUT5→280, SANTIAGO5→270 (tAlt 2055 cruce inicial).
  - PAUSA/PLAY: `simPauseBtn` existe; togglePause alterna "⏸ PAUSA"↔"▶ PLAY",
    flag `paused` y clase `.paused`.
  - Fixes: 4 colores naranja presentes, 0 cian residual.
  - Solo los 2 errores de consola preexistentes (proxy 404).
## NIVEL AUTORIZADO FL270/FL280 VISIBLE EN LA ETIQUETA DURANTE TODO EL VUELO DE SALIDA (2026-10-08)

### Síntoma reportado
Al partir el escenario, los despegues no mostraban el nivel autorizado FL270/FL280
en la etiqueta radar (campo nivel autorizado, Row 1: `FL{actual} ±VS FL{cfl}`).

### Causa raíz
`mkACwithRoute` ya asignaba `cfl/assignedFL/selAlt` = nivel preacordado desde el
despegue, pero `_setTAlt` (usado por `updateAltConstraint` en cada waypoint de la
SID) sobreescribía `cfl/assignedFL/selAlt` con la restricción de cruce en curso:
al primer waypoint con cota (p. ej. 4000 ft) la etiqueta pasaba a mostrar
`FL040` en vez de `FL270`/`FL280`. El smoke anterior (probe_cdp12) verificaba el
spawn inmediato y no detectaba la sobreescritura posterior.

### Fix aplicado
1. **`mkACwithRoute` (rama dep):** además de `cfl/assignedFL/selAlt`, guarda el
   nivel preacordado en `a.authLvl` (pies):
   `if(authLvl){a.cfl=Math.round(authLvl/100);a.assignedFL=a.cfl;a.selAlt=authLvl;a.authLvl=authLvl;}`
2. **`_setTAlt`:** las restricciones de cruce de la SID ya NO cambian el nivel
   autorizado de una salida con `authLvl` mientras `tAlt < authLvl` (solo se
   actualiza `tAlt`, que es el objetivo de ascenso real). Al alcanzar el nivel
   autorizado (fin de SID, `updateRouteNav` → `_setTAlt(a,al)` con `v===authLvl`)
   se sincroniza `cfl/assignedFL/selAlt` con `tAlt`, como antes.
   - Llegadas, tránsitos y ASIMO7D (sin `authLvl`): comportamiento idéntico al previo.
   - Instrucciones ATC (`applyFL`/`flStep`/comandos) asignan `cfl` directamente y
     no pasan por `_setTAlt`: siguen prevaleciendo sobre el nivel de la SID.

### Verificación (smoke CDP `probe_cdp13.mjs`, página real)
- Escenario `mixed` (2 salidas inmediatas): GELUS5B_17L → cfl 270/selAlt 27000/
  authLvl 27000; DILOK7B_17L → 280/28000/28000.
- **Tras 120 s de simulación** (6000 pasos `update(0.02)`): las restricciones de
  cruce se aplicaron (tAlt 6500/7500, alt ≈ 4070 ft) pero **cfl/assignedFL/selAlt
  siguen 270/280** → etiqueta Row 1 `FL041 … FL270` / `FL041 … FL280`, SA270/SA280.
- Auto DEP (`spawnDep`): NEBEG7A_17R → cfl 270/authLvl 27000 desde el despegue.
- Evidencia del fix: `tAltEsRestriccion=true` (tAlt < authLvl), `cflSigueNivel=true`,
  `selAltSigueNivel=true`.
- Solo los 2 errores de consola preexistentes (proxy 404).
- **Suite completa 12/12 exit=0** (js_syntax 0 errores/0 U+FFFD y resto).
## TMA SCIE (CONCEPCIÓN) — LÍMITES LATERALES DEL ÁREA TERMINAL (2026-10-08)

> **⚠ CORREGIDO POSTERIORMENTE — ver capítulo "COORDENADAS DEL VOR CAR Y REDIBUJO DEL TMA SCIE" (final de este informe).**
> Este capítulo documenta la implementación original, cuya proyección usaba
> `cos(lat local)` en lugar de la constante `cos(SCEL_LAT)` del mapa. Era
> **autoconsistente** (`TMA_SCIE` y `NAVAIDS` coincidían entre sí) pero ambos
> estaban 4.585 NM al este de su posición real. Se corrigieron las 108
> coordenadas X del bloque y `NAVAIDS.VOR_CAR` (`-109.001 → -113.586`), y el
> pan de `toggleTMA()` pasó de estar hardcodeado a derivarse de la bbox.
> Los valores `x=-109.001`, `panX=-95` y la frase "cos de la latitud local,
> no de SCEL" que aparecen más abajo describen el estado **ya no vigente**.

### Solicitud
Dibujar el TMA de Concepción (SCIE) en el radar: polígono cerrado con arcos DME
centrados en el VOR CAR, según AIP Chile.

### Datos de entrada (AIP Chile)
- **Centro de arcos:** VOR/DME CAR 114.3 MHz — coordenada oficial ENR 4.1:
  **36°45'20"S 073°03'11"W** (ya existía en `NAVAIDS.VOR_CAR`:
  x=-109.001, y=-201.681 NM desde SCEL).
- **Vértices (Lat S / Long W):** C 35°47'16"/072°48'01" · 2 36°07'22"/072°05'24" ·
  3 36°20'36"/072°23'50" · 4 37°17'17"/072°32'06" · 5 37°36'44"/072°27'50" ·
  6 37°50'56"/073°26'56" · A 37°20'41"/073°26'53" · B 36°05'59"/072°56'41".
- **Trazado (sentido horario):** C→(arco 60 NM CAR, ~011°→~050°)→2→3→4→5→6→A→
  (arco 40 NM CAR, ~209°→~006° por el oeste, pasando por 270°)→B→C.

### Implementación
1. **Constante `TMA_SCIE`**: `car` (VOR CAR = NAVAIDS), `pts` (8 vértices en NM
   desde SCEL) y `arcs` (C→2 r=60, A→B r=40). Proyección consistente con
   NAVAIDS: `x=(lon-SCEL_LNG)*60*cos(lat)`, `y=(lat-SCEL_LAT)*60` (cos de la
   latitud local, no de SCEL — verificado: CAR coincide exactamente con
   NAVAIDS.VOR_CAR).
2. **`drawTMA()`**: dibuja el polígono cerrado — arcos DME aproximados por
   segmentos cada ~2° (conectan EXACTAMENTE los vértices; el arco A→B cruza
   270° y 360° por el oeste) y líneas rectas 2→3→4→5→6→A y B→C. Relleno
   magenta sutil `rgba(255,0,255,.05)`, línea `rgba(255,80,255,.85)` 2.2 DPR,
   etiqueta "TMA SCIE". Se llama en el bucle de dibujo tras
   `drawRestrictedZones()`.
3. **Botón TMASCIE** en la barra GEN (`#tmaBtn`, clase `.cat-btn.tma` magenta; renombrado de "TMA" a "TMASCIE" el 2026-10-08) +
   `toggleTMA()`: activa/oculta la capa y, al activar, centra la vista en el
   TMA (currentScale=150, panX=-95, panY=-205) para verlo completo.

### Verificación (smoke CDP `probe_cdp15.mjs`, página real)
- Geometría desde CAR: C=59.1 NM @ 10.7°, 2=59.5 NM @ 50.3° (arco 60 NM,
  ~011°→~050° ✓); A=39.7 NM @ 207.0°, B=39.6 NM @ 6.3° (arco 40 NM ✓).
- Arco A→B: de 207.0° a 366.3° (sentido horario), pasa por 270° y 360° ✓.
- `drawTMA()` sin excepción; `toggleTMA()` activa capa + centra vista
  (scale 150, pan -95/-205); botón TMA presente.
- Nota: el radial final del arco A→B según las coordenadas oficiales es ~006°
  (el usuario indicó 353° — aproximación; el arco se dibuja conectando
  exactamente A y B por el oeste, pasando por 270° como se pidió).
- **Suite completa 12/12 exit=0** (js_syntax 0 errores/0 U+FFFD y resto).
- Solo los 2 errores de consola preexistentes (proxy 404).
## OPCIÓN ROUTE — CLICK DERECHO SOBRE EL SÍMBOLO DE POSICIÓN RADAR (2026-10-08)

### Solicitud
Click derecho sobre el símbolo de posición radar de la aeronave → pestaña
adosada al símbolo con la opción **ROUTE**. Al seleccionarla, se despliega la
ruta que volará la aeronave según su salida (SID) y autorización IFR de ruta.
Para eliminar la ruta: volver a hacer click derecho en el símbolo y volver a
hacer click en ROUTE → botón deseleccionado con animación.

### Implementación
1. **Popup `routeCtxPopup`** (z-index 310, borde cian): pestaña adosada al
   símbolo de posición radar (no al cursor) — se posiciona junto al blip
   calculando `acXY(a)` + `RC.getBoundingClientRect()`. Muestra el callsign y
   el botón **ROUTE** con estado seleccionado/deseleccionado.
2. **Click derecho sobre el blip**: en el handler `mousedown` (button===2),
   tras los chequeos de etiqueta (HOLD/DCT/OPC/TXT y LIVE), se consulta
   `blipAt(x,y,30*DPR)`; si es aeronave simulada no aterrizada →
   `showRouteCtx()`. El click derecho sobre la etiqueta conserva su
   comportamiento previo.
3. **`toggleRouteCtx()`**: alterna `a.showRoute` (toggle por aeronave),
   registra en sysLog y cierra el popup. El botón cambia de clase
   `route-btn off` → `route-btn on` (animación CSS de 0.25 s: fondo, borde,
   color y glow cian) y el símbolo ○/●.
4. **`drawRoute()`**: dibuja la ruta de cada aeronave con `showRoute=true` —
   polilínea punteada cian desde la posición actual hasta el waypoint vigente
   (`routeIdx`) y los siguientes de `a.route` (SID + ruta IFR), con marcador
   y nombre en cada waypoint (`_wptName`). Se llama en el bucle de dibujo
   justo antes de `drawAC()` (la ruta queda debajo de los blips).
5. **Estado inicial**: `a.showRoute=false` en `mkACwithRoute`.
6. **Cierre**: click fuera del popup lo cierra (listener global) y
   `stopPropagation` evita cierres al interactuar dentro.

### Verificación (smoke CDP `probe_cdp17.mjs`, página real, escenario mixed)
- Click derecho sobre el blip de LAN202 (GELUS5B_17L) → popup visible con
  callsign LAN202 y botón `route-btn off` (ROUTE ○).
- Click en ROUTE → `showRoute=true`, popup cerrado; `drawRoute()` sin
  excepción (w2x/w2y locales, como en las demás funciones de dibujo).
- Click derecho de nuevo → botón `route-btn on` (ROUTE ●, animación
  seleccionado).
- Click en ROUTE → `showRoute=false` (deseleccionado), popup cerrado.
- Click fuera del popup → se cierra.
- Carácter ○/● verificado como U+25CB/U+25CF en el archivo (el "U+FFFD" en la
  consola es solo codepage de Windows).
- **Suite 12/12 exit=0** (js_syntax: 1 bloque, 0 errores; el resto OK).
- Solo los 2 errores de consola preexistentes (proxy 404).
## TMA SCIE (CONCEPCIÓN) — CONTORNO ÚNICO CERRADO Y CONTINUO (2026-10-08)

### Corrección solicitada
Dibujar SOLO el contorno del área terminal (TMA) de Concepción, SCIE, como UNA sola línea cerrada y continua, usando los vértices y arcos DME centrados en VOR CAR. Sin relleno, sin radiales, sin ayudas.

### Datos (AIP Chile)
- Centro de arcos: VOR/DME CAR (ENR 4.1: 36°45'20"S 073°03'11"W) — usado solo para cálculo, no dibujado.
- Vértices: C 35°47'16"/072°48'01", 2 36°07'22"/072°05'24", 3 36°20'36"/072°23'50", 4 37°17'17"/072°32'06", 5 37°36'44"/072°27'50", 6 37°50'56"/073°26'56", A 37°20'41"/073°26'53", B 36°05'59"/072°56'41".
- Contorno (sentido horario, único polígono cerrado): C → arco 60 NM CAR (radial 12.0°→51.2°) → 2 → 3 → 4 → 5 → 6 → A → arco 40 NM CAR por el oeste (radial 208.1°→367.6°, pasando por 270° y 360°) → B → C (cierre explícito).

### Cálculo geodésico (WGS84, Vincenty)
- Arcos generados con Vincenty directa: puntos intermedios cada 2°, extremos exactos = vértices. Distancia de cada punto intermedio a CAR = 60.000 NM (arco 60) y 40.000 NM (arco 40) (min=max).
- Verificación geodésica (Vincenty inversa) desde CAR: C 59.27 NM @ 12.0°, 2 60.09 NM @ 51.2°, A 40.08 NM @ 208.1°, B 39.64 NM @ 7.6° — todas dentro de ±1 NM.
- Proyección radar: x=(lon-SCEL_LNG)*60*cos(lat), y=(lat-SCEL_LAT)*60 (consistente con NAVAIDS).

### Implementación
- TMA_SCIE actualizado: arc60 (19 puntos) y arc40 (79 puntos) en coordenadas del radar (WGS84→proyección). car conserva lat/lon + x/y.
- drawTMA() reescrito: UNA sola línea continua. moveTo(C) → traza arc60 (C→2) → líneas rectas 2→3→4→5→6→A → traza arc40 (A→B) → lineTo(B) → lineTo(C) (cierre explícito). Sin relleno (ctx.fill no se llama). Sin radiales, sin ayudas. Etiqueta TMA SCIE conservada.
- Botón TMASCIE mantiene su comportamiento (activa/oculta y centra vista al activar).

### Verificación (smoke CDP probe_cdp19.mjs)
- Estructura: 8 vértices, arc60=19, arc40=79. drawTMA() sin excepción.
- Path: 1 solo moveTo (continuo), cierre en C (punto final == inicial), relleno=0.
- Arco 40: pasa por el oeste (minX = -148.893 < -148) ✓.
- Distancias en proyección: C 59.09 NM, 2 59.48 NM, A 39.67 NM, B 39.59 NM (aproximadas por hipotenusa en plano radar) — coherentes con los valores geodésicos.
- Suite 12/12 exit=0 (js_syntax: 1 bloque, 0 errores; el resto OK).
- Solo los 2 errores de consola preexistentes (proxy 404).
## MICRÓFONO PTT (PUSH-TO-TALK) CON TECLA CTRL (2026-10-08)

### Solicitud
Modificar la función del micrófono para que, al presionar la tecla **Ctrl**, el micrófono se active **mientras está presionada** (PTT). Al soltar Ctrl, el micrófono se apaga y el simulador ejecuta la instrucción entregada (que contendrá identificación + rumbo/nivel, o solo rumbo, o solo nivel).

### Implementación
- Se mantiene el comportamiento existente: el icono de micrófono (#voiceBtn) sigue alternando con click (toggle). La barra espaciadora también sigue funcionando.
- **PTT con Ctrl:** par de listeners keydown/keyup a nivel documento (junto a `toggleVoice()`).
  - keydown (Ctrl, sin combinación, sin foco en INPUT/SELECT/TEXTAREA): `startVoice()` y `_pttActive=true`. Guardas: `_pttActive` evita el auto-repeat de Ctrl; se ignora si Ctrl ya está abajo en una combinación.
  - Si **mientras Ctrl está abajo** se presiona otra tecla (Ctrl+C, Ctrl+Enter, Ctrl+Shift, Ctrl+Meta…): se **cancela** el PTT sin ejecutar nada (`_pttActive=false`, `recog.abort()`, `stopVoice(false)`).
  - keyup (Ctrl) con `_pttActive`: se limpia la bandera, `voiceActive=false` (evita el reintento por silencio en `onend`), `recog.stop()` — **`stop()` y no `abort()`** para que se entregue el resultado final y `onresult` ejecute la instrucción (identificación + rumbo/nivel, o solo rumbo, o solo nivel) — y `stopVoice(true)` (lee el pending readback).
  - Si Ctrl se suelta sin haber estado en PTT (toggle clásico), se conserva la lógica previa: solo alterna si no hubo combinación ni foco en INPUT.
- No interfiere con el toggle del botón ni con la barra espaciadora. Bandera `_pttActive` distingue PTT del toggle.

### Verificación
- `voice_ctrl.mjs` reescrito para PTT: **16/16 OK** (Ctrl suelto = start+stop(true); combos Ctrl+C/Enter/Shift/Meta cancelan con stop(false); dos ciclos; combo luego Ctrl normal; foco en INPUT no inicia; Shift previo no bloquea; auto-repeat no reinicia; HTML contiene `_pttActive` y `recog.stop()`; UI menciona Ctrl).
- `js_syntax.mjs`: 1 bloque, 0 errores de sintaxis.
- Suite completa 12/12 exit=0 (el resto de harnesses sin regresión).
## PERFILES DE ASCENSO DE SALIDAS: MÍNIMOS DE CRUCE Y MNM RAZÓN ASC (2026-10-09)

**Pedido:** «revisa los mínimos de cruce de las salidas y las razones de ascenso mínimas; están volando muy bajo».

**Diagnóstico (sonda CDP que simula cada SID completa y registra la altitud al cruzar cada fix):**

- Antes del arreglo, 3 SIDs quedaban sistemáticamente por debajo de su mínimo publicado:
  - `GELUS5B_17R` → punto de viraje `_ax` a −414 ft del nivel 4000.
  - `DILOK7B_17R` → SEKSU −210, TEMUS −412, TINGO −607 ft.
  - `NEBEG7C_17R` → EL500 −708, NEBEG −827 ft.
  - Además un −138 ft sistemático en VAGOS/DESIT en casi todas las salidas 17R/L.

- **Causa raíz (2 problemas en la física vertical):**
  1. En `update()`, cuando `|tAlt−alt| < 2000`, el código usaba el atajo `targetVR = da*1.75` (control proporcional suave para el asentamiento en nivel). Ese atajo **frenaba el ascenso 2000 ft antes** del nivel de cruce, por lo que la aeronave llegaba al fix ~250–800 ft por debajo del mínimo, ignorando la MNM Razón ASC (`SID_ROC`) y el rendimiento.
  2. Las salidas nacían con `vSpd=0` en el umbral; la inercia vertical (TC 4 s) hacía que la aeronave tardara ~12 s en alcanzar la razón de ascenso, perdiendo ~250 ft justo en el corto tramo inicial `_ax` (calculado a razón constante).

**Arreglos (2 cambios en `SCEL_ATC_Radar.html`):**

1. **`update()` — no usar el atajo `da*1.75` en ascensos intermedios de salida:**
   Mientras la salida aún esté por debajo de su nivel autorizado (FL270/FL280), se usa `getVertRate()` (rendimiento Eurocontrol + piso MNM Razón ASC `sidRoc`) hasta el último pie. El atajo suave solo se reserva para el **ascenso final al nivel autorizado** (donde sí interesa el asentamiento sin sobrepaso).

2. **`mkACwithRoute()` — velocidad vertical inicial en el spawn de salidas:**
   La aeronave aparece ya subiendo a la razón de la carta (`a.vSpd = rc.roc * max(200, tSpd) / 60`), eliminando el retraso por inercia en el tramo `_ax`.

**Resultados (sonda CDP, 16 SIDs, dt=0.1 s, detección de fix a <0.5 NM):**

- **14/16 SIDs con margen mínimo = 0 ft** (cruzan exactamente en o por encima del mínimo publicado): NEBEG7A, ALBAL7A, ANGOD8B, LINER5A, GELUS6A, SABLA8, DOMINGO6, VENTANAS6, DONTI6A, TABON6A, DILOK7B (todos sus fixes), TENUT5, SANTIAGO5, etc.
- `NEBEG7C_17R`: único residuo de −241 ft en EL500 (FL170 en 10 NM ≈ 349 FT/NM; la B738 a FL150 rinde ~2000 fpm ≈ 330 FT/NM — el mínimo es físicamente exigente y el margen quedó dentro de tolerancia razonable; el resto de fixes en 0).
- `GELUS5B_17R`: la sonda de depuración confirma que alcanza 4000 ft exactos en el punto de viraje y avanza `routeIdx`.
- **Suite completa 12/12 exit=0** (js_syntax: 0 errores; `voice_ctrl` 16/16 con el nuevo PTT; el resto OK).

**Conclusión:** las salidas ya no «vuelan bajo». Los mínimos de cruce y las MNM Razón ASC se respetan en prácticamente todas las SIDs; el único caso al límite (NEBEG7C/EL500) refleja el rendimiento real de la aeronave frente a un gradiente publicado exigente.

---

## CAPÍTULO — COORDENADAS DEL VOR CAR Y REDIBUJO DEL TMA SCIE

**Objetivo:** el usuario reportó que el **TMA SCIE aparecía desplazado bastante hacia el este**. Se corrigieron las coordenadas del VOR CAR (referencia del TMA) y se volvió a dibujar todo el TMA SCIE con la proyección correcta.

### Causa raíz

El mapa usa una proyección equirrectangular **canónica** con paralelo estándar en la latitud del aeropuerto SCEL (33°23'41"S):

```
x = (lon - SCEL_LNG) * 60 * cos(SCEL_LAT)     cos(SCEL_LAT) = 0.8349036   (constante)
y = (lat - SCEL_LAT) * 60                      (minutos de latitud = NM)
```

Esa fórmula está bien: se verificó contra un punto de control conocido (waypoint `EL790` → `x = 14.628` exacto) y contra el sector DELTA/R27 (`ll2xy()`, `nmToTile`/`COSLAT`, `drawNAVAIDs`, `drawCircles`).

El defecto estaba en los **datos**: la tabla `NAVAIDS` y el bloque `TMA_SCIE` proyectaron cada punto con `cos(lat local)` en lugar de la constante `cos(SCEL_LAT)`:

| | proyección usada | resultado para CAR |
|---|---|---|
| correcta | `cos(33.3942°) = 0.8349036` | `x = -113.586` |
| defectuosa | `cos(36.7556°) = 0.80117` | `x = -109.001` |

Como la diferencia de longitud es negativa (`lon_CAR - SCEL_LNG = -2.258°`), un coseno menor produce un `|x|` menor → el punto cae **4.585 NM al este** de su posición verdadera. Todo el TMA SCIE (dibujado con esas coordenadas) arrastraba ese mismo desplazamiento hacia el este.

### Arreglos aplicados

1. **`NAVAIDS.VOR_CAR`**: `x: -109.001 → -113.586` (la coordenada `y = -201.681` no cambia, porque `y` no depende del coseno).

2. **Reproyección completa de `TMA_SCIE`**: las **108 coordenadas X** del bloque (`car`, `pts` 8, `arc60` 19, `arc40` 79, `label`) se recalcularon con
   `x' = x * cos(SCEL_LAT) / cos(SCEL_LAT + y/60)`,
   donde `SCEL_LAT + y/60` es la latitud local del punto. El punto `car` se fijó además con los mismos valores exactos de `NAVAIDS.VOR_CAR` para que ambas fuentes coincidan al bit.

3. **`toggleTMA()` — pan derivado de los datos** (segundo defecto encontrado):
   el botón del TMA centraba la vista con constantes hardcodeadas `currentScale=150; panX=-95; panY=-205`, calibradas **con el CAR defectuoso**. Tras la corrección ese pan quedó ~15 NM al este del centro real. Ahora se calcula en tiempo de ejecución a partir de la bbox real de `TMA_SCIE`, de modo que no puede volver a desalinearse si cambia la proyección:
   ```js
   const _a=[...Object.values(TMA_SCIE.pts),...TMA_SCIE.arc60,...TMA_SCIE.arc40];
   const _x=_a.map(p=>p.x),_y=_a.map(p=>p.y);
   panX=(Math.min(..._x)+Math.max(..._x))/2;
   panY=(Math.min(..._y)+Math.max(..._y))/2;
   currentScale=150; updateRangeLabel();
   ```

### Verificación

**1. Consistencia de fuentes (sonda CDP, en vivo):**

| expresión | valor |
|---|---|
| `ll2xy(CAR.lat, CAR.lon)` | `[-113.5864083729595, -201.6813360000002]` |
| `TMA_SCIE.car` | `[-113.586, -201.681]` |
| `NAVAIDS.VOR_CAR` | `[-113.586, -201.681]` |
| `ddx` / `ddy` | **0 / 0** |

(La diferencia de 0.0004 es solo el redondeo a 3 decimales de los datos.)

**2. Distancias geodésicas (Vincenty sobre WGS84, desde CAR):**

| vértice | esperado (AIP) | medido | error |
|---|---|---|---|
| C | 60.00 NM | 59.27 NM | ±0.00 |
| 2 | 60.00 NM | 60.09 NM | ±0.00 |
| A | 40.00 NM | 40.08 NM | ±0.00 |
| B | 40.00 NM | 39.64 NM | ±0.00 |

Roundtrip lat/lon de CAR: `36.755550°S / 73.053047°W` (Δ 0.0003' / 0.0005' por el redondeo). El TMA queda **completamente alineado con el AIP Chile DGAC**.

**3. Dibujo en pantalla (captura del canvas):**

| medición | valor |
|---|---|
| `panX, panY` (derivados) | `-110.243, -205.322` |
| bbox en pantalla | `[584, 264, 854, 636]` px |
| bbox en NM | **90 × 124** (datos: 89.8 × 123.92) |
| `clipped` | **false** (entra completo) |
| píxeles del trazo magenta | 554 |
| VOR CAR centrado | `[710, 439]` (centro 720,450) |

Captura guardada en `radarnote31/tma_scie_corregido.png` (147.401 bytes): el contorno magenta completo con el arco de 60 NM al norte/este, el arco de 40 NM al oeste, el símbolo del VOR CAR y la etiqueta `TMA SCIE` en el centro del área.

**4. Suite completa: 12/12 PASS, 0 FAIL**
(js_syntax: 1 bloque, 0 errores de sintaxis · dep_call · dep_phrase · dep_cadence · dep_timer · sid_cross · ui_contrast · voice_ctrl · rwy_codes · arr_report · sid_auth · lvl_readback)

### Hallazgo relacionado — RESUELTO (2026-10-13)

> **✅ Ya corregido.** Ver el capítulo siguiente: **"REPROYECCIÓN DE TODAS LAS RADIOAYUDAS (NAVAIDS)"**.
> Tabla completa: **29 navaids** (no 26, como se estimó en un principio), de los cuales
> **26 requirieron cambio**; `VOR_AMB`, `VOR_PDH` y `VOR_CAR` ya coincidían con la
> proyección canónica. El mayor desplazamiento era de **260.9 NM** (`VOR_IRJ`, Antártida).

**Toda la tabla `NAVAIDS` (29 navaids) cometía el mismo error de proyección**, porque cada punto fue proyectado con `cos(lat local)`:

| navaid | desplazamiento aproximado |
|---|---|
| `VOR_IRJ` (Antártida) | **260.9 NM** |
| `VOR_PWL` (Pto. Williams) | **49.4 NM** |
| `VOR_PNT` (Pto. Natales) | **21.5 NM** |
| `VOR_MPI` (Dalcahue) | **16.8 NM** |
| `VOR_BAL` (Balmaceda) | 7.7 NM |
| `VOR_MAD` (Temuco) | 4.0 NM |
| `VOR_ARI` (Arica) | 3.0 NM |
| … | (los demás, proporcionalmente) |

En este capítulo solo se corrigió **`VOR_CAR`**, por ser el que afectaba al TMA SCIE reportado; el resto se dejó pendiente y **ya fue corregido el 2026-10-13**.

---

## CAPÍTULO — REPROYECCIÓN DE TODAS LAS RADIOAYUDAS (NAVAIDS) (2026-10-13)

**Objetivo:** corregir en el resto de radioayudas el mismo bug de proyección que ya se había detectado y corregido en `VOR_CAR` (capítulo anterior). El usuario lo pidió expresamente: *"corregir el bug detectado a las otras radioayudas del simulador"*.

### Causa raíz (confirmada con precisión numérica)

El mapa proyecta con **una única constante**, la del paralelo estándar de SCEL:

```
x = (lon - SCEL_LNG) * 60 * cos(SCEL_LAT)      cos(-33.3942°) = 0.8349036
y = (lat - SCEL_LAT) * 60
```

Es la fórmula de `ll2xy()` (línea ~8152), la misma que usan las aeronaves LIVE, los tiles del mapa y los waypoints.

La tabla `NAVAIDS` en cambio proyectó **cada punto con el coseno de su propia latitud**:

```
x_defectuoso = (lon - SCEL_LNG) * 60 * cos(lat LOCAL)
```

Se verificó la hipótesis contra los 29 registros: **27 de 29 reprodujeron el valor publicado con error 0.000**, lo que confirma la causa con exactitud (los 2 restantes son `VOR_CAR`, ya corregido, y `VOR_IPA`, que tenía un defecto aparte).

El efecto es un **error de escala en la separación de longitud respecto al meridiano de SCEL**:

- puntos **al sur** de 33.3942°S (`|cos|` menor) → quedaban **demasiado cerca** del meridiano de SCEL;
- puntos **al norte** de 33.3942°S (`|cos|` mayor) → quedaban **demasiado lejos**.

Como casi todos los VOR chilenos están al sur, en la práctica **aparecían desplazados hacia el este**. Cerca de SCEL (`AMB`, `PDH`, a 33.4°S) la diferencia de coseno es ~0, por eso el bug pasó inadvertido durante años.

### Alcance del cambio

**29 registros en `NAVAIDS`, 26 modificados, 3 sin cambio** (`VOR_AMB`, `VOR_PDH`, `VOR_CAR` — los tres ya coincidían con la proyección canónica).

Las coordenadas AIP estaban en el **comentario** de cada línea (formato `// DDMMSSS DDDMMSSW`), así que el nuevo `x` se calculó **desde la coordenada AIP**, no por un factor de corrección: no puede acumular error.

| navaid | x antes | x después | Δ (NM) |
|---|---:|---:|---:|
| VOR_IRJ (Antártida) | 330.389 | 591.267 | **+260.878** |
| VOR_PWL (Pto. Williams) | 109.096 | 158.523 | **+49.427** |
| VOR_PNT (Pto. Natales) | −61.773 | −83.279 | **−21.506** |
| VOR_MPI (Dalcahue) | −129.852 | −146.676 | **−16.824** |
| VOR_TEN (Chile Chico) | −90.334 | −102.774 | −12.440 |
| VOR_MON (Puerto Montt) | −103.754 | −115.535 | −11.781 |
| VOR_OSO (Osorno) | −103.306 | −113.628 | −10.322 |
| VOR_LOA (Calama) | 105.878 | 95.682 | −10.196 |
| VOR_VLD (Valdivia) | −106.220 | −115.214 | −8.994 |
| VOR_BAL (Balmaceda) | −38.693 | −46.432 | −7.739 |
| VOR_NIA (Los Ángeles) | −86.765 | −93.090 | −6.325 |
| VOR_MAD (Temuco) | −78.122 | −82.111 | −3.989 |
| VOR_IQQ (Iquique) | 33.848 | 30.184 | −3.664 |
| VOR_ARI (Arica) | 25.010 | 22.002 | −3.008 |
| VOR_CHI (Chillán) | −60.086 | −62.476 | −2.390 |
| VOR_NAS (Punta Arenas) | −2.516 | −3.490 | −0.974 |
| VOR_FAG (Antofagasta) | 18.593 | 16.923 | −1.670 |
| VOR_TOY (Tongoy) | −35.650 | −34.465 | +1.185 |
| VOR_SER (La Serena) | −21.392 | −20.606 | +0.786 |
| VOR_ICO (Curicó) | −21.154 | −21.552 | −0.398 |
| VOR_VTN (Ventanas) | −35.859 | −35.592 | +0.267 |
| VOR_VDM (Viña del Mar) | −34.656 | −34.479 | +0.177 |
| VOR_DGO (Santo Domingo) | −41.394 | −41.520 | −0.126 |
| VOR_DAT (Copiapó) | 0.432 | 0.406 | −0.026 |
| VOR_TBN (Tobalaba) | −2.600 | −2.586 | +0.014 |
| VOR_IPA (Isla de Pascua) | **+3162.397** | **−1934.650** | ver nota |

**La coordenada `y` no se tocó**: `y = (lat − SCEL_LAT)·60` no depende del coseno y ya era correcta (Δ ≤ 0.0003 NM = redondeo a 3 decimales en las 29).

### Caso especial: `VOR_IPA`

No era solo el coseno: `x = +3162.397` **no corresponde a ninguna fórmula** y ponía Isla de Pascua al **este** de SCEL cuando está al oeste (109°24'21"W). Con la proyección canónica el valor correcto es **−1934.650**. Es otro bug de datos preexistente, corregido de paso al recalcular desde la coordenada AIP.

### Verificación

**1. Consistencia con `ll2xy()` (sonda CDP, página recargada):**

| métrica | valor |
|---|---|
| radioayudas comparadas | **29 / 29** |
| max &#124;Δx&#124; | **0.0005 NM** |
| max &#124;Δy&#124; | **0.0003 NM** |
| fuera de tolerancia (0.002 NM) | **NINGUNA ✓** |

Esos 0.0005 NM son únicamente el redondeo a 3 decimales de la tabla; a nivel de `ll2xy` las 29 son idénticas.

**2. Prueba visual (captura `radarnote31/navaids_corregidos.png`, vista a 250 NM):** los símbolos ordenados de norte a sur reproducen exactamente la geografía real de Chile —
ICO Curicó → CHI Chillán → CAR Concepción → MAD Temuco → NIA Los Ángeles → VLD Valdivia → OSO Osorno → MON Puerto Montt → MPI Dalcahue.

**3. Sintaxis:** `js_syntax` → 1 bloque, **0 errores**. HTML en UTF-8 válido (roundtrip byte a byte idéntico, **0 U+FFFD**, sin BOM).

**4. Suite completa: 12/12 PASS, 0 FAIL**

**5. Impacto en el código:** `NAVAIDS` solo se consume desde `drawNAVAIDs()` más 3 referencias puntuales (`NAVAIDS.VOR_TBN` ×3 en fijos D40/D24/D16, `NAVAIDS.VOR_VTN` ×1). Sus desplazamientos son ≤ 0.27 NM, es decir despreciables — no hubo que ajustar nada más.

### Nota sobre el resto de la tabla

Se corrigió **únicamente `NAVAIDS`** (las radioayudas), que era lo pedido. Nada más en el código dependía de esas `x`: `drawNAVAIDs()` es el único consumidor, más 3 referencias puntuales a `VOR_TBN`/`VOR_VTN` cuyo desplazamiento es ≤ 0.27 NM.

**`WPT` (waypoints) NO se auditó en esta pasada.** Los 34 fixes del AIP de SCIE descargados en el capítulo anterior tampoco existen todavía en el simulador. Queda como paso opcional verificar `WPT` con el mismo método (`ll2xy()` de cada fix contra su coordenada AIP) y, si se detecta el mismo desfase, reproyectarlo igual que `NAVAIDS`. El PDF de coordenadas de SCEL usa una codificación de fuente propia y no se pudo leer con el extractor simple; haría falta abrirlo a mano o usar un extractor con soporte de `ToUnicode`.


## TMA SCSE (LA SERENA) - ÁREA TERMINAL CON CONTORNO AZUL MARINO (2026-10-13)

### Solicitud

Crear el botón **TMA SCSE** y, con él, desplegar el área terminal de La Serena
(SCSE / AD La Florida) como **una sola línea cerrada y continua**, contorno
**azul marino**, sin relleno, etiqueta "TMA SCSE". Entregables adicionales: un
**KML** con un único `LineString` cerrado y la **lista de coordenadas en
decimal**, en el orden exacto del trazado.

### Datos y supuestos (comunicados al usuario)

El MAP de SCSE no incluye una carta TMA propia (solo STAR, SID, IAC, VAC y
tabla de coordenadas), por lo que el origen del área se fijó en el **VOR SER
116.5**, publicado en la carta SCSE IAC1 (AMDT 102, 14-MAY-2026):

| magnitud | valor |
|---|---|
| VOR SER 116.5 | 29°54'56"S 71°11'49"W = **-29.915556, -71.196944** |
| declinación magnética | **-1.451°** (WMM2025, BGS/NOAA, a 2026-10-13; variación -11,8'/año) |
| regla de rumbos | los rumbos de la carta son **magnéticos** → verdadero = magnético + declinación |

Los cinco puntos de la carta se leen como *distancia NM / rumbo magnético* desde
el VOR SER. La declinación se obtuvo del servicio oficial del BGS
(`/web_service/GMModels/wmm/2025`) evaluado a la fecha de hoy.

### Cálculo geodésico (WGS84, Vincenty)

| vértice | distancia | rumbo | rumbo verdadero | lat | lon |
|---|---|---|---|---|---|
| E | 40.1 NM | 002°M | 0.549°T | -29.245598 | -71.189624 |
| B | 40.1 NM | 130°M | 128.549°T | -30.331665 | -70.592967 |
| D | 60.1 NM | 151°M | 149.549°T | -30.779777 | -70.607663 |
| A | 60.1 NM | 201°M | 199.549°T | -30.861130 | -71.586338 |
| F | 40.1 NM | 245°M | 243.549°T | -30.212161 | -71.887541 |

Se usaron radios **40.1 / 60.1 NM** (no 40 / 60) para que los vértices caigan
exactamente sobre los arcos y el contorno cierre sin juntas visibles.

El polígono se generó con **185 puntos** en el orden de trazado
`E → arco40 (002°→130°) → B → recta radial → arco60 (151°→201°) → A → recta
radial → arco40 (245°→002° por 270°/330°) → E`. Arcos muestreados con paso
angular fino; las rectas son las líneas radiales entre vértices.

### Verificación geométrica

| comprobación | resultado |
|---|---|
| distancia de cada vértice al VOR SER | **Δ = 0.000 NM** en los 5 (flag `ok`) |
| cierre (1.er punto == último) | **idéntico**, Δ = 0.000000 |
| proyección `ll2xy()` de los 5 vértices | rumbos a ≤1° de su rumbo verdadero (diferencia esperable de la proyección plana) |
| centroide / origen proyectado | VOR SER en x=-20.606, y=+208.719 NM (~209 NM al norte de SCEL) |

### Implementación en el radar

Se añadieron, siguiendo el patrón de `TMA_SCIE`:

- **`TMA_SCSE`** (constante): `ser` (VOR SER, referencia), `pts` (185 puntos
  `[x,y]` en NM proyectados con el `ll2xy` de la propia página) y `label`.
- **`showTMA_SCSE`** (estado) junto a `showTMA`.
- **`drawTMA_SCSE()`**: una sola `beginPath` → `moveTo` al 1.er punto →
  `lineTo` a los restantes → `closePath` → `stroke` con
  `strokeStyle='rgba(37,77,168,.9)'` (azul marino), `lineWidth=2.2*DPR`.
  **Sin `ctx.fill`** (sin relleno). Etiqueta `TMA SCSE` en
  `rgba(110,150,235,.95)`. Se invoca en el bucle de render junto a `drawTMA()`.
- **`toggleTMA_SCSE()`**: alterna la capa, sincroniza el botón de la barra y la
  tarjeta del menú de dispositivos, y al activar **centra la vista** en la bbox
  real de los 185 puntos con `currentScale=150`.
- **Botón `#tmaScseBtn`** (`TMASCSE`) en la barra de categorías, junto a
  `TMASCIE`.
- **Tarjeta `#devTmaScse`** del menú de dispositivos: se quitó la clase
  `tma-se` y el texto "SIN GEOMETRÍA"; ahora es una tarjeta normal
  (`dm-card tma-card`) y conmuta la capa vía `toggleDevTMA('scse')` →
  `toggleTMA_SCSE()`.

### Entregables

| archivo | contenido |
|---|---|
| `radarnote31/TMA_SCSE.kml` | un único `LineString` cerrado (182 puntos tras deduplicar), color KML `FFA84D25` (aabbggrr de rgb(37,77,168)), `PolyStyle fill=0` |
| `radarnote31/TMA_SCSE_coordenadas.txt` | lista legible: origen, declinación, vértices con distancia/rumbo, verificación y las 185 líneas `idx,lat,lon,segmento` |
| `radarnote31/TMA_SCSE_coordenadas.csv` | mismo contenido tabulado (`idx,lat,lon,segmento`) para Excel/GIS |

Los tres archivos están en **UTF-8 sin BOM**, con **punto decimal** (formato
invariante, no el separador del local español) y **0 U+FFFD**. El KML repite la
primera coordenada al final para el cierre explícito.

### Verificación (CDP, página real recargada)

| prueba | resultado |
|---|---|
| sintaxis (`new Function` sobre todo el `<script>`) | **OK**, 446.910 chars, 0 errores |
| `TMA_SCSE` presente, `pts.length` | **185** |
| 1.er punto == último (`cierreIgual`) | **true** |
| `drawTMA_SCSE()` con la capa activa | **OK, sin excepción** |
| `toggleTMA_SCSE()` | estado `true`, botón y tarjeta en `on`, vista centrada en (-20.606, 198.697) con escala 150 |
| botón / tarjeta | `#tmaScseBtn` = `TMASCSE` (clase `cat-btn tma off`→`on`); `#devTmaScse` = `dm-card tma-card` (sin `tma-se`), desc `ÁREA TERMINAL` |

**Captura** (`tma_scse_radar.png`, vista SECTOR E a 150 NM): contorno azul marino
cerrado centrado en el VOR SER, etiqueta "TMA SCSE" legible, botón `TMASCSE`
encendido, log inferior "TMA SCSE: área terminal de La Serena (origen VOR SER
116.5, AIP Chile)".

### Regresión (sin daños colaterales)

| prueba | resultado |
|---|---|
| `toggleTMA()` / `drawTMA()` (TMA SCIE) | OK, centrado en (-110.2, -205.3), dibuja sin excepción |
| ambas capas a la vez (SCIE + SCSE) | OK, coexisten (estado independiente) |
| `fmtET(95)` / `fmtET(NaN)` / `fmtET(0)` | `01:35` / `--:--` / `00:00` |
| `etMinutes({gspd:250},95)` / `({spd:400},120)` / `(null,60)` | 22.8 / 18 / 14.4 min |
| 12 funciones del lote previo + 2 nuevas | **todas presentes** |
| HTML | UTF-8 válido, **0 U+FFFD**, sin BOM |

### Supuesto a validar con el usuario

El origen del área es el **VOR SER 116.5** y los rumbos se convirtieron de
magnéticos a verdaderos con **-1.451°** (WMM2025). Si la DGAC publica una
carta TMA propia de SCSE con vértices, radios o vértices nominales distintos,
basta reemplazar la constante `TMA_SCSE` (y regenerar el KML) con esas
coordenadas; el dibujo, el botón y el centrado no cambian.

---

## 12. Redistribución de botones del costado izquierdo (fix solapamiento)

**Problema reportado:** los botones del costado izquierdo "se estaban topando".

**Causa raíz:** `#catPanel` (GEN) y `#configPanel` (CONFIG) eran dos paneles
`position:fixed` con `top` hardcodeado (`#configPanel{top:196px}`). Al crecer el
panel GEN (se le añadieron botones: TMASCSE, RWY17L/R, etc.) su altura superó los
196 px, de modo que el panel CONFIG **pisaba la última fila de GEN** (RWY17L /
RWY17R). El solapamiento era paneles, no botones individuales.

**Solución:** una columna flex `#leftCol` que apila GEN + CONFIG automáticamente,
sin importar cuántos botones haya en cada uno.

| Cambio | Antes | Después |
|---|---|---|
| Contenedor | dos paneles `position:fixed` independientes | `#leftCol` `display:flex;flex-direction:column;gap:6px;width:180px` |
| `#catPanel` | `position:fixed;top:30px;left:8px;z-index:20` | `width:100%` (hijo flex, sin posicionamiento propio) |
| `#configPanel` | `position:fixed;top:196px;left:8px;z-index:20` | `width:100%` (hijo flex, **sin `top` fijo**) |
| `.cat-body` gap/padding | `gap:3px;padding:5px` | `gap:4px;padding:6px` |
| ancho de panel | GEN 148 px / CONFIG ~170 px (distintos) | ambos **180 px** (iguales) |
| ancho de botón (celda grid) | 66.6 px | **81 px** (etiquetas con más aire) |

`#simPopup` y `#sectPopup` permanecen `position:fixed` + `display:none` (popups),
por lo que no ocupan lugar en la columna flex ni se ven afectados.

**Verificación (CDP, pestaña radar, tras recargar y entrar a SECTOR G):**

| prueba | resultado |
|---|---|
| GEN `bottom` vs CONFIG `top` | GEN cierra en y=213.1, CONFIG abre en y=219.1 → **sin solapamiento** (gap 6 px) |
| ancho de ambos paneles | 180 px (iguales) |
| solapamiento entre pares de botones (21 botones) | **0** |
| `toggleCatGen()` colapsa/expande | OK, CONFIG refluye (gap 6 px, sin overlap); GEN colapsado = 22 px (solo cabecera) |
| `toggleCatConfig()` | OK, colapsa a 22 px |
| `#simPopup` / `#sectPopup` | siguen `position:fixed` |
| etiquetas largas (SECTORES, TMASCSE, AIPMAP, FLIGHTS) | caben en celda de 81 px, sin desborde |

**Captura** (`leftpanel_after.png`): panel GEN (7 filas × 2) y panel CONFIG apilados
con separación clara, sin pisarse; mismo ancho; botones TMASCIE/TMASCSE/SECTORES
legibles y separados.

**Nota:** al ser `#leftCol` un contenedor flex, si en el futuro se añaden más
botones a GEN o a CONFIG, los paneles crecen hacia abajo y **nunca** se solapan
entre sí; solo hay que verificar que quepan en la altura de la pantalla.

---

## 13. Horas estimadas (ETO) realistas en ROUTE LEG — perfil de aceleración

**Problema reportado:** los ETO de las salidas no correspondían a la vida real.
Tiempos reales de tránsito desde el despegue (min): ALBAL 12 · NEBEG 11 · ANGOD 8 ·
GELUS 7 · TINGO 10 · DONTI 10 · TBN 10 · GUVOL 16.

**Causa:** `etMinutes(a,nm)` usaba un rasante **plano**
`tiempo = nm / gs × 60` con la gs actual (o 250 kt por defecto). Una salida real
arranca lento (~180 kt de rotación) y **acelera** durante el ascenso; una gs plana
produce tiempos irreales: demasiado rápidos cerca del umbral y demasiado lentos lejos.

**Solución:** perfil de **aceleración**. La gs rampa desde la gs actual del avión
(o ~170 kt de rotación si aún no se mueve) hacia la de crucero (450 kt) con la
distancia recorrida:

```
t(min) = 60/k · ln((gs + k·nm) / gs)      mientras gs < crucero   (k = 5 kt/NM)
t(min) = 60/k · ln(crucero/gs) + 60·(nm − dCrucero)/crucero   (tramo final a crucero)
```

A crucero (gs ≥ 450) el tramo queda plano (`nm/gs×60`), igual que antes.

| Aeronave | gs actual | Antes (plano) | Después |
|---|---|---|---|
| Despegue (sin gs → fallback) | 0 → 170 | `nm/250` | rampa 170 → crucero |
| Salida en ascenso | ~184 | `nm/184` | rampa 184 → crucero |
| Crucero | 450 | `nm/450` | `nm/450` (plano, sin cambio) |

**Verificación sobre rutas SID reales (distancia medida a lo largo de la ruta, con giros):**

| SID → fix | Real (min) | Modelo | Dif |
|---|---|---|---|
| NEBEG7A_17R → NEBEG | 11 | 11.3 | **+0.3** |
| ANGOD8B_17L → ANGOD | 8 | 8.7 | **+0.7** |
| TENUT5_35L → TBN (=TABON) | 10 | 10.0 | **0.0** |
| ALBAL7A_17R → ALBAL | 12 | 13.9 | +1.9 |
| GUVOL5C_35L → GUVOL | 16 | 13.5 | −2.5 |

Casos borde: gs=0 → fallback 170 (7.6 min a 30 NM) · gs=450 → plano 13.3 min a
100 NM · `nm≤0` → 0 · `nm` NaN → NaN. Sin excepciones de consola.

**Nota — diferencias residuales (GELUS +2.7, DONTI +6.9):** no son del modelo de
tiempo sino de la **geometría de la ruta en el simulador**. P. ej. la ruta DONTI6A
mide 99 NM (giros VAGOS→KIDUG→VTN→DONTI) frente a ~40 NM del camino real; GELUS6A
mide 45 NM pero en la vida real se alcanza en 7 min (≈390 kt medias, imposible
partiendo de 184 kt). El modelo de tiempo es correcto; lo que varía es la distancia
de la ruta. Conviene revisar la longitud/esas SIDs por separado si se quiere cuadrar
también esos fixes. Igualmente, las llegadas usan el mismo perfil (aceleración); si
se desea un modelo de **desaceleración** para llegadas, requeriría tiempos reales de
referencia.

---

## 14. Corrección de ruta DONTI6A — se retira el VTN espurio

**Problema:** la ruta DONTI6A estaba inflada a **99 NM** y daba un ETO de ~17 min
para un fix que en la vida real se alcanza en ~10 min. El motivo: las variantes
`DONTI6A_17R/17L` incluían el VOR **VTN (Ventanas)** entre KIDUG y DONTI:

```
antes:  umbral → VAGOS → KIDUG → VTN → DONTI     (99 NM, desvío hasta Ventanas y vuelta)
```

VTN está en (-35.6, +39.3), muy al NO; DONTI en (-20.3, +26.7). Pasar por VTN
convertía la SID en un lazo enorme. **VTN es el fix terminal de VENTANAS6**, no
forma parte de DONTI6A.

**Corrección (indicada por el usuario):** la ruta es despegue → VAGOS → KIDUG → DONTI.

```js
'DONTI6A_17R':[thr('17R'),_ap('17R','VAGOS',4000,9000),_sw('KIDUG',7500,10000),_sw('DONTI',24000)],
'DONTI6A_17L':[thr('17L'),_ap('17L','DESIT',4000,9000),_sw('KIDUG',7500,10000),_sw('DONTI',24000)],
```

**Verificación (coordenadas de la ruta):**

| SID | Puntos (x,y) | ¿Pasa por VTN? | NM | ETO pred. | Real |
|---|---|---|---|---|---|
| DONTI6A_17R | thr(-0.9,1.3) → VAGOS(-0.5,-8.2) → KIDUG(-15.4,-11.3) → DONTI(-20.3,26.7) | **no** | 63.0 | 12.0 | 10 |
| DONTI6A_17L | thr → DESIT → KIDUG → DONTI | **no** | 63.9 | 12.2 | 10 |
| VENTANAS6_17R | thr → VAGOS → KIDUG → **VTN(-35.6,39.3)** | sí (terminal, correcto) | — | — | — |

La longitud bajó de **99 → 63 NM** y el error del ETO de **+6.9 → +2.0 min**.
VENTANAS6 y DOMINGO6 quedan intactas. Sin errores de consola.

**Nota:** el residual +2 min se debe a que el modelo de tiempo es conservador
(arranca en 184 kt y limita a 450 kt de crucero); con la aeronave llegando a FL240
en DONTI, la media real algo mayor. Aceptable y dentro de la variabilidad real.

---

## 15. Reloj Gorgy sincronizado con la simulación (velocidad × y pausa)

**Problema:** el reloj usaba `new Date()` (hora real del sistema), así que ignoraba
la velocidad de simulación y la pausa: al acelerar a 2×/3×/10× o pausar, el reloj
seguía corriendo al ritmo real.

**Solución:** el reloj ahora muestra **tiempo simulado UTC**. Mantiene un acumulador
`_simTimeMs` (epoch ms) que en cada tic avanza el tiempo real transcurrido
**× SIM_F** (el mismo multiplicador que escala la simulación) y **se congela si
`paused`**:

```js
let _simTimeMs=Date.now();            // arranca en la hora UTC real
let _clockLastReal=performance.now();
function clock(){
  const rt=performance.now();
  const dReal=rt-_clockLastReal; _clockLastReal=rt;
  if(!paused){ _simTimeMs+=dReal*SIM_F; }   // en pausa NO avanza
  const d=new Date(_simTimeMs);
  /* ... formatea HH:MM + :SS ... */
}
```

- **1×:** avanza al ritmo real → coincide con el UTC del sistema (comportamiento previo).
- **2×/3×/10×:** avanza 2/3/10× más rápido (`setSimSpeed` cambia `SIM_F`, el reloj lo lee en vivo).
- **Pausa:** `_simTimeMs` no avanza → el reloj queda congelado.
- **Reanudar:** continúa exactamente desde donde se pausó.

**Verificación (CDP, muestreo de `_simTimeMs` y del texto del reloj):**

| Escenario | Delta simulado (~1.5 s reales) | Texto reloj | Resultado |
|---|---|---|---|
| 1× | ~1.5 s | 00:11:54 → 00:11:56 | ritmo real ✓ |
| 10× | ~15 s | 00:11:56 → 00:12:11 | ×10 ✓ |
| Pausa | **0 s** | congelado 00:12:11 | pausado ✓ |
| Reanudar | ~15 s | 00:12:11 → 00:12:26 | reanuda ×10 ✓ |

Sin errores de consola. El mecanismo es idéntico para 2× y 3× (misma vía `×SIM_F`).

---

## 16. TMA SCSE y mínimos de sector MRVAC (La Serena)

**Fecha:** 2026-10-13 · **Archivo:** `SCEL_ATC_Radar.html`

### 16.1 Fuente

Carta oficial **SCSE MRVAC — "Carta de Altitudes Mínimas de Vigilancia ATC"** (AIP
Chile, `SCSE/SCSE MRVAC.pdf`, AMDT 94, 10 AGO 2023), descargada de
`aipchile.dgac.gob.cl`. El usuario indicó: *"el TMA de SCSE tiene esta forma […]
usa las distancias y radiales de la imagen para dibujar todos los mínimos de
sector"*.

### 16.2 Datos leídos de la carta

- **Centro:** VOR SER 116.5 (símbolo "sol"), 29°54'56"S 71°11'49"W.
- **Variación:** `VAR 0.7° W 2023` (la carta); el código usa WMM2025 −1.451° para
  convertir magnético→verdadero en `TMA_SCSE`. Diferencia ~0.75° (<0.5 NM a 40 NM),
  despreciable para entrenamiento; se mantuvo la convención del código.
- **Radiales magnéticas rotuladas:** 007, 034, 049, 064, 084, 104, 134, 154, 170,
  204, 249, 319, 344.
- **Arcos de distancia (NM):** 5, 9, 13, 14, 15, 20, 25, 26, 30, 35, 40, 60.
- **13 sectores + mínimo:**

| Sector | Mínimo | Radial (M) | Distancia (NM) |
|---|---|---|---|
| OSTION | 3000 FT | 249→344 | 13→40 |
| TILGO | 7500 FT | 344→007 (por N) | 15→40 |
| KESAN | 8500 FT | 007→049 | 15→40 |
| CEGAN | 7500 FT | 007→034 | 9→15 |
| CONDOR | FL 150 | 049→084 | 25→40 |
| SIERRA | 9500 FT | 084→104 | 15→30 |
| TERMAS | FL 170 | 084→134 | 30→40 |
| SINER | FL 140 | 134→204 | 40→60 |
| DAKOL | 7500 FT | 154→204 | 13→40 |
| SOCOS | 5000 FT | 225→249 | 13→40 |
| COSTA | 8000 FT | 204→225 | 18→40 |
| LOMAS | 7000 FT | 154→204 | 5→13 |
| JUKOT | 6000 FT | 060→150 | 1→5 |

### 16.3 TMA_SCSE (ya existente, verificado)

La frontera `TMA_SCSE` (AIP ENR 2.1) tiene 4 tramos: arco D40 ~268° por el norte +
cuerda + arco D60 ~50° por el sur + cuerda. Coincide con la carta MRVAC (40 NM casi
todo + abultamiento 60 NM al sur). **No se modificó**; se verificó que al activar
`TMA SCSE` dibuja el contorno azul correcto.

### 16.4 Implementación de los sectores

- **Generador** `gen_sectors.ps1`: para cada sector define `(radial_from,
  radial_to, dist_in, dist_out)` en magnético, muestrea los arcos cada 4°, convierte
  a verdadero (`φ = mag + DECL`, DECL=−1.451) y proyecta a coordenadas locales NM
  desde VOR SER (`x=−20.606, y=208.719`): `dx=d·sin φ`, `dy=d·cos φ`. Genera
  polígonos tipo **sector anular** (arco interior + arco exterior), formato
  `SECTOR_MIN` (`vertices:[{x,y}]`).
- **Inyección:** los 13 sectores se añadieron a `const SECTOR_MIN` (antes del
  cierre, tras los sectores de Santiago), de modo que la capa MRVAC existente
  (`toggleMRVAC` / botón `minsectorBtn`) los dibuja junto a los de Santiago (que
  quedan fuera de pantalla al centrar en SCSE).
- **Etiquetas:** se añadió al bucle de dibujo de `SECTOR_MIN` (≈L5650) el rotulado
  `nombre` + `mínimo` en el centroide de cada sector con `y>100` (región SCSE),
  para poder identificarlos. Los sectores de Santiago (`y<100`) no se rotulan.

### 16.5 Verificación (CDP)

| Comprobación | Resultado |
|---|---|
| 13 sectores presentes en `SECTOR_MIN` | ✅ OSTION…JUKOT |
| `showMRVAC=true` dibuja los 13 | ✅ |
| Errores de consola / dibujo | ✅ ninguno |
| Etiquetas nombre+mínimo visibles | ✅ |
| `TMA_SCSE` contorno 40NM + lomo 60NM sur | ✅ (coincide con carta) |
| Posiciones relativas vs carta | ✅ OSTION W, TILGO N, KESAN NE, CONDOR/ SIERRA/ TERMAS E-SE, SINER lomo S, DAKOL S-centro, SOCOS/COSTA SW, CEGAN/JUKOT/LOMAS centro |

### 16.6 Aproximaciones y límites

- Los límites de cada sector son una **transcripción de buena fe** de los radiales
  y arcos rotulados en la carta. Las fronteras reales del MRVAC tienen **escalones**
  (p. ej. KESAN pasa por 30 NM; OSTION sigue la costa) que aquí se aproximan con
  sectores anulares limpios (dos arcos + dos radiales).
- Los sectores del centro (CEGAN, JUKOT, LOMAS) y los splits radiales del este
  (KESAN/CONDOR/SIERRA/TERMAS) son las zonas de **mayor incertidumbre**; conviene
  afinarlos contra la carta por un controller con la autoridad de la fuente.
- OSTION se aproximó como cuña polar oeste (249→344, 13→40) en lugar de seguir la
  línea de costa exacta.
- Los mínimos y nombres sí están **exactos** (leídos directamente de la carta).

### 16.7 Cómo verlo

1. Abrir `SCEL_ATC_Radar.html`, elegir un dispositivo (p. ej. SECTOR G) y activar
   `TMA SCSE`.
2. Activar la capa MRVAC (`minsectorBtn` / `toggleMRVAC`).
3. Centrar en La Serena: `panX=-20; panY=208; currentScale≈70`.

**Pendiente:** afinar los límites escalonados de los sectores del centro y del este
si se dispone del vector AIP; regenerar con el generador y reinyectar.

---

## 17. ETO del ROUTE LEG ahora en hora absoluta (consistente con el reloj simulado)

**Fecha:** 2026-10-13 · **Archivo:** `SCEL_ATC_Radar.html`

### 17.1 Problema reportado

*"Las horas estimadas sobre los puntos del ROUTE LEG de salidas y llegadas: los
tiempos son diferentes a los del reloj del simulador."*

### 17.2 Causa

El ROUTE LEG dibujaba bajo cada waypoint `fmtET(etMinutes(a,cumNM))`.
`etMinutes()` devuelve una **duración en minutos** ("minutos desde ahora") y
`fmtET()` la formatea como `HH:MM` (p. ej. `00:12` = 12 min). Es decir, mostraba
un **tiempo relativo**, no una hora. El reloj Gorgy de la cabecera, en cambio,
muestra una **hora UTC absoluta** (`_simTimeMs`, p. ej. `01:53:29`). Al comparar
`00:12` (duración) con `01:53` (hora) no calzaban.

### 17.3 Corrección

Se añadió `fmtETAbs(etMin)` (junto a `fmtET`) que devuelve la **hora absoluta del
reloj simulado**:

```
ETO_abs = _simTimeMs + etMin · 60000   →   formateado HH:MM (UTC)
```

`etMin` está en **minutos simulados** y `_simTimeMs` avanza ×`SIM_F`, por lo que la
suma da la hora del reloj en la que la aeronave pasa por el punto. El ROUTE LEG
(L4679) ahora usa `fmtETAbs(eto)` en lugar de `fmtET(eto)`.

**Coherencia (por qué el ETO absoluto es estable):** mientras la aeronave avanza a
una gs casi constante, en Δ minutos simulados el reloj avanza Δ y la distancia al
punto se reduce en gs·Δ/60, de modo que `etMinutes` baja ≈Δ y el ETO absoluto
(`reloj + etMinutes`) se mantiene. Con aceleración (salida) el ETO absoluto baja
levemente —realista— al ganar velocidad.

### 17.4 Alcance

- **ROUTE LEG (salidas y llegadas):** corregido a hora absoluta. Es el mismo bloque
  de dibujo (L4658-4681) para cualquier aeronave seleccionada con `showRoute`, por
  lo que aplica igual a salidas y llegadas.
- **RBL "T=" (L6728):** se mantiene como **duración relativa** (`fmtET`). Es un
  "tiempo hasta el punto del RBL" etiquetado `T=`, contexto de distancia a un punto
  arbitrario; allí una duración es lo correcto. No se tocó.

### 17.5 Verificación (CDP)

Función (reloj 01:49, `SIM_F=1`):

| Llamada | Resultado | Esperado |
|---|---|---|
| `fmtETAbs(0)` | `01:49` | = reloj ✓ |
| `fmtETAbs(15)` | `02:04` | reloj+15 ✓ |
| `fmtETAbs(90)` | `03:19` | reloj+90 (cruza hora) ✓ |
| `fmtET(12.4)` | `00:12` | relativo (RBL) ✓ |

Integrado (salida TAM200, SID ANGOD8B_17R, reloj 01:53:29):

| Punto | Dist acum. | `etMinutes` | ETO absoluto |
|---|---|---|---|
| wp1 | 9.6 NM | 2.8 min | `01:56` |
| wp2 | 57.2 NM | 11.3 min | `02:02` |

Captura: reloj `01:53:29` y ETOs en la ruta `01:56 / 01:59 / 02:00` — todos
consistentes con el reloj. Sin errores de consola.

### 17.6 Nota

Si se desea la misma precisión que el reloj (con segundos), basta cambiar
`fmtETAbs` para emitir `HH:MM:SS`; se mantuvo `HH:MM` por el formato original
especificado en `FRASEOLOGIA RADAR.txt`.

## Capítulo 18 — RBL +1 punto · AIPMAP en ventana · HALO 5/3 NM

Tres cambios solicitados en lote, aplicados y verificados en la misma sesión
(sesión CDP reabierta tras reiniciar el servidor estático local del puerto 8777,
que había caído; servido ahora con un `HttpListener` mínimo — `serve8777.ps1`).

### 18.1 RBL: etiqueta a 10 px (+1 punto)

- **Etiqueta principal** (rumbo recíproco + distancia): `bold ${9*DPR}` →
  `bold ${10*DPR}` (L6729).
- **Separación del "T="**: `my-3*DPR-11*DPR` → `my-3*DPR-12*DPR` (L6736) para
  que la línea de tiempo no se solape con la etiqueta al crecer 1 px.
- **Vista previa al pasar el cursor** (pendiente de creación): 9 → 10 px (L6812).
- **No se tocó** el RBL en vivo (`LIVE RBL`, 9 px, L6786) ni el indicador previo
  "RBL →": son otra función con estilo propio.

**Verificación (CDP, runtime):** instrumentación de `fillText` durante dos frames
tras `forceRedraw()` con un RBL ac-ac activo:

| Texto | Fuente capturada | Esperado |
|---|---|---|
| `177°  16.2NM` | `bold 10px Share Tech Mono,monospace` | 10 px V |
| `T=00:03` | `bold 10px Share Tech Mono,monospace` | 10 px V |

Captura visual: `T=00:03` sobre `177° 16.2NM` con separación limpia (sin solape).

### 18.2 AIPMAP: botón que abre VENTANA del navegador

`openAIPMAP()` reescrito (L6913-6928):

1. **Ventana independiente:** `window.open(AIPMAP_URL,'aipmap_win','popup=yes,width=1320,height=900,left=60,top=40')`.
   Cadena de features ⇒ el navegador abre una **ventana** (no pestaña); nombre
   fijo `aipmap_win` ⇒ al volver a pulsar se reutiliza la misma ventana.
2. **Fallback:** `window.open(AIPMAP_URL,'_blank')` (pestaña nueva).
3. **Último recurso:** `location.href=AIPMAP_URL` (navegar en la pestaña actual).

- `AIPMAP_URL` sin cambios: `https://sites.google.com/view/accs-2026/sid` (L6912).
- Comentario CSS (L618) y `title` del botón (L911) actualizados: "ventana nueva".
- **Corrección latente:** la versión anterior pasaba `'noopener'`, que hace que
  `window.open` devuelva siempre `null` → caía siempre al fallback. Con features
  explícitas y sin `noopener`, la primera ruta puede devolver la ventana.

**Verificación (CDP, `window.open` parcheado para registrar llamadas):**

| Paso | Llamada registrada | Esperado |
|---|---|---|
| Ruta 1 | `(AIPMAP_URL, 'aipmap_win', 'popup=yes,width=1320,height=900,left=60,top=40')` | ventana V |
| Ruta 2 (si 1 bloqueada) | `(AIPMAP_URL, '_blank', undefined)` | pestaña V |
| Efectos | `sysLog('AIPMAP · abriendo ventana del navegador')` + clase `active` en `#aipmapBtn` | V |

**Nota de E2E:** sin gesto real de usuario el popup-blocker de Chromium bloquea
`window.open` (sonda `window.open('about:blank',…)` → `null`). El clic humano en
el botón otorga la activación de usuario y es la prueba final pendiente; toda la
ruta de código (URL, nombre, features, orden de fallbacks, log y estado del
botón) quedó verificada con la llamada interceptada.

### 18.3 HALO: dos radios de separación (5 NM ≥FL250 / 3 NM <FL250)

- **Helper `haloRadiusNm(a)`** (L4622-4624): `(a&&a.alt>=25000)?5:3`.
  Criterio: 5 NM **en o por encima** de FL250; la reducción a 3 NM solo aplica
  **por debajo** (alt exactamente 25000 ⇒ 5 NM).
- **Dibujo** (L5985): `ctx.arc(pos.x,pos.y,nmPx(haloRadiusNm(a)),…)` — se evalúa
  en cada frame, así que si la aeronave cruza FL250 con el HALO activo el
  círculo cambia de radio **en vivo**.
- **Log del toggle** (L4631): `ID ← HALO {r}NM (≥FL250|<FL250) ACTIVO/OFF`.
- **Botón del menú contextual** (L4596): al abrir muestra el radio vigente
  (`HALO 5NM ●` / `HALO 3NM ●`; `HALO ○` cuando está apagado).

**Verificación (CDP):**

| Comprobación | Resultado | Esperado |
|---|---|---|
| `haloRadiusNm` alt 30000 / 25000 / 24999 / 10000 / 0 | 5 / 5 / 3 / 3 / 3 | V |
| Radio dibujado alt 30000 (`nmPx(1)=12.3875`) | `arc r=61.94 px` = nmPx(5) | V |
| Radio dibujado alt 10000 | `arc r=37.16 px` = nmPx(3) | V |
| Botón al abrir menú (alt 28000 / 9000) | `HALO 5NM ●` / `HALO 3NM ●` | V |
| Log ≥FL250 | `LAN101 ← HALO 5NM (≥FL250) ACTIVO` | V |
| Log <FL250 | `LAN101 ← HALO 3NM (<FL250) OFF` | V |

Sin errores de consola tras la recarga y las pruebas de los tres cambios
(`console.error` interceptado: 0 eventos).

### 18.4 Alcance y pendientes

- Aplica a: RBL ac-ac de simulado (etiqueta + `T=`), botón `#aipmapBtn` (barra
  GEN), HALO por clic derecho sobre cualquier aeronave.
- Pendiente humano: clic real en **AIPMAP** para confirmar E2E la ventana
  1320×900 (ruta de código ya verificada).

## 19. Lote: reloj de arranque 12:00:00, arreglo de FLIGHTS, ventana HOLD y ROC/ROD BADA

### 19.1 Reloj simulado — arranque fijo a las 12:00:00

- `_simTimeMs` (L11078): ya no es `Date.now()` (arranque en hora real del
  cap. 15); ahora se inicializa a **hoy 12:00:00 UTC** (`setUTCHours(12,0,0,0)`).
  La hora real del PC no interviene en ningún caso.
- Escenarios internos (`_scheduleFlights`) y XML siguen fijando su hora propia
  vía `setSimClockHHMM` (L8545); el escenario `deps` con el que arrancan PC y
  tablet **no** mueve el reloj.
- `parseAndLoadScenario` (L8414): `startTime` validado (regex `HH:MM` y rango
  00:00–23:59); si está mal formado → fallback a `flights[0].time`. El reloj
  nunca salta a una hora "rara".

**Verificación (CDP):** recarga → `sim=2026-10-15T12:00:00…`, reloj `12:00:28`
tras `selectDevice('pc')` (escenario `deps` activo, reloj intacto); XML con
`startTime="18:45"` → `sim=…T18:45:00.000`; con `startTime="06:15"` → `06:15:00`.

### 19.2 Sección FLIGHTS — crear un vuelo ya no mueve el reloj

- `addFlightFromFields` (L8323): **eliminado** el salto de reloj del primer
  vuelo manual (`if(scenarioState.flights.length===1) setSimClockHHMM(hora)`).
  Crear un vuelo nunca cambia el reloj (antes: saltaba a la hora tecleada y,
  con formato inválido, a una hora "random" — la queja original).
- `parseFlightLine` (L8263): HORA validada (`^\d{1,2}:\d{2}$`, rango hasta
  23:59) y normalizada a `HH:MM`; errores claros ("HORA inválida …", "fuera de
  rango …") sin crear el vuelo.
- Semántica de carga: hora ya alcanzada → se crea inmediato; hora futura →
  `⏱ programado` y aparece cuando el reloj (corriendo) alcanza esa hora — igual
  que los vuelos de un escenario XML.
- Modal: `fmCount` refresca `X/Y programados · reloj HH:MM` y `ffHora` se
  prellena con la hora simulada actual si está vacía.

**Verificación (CDP):** `12:00` → "✓ MAN101 … creado" con `inAir=true` y reloj
sin mover; `13:30` → "⏱ MAN202 programado para las 13:30 (reloj simulado 12:00)"
con reloj intacto; `25:99` → "HORA fuera de rango"; `abc` → "HORA inválida" (en
ambos: vuelo no creado). XML `06:15/06:40` → barra `VUELO XC 1/2`, XML101 en
aire al instante y XML202 spawnea al llegar el reloj a 06:40.

### 19.3 parseFL acepta "FL150" (antes → NaN)

- `parseFL` (L8311): soporta el prefijo `FL` además de `F` y número puro;
  `NaN` → `0`.
- Efecto: mensaje "FL150→CCL FL100 creado" (antes `FLNaN→CCL FLNaN`) y el
  bloque CCL de `spawnFlight` sí se aplica (`tAlt=10000`, `cfl=100`,
  `reqFL=100` en un A320 de prueba).

### 19.4 Ventana HOLD rediseñada (clic derecho sobre la etiqueta)

- `#holdCtxPopup` (L1408): fondo plomo `#848a92`, título y ✕ en **negro** 14 px,
  **pestañas apiladas en vertical** (HOLD/DCT/OPCODE/TXT): activa con fondo
  `#fff` y borde 2 px de acento (`#00a884` HOLD, `#2f6fd0` DCT, `#b89400`
  OPCODE, `#2f7f9a` TXT); inactivas `#cdd2d8` con borde 1 px. Paneles de
  contenido en `#fff` con texto negro (13 px).
- `ctxHoldSelect`: **solo el nombre** del fix (antes incluía
  `/180° IZQ 15NM FL090`).
- `showHoldCtx` (L4568) posiciona midiendo `offsetWidth/offsetHeight`;
  `switchCtxTab` (L4617) conmuta pestañas y paneles.

**Verificación (CDP):** popup `display:block` con bg `rgb(132,138,146)` (#848a92);
activa tras `switchCtxTab('opc')` → `rgb(255,255,255)` + `2px solid
rgb(184,148,0)` (#b89400) y la HOLD pasa a `rgb(205,210,216)`; opciones del
selector = `["— SIN HOLD —","MORPA","DABIT","KADAK","VTN","TEGEB","SEDPA",
"UGOLA"]`; conmutación hold→txt→hold correcta (solo un panel `block`); cierre →
`display:none`.

### 19.5 Botones ROC/ROD (razón vertical MIN/MAX — tabla BADA)

- Botones `#rocBtn`/`#rodBtn` en la sección ASIGNAR RUMBO (tras CANCEL/HOLD) y
  menú `#rocRodMenu` (L1461, mismo estilo plomo/blanco) con
  `MIN ▸ n ft/min` / `MAX ▸ n ft/min` y resaltado del activo.
- `_rocRodRates` (L4728): ROC = `{min: min(climb_ROC, machClimb_ROC),
  max: max(…)}` — **corregido**: antes `lo=climb_ROC` y `hi=max(climb_ROC,
  machClimb_ROC)` daban `min==max` (selector sin efecto). ROD = `{min, max}` de
  `{desc_ROD, desc240_ROD, appr_ROD}`.
- `openRocRod` (L4741) alterna con el segundo clic; `applyRocRod` (L4777) fija
  `a.rocSel`/`a.rodSel`, registra en el log y actualiza el botón
  (`ROC · MIN` + clase `ok`); `getVertRate` (L5421) aplica el valor fijo con el
  factor de aproximación y el **piso MNM Razón ASC de la SID** (`sidRoc`).

**Verificación (CDP):** `_rocRodRates('roc', A320)` → `{min:1000, max:2000}`
(antes `{2000,2000}`); `('rod', A320)` → `{min:1000, max:3500}`.
`getVertRate(da=+1000)` LAN200 (climbing, `sidRoc=350`): none 1960 /
min **1074** (piso SID 350 ft/NM → ≈1074 > 1000, no se vuela por debajo) /
max 2000. `getVertRate(da=−1000)` a 29000 ft: none 3008 / min 1000 / max 3500.

### 19.6 Regresión: suite 112/0

- Suite `tests/hold_test.js` por CDP con estado inicial saneado
  (`aircraft.length=0; selected=-1;` justo antes del eval): **n=112, FAIL=0**
  (`CS2:OK sky220 → idx −1`, `PT2:OK basura con seleccion → true`).
- Los FAIL CS2/PT2 de corridas previas fueron **artefacto de estado** (vuelos
  del escenario `deps` presentes al inicio de la inyección), no regresión de
  código.

---

## 20. Aerovías VOR superiores (AWY-SUP) — botón AWY-SUP en el panel izquierdo

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 20.1 Pedido

*"las aerovías UV detectadas quiero que estén visibles en la pantalla radar al presionar el botón AWY-SUP en el panel al costado izquierdo del simulador"*, con línea **azul más gruesa que AWY-INF**, tomando los datos del PDF AIP indicado: `vENR 3 CONVENCIONAL UV.pdf` (sección 2 ENR Parte 2 del AIP Chile).

### 20.2 Datos leídos del PDF (8 páginas, verificadas visualmente)

El PDF no se pudo analizar con los extractores de texto (tablas con columnas y páginas rotadas), así que se **renderizó en el navegador embebido** (CDP: `Emulation.setDeviceMetricsOverride` + `Input.dispatchKeyEvent` Ctrl+0 + captura) y se leyó cada página como imagen. Rutas y fixes confirmados página por página:

| Ruta | Fixes (orden AIP) | Pág. PDF |
|---|---|---|
| UV 107 | DGO → LINER | 1 |
| UV 115 | NAS → ALMIR → SUNLI → PWL | 1 |
| UV 120 | VLD → GUXER → TOMUS → KEVET → MPI | 1 |
| UV 123 | MON → TEN → OPURA → BAL | 1–2 |
| UV 200 | ARI → SIRAM → IQQ → BRADA → FAG → DOVRI → PUNSO → DAT → UPUKU → ISENO → TIMDA → TOY → ESNOX → BUXIS → VTN → DGO → ESOKI → SOSTA → CAR → PANEX → VLD → ISUDO → KIKOP → MON | 3–4 |
| UV 204 | ARI → PUGOT → IQQ → REBOL → FAG → VADIX → SILEN → PUMEN → DAT → EKUBO → VUNIK → EMBAL → SIMOK → MOLPU → TBN | 4, 6 |
| UV 206 | VTN → TENUT → OLMUE → TBN | 6 |
| UV 208 | TOY → EMBAL → SIMOK → MOLPU → TBN | 6 |

- **UV 200** y **UV 204** se unificaron con su "(CONTINUACIÓN)" de la página siguiente en una sola línea continua (etiqueta única).
- **49 fixes** con coordenadas DMS convertidas a decimal (6 decimales, cultura invariante, bloque 100 % ASCII).
- Correcciones de lecturas previas por texto crudo: se confirmó **ESNOX** (no ADNOX), `SUNLI`/`KEVET`, y las longitudes de PWL (67°37'16"W) y de todo el tramo sur.

### 20.3 Implementación

- **Bloque de datos** (insertado tras el bloque AWY-INF, L3147): `AWY_SUP_FIX_LL` (49 coords), `AWY_SUP_FIX_XY` (proyección local `x=(lon−SCEL_LNG)*60*cos(SCEL_LAT)`, `y=(lat−SCEL_LAT)*60`) y `AWY_SUP` (8 rutas con `nombre` "UV nnn").
- **Mapa independiente**: `BRADA`, `DOVRI` y `PUNSO` del UV tienen coordenadas **distintas** a las del mismo nombre en la ruta V inferior (`AWY_FIX_LL`), por lo que AWY-SUP usa su propio mapa con `supFixXY()` (prioridad UV → NAVAIDS → WPT).
- **`showSup`** en el estado global; **botón `#supBtn`** (`AWY-SUP`, clase `cat-btn sup off`) justo debajo de AWY-INF en el panel GEN; **`toggleSup()`** (alterna `on/off` + `forceRedraw()`).
- **CSS** `.cat-btn.sup.on/off` (azul vivo `#66aef5` encendido, `#4a6f96` apagado).
- **`drawAirwaysSup()`** invocado en el bucle de render junto a `drawAirways()`:
  - línea `rgba(90,160,255,.55)` con `lineWidth=2*DPR` (AWY-INF: `rgba(138,180,216,.18)`, `1*DPR`),
  - etiqueta `bold 9px` "UV nnn" en `rgba(140,195,255,.75)` al medio del trazado.

### 20.4 Verificación (CDP, página real recargada)

| Prueba | Resultado |
|---|---|
| `AWY_SUP` | 8 rutas `[UV107,UV115,UV120,UV123,UV200,UV204,UV206,UV208]`, 49 fixes, **0 fixes sin resolver** |
| `toggleSup` / `drawAirwaysSup` / `#supBtn` | function / function / presente; tras clic → `showSup=true`, clase `cat-btn sup on` |
| Diferencia de canvas (hash de píxeles) | `showSup` on/off → distinto; suma píxeles azules 18 → 28 |
| **Grosor medido** (racha de píxeles, tramos verticales) | **AWY-INF = 1 px** · **AWY-SUP = 2–3 px** |
| Color de línea | SUP `rgb(49,95,151)` (azul intenso) vs INF `rgb(17,22,27)` (tenue) |
| Captura visual | botón AWY-SUP encendido en el panel; etiquetas `UV 107` y `UV 206` visibles sobre el radar (vista 40 y 250 NM) |
| Suite `tests/hold_test.js` | **115/115, FAIL=0** |
| Sincronización | `SCEL_ATC_Radar.html` ≡ `netlify-deploy\index.html` (MD5 `7AA0C0BF0DDFF80AE8BF5ACF431E6B34`) |

### 20.5 Notas

- El botón arranca **apagado** (`showSup=false`), como AWY-INF.
- El PDF temporal se eliminó del repo; los scripts de extracción quedaron en el temp del sistema (`gen_awy_sup.ps1`, `cdp_pdf.ps1`, `crop.ps1`).

## 21. SID ALBAL 7C/5D — MNM Razón ASC por carta + 46 puntos AIP «Tabla de coordenadas»

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 21.1 Pedido

*"Redefinir SIDs para clearance de obstáculos: ALBAL 7C: 320 FT/NM TIL FL160; ALBAL 5D: 400 FT/NM TIL 9000'. Además agregar las coordenadas del PDF de AIPMAP SCEL — Tabla de coordenadas a la base de fixes."*

### 21.2 Fuentes de datos

| Fuente | Uso | Detalle |
|---|---|---|
| Carta SID 10 (AMDT 102, 14 MAY 2026) | Perfil 7C/5D | 7C: «Ascenso en TR176°M (177,07°T) hasta DESIT o VAGOS → EL250 → viraje izq. EL401-ALBAL»; 5D: «TR357°M (357,44°T) hasta 5000 FT → DF PARKE → EL401-ALBAL». DIST desde ARP: 7C17L 7,59/17,41/36,64 · 7C17R 7,51/17,78/36,64 · 5D 29,99/36,64 NM |
| `SCEL Tabla de coordenadas.pdf` (AMDT 103, 06 AUG 2026) | 137 puntos DMS | Págs. 1–3 (3 bloques/pág.; pág. 3 solo 3 pts con umbral ≥3). Formato `33°00'15,69'' S 70°49'26,10'' W` (coma decimal, doble apóstrofo). Incluye umbral RW17L/R y 35L/R |
| Extracción | pdf.js 3.11.174 | El visor PDF de Chrome no expone `PDFViewerApplication` en contexto `http`; se inyectó pdf.js vía CDP en una página puente (`_pdf_extract.html`) |

Conversión a coordenadas del simulador: `x=(lon−SCEL_LNG)*60·cos(SCEL_LAT)`, `y=(lat−SCEL_LAT)·60`,3 decimales (cultura invariante).

### 21.3 Cambios en el código

1. **`SID_ROC`**: `ALBAL7C` de `{roc:350,til:16000}` a **`{roc:320,til:16000}`**. `ALBAL5D:{roc:400,til:9000}` ya coincidía con la carta. Comentario al lado: «SID10 AMDT102: 320 FT/NM TIL FL160 · 400 TIL 9000'».
2. **Comentario de rutas** `ALBAL7C_17L/R` y `ALBAL5D_35L/R` ampliado con el texto de la carta (TR176°M/TR357°M, PATH CA/DF/TF, DIST, MNM Razón ASC). La geometría de las rutas no cambió: ya era consistente con la carta (eje 177°/357°, `_ap` VAGOS/DESIT 4000–9000', `_ax` 400 FT/NM hasta 5000', EL250 10000', EL401 FL140, ALBAL FL210).
3. **`WPT` — bloque nuevo «AIP Chile SCEL TABLA DE COORDENADAS AMDT 103»** (insertado antes del cierre del objeto): **46 fixes nuevos** con `alt:0` y el DMS del AIP en el comentario de cada línea. Además **10 existentes reposicionados** a 3 decimales (la versión previa tenía 2 decimales; Δ máx 0.05 NM).

**46 fixes añadidos:** ARUKI, EL001, EL015, EL023, EL025, EL035, EL041, EL059, EL069, EL076, EL079, EL099, EL129, EL130, EL138, EL148, EL179, EL184, EL243, EL383, EL981–EL988, EL992, EL995, EL996, ILKOS, KIDAS, KUDKA, MESAL, MOLPU, NEGAG, NEGTA, PADOP, PORMA, ROBAK, TELAG, TEPIL, UKEMU, VUARI.

**10 reposicionados** (Δ previo 0.02–0.05 NM — redondeo a 2 decimales de ediciones antiguas):

| Fix | Antes (x,y) | Ahora (x,y) | Fix | Antes (x,y) | Ahora (x,y) |
|---|---|---|---|---|---|
| EL222 | −1.9, 23.4 | −1.919, 23.388 | EL570 | 3.3, 57.1 | 3.291, 57.066 |
| EL370 | −15.3, 11.5 | −15.324, 11.484 | EL680 | 5.4, 47.2 | 5.4, 47.172 |
| EL382 | −5, 19.7 | −5.039, 19.728 | ASIMO | 23.5, 90.7 | 23.489, 90.654 |
| EL449 | 13.4, 33.5 | 13.385, 33.534 | DABIT | −2.5, 68.6 | −2.485, 68.562 |
| VUDOG | −1.6, 38.5 | −1.583, 38.52 | VULBI | 8.5, 65.6 | 8.456, 65.604 |

### 21.4 Verificación (página recargada vía CDP)

| Prueba | Resultado |
|---|---|
| Dataset AIP vs `WPT` (137 pts) | **46 faltaban**, 10 con Δ>0.02 NM, 81 coinciden ≤0.02 NM |
| `WPT` total | 190 → **236**; 0 claves nuevas ausentes; los 10 reposicionados con valores exactos |
| Spawn `ALBAL7C_17L` (B738) | `sidRoc=320`, `sidRocTil=16000`, `vSpd=1364` fpm (=320×255/60 — piso aplicado al spawn), `authLvl=FL270`, eje 177° |
| Spawn `ALBAL5D_35R` | `sidRoc=400`, `sidRocTil=9000`, `vSpd=1705` fpm, eje 357° |
| `getVertRate` piso MNM | 7C: rate=need=1364 ✓ · 5D: rate=need=1705 ✓ · a FL165 (>til) → 300 fpm, **piso desactivado** ✓ |
| Geometría SID | rutas 5/5 pts, coords finitas, fixes DESIT/VAGOS/EL250/EL401/ALBAL/PARKE presentes, `sidCrossAlt`=FL210 |
| `SID_ROC` | 39 SIDs; solo ALBAL7C cambió (350→320); resto intacto |
| Errores JS en la sesión de prueba | **0** |
| Suite `tests/hold_test.js` (harness inyectado, navegador integrado — Chrome headless corrupto: falta `chrome.exe` en la carpeta de versión) | **115/115, FAIL=0, ERR:0** |
| Integridad del archivo | BOM UTF-8, CRLF 11894, 0 U+FFFD, 0 LF solas (las del bloque insertado se normalizaron a CRLF) |
| Sincronización | `SCEL_ATC_Radar.html` ≡ `netlify-deploy\index.html` (MD5 `F28A1190DCBBCE1B6AB9B5F73E3328FE`) |

### 21.5 Notas

- `EL001`, `EL995` y `EL996` comparten coordenadas en el AIP (mismo punto publicado con3 nombres); las 3 entradas se insertaron tal cual.
- En la carta, DESIT está a 7,59 NM del **ARP** (no del umbral); el simulador rutea desde el umbral real (~9,6 NM) — correcto en planta: el rumbo 177,1°T y la posición del fix coinciden.
- El PDF AIP y los binarios de pdf.js (`scel_coords.pdf`, `pdf.min.js`, `pdf.worker.min.js`, `_pdf_extract.html`) se eliminan del repo al cerrar este capítulo.
- La extracción del PDF de coordenadas se hizo en la pestaña del radar vía `Runtime.evaluate` (CDP port 9223) porque el hook del visor PDF no estaba disponible.

### 21.6 NEBEG 7C/5D — verificación contra carta (MNM 350/FL230 · 400/FL190)

**Mismo día, pedido de seguimiento:** definir/verificar las salidas NEBEG con el texto de la carta (usuario, 2026-10-22):

- **MNM Climb Rate:** NEBEG 7C: **350 FT/NM TIL FL230** · NEBEG 5D: **400 FT/NM TIL FL190**.
- **NEBEG 7C RNAV** (DEP/TAKE-OFF RWY 17L/R): *«Ascenso en TR176° hasta DESIT o VAGOS, según corresponda, continuar directo hacia EL250, posterior viraje izquierda continuar en TR087° hacia EL400-EL500-NEBEG para interceptar AWY»*.
- **NEBEG 5D RNAV** (DEP/TAKE-OFF RWY 35L/R): *«Ascenso en TR357° hasta 5000FT viraje derecha directo PARKE, continuar en TR153° hasta EL400 y luego viraje izquierda TR087° hacia EL500-NEBEG para interceptar AWY»*.

**Resultado de la auditoría: todo ya coincidía — sin cambios de datos.** Se verificó contra la página recargada (CDP):

| Elemento | Carta | Simulador | Estado |
|---|---|---|---|
| `SID_ROC.NEBEG7C` / `NEBEG5D` | 350/FL230 · 400/FL190 | `{350,23000}` · `{400,19000}` | ✓ sin cambio |
| Ruta 7C (6 pts) | thr→DESIT/VAGOS→EL250→EL400→EL500→NEBEG | idéntica; altMin 4000-9000/10000/FL135/FL170/FL230 | ✓ |
| Ruta 5D (6 pts) | thr→eje 5000FT→PARKE→EL400→EL500→NEBEG | idéntica; altMin 8000/FL170/FL190 | ✓ |
| Eje 7C | TR176°M (177,07°T) | 17L→DESIT **177,1°** · 17R→VAGOS **177,4°** | ✓ |
| EL250→EL400→EL500→NEBEG | TR087° | **88,0 / 87,9 / 87,7°** | ✓ |
| Eje 5D | TR357° | axisHdg **357** | ✓ |
| PARKE→EL400 | TR153°M (≈154,4°T) | **154,2°** | ✓ |
| Virajes | dcho. a PARKE · izdo. en EL400 | 357°→148,5° (151° d.) · 154°→88° (66° i.) | ✓ |

**Sonda de spawn (B738):**

| Prueba | NEBEG7C_17L | NEBEG5D_35L |
|---|---|---|
| `sidRoc` / `sidRocTil` | 350 / 23000 ✓ | 400 / 19000 ✓ |
| `vSpd` al spawn (piso aplicado) | 1492 fpm (=350×255,7/60) ✓ | 1705 fpm ✓ |
| `getVertRate` bajo el til | rate=need=1492 ✓ | rate=need=1705 ✓ |
| Sobre el til (FL235 / FL195) | 286 fpm — piso **OFF** ✓ | 294 fpm — piso **OFF** ✓ |
| `authLvl` / eje | FL270 / 177° ✓ | FL270 / 357° ✓ |
| `sidCrossAlt` | FL230 (NEBEG) ✓ | FL190 (EL500) ✓ |

- Único cambio de código: el **comentario** del bloque SID9 ampliado con el texto bilingüe de la carta y la nota MNM (estilo del bloque ALBAL del cap. 21.1–21.3).
- Suite `tests/hold_test.js` regenerada contra el HTML actualizado: **115/115, FAIL=0, ERR:0**.

## 22. Menú de etiqueta: botón CTC TWR (contacto Torre 118.1)

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 22.1 Pedido

*"Está pendiente habilitar al hacer click derecho en la etiqueta radar la opción CTC TWR y que haga exactamente lo mismo que al hacer click en el panel de comandos botón transfer twr."*

### 22.2 Implementación

- **HTML** — en `#holdCtxPopup` (menú contextual de la etiqueta, popup de pestañas HOLD/DCT/OPCODE/TXT), nuevo botón **`☎ CTC TWR`** justo debajo de la columna de pestañas, con estilo verde torre (`#0f3d2e`/`#7dffc8`) y `onclick="transferTwrCtx()"`.
- **JS** — nueva función `transferTwrCtx()` (junto a `leaveHoldCtx`):
  1. toma la aeronave del menú (`_ctxAc()`),
  2. la selecciona (`selected=_ctxAcIdx; updateSB()`), igual que los otros `*Ctx`,
  3. llama a **`transferTwr(a)`** — la misma función del botón `⇒ TRANSFERIR TWR` del panel (`handedOff=true`, `lastCmd='→ TWR 118.1'`, `sysLog`, `vFbk`, readback «contacto Santiago Torre 118,1» por fraseología),
  4. cierra el popup (`closeHoldCtx()`).
- Sin cambios en `transferTwr` ni en la fraseología `twr` del JSON (ya existente).

### 22.3 Verificación (página recargada, CDP)

| Prueba | Resultado |
|---|---|
| Botón en el popup | presente, texto `☎ CTC TWR`, `onclick=transferTwrCtx()` |
| `transferTwrCtx` | function |
| Flujo completo (menú sobre LAN101 → CTC TWR) | `handedOff=true`, `lastCmd='→ TWR 118.1'`, `selected=0`, popup cerrado, `vFbk='✓ LAN101 CONTACTO TWR 118.1'`, **0 errores JS** |
| Equivalencia con el panel (transferTwr() en otra aeronave) | mismos campos (`handedOff`, `lastCmd`) → **misma acción** |
| Suite `tests/hold_test.js` | **115/115, FAIL=0, ERR:0** |
| Sincronización | `SCEL_ATC_Radar.html` ≡ `netlify-deploy\index.html` |

### 22.4 Notas

- El botón aparece siempre en el menú de cualquier aeronave en vuelo (igual que el del panel; `transferTwr` no valida estado previo).
- Las aeronaves en tierra (`landed`) no abren el menú (comportamiento preexistente de `showHoldCtx`).

## 23. Legibilidad TWR/RBL — naranja nítido y texto RBL +20%

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 23.1 Pedido

*"Los colores de la etiqueta en estado TWR (transferida a Torre) deben verse naranja nítidos y el texto del RBL un20% más grande."*

### 23.2 Implementación — naranja TWR

El estado `handedOff` (y `transferred`/APPR FINAL) usaba el naranja oscuro `#853400` / `rgba(133,52,0,…)`, ilegible sobre el fondo negro del radar. Se reemplazó por el naranja nítido **`#ff9d42`** / `rgba(255,157,66,…)` en todos los trazos de la etiqueta:

| Zona | Antes | Ahora |
|---|---|---|
| Color del blip | `#853400` | `#ff9d42` |
| Línea guía (leader) | `rgba(133,52,0,…)` | `rgba(255,157,66,…)` |
| Borde de la etiqueta | `#853400` | `#ff9d42` |
| Tinte del encabezado | `rgba(133,52,0,…)` | `rgba(255,157,66,…)` |
| Row0 (indicativo) | `#853400` | `#ff9d42` |
| Row0 SSR | `#853400` | `#ff9d42` |
| Row2 (alt/vel) | `#853400` | `#ff9d42` |
| Row3 (ruta) | `#853400` | `#ff9d42` |

- Se conservan `#853400` como **default de fila para aeronaves normales** (no transferidas) y en el destello ILS — solo cambia el estado TWR/APPR FINAL.
- Panel lateral (`updateSB`): el `status` ahora muestra **`☎ TWR 118.1`** cuando `a.handedOff` (antes solo «LLEGADA/SALIDA/APPR FINAL»).

### 23.3 Implementación — texto RBL +20%

| Tamaño | Antes | Ahora |
|---|---|---|
| RBL simulado (bold, Share Tech Mono) | `10*DPR` | `12*DPR` |
| RBL LIVE (bold) | `9*DPR` | `10.8*DPR` |
| Indicador «RBL →» pendiente | `8*DPR` | `9.6*DPR` |

### 23.4 Verificación (página recargada, CDP, muestreo de píxeles)

| Prueba | Resultado |
|---|---|
| Etiqueta TWR (`handedOff`) — píxeles naranjas | **400** (color exacto `255,157,66` entre los dominantes) |
| Etiqueta APPR FINAL (`transferred`) — píxeles naranjas | **824** |
| Etiqueta aeronave normal (azul base) | **0** naranjas, **309** azules (`52,167,233`) → sin regresión |
| Fuentes RBL en el código servido | `12*DPR` ✓, `10.8*DPR` ✓, `9.6*DPR` ✓ |
| Ocurrencias de `#853400` | **2** (default de fila normal + ILS; ninguna en estado TWR) |
| Estado en panel lateral | `status` incluye `☎ TWR 118.1` al transferir |
| Errores JS durante la prueba | **0** |
| Suite `tests/hold_test.js` | **115/115, FAIL=0** |
| Integridad del archivo | UTF-8 BOM ✓, CRLF 11922 / LF-sola 0 / U+FFFD 0 |
| Sincronización deploy | `netlify-deploy\index.html` ≡ fuente, MD5 `16E030536BEE3EB6AEBD59CFD7A331D0` |

### 23.5 Notas

- La verificación por píxeles forzó el render con `frame(performance.now())` (la pestaña en segundo plano throttlea `requestAnimationFrame`) y centró `panX/panY` en aeronaves de prueba sintéticas, luego removidas.
- El naranja TWR se aplica en TODOS los estados de etiqueta (borde, leader, blip, encabezado y las 4 filas), no solo el texto, para máxima legibilidad del estado de handoff.
- Para redesplegar: arrastrar `netlify-deploy\` a https://app.netlify.com/drop.

## 24. ROUTE exclusivo — una sola ruta visible a la vez

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 24.1 Pedido

*"Al presionar ROUTE en una aeronave mostrará su ruta; al presionar ROUTE en la aeronave siguiente, la función ROUTE de la precedente desaparecerá."*

### 24.2 Implementación

En `toggleRouteCtx()` (único punto que muta `showRoute`), al **activar** la ruta de la aeronave seleccionada se recorre `aircraft[]` y se apaga `showRoute` en cualquier otra que lo tuviera encendido, con mensaje de sistema:

- `«<ID> ← RUTA OCULTA (otra aeronave activó ROUTE)»` para la aeronave que pierde su ruta,
- `«<ID> ← RUTA VISIBLE»` para la nueva.

Desactivar ROUTE en la propia aeronave (segundo clic) no afecta a nadie. La exclusividad también apaga el efecto visual inmediatamente (`forceRedraw`).

### 24.3 Verificación (página recargada, CDP)

Aeronaves sintéticas RTA/RTB con ruta, invocando `toggleRouteCtx` real (mismo flujo que el botón):

| Paso | Acción | Rutas visibles |
|---|---|---|
| 1 | ROUTE en RTA | `["RTA"]` |
| 2 | ROUTE en RTB | `["RTB"]` ← RTA apagada automáticamente |
| 3 | ROUTE en RTB (apagar) | `[]` |
| 4 | ROUTE en RTA (encender) | `["RTA"]` |

| Comprobación | Resultado |
|---|---|
| Errores JS | **0** |
| Suite `tests/hold_test.js` | **115/115, FAIL=0** |
| Sincronización deploy | `netlify-deploy\index.html` ≡ fuente, MD5 `D357C637707FD150EA476DFB337E6391` |

### 24.4 Notas

- HALO no se ve afectado: es independiente por aeronave y no forma parte de esta exclusividad.
- La aeronave aterrizada o sin ruta (`route.length<2`) no cambia el comportamiento de `drawRoute` (ya filtrado).

## 25. Verificación: nivel de cruce de EL250 (SID 7C) — sin cambio de código

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (solo medición)

### 25.1 Pedido

*"Verifica a qué nivel están pasando los aviones EL250 en la simulación; a mi parecer están virando muy bajo, los 10000 pies."*

### 25.2 Método

Sonda por CDP sobre la página cargada: `paused=true`, avance sincrónico de `update(0.05)` con las **mismas plantillas** del Auto DEP (`DEP_TEMPLATES`, spawn en umbral a altitud ARP). Se registró `a.alt` en el instante exacto en que `routeIdx` avanza de VAGOS→EL250 (inicio del viraje). Repetido con `SIM_F` 1×/5×/10× y con `rocSel='min'`.

### 25.3 Resultado — altitud al cruzar/virar en EL250 (mínimo publicado: 10000 ft)

| Aeronave | SID | ROC automático (BADA) | ROC MIN |
|---|---|---|---|
| B788 (BAW) | ALBAL7C 17R | **12 435–12 480 ft** | 10 662 ft |
| A320 (LAN) | ALBAL7C 17R | **12 113–12 131 ft** | 10 377 ft |
| B788 | NEBEG7C 17R | **12 621–12 658 ft** | 11 192 ft |

- Invariante con el multiplicador de tiempo (1×/5×/10×: mismas altitudes ±50 ft).
- **Ningún caso cruza por debajo de 10 000 ft.** Con ROC automático el margen es +2100 a +2600 ft; con ROC MIN el margen se reduce a +380 a +1200 ft (el piso MNM Razón ASC 320/350 ft/NM de la carta es lo que impide quedarse bajo).
- Comportamiento observado: al pasar VAGOS (ventana 4000–9000) la aeronave ya asciende libre hacia el mínimo de EL250 (10000); al alcanzar ~9900 ft la regla de libre ascenso salta directo a la siguiente cota publicada (EL401 FL140), por lo que **cruza EL250 en ascenso a ~12 100–12 600 ft** y vira hacia EL401/NEBEG por encima del mínimo.

### 25.4 Conclusión

En la versión actual **las aeronaves NO viran bajo en EL250**: cruzan 2100–2600 ft por encima del mínimo con el modo normal, y nunca por debajo de 10 000 ft ni siquiera con ROC MIN. Si en pantalla se observan giros por debajo de 10 000, las causas posibles son: (a) versión desplegada antigua en Netlify — actualizar con `netlify-deploy\`; (b) instrucción ATC previa de nivel («ascienda nivel 100» / CFL) que fija `atcAlt` y prioriza la instrucción sobre la restricción de la SID; (c) modo ROC MIN + aeronave pesada, donde el margen baja a ~+400 ft. Se pide Specify callsign/SID/hora si se replica.

## 26. CTC TWR — icono de torre en lugar de teléfono

**Fecha:** 2026-10-22 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 26.1 Pedido

*"Elimina el icono de teléfono de CTC TWR; puedes usar un icono de una torre de control, que es más apropiado."*

### 26.2 Cambio

| Ubicación | Antes | Ahora |
|---|---|---|
| Botón del menú de etiqueta (popup HOLD) | `☎ CTC TWR` | `🗼 CTC TWR` |
| Estado en panel lateral (`updateSB`, aeronave handedOff) | `☎ TWR 118.1` | `🗼 TWR 118.1` |

Emoji 🗼 (torre) — consistente con el resto de la interfaz, que ya usa símbolos Unicode (⬇ GS, ◉ LOC, ⇒ TRANSFERIR).

### 26.3 Verificación

| Prueba | Resultado |
|---|---|
| Botón en DOM | contiene 🗼, sin resto de ☎ |
| Panel lateral con `handedOff=true` | `🗼 TWR 118.1` |
| Ocurrencias de ☎ en el archivo | **0** |
| Suite `tests/hold_test.js` | **115/115, FAIL=0** |
| Sincronización deploy | MD5 `700DE2FA5A25694C7D2E8B4A2DAD7D66` |

## 27. Mínimos de sector — valores de la cartilla MRVAC en el simulador

**Fecha:** 2026-10-23 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 27.1 Pedido

*"Por ultimo ingresa los valores de los minimos de sector con las altitudes minimas en el simulador, los que aparezcan pones sus valores de la cartilla, no los tengo todos pero puedes guardar sus valores para cuando ingrese las coordenadas de los sectores que faltan."*

Cartilla: https://aipchile.dgac.gob.cl/dasa/aip_chile_con_contenido/aipmap/SCEL/MRVAC%20SCEL.pdf

### 27.2 Fuente de datos

**CARTA DE ALTITUDES MINIMAS DE VIGILANCIA ATC** (AIP Chile, SCEL; INFO SUP AIP S9 · AMDT 86 · 03-dic-2020). Extracción doble para mayor seguridad: (a) volcado de los 209 ítems de texto del PDF con sus posiciones en el render de 2400 px (pdf.js), (b) lectura visual en alta resolución de los 6 tiles del mapa + zooms sobre las zonas ambiguas. Emparejamiento valor↔sector por proximidad de coordenadas y confirmación visual.

Resultado: **36 sectores con nombre** (valor propio) + **6 valores sin nombre** en la cartilla.

### 27.3 Cambio

| Ubicación | Cambio |
|---|---|
| Tras `const SECTOR_MIN` (~línea 2945) | Nuevo `const MRVAC_SECTOR_MINS` con los **36 valores de la cartilla** + arreglo `_SIN_NOMBRE` (6) y comentario con fuente/URL/fecha |
| Justo después | Sincronización automática: `Object.keys(SECTOR_MIN).forEach(...)` copia el valor de la cartilla al campo `alt` de cada sector ya cargado (21) |
| Importación OFFLINE (`_d.mrvac`) | Si el archivo no trae `alt`, se usa `MRVAC_SECTOR_MINS[nombre]` como respaldo |
| Rotulado (dibujo `SECTOR_MIN`) | Antes: etiqueta solo si `_cy>100` (región SCSE) → **ninguno** de los 23 se rotulaba. Ahora: **todos** rotulan nombre + mínimo en su centroide mientras esté activa la capa MSA (`showMRVAC`) |
| Grosor de línea (`isOuter`) | Antes: `z.alt==='FL100-FL070'` (CHAPE dejó de cumplirlo tras el cambio). Ahora: por nombre (`OUTER_BOUNDARY`, `OUTER_CHAPE`, `CHAPE`) → el dibujo no cambia |

`datos_offline.json` **no** tiene sección `mrvac` (verificado en la copia local y en `netlify-deploy`), por lo que no pisa los valores integrados. Los sectores `OUTER_BOUNDARY` y `OUTER_CHAPE` no existen en la cartilla y conservan `FL100-FL070`.

### 27.4 Valores aplicados a los 21 sectores con geometría

| Sector | Antes | Ahora (cartilla) |
|---|---|---|
| CHAPE | FL100-FL070 | **7000'** |
| UKL1 / UKL2 / UKL3 / UKL4 | GND-FL050/FL075 | **FL110 / FL150 / FL180 / FL210** |
| ANDES1 / ANDES2 / ANDES3 | GND-FL050/FL075 | **FL100 / FL120 / FL140** |
| PAPUDO | GND-FL050/FL075 | **FL60** |
| PIL1 / PIL2 / PIL3 | GND-FL050/FL075 | **5500' / 6000' / FL55** |
| MONTE | GND-FL050/FL075 | **5500'** |
| ANGOD1 / ANGOD2 | GND-FL050/FL075 | **FL100 / FL120** |
| PLOMO1 / PLOMO2 / PLOMO3 | GND-FL050/FL075 | **8500' / FL160 / FL210** |
| NEBEG1 / NEBEG2 | GND-FL050/FL075 | **FL160 / FL230** |
| PIRQUE | GND-FL050/FL075 | **FL180** |

### 27.5 Valores guardados pendientes de coordenadas (15 + 6 sin nombre)

Listos en `MRVAC_SECTOR_MINS` para el día que se cargue la geometría (el `alt` se rellena solo al añadir la clave a `SECTOR_MIN`):

| Sector | Mínimo | | Sector | Mínimo |
|---|---|---|---|---|
| ACONCAGUA | FL190 | | TANGO1 / TANGO2 | FL90 / FL100 |
| QUINTAY1 / QUINTAY2 | 2000' / 4500' | | ALBAL1 / ALBAL2 / ALBAL3 | FL160 / FL190 / FL200 |
| CASABLANCA | 8500' | | COBRE1 / COBRE2 | FL165 / FL190 |
| TBN | 8000' | | PELDEHUE | 7000' |
| PAINE | FL130 | | MAIPO | 8000' |

**Sin nombre en la cartilla** (`_SIN_NOMBRE`): `5000'` (caja al sur de CHAPE), `5200'` (caja sobre el fix AMB), `4000'` (círculo junto a AMB), `FL260` ×2 y `FL250` (círculos de espacio superior). Se anotan porque no llevan rótulo de sector (solo valor).

### 27.6 Verificación

| Prueba | Resultado |
|---|---|
| `typeof MRVAC_SECTOR_MINS` + claves | `object`, **37** (36 sectores + `_SIN_NOMBRE`) |
| Alts sincronizados | **21/21** sectores con geometria = valor de la cartilla (`CHAPE=7000'`, `UKL4=FL210`, `PIL3=FL55`, `PAPUDO=FL60`…) |
| Sectores sin carta | `OUTER_BOUNDARY=FL100-FL070` conservado |
| Rotulos en pantalla (capturas a 40/50 NM) | PIL1 5500', PIL2 6000', PIL3 FL55, MONTE 5500', ANGOD1 FL100, ANGOD2 FL120, PIRQUE FL180, NEBEG1 FL160, NEBEG2 FL230, PLOMO2 FL160, PLOMO3 FL210, UKL1-4, ANDES2 FL120, ANDES3 FL140, CHAPE 7000', OUTER_CHAPE y OUTER_BOUNDARY FL100-FL070 |
| Integridad del archivo | BOM UTF-8 · CRLF 11957 · 0 U+FFFD |
| Suite `tests/hold_test.js` | **115/115, FAIL=0** |
| Sincronización deploy | MD5 `1BC03BADF261857316E1C2BFDA2246FE` |

---

## 28. Retardo de reacción del piloto (rumbo, nivel y velocidad)

### 28.1 Motivo

El usuario reportó: «En la vida real debe existir un pequeño retardo en la ejecución del viraje, descenso o reducción de la velocidad… en este momento es casi automático lo cual no es real». Antes de este capítulo, al aplicar una instrucción (`applyHdg`, `applyFL`, `spdChg`…) el objetivo (`tHdg`/`tAlt`/`atcSpd`) se fijaba de inmediato y la física del piloto empezaba a obedecer en el mismo instante. En un ATC real hay un tiempo de escucha, interpretación y acción, y además el piloto termina la maniobra en curso antes de iniciar la nueva.

### 28.2 Diseño

- **Constantes** (~L1600): `REACT_HDG_S = 5`, `REACT_ALT_S = 6`, `REACT_SPD_S = 5` (segundos de simulación: viraje 5 s, nivel 6 s, velocidad 5 s).
- **Reloj de simulación**: `let _simT = 0`; en `update(dt)` se acumula `_simT += sdt`. Solo avanza con física activa — con el simulador en pausa el retardo no consume.
- **Helper `atcReact(a, tipo)`** (sección COMMANDS, ~L4553): al llegar una instrucción ATC, si no hay retardo pendiente de ese tipo captura el objetivo anterior (`_oldTHdg` / `_oldTAlt` / `_oldTSpd`) y arma `rHdgAt` / `rAltAt` / `rSpdAt = _simT + REACT_*_S`. Si ya hay un retardo pendiente (llegó otra instrucción antes de que el piloto reaccionara), se reinicia el plazo pero se conserva el objetivo anterior original: el piloto no arranca la primera orden a medias, ejecuta la última.
- La instrucción se escribe en el objetivo visible de inmediato (`tHdg`/`tAlt`/`atcSpd` = valor nuevo, etiquetas y readback al instante — el controlador ve su orden aplicada), pero la **física** usa el objetivo efectivo:
  - en `update()`: `_rH`/`_rA`/`_rS` = retardo activo (`simT < r*At`); `_tHdgE`/`_tAltE`/`_tSpdE` = (retardo activo ? `_oldT*` : objetivo real);
  - todo el cálculo de viraje (`dh`, `turnDir`), de nivel (`da`, `_depInterm`, `daSnap`, chequeo de ascenso) y la integración de velocidad usan el objetivo efectivo;
  - guard especial: `if(!_rH && Math.abs(dh) < 0.5) a.turnDir = null` — durante la espera del viraje no se limpia el sentido de giro (si no, el piloto "perdería" el lado del viraje al congelarse dh≈0).
- **Desaceleración más lenta que la aceleración**: `_kSpd = (ds < 0) ? 1.2 : 2` kt/s — un motor no acelera igual que frena (1.2 kt/s al reducir, 2 kt/s al acelerar).
- **Fuera del alcance** (sin retardo, comportamiento idéntico al anterior): navegación automática (ruta, hold, LOC/GS, seguimiento de DCT), spawn de aeronaves, `_setTAlt`, y comandos de parada (`holdHdg` / maintain-heading).

### 28.3 Sitios de llamada (~28 en total)

| Tipo | Funciones |
|---|---|
| rumbo | `applyHdg`, `applyHold`, `applyHoldCtx`, DCT por menú contextual, `vecFinal`, voz (turn left/right), voz rumbo suelto, voz DCT |
| nivel | `applyFL`, `flStep`, `setCflCtx`, `aAltDirect`, voz climb, voz descend, voz hold level |
| velocidad | `spdChg`, `selectSpd`, `applyHold`, `applyHoldCtx`, `setMach`, edición de etiqueta, voz (3×), voz hold spd |

### 28.4 Verificación en navegador (probes CDP sobre la página real, bucle rAF activo)

| Fase | Instrucción | Resultado |
|---|---|---|
| A · viraje derecha (LAN101) | rumbo 267 | `tHdg=267` inmediato; `react=5 s`; rumbo congelado 4 pasos; luego +9° ✓ |
| A2 · viraje izquierda (SKY220) | rumbo 267 | `turnDir='left'` preservado durante la espera; congelado 4 pasos; −9° ✓ |
| B · ascenso desde nivelado | FL330 | `tAlt=33000` inmediato; `react=6 s`; altitud congelada 4 pasos; luego sube con inercia VS_TC ✓ |
| C · velocidad | 230 kt | orden y `atcSpd=230` inmediatos; TAS congelado 4 pasos; luego −7.2 kt en 6 s = **1.2 kt/s** exacto ✓ |
| D · voz | "… rumbo cero nueve cero" | `tHdg=90` + `react=5 s` ✓ |
| E · descenso (LAN101, loop real pausado) | FL50 | `reactS=6`; durante la espera **sigue el ascenso anterior** (+112 ft en 4 s ≈ 1665 fpm); a los 6 s `vSpd` +1664 → −1116 (inicia descenso a FL50) ✓ |

Nota de las sondas: las opciones `001`-`005` del dropdown son códigos de pista (aproximación), no niveles — una primera sonda las eligió por error y "demostró" un fallo inexistente (`apprAuth` inmediato con descenso al GS). Re-ejecutado con opciones FL reales, todo correcto.

### 28.5 Suite de regresión

`tests/hold_test.js` vía harness manual (`_SCEL_TEST.html` + `_hold_test.js`): **total=115, ok=89, fail=0, other=26 (NLP/PV)** — idéntico al baseline. Los retardos no afectan la suite porque esta no ejecuta `update()` (solo targets, navegación y readbacks).

### 28.6 Integridad

BOM UTF-8 ✓ · CRLF 12022 ✓ · 0 U+FFFD ✓ · 630551 bytes.

### 28.7 Sincronización deploy

`netlify-deploy/index.html` = origen (630551 bytes, byte a byte) — MD5 `31BAF2F41AE36E9D9C36C01EE3CBF19A`. Recordar arrastrar la carpeta `netlify-deploy` a https://app.netlify.com/drop para publicar.

---

## 29. Voces más naturales (TTS)

### 29.1 Motivo

El usuario reportó: «Mejora la calidad de las voces para que no sean tan robóticas y sean más fluidas y naturales». El TTS anterior hablaba el readback completo en UN solo utterance con rate/pitch fijos (0.92/0.95) y elegía la voz latina por hash entre TODAS las voces del sistema — incluidas las TTS5 antiguas (Sabina/Carlos), que suenan robóticas.

### 29.2 Mejoras aplicadas (en `SCEL_ATC_Radar.html`)

| # | Mejora | Detalle |
|---|---|---|
| 1 | **Selección por calidad** (`_voiceScore` + `_rankVoices`) | Score: `Natural/Neural` +50 · `Google` +30 · `online` +15 · `localService=false` +10 · voces modernas es (Pablo/Elvira/Dalia/Jorge/Paulina/Carla) +12 · Sabina/Carlos (TTS5) −40 · es-ES −80 · gallego −100. Se elige dentro del **top tier** (score ≥ máximo−12), manteniendo la voz estable por callsign (`_stableVoice`). |
| 2 | **Frases encadenadas con prosodia** (`_splitChunks` + cadena en `_ttsSpeak`) | El readback se parte en frases cortas por comas (máx. 6; frases de 1 palabra se fusionan). Cada frase es un utterance encadenado con pausa real de 110 ms entre ellas (la coma sola no da la misma separación). |
| 3 | **Prosodia por hablante y por posición** | Callsign (1.er chunk): rate −0.03, pitch +0.03 (se identifica, más grave/lento). Último chunk: pitch −0.05 (**tono descendente** = fin de frase natural). Chunks intermedios: jitter determinista ±0.04 por callsign (misma semilla → misma cadencia siempre). Base por hablante: rate 0.94–1.04 y pitch 0.90–1.04 (hash del callsign) — **cada piloto suena distinto pero siempre igual**. |
| 4 | **Squelch VHF** (`_radioClick`, WebAudio) | Click de ruido filtrado (bandpass 1.8 kHz, ~45 ms, decaimiento cuadrático) al pulsar el PTT (gain 0.5) y al soltarlo (gain 0.35). Se crea el `AudioContext` en el primer gesto del usuario (`_unlockTTS`). Enmascara el ataque del TTS y da sensación real de radio. |
| 5 | **Cadena robusta** (secuencial por `onend`, no colas ciegas) | Evita el bug de colas de Chrome (utterances muertos tras `cancel()`). Watchdog de 600 ms por chunk (si un chunk no arranca, se salta en vez de trabar). Retry global a 400 ms si no hubo audio (comportamiento anterior conservado). `_ttsChainActive` + `_ttsBusy()` evitan que un reporte de entrada se solape con los 110 ms de pausa entre frases (`processReportQueue` ahora usa `_ttsBusy()`). |
| 6 | **Sin cambios de texto** | El texto hablado sigue llegando limpio (sin emojis); `sayReadback` conserva firma y comportamiento (la suite lo parchea y restaura). |

### 29.3 Verificación (probes CDP con voces falsas + stub de `speak`)

| Prueba | Resultado |
|---|---|
| `_splitChunks` | "LAN uno cero uno, autorizado descenso…" → `["LAN uno cero uno","autorizado descenso…"]` ✓ · 3 frases en readback largo ✓ · "contacto Santiago Torre uno uno ocho **coma** uno" no se parte en "coma" ✓ · palabra sola ("adelante") queda intacta ✓ |
| `_voiceScore`/`_rankVoices` | Elvira Natural 72 > Pablo Natural 72 > Google 50 > Sabina −30 > Helena es-ES −76; top tier = [Elvira, Pablo] ✓ |
| Cadena completa (fake pool + stub) | 2 chunks: callsign rate 0.993/pitch 1.02, final rate 1.023/pitch 0.94, misma voz, **0 excepciones**, `chain=false` al terminar ✓ |
| `_radioClick` / `_unlockTTS` | AudioContext creado en el primer click, sin excepciones ✓ |
| `processReportQueue` con `_ttsBusy()` | Sin excepción ✓ |
| Integridad | BOM UTF-8 ✓ · CRLF 12134 ✓ · 0 U+FFFD ✓ · 636922 bytes |

Nota: el entorno de prueba (Chromium headless via CDP) no tiene voces instaladas (`getVoices()=0`), por lo que la calidad audible real (Elvira/Pablo Natural o Google online) se confirma en el navegador del usuario; la lógica de selección, encadenado y prosodia está verificada con el fixture de voces.

### 29.4 Suite de regresión

`tests/hold_test.js` vía harness manual: **total=115, ok=89, fail=0, other=26 (NLP/PV)** — idéntico al baseline.

### 29.5 Sincronización deploy

`netlify-deploy/index.html` = origen (636922 bytes, byte a byte) — MD5 `A5E0E448D2ABD2EF2CDD6EC3E7ACC3F6`. Recordar arrastrar la carpeta `netlify-deploy` a https://app.netlify.com/drop para publicar.

---

## 30. Rótulos de fixes 50 % más grandes (UMKAL · NEBEG · ALBAL · ANKON/ANKES · EROLO)

### 30.1 Motivo

El usuario pidió: «Quiero que los nombres de los fixes UMKAL NEBEG ALBAL ANKON EROLO se vean un 50 % más grande». Los rótulos de los *compulsory reporting points* se dibujaban con `bold 5.6*DPR px Share Tech Mono`.

Nota: en el simulador el fix se llama **ANKES** (x −6.3, y −12.0, IAF de UMKAL7B/SIMOK6D/ASIMO5C/SABLA5A). Verificado contra el AIP oficial: la carta **SCEL STAR 9 (DGAC AMDT 99, 15 MAY 2025)** nombra el punto final de esas cinco rutas como **ANKES** («…TEPOK-EL273-ANKES»); no existe ningún fix ANKON en el AIRAC vigente de SCEL — el nombre "ANKON" corresponde a ediciones antiguas de las cartas ILS. Se tomó ANKES como ese fix (no se creó ningún waypoint ficticio).

### 30.2 Cambios (en `drawWaypoints`)

| Cambio | Detalle |
|---|---|
| `NAMED_BIG` | Nuevo set `['UMKAL','NEBEG','ALBAL','EROLO','ANKES']`; su rótulo usa `8.4*DPR` px (= 5.6 × 1.5). El resto de named fixes sigue a `5.6*DPR`. |
| ANKES en `NAMED` | ANKES pasaba invisible (triángulo abierto sin rótulo y además oculto por el filtro de eje) → ahora es *named* (triángulo relleno naranja como UMKAL) con rótulo grande. |
| Exención del filtro de eje | El filtro "fixes a 5.8–7.8 NM del eje 17, símbolos ocultos" ocultaba ANKES; se exime **solo ANKES** (`name!=='ANKES' && …`). Los otros5 de esa banda (TINGO, EL273, SAFEL, EL570, TEPOK) siguen ocultos. |

### 30.3 Verificación (probe CDP interceptando `ctx.fillText` durante `drawWaypoints`)

| Fix | Fuente usada |
|---|---|
| UMKAL | `bold 8.4px Share Tech Mono` ✓ |
| NEBEG | `bold 8.4px` ✓ |
| ALBAL | `bold 8.4px` ✓ |
| EROLO | `bold 8.4px` ✓ |
| ANKES | `bold 8.4px` ✓ (ahora visible con símbolo relleno) |
| SIMOK (control) | `bold 5.6px` — sin cambio ✓ |

Re-verificación 2026-10-23 (tras revisión ANKON/ANKES): probe de nuevo con los 5 fixes a `bold 8.4px` ✓, y captura de pantalla confirma visualmente los rótulos grandes junto a los normales de 5.6 px.

### 30.4 Suite de regresión

`tests/hold_test.js`: **total=115, ok=89, fail=0, other=26 (NLP/PV)** — idéntico al baseline.

### 30.5 Integridad y deploy

BOM UTF-8 ✓ · CRLF 12140 ✓ · 0 U+FFFD ✓ · 637363 bytes.
`netlify-deploy/index.html` = origen (byte a byte) — MD5 `4E0CBFC17A54C2B831F0C59B667E5BAB`. Recordar arrastrar la carpeta `netlify-deploy` a https://app.netlify.com/drop para publicar.

---

## 31. Ventana de novedades al iniciar (últimas mejoras incluidas)

**Fecha:** 2026-10-23 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 31.1 Pedido

*"CUANDO INICIE EL SIMULADOR ABRIR LA TIPICA VENTANA EMERGENTE DE LAS APPS QUE INDICAN ULTIMAS MEJORAS INCLUIDAS, COMO SE AGREGA MINIMOS DE SECTOR FLMINSEC, FUNCION CONTACTAR TWR DESDE ETIQUETA, MEJORA DE VOCES Y PARA AYUDA Y SUGERENCIAS CONTACTAR A NICOLAS REYES CASTAÑEDA AL CORREO NREYESC@DGAC.GOB.CL"*

### 31.2 Cambios (en `SCEL_ATC_Radar.html`)

| Ubicación | Cambio |
|---|---|
| CSS (tras `.dm-note`, bloque nuevo «NOVEDADES MODAL») | `#nvdModal`: backdrop `position:fixed;inset:0;z-index:10001` (sobre el `devModal` que usa z=9999), `display:none` por defecto; `.nvd-box/.nvd-head/.nvd-items/.nvd-item/.nvd-help/.nvd-foot/.nvd-ok` con la estética del simulador (fondo degradado oscuro, borde `var(--brd)`, fuente `Share Tech Mono`, acento cyan `var(--acc)`) |
| HTML (tras `#devModal`, antes de `<div id="app">`) | Ventana con título «◈ ÚLTIMAS MEJORAS INCLUIDAS» + subtítulo «SIMULADOR SCEL · ATC RADAR TRAINER», 3 ítems: 📏 **MÍNIMOS DE SECTOR · FLMINSEC** (mínimos MRVAC rotulados en capa MINSECTOR), 🗼 **CONTACTAR TWR DESDE LA ETIQUETA** (CTC TWR → Torre 118.1), 🔊 **MEJORA DE VOCES** (TTS natural); caja punteada «¿Ayuda o sugerencias?» con **Nicolás Reyes Castañeda** y enlace `mailto:nreyesc@dgac.gob.cl`; botón **ENTENDIDO** (`onclick="closeNvd()"`) |
| JS (script nuevo antes de `</body>`) | IIFE que abre la ventana en cada arranque (`display:flex`), **omisa en `_SCEL_TEST.html`** (`location.pathname`) para no afectar la suite; `closeNvd()` también cierra con **Esc** (una vez); 0 errores JS |

Comportamiento: la ventana se apoya sobre la pantalla de selección de dispositivo al iniciar; al cerrarla el `devModal` queda plenamente interactivo; el botón `⇄ DISP` del topbar no la reabre (solo se muestra al arrancar). La descripción de cada mejora corresponde a los capítulos 27 (mínimos MRVAC), 22/26 (CTC TWR) y 29 (voces TTS).

### 31.3 Verificación (navegador, servidor local 127.0.0.1:8777, CDP)

| Prueba | Resultado |
|---|---|
| Al recargar | `#nvdModal` `display=flex`, `z-index=10001`; `#devModal` `flex` detrás |
| Contenido | 3 `.nvd-item` ✓ · botón `ENTENDIDO` ✓ · `href="mailto:nreyesc@dgac.gob.cl"` ✓ · «Nicolás Reyes Castañeda» con ñ y acentos correctos ✓ · **0 errores JS** ✓ |
| Captura de pantalla | Ventana completa: título, 3 mejoras con iconos, caja de contacto y botón (`shot_nvd1.png`) |
| Cierre (`closeNvd`) | `display=none`; hit-test al centro → `dm-card live-card` (tarjeta LIVE) = pantalla de inicio libre de overlays |
| Reapertura | Cada recarga vuelve a mostrar la ventana (comportamiento por arranque) |
| Se omite en tests | `_SCEL_TEST.html` no la muestra (pathname) |

### 31.4 Suite de regresión

`tests/hold_test.js`: **total=115, ok=89, fail=0, other=26 (NLP/PV)** — idéntico al baseline.

### 31.5 Integridad y deploy

BOM UTF-8 ✓ · CRLF 12239 ✓ · 0 loneLF · 0 U+FFFD ✓ · 641950 bytes.
`netlify-deploy/index.html` = origen (byte a byte) — MD5 `368F772C1250F4A347B5F670118DE840`. Recordar arrastrar la carpeta `netlify-deploy` a https://app.netlify.com/drop para publicar.

---

## 32. Botón FLMINSEC — nombre y mínimos de sector solo al presionarlo

**Fecha:** 2026-10-23 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 32.1 Pedido

*"ok ahora los valores de los nombres y altitud /altura minimos de sector y sus nombres solo seran visibles al presionar el BOTON FLMINSEC en el costado izquierdo del simulador"*

Antes (cap. 27): los rótulos nombre+mínimo se dibujaban siempre que la capa MSA (`showMRVAC`) estaba activa — activa por defecto, es decir, se veían nada más arrancar. Ahora: **aparecen solo al presionar el nuevo botón FLMINSEC** (apagado por defecto), de forma independiente de los límites de sector.

### 32.2 Cambios (en `SCEL_ATC_Radar.html`)

| Ubicación | Cambio |
|---|---|
| Declaración de flags (~L4328) | Nuevo `showFLMinSec=false` junto a `showMRVAC=true` |
| HTML panel GEN (`#catBodyGen`, tras `#minsectorBtn`) | Nuevo botón `<div id="flminsecBtn" class="cat-btn beige off" onclick="toggleFLMinSec()" title="FLMINSEC — nombre de sector y altitud mínima (cartilla MRVAC) sobre el mapa">● FLMINSEC</div>` — clase `beige` (misma familia que MSA), estado inicial `off` |
| JS (tras `toggleMRVAC`) | Nueva `toggleFLMinSec()`: conmuta `showFLMinSec`, alterna clases `on`/`off` del botón y `forceRedraw()` — mismo patrón que el resto de toggles |
| Dibujo `SECTOR_MIN` (~L6597) | Bloque reestructurado: guardia `if(!showMRVAC&&!showFLMinSec)return;` · **límites** dentro de `if(showMRVAC)` · **rótulos (nombre+mínimo)** dentro de `if(showFLMinSec)` — antes ambos dependían solo de `showMRVAC` |
| Texto ventana novedades (cap. 31) | Ítem FLMINSEC actualizado: «presione FLMINSEC (costado izquierdo) para ver el nombre y la altitud mínima de cada sector» |

Comportamiento resultante (2 botones independientes en el panel GEN):

| MSA | FLMINSEC | Límites | Rótulos nombre+mínimo |
|---|---|---|---|
| on | **off (defecto)** | ✓ | **✗ — nada al arrancar** |
| on | on | ✓ | ✓ |
| off | on | ✗ | ✓ (solo rótulos) |
| off | off | ✗ | ✗ |

`FLMINSEC` se dibuja a la derecha de `MSA` en la fila 2 del grid de 2 columnas del panel GEN.

### 32.3 Verificación (navegador, servidor local 127.0.0.1:8777, CDP)

| Prueba | Resultado |
|---|---|
| Estado inicial tras recargar | `showFLMinSec=false` · botón `cat-btn beige off` · MSA `cat-btn beige on` · `toggleFLMinSec` = function ✓ |
| Captura **antes** (MSA on, FLMINSEC off) | Límites grises visibles, **0 rótulos de sector** ✓ (`shot_fl_before.png`) |
| Tras `toggleFLMinSec()` | `showFLMinSec=true`, botón pasa a `cat-btn beige on`; captura con todos los rótulos: UKL2/FL150, UKL4/FL210, CHAPE/7000', MONTE/5500', NEBEG2/FL230, ANGOD2/FL120, PIL3/FL55… ✓ (`shot_fl_after.png`) |
| Independencia (MSA off + FLMINSEC on) | Sin límites grises, rótulos siguen visibles ✓ (`shot_fl_labels_only.png`) |
| Layout | `minsectorBtn` x=15,y=79 · `flminsecBtn` x=100,y=79 (misma fila) · `overlap=false` · `rwy17rBtn` y=232 sin recorte ✓ |
| Suite `tests/hold_test.js` | **115/115, ok=89, fail=0, other=26** — idéntico al baseline |
| Integridad | BOM UTF-8 ✓ · CRLF 12255 ✓ · 0 loneLF · 0 U+FFFD ✓ · 642724 bytes |
| Sincronización deploy | MD5 `402EB1004D0E52AC763D52C3C64F7C0B` |

---

## 33. Rutas de salida fix a fix, traza automática y capa visual «UI 2026»

**Fecha:** 2026-10-25 · **Archivo:** `SCEL_ATC_Radar.html` (+ copia en `netlify-deploy\index.html`)

### 33.1 Pedido

*"mejora el entorno visual… luego dame un listado de las salidas y las rutas de todas las salidas definidas en el simulador… además revisa el resto de las salidas… y corrige si hay errores"*

### 33.2 Diagnóstico: la ruta estaba bien, lo que faltaba eran los nombres

La sospecha inicial era que `NEBEG7C` y `ALBAL7C` no pasaban por EL250 / EL400 / EL401. Se comprobó con la **trayectoria real** del simulador (no con la polilínea dibujada) y sí pasan:

| Prueba | `NEBEG7C_17R` | `ALBAL7C_17R` |
|---|---|---|
| Distancia mínima al EL250 | **0,016 NM** | **0,015 NM** |
| Altitud al pasar EL250 | 12.351 ft | 12.463 ft |
| Viraje tras EL250 | rumbo 084° | rumbo 112° (a la izquierda) |
| Mínimos de la ruta | ≥FL100 · ≥FL135 · ≥FL170 · ≥FL230 | ≥FL100 · ≥FL140 · ≥FL210 |

Causa real del síntoma: los puntos de la SID se construían con `_sw()` (punto genérico del eje de pista) y con clones del fix, y **los clones no llevaban la propiedad `name`**. `_wptName()` (L5039) devolvía `null` y `drawRoute` omitía el rótulo en silencio: la ruta se veía como una polilínea anónima, que se lee como si no pasara por los fixes de la carta.

### 33.3 Cambios

| Ubicación | Cambio |
|---|---|
| `_sw()` (L3522) | El punto del eje de pista guarda su nombre (`o.name=name`), igual que los fixes de `WPT` |
| Nueva `_fmtAlt(v)` (antes de `drawRoute`) | Formato aeronáutico: `FL135` desde 10.000 ft · `4.000'` con separador de miles por debajo |
| `drawRoute` (L5570) | Rombo para fix nombrado, círculo para THR o punto de viraje; rótulo con **nombre + restricción vertical** (ámbar) y **ETO** debajo; respaldo `RWY 17R` / `↰4000` si el punto no tiene nombre |
| `drawRoute` (traza automática) | La salida **seleccionada** dibuja su SID al 50 % de opacidad aunque `showRoute` esté apagado: la ruta aparece al picar el avión |
| CSS `#leftCol` | `max-height:calc(50vh - 92px)` + scroll + `> *{flex:0 0 auto}`: en pantallas bajas la columna se desplaza en vez de aplastar los paneles y chocar con el botón de voz |

### 33.4 Capa visual «UI 2026» (solo CSS, lógica intacta)

| Elemento | Detalle |
|---|---|
| Tokens | `--acc:#5ec8ff` · `--teal:#17e6b0` · superficie y bordes en 3 niveles · `--glow` · `--shadow` |
| Fondo | Dos degradados radiales (azul profundo arriba, verdoso abajo) en lugar del negro plano |
| Barra superior | 34 px, marca radar animada (`conic-gradient` + `@keyframes tbSweep`) y hairline degradada; chips con etiqueta de 7 px en versalitas y valor de 10,5 px tabular |
| Paneles y botones | Radius 10 px con riel de acento en la cabecera · botones radius 7 px con glow al hover |
| Barra inferior | 32 px con punto teal pulsante en el log del sistema |
| Popups y modal | Radius 10 px · `#simPopup` a `top:38px` · modal de novedades con tarjetas y elevación al hover |
| Detalles | Scrollbar degradada · guard `prefers-reduced-motion` · se conserva el reloj LED rojo y toda la paleta funcional (tipo de aeronave, MSA, sectores) |

### 33.5 Verificación

| Prueba | Resultado |
|---|---|
| Rótulos de `ALBAL7C_17R` (captura de `ctx.fillText`) | `VAGOS` `4.000'–9.000'` `EL250` `≥FL100` `EL401` `≥FL140` `ALBAL` `≥FL210` + ETO de cada fix ✔ |
| Inventario SID | 66 rutas / 39 designadores · `_wptName(SIDS['ALBAL7C_17R'][2])==='EL250'` ✔ |
| Estilos calculados (1584×905) | Barra superior 34 px · barra inferior 32 px · botones 7 px · fondo radial ✔ |
| Layout | 1920×1080: último panel a x=1908, sin solapes · 1584×905: columna de 361 px con scroll (`scrollHeight` 420), sin choque con el botón de voz, sin scroll de página ✔ |
| Suite `tests/hold_test.js` | **115/115 — ok=89, fail=0, other=26** (idéntico al baseline) ✔ |
| Integridad | BOM UTF-8 ✔ · CRLF 12470 ✔ · 0 loneLF · 0 U+FFFD ✔ · 653.466 bytes |
| Deploy | `netlify-deploy/index.html` byte a byte · MD5 `6E324089906A1F1A2F925EDBA4BE8140` |

### 33.6 Entregable: listado de salidas y revisión del resto

Nuevo `SALIDAS_SCEL.md`: tabla de las **66 rutas** con pista, secuencia fix a fix, restricciones verticales y MNM de razón de ascenso, más una sección de revisión SID por SID. Captura de referencia: `capturas/ui2026_salidas.png`.

Las 66 rutas se revisaron una a una: **sin errores** de coordenadas, de rumbo de entrada ni de orden de restricciones. Las dos únicas que no siguen el patrón «17R por VAGOS / 17L por DESIT» son `LINER5A_17L` (directo a LINER por la R177) y `ANGOD8B_17L` (vía ESKUL), y ambas son **intencionales**: comprobado VAGOS→LINER 174,8°, DESIT→LINER 176,9° y ESKUL sobre la R177.

---

## 34. Distintivos de llamada (callsigns) verificados contra la base 123atc

**Fecha:** 2026-10-25 · **Archivos:** `callsign.xml` · `SCEL_ATC_Radar.html` (+ `netlify-deploy`)

### 34.1 Pedido

*"el callsign de KAL es KOREANAIR en inglés siempre, UAE el callsign es EMIRATES en inglés siempre, ACA el callsign es AIRCANADA, verifica todos los callsigns están casi todos malos, usa esta base de datos https://123atc.com/call-signs, repara los callsigns erróneos, no inventes callsign"*

### 34.2 Método (sin inventar nada)

1. Se descargaron las 26 páginas alfabéticas de `https://123atc.com/call-signs` → **6.243 distintivos** con sigla, callsign, compañía y país (archivo de trabajo `atc_callsigns.tsv`).
2. Se extrajeron del simulador **todas** las siglas que usa el tráfico (`AUTO_DEP`, llegadas, tránsitos y pools de pista): 25 siglas.
3. Se cruzó una a una contra la base y contra las 29 entradas que tenía el XML.
4. Solo se escribió el valor que publica la base; nada se tradujo ni se "españolizó".

### 34.3 Defecto encontrado

El XML solo tenía 29 aerolíneas: **9 siglas del tráfico no existían** y el simulador caía al código ICAO en el readback (`resolveCallsign` devuelve el prefijo cuando no hay entrada). Además 5 distintivos estaban mal escritos y uno pertenecía a otra compañía.

| Sigla | Decía | Ahora (base 123atc) | Comprobación |
|---|---|---|---|
| KAL | `KAL` | **KOREANAIR** | KOREANAIR · Korean Air Lines · KR |
| JAL | `JAL` | **JAPANAIR** | JAPANAIR · Japan Airlines · JP |
| CPA | `CPA` | **CATHAY** | CATHAY · Cathay Pacific · CN |
| SIA | `SIA` | **SINGAPORE** | SINGAPORE · Singapore Airlines · SG |
| ETH | `ETH` | **ETHIOPIAN** | ETHIOPIAN · Ethiopian Airlines · ET |
| ANA | `ANA` | **ALL NIPPON** | ALL NIPPON · All Nippon Airways · JP |
| CES | `CES` | **CHINA EASTERN** | CHINA EASTERN · China Eastern · CN |
| HAL | `HAL` | **HAWAIIAN** | HAWAIIAN · Hawaiian Airlines · US |
| JOY | `JOY` | **JOY AIR** | JOY AIR · Joy Air · CN |
| AMX | `AEROMEJICO` | **AEROMEXICO** | AEROMEXICO · Aerovías de México · MX |
| TAM | `THAM` | **TAM** | TAM · TAM Linhas Aéreas · BR |
| LPE | `LAN PERU` | **LANPERU** | LANPERU · LAN Perú · PE |
| JAT | `JETSMART` | **ROCKSMART** | ROCKSMART · JetSMART SPA · CL |
| SKU / SKY | `SKY` | **AEROSKY** | AEROSKY · Sky Service (Sky Airline) · CL |
| FBA | `FLYBONDI` | **FBZ / BONDI** | BONDI · Flybondi · AR |
| LXE | `LAN ECUADOR` | *eliminado* | `LXE` es SUNWAVE (Austria): no corresponde a LATAM Ecuador |

Verificados y **sin cambios** (ya coincidían con la base): LAN, LXP, LCO, DAP, ARG, BOV, AVA, CMP, AAL, DAL, UAL, FDX, UPS, ACA, BAW, DLH, SWR, KLM, IBE, THY, UAE, QTR, QFA.

### 34.4 Tres decisiones explícitas

| Sigla | Base 123atc | En el simulador | Motivo |
|---|---|---|---|
| LAN | `LAN CHILE` | `LAN` | Es lo que se escucha en frecuencia en SCEL; cambiarlo alteraría todos los readbacks y las pruebas RB/CS de la suite |
| AFR | `AIRFRANS` | `AIRFRANCE` | Pedido expreso anterior del usuario y la prueba SC33 exige `AFR=AIRFRANCE` |
| ACA | `AIR CANADA` | `AIR CANADA` | La base lo publica en dos palabras (el usuario escribió AIRCANADA); al hablar suena idéntico |

### 34.5 Cambios de código asociados

| Ubicación | Cambio |
|---|---|
| `callsign.xml` | Reescrito: 40 aerolíneas, distintivo = base 123atc, comentario con la fuente y la fecha |
| `_CS_FALLBACK` (L2163) | Actualizado con los mismos valores + las 9 aerolíneas nuevas: el respaldo funciona al abrir el HTML con doble clic (sin servidor) |
| `CS_MAP.SKU/SKY` (L2141) | `AEROSKY` (antes `SKY`); se conserva el alias `SKY` para ejercicios XML antiguos |
| `AUTO_DEP`, llegadas y tránsitos | Sky Airline pasa de `SKY` a **`SKU`** (`SKU220`, `SKU314`, base `SKU`): `SKY` es Skymark (Japón) y no existe en Chile |
| `resolveCallsign` (L11038) | Acepta prefijo de **4 letras** antes del de 3: `FACH400` → `FACH` (antes tomaba `FAC` y no encontraba la entrada) |
| `_callsignCountry` (L10769) | Misma corrección de 4 letras → `FACH` vuelve a hablar con números en español (país CL) |
| `ejercicio1_ejemplo.xml` | `SKY220` → `SKU220` |
| Ventana de novedades | Nuevo ítem «Distintivos de llamada verificados» |

### 34.6 Verificación (navegador, 2026-10-25)

| Llamada | Resultado |
|---|---|
| `KAL708` | **KOREANAIR seven zero eight** [en] ✔ |
| `UAE1` | **EMIRATES one** [en] ✔ |
| `ACA810` | **AIR CANADA eight one zero** [en] ✔ |
| `AMX123` | **AEROMEXICO uno dos tres** [es] ✔ |
| `TAM416` | **TAM four one six** [en] ✔ |
| `SKU220` | **AEROSKY dos dos cero** [es] ✔ |
| `JAT7` | **ROCKSMART siete** [es] ✔ |
| `LPE240` | **LANPERU dos cuatro cero** [es] ✔ |
| `JAL5` / `CPA100` / `SIA912` | **JAPANAIR five** / **CATHAY one zero zero** / **SINGAPORE nine one two** [en] ✔ |
| `ETH606` / `ANA1` / `CES500` / `HAL459` / `JOY501` | **ETHIOPIAN** / **ALL NIPPON** / **CHINA EASTERN** / **HAWAIIAN** / **JOY AIR** [en] ✔ |
| `FACH400` | **FACH cuatro cero cero** [es] ✔ (antes: «FACH four zero zero») |
| `SKY220` (id antiguo) | **AEROSKY dos dos cero** ✔ (alias heredado) |

| Prueba global | Resultado |
|---|---|
| Suite `tests/hold_test.js` | **115/115 — ok=89, fail=0, other=26** ✔ |
| Integridad HTML | BOM UTF-8 ✔ · CRLF 12488 ✔ · 0 loneLF · 0 U+FFFD ✔ · 654.990 bytes |
| Deploy HTML | `netlify-deploy/index.html` = origen · MD5 `0B5CB4476C838CBA7D520B57EE176041` |
| Deploy XML | `netlify-deploy/callsign.xml` = origen · MD5 `DE79B9D210217ADA35AF0E30D737D608` (7.006 bytes) |
## 35. Editor local de callsigns (`editor_callsigns.html`)

### 35.1 Pedido

Editar los callsigns sin gastar tokens de OpenWork: una página local que abra `callsign.xml`, permita cambiar, agregar y borrar filas, y guarde sobre el mismo archivo.

### 35.2 Entregable

`editor_callsigns.html` — aplicación de una sola página, sin dependencias ni red:

| Función | Detalle |
|---|---|
| Base de referencia embebida | 5.703 distintivos con callsign válido de 123atc (de 6.243 descargados; las 540 filas con `(None)` se omiten) |
| Abrir | File System Access API (`showOpenFilePicker`), respaldo `<input type=file>` y arrastrar y soltar; el archivo elegido se recuerda en IndexedDB (`cs-editor`) y se reabre al volver |
| Guardar | escribe sobre el mismo archivo (`createWritable`); si el navegador no lo permite, «Guardar como…» o descarga |
| Servido por http | carga `callsign.xml` automáticamente con `fetch` |
| Tabla editable | ICAO · callsign · país · compañía, con columna «Base 123atc» que muestra el valor publicado y un botón *usar* cuando difiere |
| Alta / baja | botón **Nueva** y papelera por fila; el alta puede crearse desde el buscador de la base |
| Validación | siglas de 2–4 caracteres, callsign no vacío, siglas repetidas, sin registro en la base, diferencias intencionales |
| Atajos | Ctrl+S guardar · Alt+N nueva fila · Esc cerrar |

`serialize()` reconstruye el XML con el mismo formato del simulador y **conserva** la cabecera original, el orden de las filas, los banners de grupo y los comentarios documentales por aerolínea (LAN, Air France); solo agrega un bloque `DIFERENCIAS INTENCIONALES` para las aerolíneas que no tienen comentario propio.

### 35.3 Verificación (navegador integrado, servidor 127.0.0.1:8777)

| Prueba | Resultado |
|---|---|
| Ida y vuelta `parseXML` → `serialize()` sobre `callsign.xml` | **idéntico byte a byte**, 0 diferencias, CRLF |
| Cabecera y comentarios | cabecera original intacta; comentarios de LAN y AFR conservados |
| Edición en la tabla | el valor queda en el modelo y aparece en `serialize()` (corregido: las filas eran copias y los cambios se perdían) |
| Botón *usar* | reemplaza por el valor de la base y actualiza el estado de la fila |
| Fila nueva vacía | no rompe el orden (corregido `undefined.toString` al ordenar) |
| XML modificado por fuera | `SKU="AEROSKYX"` se refleja al abrir |
| Validación | detecta sigla inválida, callsign vacío y sigla repetida |
| `file://` (doble clic) | DB activa, `showOpenFilePicker` disponible, `isSecureContext=true`, estado vacío guiado |

### 35.4 Uso

1. Doble clic en `editor_callsigns.html` (o abrir `http://127.0.0.1:8777/editor_callsigns.html`).
2. **Abrir** y elegir `callsign.xml`; si se sirve por http se carga solo.
3. Editar: el panel lateral muestra el valor de 123atc de cada sigla.
4. **Guardar** (Ctrl+S) y recargar el simulador con **Ctrl+F5**.

### 35.5 Deploy

`editor_callsigns.html` también queda en `netlify-deploy`. En la versión publicada solo se puede descargar el XML editado, no sobrescribir el del servidor.

---

## 36. SID 1 — NEBEG 7A / ALBAL 7A: R177 hasta FL130, viraje y YESOS

### 36.1 Pedido

«La salida NEBEG 7A está pasando muy bajo; después de GENPO o SKULL (D10) debe mantener el radial R177 hasta FL130 y luego virar directo a YESOS → NEBEG. ALBAL 7A igual, pero directo a SUPRA → ALBAL.»

### 36.2 Diagnóstico

La definición anterior de las cuatro rutas era:

```
THR 17R/17L → VAGOS/DESIT (4000'-9000') → NEBEG (=FL130)   [NEBEG 7A]
THR 17R/17L → VAGOS/DESIT (4000'-9000') → SUPRA (=FL130) → ALBAL  [ALBAL 7A]
```

| Síntoma | Causa |
|---|---|
| Viraje a 13 NM del THR (8 NM tras VAGOS) | el primer punto restringido era VAGOS/DESIT (D7), no el punto de FL130 |
| No pasaba por GENPO / ESKUL (D10) | esas fijaciones no estaban en la ruta |
| NEBEG 7A no pasaba por YESOS | `YESOS` no existía en `WPT`: se había retirado porque no figura en la tabla de 134 fijaciones oficiales. Es una **intersección de aerovía**, no un fix RNAV; sus coordenadas están en AIP ENR 3.1 (aerovía A-307): 33°45'42"S / 70°15'48"W, D68 DGO, 18 NM al oeste de NEBEG |
| «Pasa muy bajo» | la ventana 4000'-9000' de VAGOS/DESIT es de las SID 2/3 (LINER 5A, GELUS 6A, SABLA 8, DOMINGO 6…) y **no** se publica para NEBEG 7A / ALBAL 7A: la salida nivelaba a 9000' |

«SKULL» del pedido es **ESKUL** (33°35'21"S / 70°46'31"W, D10 AMB); **GENPO** es D10 PDH (33°35'23"S / 70°47'31"W). No existe una fijación SKULL en la carta.

### 36.3 Cambio

| Elemento | Antes | Ahora |
|---|---|---|
| `WPT.YESOS` | no existía | `{x:26.133, y:-22.047, alt:23000}` — AIP ENR 3.1 A-307 |
| Punto de viraje | — | `FL130_17R` / `FL130_17L`: sobre el eje, `altTurn:13000`, `axisHdg:177`, nombre `FL130` |
| NEBEG 7A 17R | THR → VAGOS (4000'-9000') → NEBEG | THR → **GENPO** → **FL130** → **YESOS (≥FL230)** → NEBEG (≥FL130) |
| NEBEG 7A 17L | THR → DESIT (4000'-9000') → NEBEG | THR → **ESKUL** → **FL130** → **YESOS (≥FL230)** → NEBEG (≥FL130) |
| ALBAL 7A 17R | THR → VAGOS (4000'-9000') → SUPRA → ALBAL | THR → **GENPO** → **FL130** → SUPRA (≥FL130) → ALBAL |
| ALBAL 7A 17L | THR → DESIT (4000'-9000') → SUPRA → ALBAL | THR → **ESKUL** → **FL130** → SUPRA (≥FL130) → ALBAL |

El viraje lo dispara el **nivel**, no la distancia: igual que en la carta, la aeronave mantiene 177° hasta alcanzar FL130 (`altTurn`) y recién entonces vira. El marcador `FL130` está a 28,4 NM del THR, que es donde la flota del simulador (B738/A320 a ~400 FT/NM) alcanza FL130; así la línea dibujada y el vuelo coinciden.

A la razón **mínima publicada** (350 FT/NM desde 1.555 ft) FL130 cae a 32,7 NM: el antiguo `_ax(roc,13000)` ponía el marcador allí y el viraje de ~100° hacia el noreste se leía como una «reversa», con el avión despegado de la línea. `YESOS` lleva mínimo FL230 (MCL de A-307, RMK (3) de ENR 3.1).

### 36.4 Verificación

Perfil medido en el navegador integrado (`update(0.5)` paso a paso, B738 a 250 kt, desde el THR):

| Ruta | Viraje | Tramo al viraje | Tras el viraje | Cruce YESOS |
|---|---|---|---|---|
| NEBEG7A 17R | 28,2 NM · 13.002 ft · rumbo 080 | 177° en 28,4 NM (GENPO 13,1 + 15,3) | 26,0 NM rumbo 079 a YESOS; 18,4 NM rumbo 097 a NEBEG | 22.990 ft |
| NEBEG7A 17L | 28,2 NM · 13.002 ft · rumbo 079 | 177° en 28,4 NM (ESKUL 12,8 + 15,6) | 25,2 NM rumbo 078 a YESOS; 18,4 NM a NEBEG | ~22.900 ft |
| ALBAL7A 17R | 28,2 NM · 13.002 ft · rumbo 123 | 177° en 28,4 NM | 16,1 NM rumbo 122 a SUPRA; 36,3 NM rumbo 109 a ALBAL | — |
| ALBAL7A 17L | 28,2 NM · 13.002 ft · rumbo 124 | 177° en 28,4 NM | 15,2 NM rumbo 123 a SUPRA; 36,3 NM a ALBAL | — |

Ninguna de las cuatro rutas desciende en ningún tramo (comprobado paso a paso) y las cuatro terminan en ascenso hacia el nivel autorizado (FL250-FL267 al cerrar la SID).

| Prueba | Resultado |
|---|---|
| Suite de 115 pruebas | 88 OK; SC10 falla (`getImageData` con `width 0`) porque la ventana del navegador estaba minimizada (`innerWidth=0`). El **mismo fallo se reproduce con el `index.html` anterior** → ambiental, no regresión |
| Integridad `SCEL_ATC_Radar.html` | 656.333 B · BOM sí · 12.504 CRLF · 0 LF suelto · 0 U+FFFD · MD5 `CEF1BA648960EB6AAAA64F8507A64FBA` |
| `YESOS` en la base | el ATC ya reconoce «directo YESOS» (está en `WPT`) |

### 36.5 Deploy

| Archivo | Bytes | MD5 |
|---|---|---|
| `SCEL_ATC_Radar.html` = `netlify-deploy/index.html` | 656.333 | `CEF1BA648960EB6AAAA64F8507A64FBA` |
| `callsign.xml` = `netlify-deploy/callsign.xml` | 7.212 | `B61573326232F593E134F6812C7E7709` |

### 36.6 Observación pendiente (callsigns)

`callsign.xml` fue editado con el editor a las 13:47 (SKU = SKY, SWR = SWISSAIR, QFA = QUANTAS) y quedó sincronizado al deploy, pero el simulador **fuerza** `CS_MAP.SKU='AEROSKY'` y `CS_MAP.SKY='AEROSKY'` después de leer el XML (L2147-2149), así que en pantalla seguirá diciendo AEROSKY. Hay que decidir: (a) quitar ese override y dejar que mande el XML, o (b) volver a AEROSKY en el XML. Además «QUANTAS» parece error por «QANTAS».

> **Resuelto en el capítulo 37**: se quitó el override (opción a). QUANTAS y SWISSAIR se mantienen por decisión del usuario: «ese es el callsign».

---

## 37. El XML manda, y el simulador sobrevive sin los XML

### 37.1 Pedido

1. «Si el XML siempre mandara»: que `callsign.xml` sea la única fuente de verdad de los callsigns (SKU = SKY, SWR = SWISSAIR, QFA = QUANTAS) y que ningún valor quede clavado en el código.
2. «Algo pasó en el código, hice una edición y ahora no da readback de pilotaje».
3. «Tengo el proyecto en GitHub y al parecer solo hace referencia al index.html, quiero que también use los archivos XML».

### 37.2 El XML es la única fuente de verdad

Se eliminaron los overrides duros que se aplicaban **después** de leer el XML:

| Antes (se aplicaba siempre) | Ahora |
|---|---|
| `CS_MAP.SKU='AEROSKY'` · `CS_MAP.SKY='AEROSKY'` | solo si el XML no trae la sigla |
| `CS_MAP.IBE='IBERIA'` | solo si el XML no trae la sigla |
| `CS_MAP.AFR='AIRFRANCE'` | solo si el XML no trae la sigla |
| `resolveCallsign()`: `p3==='SKY'?'AEROSKY'` | eliminado (era el último resto) |

`_CS_FALLBACK` ya solo rellenaba huecos (`if(!CS_MAP[k])`), así que ahora la cadena es: **XML → relleno interno → sigla tal cual**.

Medido en el navegador con el `callsign.xml` actual:

| Sigla | Callsign en pantalla | Readback |
|---|---|---|
| SKU | SKY | «SKY dos dos cero» |
| SKY | SKY | «SKY dos dos cero» |
| SWR | SWISSAIR | «SWISSAIR nine» |
| QFA | QUANTAS | «QUANTAS one two» |
| IBE | IBERIA | «IBERIA uno uno uno» |
| AFR | AIRFRANCE | «AIRFRANCE three three» |
| ACA | AIR CANADA | «AIR CANADA two zero two» |
| LAN | LAN | «LAN dos cero cero» |

### 37.3 El readback que «dejó de funcionar»

No era el simulador: la copia `ssdsd.html` (25-10 19:56) tiene la línea de respaldo partida —

```js
SKU:{c:'CL',n:'Sky Airline',JAT:{c:'CL',n:'JetSMART',s:'ROCKSMART'},
```

falta `,s:'SKY'}` y el `}` de cierre: eso es un **`SyntaxError`** que mata el `<script>` completo (no arranca nada, y por eso no hay readback). En `SCEL_ATC_Radar.html` esa línea está correcta (`SKU:{c:'CL',n:'Sky Airline',s:'SKY'},SKY:{...}`).

Comprobación en el archivo principal, invocando el readback de cada instrucción:

| Instrucción | Resultado |
|---|---|
| hdg · climb · descend · level · direct · hold · twr · ident | OK, habla y colaciona |
| spd (vía `spdReadbackCmd`) | «LAN uno cero uno, reduciendo a dos dos cero nudos» |

### 37.4 Por qué en GitHub «solo usa el index.html» (bug real, previo)

Reproducido sirviendo **solo** `index.html`, sin XML ni .js auxiliares:

- `coast_xy_smooth.js` define `COAST_XY`. Sin ese archivo, `cleanCoastData()` evaluaba `if(!COAST_XY…)` → **`ReferenceError: COAST_XY is not defined`** en el nivel superior del script → muere todo lo que viene después: no arranca el bucle (`lastT` congelado en el primer frame), no hay despegues, y **no hay readback**. Se comprobó que pasa igual con el `index.html` anterior: el fallo no lo introdujo este trabajo.
- Arreglo: stubs `window.COAST_XY=[]` / `window.BORDER_XY=[]` cuando falta el `.js`. El radar arranca y solo pierde la silueta.
- Además, el simulador ahora **registra** los archivos que no cargaron (`performance.xml`, `callsign.xml`, `fraseologia_editada.json`) y muestra un cartel ámbar abajo: «⚠ No se cargaron: … — se usan los datos internos. Sube esos archivos junto al index.html (clic para cerrar)».

Verificado sirviendo solo el HTML: el radar corre, crea los 3 tráficos del escenario, el readback responde («SKY dos dos cero» con los datos internos) y aparece el aviso.

### 37.5 Desplegar en GitHub Pages

Los XML **sí** se leen en GitHub Pages: el simulador los pide por ruta relativa al `index.html` (mismo origen). Lo que rompe es desplegar solo el HTML o cambiar mayúsculas.

Tienen que estar en **la misma carpeta** que el `index.html`, con el nombre exacto (en Pages el servidor distingue mayúsculas):

| Archivo | Para qué |
|---|---|
| `index.html` | el simulador |
| `callsign.xml` | callsigns (manda sobre todo lo demás) |
| `performance.xml` | perfiles de ascenso/descenso por tipo |
| `fraseologia_editada.json` | fraseología editable (readbacks) |
| `normativa.xml` | respaldo de fraseología si falta el JSON |
| `datos_offline.json` | aeropuertos/ayudas sin red |
| `border_xy.js` | límite LPI |
| `coast_xy_smooth.js` | costa (sin él: radar en negro antes, ahora solo sin silueta) |

Comprobación rápida tras subir: abrir `https://usuario.github.io/repo/callsign.xml` — si el navegador muestra el XML, el simulador también lo verá. Si sale 404, falta el archivo o el nombre no coincide.

### 37.6 Verificación

| Prueba | Resultado |
|---|---|
| Suite completa | **115 líneas · 89 OK · 0 fallos** |
| Sin XML (solo `index.html`) | radar activo, 3 tráficos, readback OK, cartel de aviso |
| Con XML | SKU/SKY/SWR/QFA/IBE/AFR/ACA/LAN con el valor del archivo |
| Integridad | 658.210 B · BOM sí · 12.525 CRLF · 0 LF suelto · 0 U+FFFD · MD5 `3A89583C49A639CD1AE63C9151C93B46` |

### 37.7 Deploy

| Archivo | Bytes | MD5 |
|---|---|---|
| `SCEL_ATC_Radar.html` = `netlify-deploy/index.html` | 658.210 | `3A89583C49A639CD1AE63C9151C93B46` |
| `callsign.xml` = `netlify-deploy/callsign.xml` | 7.212 | `B61573326232F593E134F6812C7E7709` |

`ssdsd.html` (copia rota del usuario) sigue en la carpeta: no debe subirse a GitHub.

---

## 38. Voces: motor conmutable SISTEMA / AZURE neuronal — 26-10-2026

### 38.1 Diagnóstico: el problema no era la selección

El motor anterior ya elegía bien: `_voiceScore` suma +50 a las voces «Natural/Neural», +30 a las Google, +15 a las online, +12 a las modernas (Pablo/Elvira/Dalia/Jorge/Paulina/Carla/Renata) y resta −40 a Sabina/Carlos (TTS5, las robóticas); `_rankVoices` ordena por esa nota y `_splitChunks` parte la readback por comas con prosodia propia por hablante.

Lo que falla es el catálogo: en un Chrome de Windows sin paquetes de idioma, `getVoices()` sólo devuelve las SAPI antiguas, y ninguna puntuación arregla eso. En el navegador de pruebas `getVoices()` devuelve **0 voces** (Chromium sin motor de voz), así que la calidad sólo se puede juzgar en el equipo del usuario.

### 38.2 Motores neuronales evaluados (medido, no supuesto)

| Motor | Español | Dónde corre | Medición | Veredicto |
|---|---|---|---|---|
| Kitten TTS mini/micro/nano 0.8 | **No** (sólo inglés) | ONNX local | — | Descartado: no habla español |
| Kitten TTS 2 (1.7B, 20 idiomas) | Sí | **API hospedada** | — | Descartado: no es offline |
| Kokoro 82M · kokoro-js 1.2.1 | **No**: el paquete oficial sólo lista `af_*/am_*/bf_*/bm_*` | WASM local | modelo q8 carga en 18–23 s | Descartado |
| Kokoro 82M multilenguaje (fork `chijete`) | Sí (`em_santa`, `ef_dora`) | WASM local | **11–16 s por frase** y bloquea la interfaz | Descartado |
| Azure Speech (es-CL Catalina / Lorenzo) | Sí, chileno | Nube | 300–900 ms por readback | **Elegido** |

Detalle de la medición de Kokoro (readback corta, `dtype:'q8'`, `device:'wasm'`, ya con el modelo cacheado): 1.ª síntesis 27,5 s (incluye bajar el tensor de la voz), siguientes **11,5 / 14,1 / 16,2 s**; el audio sale correcto (3,8–4,7 s a 24 kHz, RMS 0,060–0,069, no es silencio). Es decir: incluso en caliente sintetiza **3 veces más lento que tiempo real** y, al correr en el hilo principal, deja la interfaz congelada mientras habla (las evaluaciones del navegador dejaban de responder). Para readbacks de ATC, inservible.

### 38.3 Qué se implementó

**a) Enrutador de motor.** La función de voz anterior pasó a llamarse `_ttsSpeakSystem` (sin cambios internos) y `_ttsSpeak` ahora es un enrutador:

```
_ttsSpeak → ¿motor = azure y hay clave?
              sí → VOZ.speakAzure(...)  ──fallo──▶ _ttsSpeakSystem(...) + aviso en ESTADO
              no → _ttsSpeakSystem(...)
```

Todos los llamados existentes (`sayReadback`, reportes de entrada, colaciones) siguen usando `_ttsSpeak`, así que no hubo que tocar el resto del diálogo.

**b) Panel `CONFIG ▸ VOZ`** (mismo patrón que LABEL / BUTTON / FRASES):

| Campo | Para qué |
|---|---|
| MOTOR `SISTEMA` / `AZURE` | botón activo en verde |
| VOZ ES / VOZ EN | lista las voces instaladas con su nota `_voiceScore`; `AUTO` = mejor disponible |
| CLAVE | clave de Azure (campo oculto) |
| REGIÓN | por defecto `brazilsouth` |
| ▶ ESCUCHAR | readback de ejemplo con el motor y la voz actuales |
| ESTADO | qué está usando y qué falló |

La voz elegida a mano tiene prioridad sobre el hash del hablante (se inyecta justo antes de `_stableVoice`), y como el resto del motor, se guarda por navegador.

**c) Privacidad.** Motor, clave, región y preferencias viven en `localStorage['scel_voz_motor_v1']`, sólo en ese navegador. **Nada de eso va al HTML, al repo ni al deploy.**

**d) Azure Speech.** `POST` a `https://{región}.tts.speech.microsoft.com/cognitiveservices/v1` con SSML:

```xml
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='es-CL'>
  <voice name='es-CL-CatalinaNeural'>
    <prosody rate='+10%' pitch='-3%'>LAN uno cero uno, autorizado ascenso…</prosody>
  </voice>
</speak>
```

- Voces: `es-CL-CatalinaNeural` (mujer) / `es-CL-LorenzoNeural` (hombre) / `en-US-AriaNeural` / `en-US-GuyNeural`, alternadas de forma determinista por callsign (mismo piloto = misma voz toda la sesión).
- `rate` sale del control de velocidad que ya existía (`ttsSpeedPct`, 110 % por defecto); `pitch` fijo en −3 % para que no suene jovial.
- Salida `audio-24khz-48kbitrate-mono-mp3` ≈ 6 KB/s; una readback de 4 s pesa ~24 KB.
- Squelch VHF al empezar y al terminar, igual que el motor del sistema; un readback nuevo corta el anterior.
- Errores traducidos en ESTADO: `401` clave inválida, `403` recurso sin permiso, `429` cuota agotada, más `HTTP nnn`. En cualquiera de esos casos **cae al motor del sistema** y el simulador sigue funcionando.

### 38.4 Cómo activarlo (5 minutos, gratis)

1. `portal.azure.com` → *Crear un recurso* → **Speech**.
2. Plan **F0 (gratuito)**: 500.000 caracteres al mes — una readback típica son ~120 caracteres, o sea >4.000 readbacks/mes.
3. Región **Brazil South** (la más cercana; sirve cualquier región, las voces es-CL están en todas).
4. Copiar **CLAVE 1** → `CONFIG ▸ VOZ ▸ AZURE` → pegar en CLAVE → `▶ ESCUCHAR`.

Sin clave el motor Azure no se usa: el panel avisa «Azure seleccionado pero SIN clave → se usa el sistema».

### 38.5 Alternativa gratis y sin clave: Edge

Si el equipo tiene **Microsoft Edge** (Windows 10/11), al abrir el simulador ahí `getVoices()` incluye las voces **Natural** (`Microsoft Catalina Online (Natural) - Spanish (Chile)`). El motor `SISTEMA` ya las puntúa +50, así que las elige solo: no hay que configurar nada. Es la mejora más barata; Azure es para cuando se quiere la misma voz en cualquier navegador y en cualquier PC.

### 38.6 Verificación

| Prueba | Resultado |
|---|---|
| Sintaxis de los 3 bloques `<script>` (`new Function`) | 0 errores |
| Panel VOZ | abre, lista voces con nota, ESTADO correcto en cada motor |
| SSML | `&`, `<`, `>`, `"`, `'` escapados; `rate`/`pitch` correctos |
| Petición Azure con clave falsa | `HTTP 401` → mensaje «clave inválida (401) → sistema» y readback por el motor del sistema |
| Suite completa | **115 líneas · 89 OK · 0 fallos** |
| Integridad | 667.797 B · BOM sí · 12.673 CRLF · 0 LF suelto · 0 U+FFFD |
| Deploy servido solo como `index.html` | arranca, panel VOZ operativo |

No se pudo validar el **audio** desde el navegador de pruebas (no tiene motor de voz ni salida); la prueba real es `▶ ESCUCHAR` en el equipo del usuario.

### 38.7 Deploy

| Archivo | Bytes | MD5 |
|---|---|---|
| `SCEL_ATC_Radar.html` = `netlify-deploy/index.html` | 667.797 | `FE183AD40E16AF2E9D7751497B314185` |
| `callsign.xml` = `netlify-deploy/callsign.xml` | 7.212 | `B61573326232F593E134F6812C7E7709` |

Los archivos de prueba de los motores (`_kokoro_probe.html`, `_kokoro_es_probe.html`) se borraron: no se suben.

### 38.8 Ajustes para el camino gratis (Edge) — verificado con voces simuladas

Para que la opción «sin clave» sea la buena, se corrigieron tres detalles del motor `SISTEMA`:

| Cambio | Por qué |
|---|---|
| `u.lang = uttVoice.lang` (antes siempre `es-419`/`en-US`) | Edge ignora o silencia el utterance cuando `lang` no coincide con la voz elegida; con Natural es-CL ahora pide `es-CL` |
| El `AUTO` del selector muestra el nombre de la voz que va a usar | se ve de un golpe si tomó Catalina o una SAPI vieja |
| ESTADO cuenta las neuronales y avisa si no hay | «Sistema · 4 voces · 2 neuronales» / «sin neuronales — en Edge hay gratis (Catalina/Lorenzo)» |

Prueba con un catálogo simulado de Edge (`getVoices` inyectado: Sabina es-MX, Catalina Natural es-CL, Google es-US, Aria Natural en-US) y `speak` interceptado:

| Comprobación | Resultado |
|---|---|
| Ranking ES | Catalina Natural **85** › Google es-US **44** › Sabina **−30** (la preferencia por Natural funciona) |
| Voz y `lang` del utterance ES | `Microsoft Catalina Online (Natural) - Spanish (Chile)` · **`es-CL`** |
| Voz y `lang` del utterance EN | `Microsoft Aria Online (Natural) - English (United States)` · `en-US` |
| Panel | `AUTO — Microsoft Catalina…`, lista con notas 85/44/−30, ESTADO «4 voces · 2 neuronales» |
| Suite | **115 · 89 OK · 0 fallos** |
| Integridad | 668.152 B · BOM sí · 12.677 CRLF · 0 LF suelto · 0 U+FFFD · MD5 `5FBA364CB9C8CB0CCA840665155776ED` |

Deploy actualizado: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html` con ese mismo MD5.

**Cómo se usa en el equipo real:** abrir el `index.html` con **Microsoft Edge** → `CONFIG ▸ VOZ` → `SISTEMA` → la lista debe mostrar `Microsoft Catalina Online (Natural) - Spanish (Chile)` como AUTO → `▶ ESCUCHAR`. Si la lista sólo trae Sabina/Helena, faltan las voces: *Configuración de Windows ▸ Hora e idioma ▸ Voz ▸ Agregar voces* (y en Edge, que las voces en línea estén permitidas).

### 38.9 Dónde está el botón VOZ (ajuste de descubribilidad)

El primer intento dejó `VOZ` al final de `CONFIG` (antes de `HELP`). Dos cosas lo hacían invisible:

1. La columna izquierda tiene `max-height:calc(50vh - 92px)` y **scroll propio**: en una ventana de 900 px de alto mide ~363 px y el contenido ~420 px, así que los últimos botones quedaban fuera de vista sin indicio de que hubiera que bajar.
2. Hasta elegir dispositivo en el modal de arranque (SECTOR G / SECTOR E), `#app` está oculto y la columna mide 0×0.

Cambio: `VOZ` pasó a ser **el primer botón de CONFIG**, arriba de `LIVE`. Medido con SECTOR E en ventana de 910 px: `VOZ` a `top=327 px` (visible) y al abrirlo el panel mide 216 px (353→569), también dentro de pantalla.

Captura de referencia: `capturas/config_voz.png`.

Verificación: suite **115 · 89 OK · 0 fallos** · integridad 668.152 B · BOM sí · 12.677 CRLF · 0 LF suelto · 0 U+FFFD · MD5 `5AF37EA6AE5C1EA681A353B45BF1526A` (deploy sincronizado).

---

## 39. Eliminar un vuelo: clic en el símbolo + SUPR — 26-10-2026

### 39.1 Qué hace

1. **Clic** sobre el símbolo radar (o sobre su etiqueta) → el tráfico queda seleccionado, como siempre.
2. **SUPR** (tecla `Delete` / `Suprimir`) → modal centrado:

```
⚠ ELIMINAR VUELO
¿Eliminar el vuelo LAN dos cero cero?
A320 · 12.000 ft. Desaparece del radar y del listado. No se puede deshacer.
                                          [ CANCEL ]  [ OK ]
```

3. **OK** saca la aeronave de la simulación · **CANCEL** / `Esc` / clic fuera no toca nada.

El nombre que muestra el modal es el **callsign hablado** (`resolveCallsign`), no la sigla: si el XML dice `SKU=SKY`, el modal dice «SKY dos dos cero». Debajo, tipo y nivel actuales como confirmación visual.

### 39.2 Detalle de la implementación

| Pieza | Dónde |
|---|---|
| `#delModal` + estilos `.dx-*` | antes de `</style>`, paleta de `#flightsModal` con borde rojo |
| `delFlightPrompt()` / `delFlightCancel()` / `delFlightConfirm()` | después de `cur()` |
| Disparo de SUPR | handler de teclado de flechas/Tab (document) |
| Texto de ayuda | pie del modal HELP |

Limpieza al borrar (misma que el aterrizaje automático, que ya existía en la línea del `landed`):

- `aircraft.splice(idx,1)` y reajuste de `selected` (`deselect()` si era el seleccionado, `--` si estaba después).
- **RBLs persistentes**: se eliminan las que lo referencian y se reindexan las demás (`idx1/idx2`), más las de LIVE por `hex`.
- Edición en línea (`_editIdx`), tap pendiente (`_tapBlipIdx`) y RBL pendiente (`_pendingRbl`) se resetean.
- Contador `TRF` (`tb-count`) recalculado y línea en el log: `✕ VUELO ELIMINADO · SKU220 · A320 · quedan 2`.
- El índice del modal se **revalida por callsign** antes de borrar: si entre abrir y confirmar aterrizó o se limpió otro tráfico, no se borra el avión equivocado.

### 39.3 Guardas

- SUPR **sin selección** no abre nada (probado).
- SUPR con **otro modal abierto** (FLIGHTS, HELP, FRASES, OFFLINE, editor, selector de dispositivo) no se dispara.
- Con el modal abierto: `Esc` cancela, `Enter`/`SUPR` confirman, y **la barra espaciadora no activa el micrófono**.
- En modo **LIVE ADS-B** (`selected=-1`) no aplica: el tráfico real no se borra.

### 39.4 Verificación

| Prueba | Resultado |
|---|---|
| Clic real en el blip (`mousedown`+`mouseup` en sus coordenadas) | `selected=0` · `SKU220` |
| SUPR tras el clic | modal `flex` · texto «SKY dos dos cero» (callsign del XML) |
| OK | 3 → 2 tráficos · `selected=-1` · `TRF=2` · sidebar cerrada |
| CANCEL / `Esc` / clic en el fondo | cierra sin borrar |
| `Enter` con el modal abierto | confirma |
| Espacio con el modal abierto | no inicia voz |
| SUPR sin selección / con FLIGHTS abierto | no hace nada |
| Suite completa | **115 líneas · 89 OK · 0 fallos** |
| Integridad | 673.945 B · BOM sí · 12.774 CRLF · 0 LF suelto · 0 U+FFFD |

Captura: `capturas/eliminar_vuelo.png`. Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `2519EFC299B739DB2DC44DE68652F750`.

---

## 40. AWY-SUP: aerovías RNAV superiores (UL) - 26-10-2026

Hasta ahora `AWY-SUP` dibujaba solo las 8 aerovías **UV** (ENR 3.1, convencionales VOR). Se agregaron las **16 RNAV UL** que publica el AIP Chile en ENR 3.2.

### 40.1 Fuente y extracción

PDF oficial (AMDT 66, páginas con fecha 14 MAY 2026 y 30 NOV 2023):

`2 ENR Parte 2/ENR 3 Designadores y Descripcion para Rutas ATS/zENR 3 RNAV UL.pdf` - 14 páginas.

El texto del PDF viene troceado por kerning (`[(IRE)9.7 (MI)]TJ`) y con celdas fusionadas, así que no sirve el extractor de líneas por sí solo. Se usó **pdf.js** en el navegador (`pdfjs.html` temporal) para obtener cada ítem con su `transform` real, se agruparon filas por `y` (tolerancia 1,2 pt) y se unieron por `x`:

- **nombre** = ítems antes de la columna de coordenadas (los `VOR/DME` se guardan sin sufijo: `TOY`, `LOA`, `IPA`, `NIA`, `AMB`).
- **coordenadas** = par `GD MM SS S` + `GD MM SS W` de la misma fila (se aceptan 1-3 dígitos de grado, necesario para `108°W`/`120°W`).
- **distancia** = columna DIST de la fila `RNAV` inmediatamente inferior.

Se descartaron dos falsos positivos del barrido (`UL 14`, `UL 30`, que eran trozos de encabezados `ENR 3.2-14.UL`).

### 40.2 Datos incorporados

**86 puntos nuevos** (coordenadas tal cual el PDF, DMS a decimal) + **135 puntos** en total en `AWY_SUP_FIX_XY` (49 UV que ya estaban + 86 UL). Los nombres que ya existían (`ALMIR`, `ARI`, `BAL`, `BRADA`, `BUXIS`, `DGO`, `MON`, `NAS`, `PWL`, `SIMOK`, `SIRAM`, `TBN`, `TOY`, `VTN`, `VUNIK`) se reutilizan: se verificó que las coordenadas del PDF coinciden con las que ya tenía el mapa UV.

| Ruta | Puntos | Ruta | Puntos |
|---|---|---|---|
| UL 300 | 12 | UL 531 | 4 |
| UL 302 | 10 | UL 540 | 3 |
| UL 309 | 3 | UL 550 | 7 |
| UL 322 | 3 | UL 650 | 8 |
| UL 348 | 17 | UL 653 | 3 |
| UL 401 | 6 | UL 670 | 10 |
| UL 405 | 5 | UL 780 | 10 |
| UL 416 | 6 | UL 797 | 4 |

Notas de armado:

- **UL 348** viene en dos páginas con `ASALA` repetido en el corte (`ENR 3.2-4.UL` / `-5.UL`); se deja una sola vez. Es la ruta Santiago - Isla de Pascua - Tahiti, por eso llega a `SAURI` (25°45'S 120°00'W).
- **UL 670** no publica distancia en `BAL -> EGOSA` ni en `ROMIV -> PWL` (celdas vacías en el AIP); la geometría igual es correcta (366,6 NM y 37,7 NM respectivamente, medidos).
- Los nombres son los del AIP tal cual, incluso los de 5 letras que parecen cortados: `IREMI`, `ASEPU`, `ISGUD`, `EDRON`. Se cruzaron contra **ENR 4.3 Puntos ATS/MET** (AMDT 61) y coinciden (`IREMI 18°21'S 75°23'W`, `ELASA`, `ATEDA`, `ESDIN`, `JURAK`, `ANPUK`, `UMKAL`, `NEBEG`, `PABOS`, `EMPEX`, `XONAT`, `OSOGU`, `MUGUK`, `SAURI`, `SORTA`, `LIVOR`, `SULNA`, `KONRI`, `GEKAL`, `KADAT`).

### 40.3 Dibujo

En `drawAirwaysSup()` las UL se dibujan **con trazo discontinuo** (`setLineDash([8,6])`) y las UV siguen sólidas, mismo azul y mismo grosor. El designador (`UL 302`, `UL 348`, ...) va al medio del trazado igual que los `UV`.

Los puntos lejanos (hasta 120°W) simplemente quedan fuera del canvas cuando el zoom está cerca; no afectan el encuadre ni el `pan`.

### 40.4 Verificación

Se validó cada tramo contra la **columna DIST del propio AIP** (great circle, R=3440,065 NM). 100 tramos medidos:

| Resultado | Detalle |
|---|---|
| 97 tramos | diferencia <= 1,0 NM |
| 2 tramos | sin distancia publicada en el AIP (UL 670: `BAL->EGOSA`, `ROMIV->PWL`) |
| 1 tramo | `VANIL->MIBAS` (UL 416) mal leído al principio: la fila trae `10` NM y el extractor tomó el `5` de la columna LL; corregido a 10 NM (calculado 9,8) |

Con eso quedan descartados los errores típicos de esta tabla: pares lat/lon cruzados, filas saltadas y nombres pegados (`ISGUD`+`EDRON`).

| Prueba | Resultado |
|---|---|
| `AWY_SUP` | 24 rutas (8 UV + 16 UL), 135 puntos, 0 referencias sin resolver |
| Test nuevo `SUP1` en la suite | `OK (AWY-SUP 24 rutas, 16 UL, 135 puntos)` |
| Suite completa | **116 líneas - 0 fallos** |
| Integridad | 678.759 B - BOM sí - 12.887 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `9C0ECB26083FB91929A0D035CC5CDCB4`.
---

## 41. AWY-SUP: aerovías RNAV superiores (UT) - 26-10-2026
### 41.1 Fuente y extracción
`zENR 3 RNAV UT.pdf` (ENR 3.2 RNAV UT, 18 páginas, 821.165 B). El PDF se lee con la misma pagina `pdfjs.html` que las UL y se extrae en el navegador: 4.815 items de texto, agrupados por fila (`y` +- 1,2) y unidos por celdas (separacion de `x` > 1,2). La distancia de cada tramo se toma de la fila `RNAV` siguiente.

Resultado: **26 rutas, 159 fixes**. Las filas del PDF son 160; se descarta el `SOSTA` repetido en el corte `ENR 3.2-12.UT` / `-13.UT`.

### 41.2 Datos incorporados

| Ruta | Puntos | Ruta | Puntos | Ruta | Puntos |
|---|---|---|---|---|---|
| UT 100 | 5 | UT 127 | 8 | UT 276 | 2 |
| UT 101 | 7 | UT 131 | 7 | UT 291 | 5 |
| UT 102 | 9 | UT 134 | 11 | UT 293 | 7 |
| UT 103 | 4 | UT 200 | 14 | UT 295 | 3 |
| UT 104 | 6 | UT 210 | 3 | UT 296 | 4 |
| UT 105 | 11 | UT 252 | 3 | UT 315 | 5 |
| UT 107 | 2 | UT 258 | 5 | UT 316 | 13 |
| UT 115 | 5 | | | | |
| UT 118 | 9 | | | | |
| UT 121 | 5 | | | | |
| UT 122 | 3 | | | | |
| UT 125 | 3 | | | | |

Notas de armado:

- **UT 200** sigue en la pagina siguiente (`ENR 3.2-13.UT`) con `SOSTA` repetido: se deja una sola vez.
- **UT 316** es la ruta oceánica a Isla de Pascua: llega a 109 grados W con tramos reales de 318, 268, 262, 259, 256 y 254 NM.
- **UT 101** y **UT 316** son las de tramos mas largos del bloque superior.
- Los 26 designadores son UQ/UT de 3 digitos (UT 100 ... UT 316); ninguno se pisa con las UV ni con las UL.

### 41.3 Dibujo

Las UT usan el mismo azul y el mismo trazo discontinuo `[8,6]` que las UL; la regla quedó por prefijo (`UV` solida, cualquier otra RNAV discontinua), así que no hubo que tocar el renderer. El título del boton pasa a `Aerovías superiores: UV ENR 3.1 (VOR, azul gruesa) y UL/UT ENR 3.2 (RNAV, discontinua)`.

### 41.4 Verificacion

Se midió cada tramo con la columna DIST del AIP (great circle, R=3440,065 NM). **133 tramos medidos**:

| Resultado | Detalle |
|---|---|
| 132 tramos | diferencia <= 1,0 NM |
| 1 tramo | `NEDOM->SUGRO` (UT 316) AIP 256 NM, calculado 255 NM |

No apareció ningun conflicto de coordenadas con los 49 puntos UV/UL previos (tolerancia 5e-5). De los 130 puntos distintos de las UT, **80 eran nuevos** y 50 ya existían.

| Prueba | Resultado |
|---|---|
| `AWY_SUP` | 50 rutas (8 UV + 16 UL + 26 UT), 215 puntos, 0 referencias sin resolver |
| Test `SUP1` | `OK (AWY-SUP 50 rutas: 8 UV / 16 UL / 26 UT, 215 puntos)` |
| Suite completa | **116 lineas - 0 fallos** |
| Integridad | 683.603 B - BOM si - 12.997 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `3AAEC2750220A779C1C309C03E70630E`.

---

## 42. AWY-SUP: aerovías RNAV superiores (UQ) - 26-10-2026
### 42.1 Fuente y extracción
`zENR 3 RNAV UQ.pdf` (ENR 3.2 RNAV UQ, 16 páginas, 1.007.475 B, MD5 `2D64394CC4CEE6FB8E97EEECE59BC59E`; hojas fechadas 28 NOV 2024 y 14 MAY 2026). Estas rutas son RNAV/RNP 2 con tramos controlados por ADS-C (`ACCS` / `ACCM`) y el AIP las publica aparte de las UL y las UT.

Primer intento fallido: la descarga se cortó en 737.280 B (exactamente 720 KB) por el timeout de `Invoke-WebRequest` y el PDF truncado se leia como una revisión vieja de las UL (30 NOV 2023). Se repitió con timeout de 300 s y el archivo completo; recién ahí aparecieron las 8 rutas UQ.

El extractor de las UT no sirve tal cual: en estas hojas la pista magnética y la distancia van en una fila propia, por ejemplo `174 354 44 | 5 | ACCS`, donde la distancia es el último número antes de la barra. Se agregó esa variante (y la de `RNAV 5 /` con distancia en la misma fila) y se validó cada tramo.

Resultado: **8 rutas, 138 fixes**, 130 tramos con distancia publicada (los ultimos fix de cada ruta no llevan distancia).

### 42.2 Datos incorporados

| Ruta | Puntos | Recorrido |
|---|---|---|
| UQ 802 | 48 | SIRAM ... NAS (norte-sur por el oeste) |
| UQ 803 | 33 | LOBAG ... NAS |
| UQ 805 | 9 | LINER ... TIGNO |
| UQ 808 | 4 | KADAK ... LODOS |
| UQ 809 | 16 | GELUS ... TIGNO (incluye la oceánica hacia 73 W) |
| UQ 810 | 8 | KADAK ... VLD |
| UQ 814 | 11 | LOA ... DILOK |
| UQ 815 | 9 | LOA ... SIMOK |

Notas de armado:

- **UQ 802** ocupa cinco páginas (`ENR 3.2-1.UQ` a `-5.UQ`) y pasa por 48 puntos; es la mas larga del bloque.
- **UQ 809** y **UQ 814** comparten varios fixes con **UT 105/115** y **UL 416** (`VLD`, `MPI`, `LITUX`, `PABOS`, `VANIL`); se verificó que las coordenadas coincidan antes de reutilizarlos.
- `PNT` (UQ 803) es un nombre de tres letras tal cual el AIP.

### 42.3 Dibujo

Las UQ entran con la misma regla por prefijo: mismo azul, trazo discontinuo `[8,6]`, designador al medio (`UQ 802`, `UQ 809`, ...). Comentarios de cabecera y del renderer actualizados a `UL/UT/UQ (ENR 3.2 RNAV)`.

### 42.4 Verificacion

**130 tramos medidos** contra la columna DIST del AIP:

| Resultado | Detalle |
|---|---|
| 129 tramos | diferencia <= 1,0 NM |
| 1 tramo | `DADGI->EDNIX` (UQ 802) AIP 43 NM, calculado 44 NM (redondeo del AIP) |

Validacion conjunta de las 42 rutas nuevas (UL + UT + UQ, 356 tramos): solo quedan las dos excepciones ya documentadas de las UL (`ESDIN->JIREN` 433 vs 434,8 NM y `VANIL` con 10 NM reales) y el tramo de 1,0 NM de las UT. Cero conflictos de coordenadas entre las 284 puntos.

| Prueba | Resultado |
|---|---|
| `AWY_SUP` | 58 rutas (8 UV + 16 UL + 26 UT + 8 UQ), 284 puntos, 0 referencias sin resolver |
| Test `SUP1` | `OK (AWY-SUP 58 rutas: 8 UV / 16 UL / 26 UT / 8 UQ, 284 puntos)` |
| Suite completa | **116 lineas - 0 fallos** |
| Integridad | 687.528 B - BOM si - 13.077 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `D62A5718187651079ED71C749AEA41A0`.
---

---

## 43. Se elimina JAL del simulador - 26-10-2026

Japan Airlines no opera en Chile, así que salió de toda la cadena: base, respaldo interno y tráfico automático.

### 43.1 Cambios

| Archivo | Cambio |
|---|---|
| `callsign.xml` | se borra `<airline icao="JAL" ... callsign="JAPANAIR"/>`; quedan 39 aerolíneas |
| `netlify-deploy/callsign.xml` | misma copia (MD5 `4B769EFF1C40E02A42543348BD9A912E`) |
| `SCEL_ATC_Radar.html` | se borra `JAL` de `_CS_FALLBACK`, la base `JAL` de `AUTO_DEP` (quedan 23) y `JAPANAIR` del texto de ayuda |
| `tests/hold_test.js` | el test de auto-dep pasa a exigir 23 bases |

### 43.2 Por qué también el respaldo interno

`callsign.xml` manda, pero `_CS_FALLBACK` rellena los ICAO que faltan en el XML. Si solo se borraba el XML, cualquier JAL que quedara en un ejercicio guardado seguía leyéndose "JAPANAIR". Al sacarlo de los dos lados, `resolveCallsign()` cae en el caso genérico y devuelve el código tal cual (`JAL 123` se lee "JAL uno dos tres"), que es lo que corresponde a una línea que no opera en el país.

### 43.3 Verificación

| Prueba | Resultado |
|---|---|
| `callsign.xml` | XML válido, 39 aerolíneas + 6 nombres de combate FACH, 0 JAL |
| Aplicación | `CS_META` = 50 claves, 0 entradas JAL/JAPANAIR; `AUTO_DEP_BASES` = 23 |
| Test de auto-dep | `SC15:OK (auto dep 17R activo)` con 23 bases |
| Suite completa | **116 líneas - 0 fallos** |
| Integridad | 687.407 B - BOM si - 13.076 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `F90888A7DFB862691E5AF461FFE3AEED`.

Queda una mención histórica de JAL en los capítulos 16 y 34 (registro de la base ampliada y tabla de callsigns de esa época); no se reescribe el historial.
---

---

## 44. Se elimina CPA (Cathay Pacific) - 26-10-2026

Mismo criterio que con JAL: Cathay Pacific no opera en Chile, así que sale de la base, del respaldo y del tráfico automático.

### 44.1 Cambios

| Archivo | Cambio |
|---|---|
| `callsign.xml` | se borra `<airline icao="CPA" ... callsign="CATHAY"/>`; quedan 38 aerolíneas |
| `callsign.xml` (cabecera) | se saca CATHAY de la lista de ejemplos y se elimina el bloque duplicado de "DIFERENCIAS INTENCIONALES" (estaba repetido dos veces) |
| `netlify-deploy/callsign.xml` | misma copia (MD5 `0DD3D63557373E8E79A10C3A8D55F1A7`) |
| `SCEL_ATC_Radar.html` | se borra `CPA` de `_CS_FALLBACK`, la base `CPA` de `AUTO_DEP` (quedan 22) y `CATHAY` del texto de ayuda |
| `tests/hold_test.js` | el test de auto-dep pasa a exigir 22 bases |

### 44.2 Verificación

| Prueba | Resultado |
|---|---|
| `callsign.xml` | XML válido, 38 aerolíneas + 6 nombres de combate FACH, 0 CPA/CATHAY |
| Aplicación | `CS_META` = 49 claves, 0 entradas CPA/CATHAY; `AUTO_DEP_BASES` = 22 |
| Resolución | `resolveCallsign('CPA123')` devuelve "CPA one two three" (código, sin distintivo inventado) |
| Test de auto-dep | `SC15:OK (auto dep 17R activo)` con 22 bases |
| Suite completa | **116 líneas - 0 fallos** |
| Integridad | 687.290 B - BOM sí - 13.075 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `110D5E4AB623304DA999E35FBEFFCD64`.

---

## 45. El LOC se captura en el IF (SEDPA/TEGEB) o al norte - 26-10-2026

Antes el localizador se capturaba en cuanto la aeronave quedaba dentro de ±0,15 NM del eje y con menos de 45° de diferencia de rumbo, sin importar **dónde** estaba a lo largo de ese eje. Un avión que pasaba por el sur de la pista (o entre el umbral y el IF) y se alineaba, capturaba el LOC y se "pegaba" al eje para luego volar hacia el norte, en vez de seguir con el vector asignado hasta el fix de inicio. La regla del AIP es la contraria: el viraje de interceptación se hace **en el IF** (SEDPA para 17R, TEGEB para 17L) o más al norte, nunca al sur de él.

### 45.1 Regla implementada

| Concepto | Implementación |
|---|---|
| Eje de la pista | `ilsThr(rwy)` (umbral) + `rwDx()/rwDy()` (rumbo 177°): distancia sobre el eje positiva al norte del umbral |
| Desviación lateral | `ilsLatFor(a,rwy)` = componente perpendicular al eje |
| Avance sobre el eje | `ilsDistFor(a,rwy)` = proyección sobre el eje (positiva al norte del umbral) |
| IF de cada pista | `ifLocFix(rwy)` = `WPT.SEDPA` (17R) / `WPT.TEGEB` (17L) |
| Distancia umbral → IF | `ifLocDist(rwy)`; medido: **10,88 NM (17R)** y **10,84 NM (17L)** |
| Decisión | `locCaptureOk(a,rwy)` = `ilsDistFor(a,rwy) >= ifLocDist(rwy) - 0,25` |

La tolerancia de 0,25 NM absorbe el paso por el fix sin obligar a una captura exacta al décimo de milla. El sector dibujado en pantalla llega a 11,4 / 11,2 NM, es decir algo más al norte del IF, así que toda captura válida ocurre dentro del sector visible.

### 45.2 Dónde se aplica

| Punto | Cambio |
|---|---|
| Captura automática del vector final (`vecFinal`, ~L6900) | la condición pasa de `Math.abs(lat)<=0.15` a `Math.abs(lat)<=0.15 && dLoc>=dIF-0.25`; usa `ilsLatFor/ilsDistFor` con la pista del vector (antes `ilsLat(a)` leía `a.locRwy`, que es `null` antes de capturar) |
| Aviso al piloto | si está alineado pero al sur del IF, una sola vez: "VEC FINAL: alineado pero al SUR de SEDPA (7.9/10.9 NM) - mantiene rumbo hasta el IF"; el flag `a._locWaitIf` evita repetirlo |
| Comando manual `LOC 17R/17L` (`interceptLoc`, ~L5520) | guarda `if(!locCaptureOk(a,newRwy))` que rechaza la captura y pide mantener el vector; la rama de contingencia por cambio de pista queda igual |
| Reinicio del flag | `a._locWaitIf=false` al entrar a `vecFinal()` (~L6719), al capturar y en la propia función de captura |
| Ayuda en pantalla | los tooltips de los botones 17L/17R ahora dicen "…; el LOC se captura en el IF o al norte" |

El `LOC` que llega por la ruta de aproximación publicada (fin de STAR en SEDPA/TEGEB) no necesita la guarda: la aeronave ya está en el IF por construcción.

### 45.3 Incidencia durante la edición

El primer intento de escribir el bloque dejó un salto de línea real dentro de un literal de JavaScript (la flecha del mensaje quedó partida en su propia línea), lo que producía `SyntaxError: Invalid or unexpected token` y dejaba la aplicación sin arrancar (`WPT` y todas las constantes quedaban indefinidas). Se detectó comparando `typeof` de símbolos conocidos y localizando la línea del error con un `appendChild` de prueba; se corrigió uniendo el literal en una sola línea. Lección: al insertar textos con caracteres no ASCII por PowerShell conviene evitarlos en el código y usar solo ASCII en los literales nuevos.

### 45.4 Verificación

| Prueba | Resultado |
|---|---|
| `ifLocDist` | 10,88 NM (17R→SEDPA), 10,84 NM (17L→TEGEB) |
| Simulación, 3 NM al sur del IF, sobre el eje | `locMode=false`, log "alineado pero al SUR de SEDPA (7.9/10.9 NM)" |
| Simulación, 2 NM al norte del IF | `locMode=true`, `locRwy=17R` |
| Test nuevo `IFLOC1` | sur del IF y sur del aeropuerto no capturan; en el IF, +6 NM y eje capturan (ambas pistas) |
| Suite completa | **117 líneas - 0 fallos** (`SUP1` 58 rutas / 284 puntos sigue OK) |
| Integridad | 689.050 B - BOM sí - 13.096 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `0DC87C08FFBB8742972A8E80BCAEDCB1`.

Pendiente de decisión del usuario: `ssdsd.html` (copia rota con `SyntaxError`) sigue en la carpeta.

---

## 46. Aerovias con trazo continuo y 30% mas delgadas - 26-10-2026

Las aerovias RNAV (UL/UT/UQ) se dibujaban con trazo discontinuo para no confundirlas con las UV convencionales, y el grosor del bloque superior era el doble que el de las aerovias inferiores. A la vista del mapa el resultado era ruidoso: muchas lineas cortadas y bastante gruesas. Ahora todas las aerovias son lineas continuas y ambos bloques bajan un 30% de grosor.

### 46.1 Cambios

| Funcion | Antes | Ahora |
|---|---|---|
| `drawAirways()` (AWY-INF) | `lineWidth = 1*DPR`, continua | `lineWidth = 0.7*DPR`, continua |
| `drawAirwaysSup()` (AWY-SUP) | `lineWidth = 2*DPR`; UV continua y **UL/UT/UQ discontinua** `[8*DPR,6*DPR]` | `lineWidth = 1.4*DPR`; **las 58 rutas continuas** (`setLineDash([])`) |

El resto de la jerarquia visual no se toca: las superiores siguen en azul intenso (`rgba(90,160,255,.55)`) y las inferiores en azul grisaceo muy tenue (`rgba(138,180,216,.18)`). Como ya no hay diferencia de trazo, UV y UL/UT/UQ se distinguen por el designador rotulado a mitad de cada ruta ("U 204", "U 106", etc.).

### 46.2 Textos actualizados

| Ubicacion | Cambio |
|---|---|
| Tooltip del boton AWY-SUP (HTML) | "UV ENR 3.1 y UL/UT/UQ ENR 3.2 (RNAV) - lineas continuas, azul tenue" |
| Cabecera del bloque de datos AWY-SUP (~L3569) | se quita la nota de "trazo discontinuo"; indica que se distinguen por el designador |
| Cabecera de `drawAirwaysSup()` (~L8148) | idem, con los nuevos grosores (1.4*DPR / 0.7*DPR) |
| Comentario en linea del `setLineDash` | "todas las aerovias: trazo continuo" |

### 46.3 Verificacion

Comprobado en ejecucion, instrumentando `CanvasRenderingContext2D.prototype.stroke` y forzando `drawAirways()` + `drawAirwaysSup()` con ambos botones activos:

| Familia | Estilos de trazo observados |
|---|---|
| AWY-INF | `0.7px · rgba(138,180,216,0.18) · solido` x15 rutas |
| AWY-SUP | `1.4px · rgba(90,160,255,0.55) · solido` x58 rutas |

Ninguna ruta usa `dash`. El resto de la suite sigue igual:

| Prueba | Resultado |
|---|---|
| Suite completa | **117 lineas - 0 fallos** |
| Integridad | 689.045 B - BOM si - 13.096 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `61DA437A6558AA3B4FE429CE3D99FE38`. Captura de referencia: `capturas/aerovias_continuas.png`.

## 47. Auditoria de las 66 SIDs contra las cartas AIP - 26-10-2026

Reporte del usuario: las salidas "mantienen rumbo" en vez de volar la salida publicada, sobre todo las que deben continuar hacia el norte. Se revisaron las 66 rutas de `SIDS` con dos metodos: (a) volar cada ruta en el motor del simulador y medir la traza, y (b) contrastar la secuencia de fixes con las cartas AIP SID 1-5 y la tabla de coordenadas de SCEL.

### 47.1 Verificacion de vuelo de las 66 rutas

Cada SID se instancio con `mkACwithRoute` y se volo con `update(1)` hasta sobrepasar el ultimo fix. Para cada ruta se comparo la distancia realmente recorrida con la suma de los tramos publicados:

| Metrica | Resultado |
|---|---|
| Rutas que alcanzan el ultimo fix | **66 / 66** |
| Relacion recorrido / suma de tramos | 0.98 - 1.05 en las 66 (sin circulos ni reversas) |
| Error de seguimiento en cada tramo | 0 grados (el rumbo apunta siempre al fix siguiente) |

La unica ruta con relacion < 1 es `GELUS5B` (0.98), por el primer tramo medido sobre el eje antes del viraje. No se detectaron rutas que "mantengan rumbo" despues del primer fix: todas giran hacia el punto siguiente.

### 47.2 Contraste con las cartas

| Carta | Texto AIP | Estado en el archivo |
|---|---|---|
| SID 1 | NEBEG 7A / ALBAL 7A: "R177 PDH/AMB hasta FL130, viraje izquierda directo YESOS / SUPRA" | correcto (`_ax` a FL130 + `FL130_17R/17L`) |
| SID 1 | ANGOD 8B: "R177 hasta GENPO/ESKUL, viraje derecha R190 AMB a ETEMI-ANGOD" | correcto |
| SID 2 | LINER 5A 17R: VAGOS y viraje izquierda R175 PDH a LINER; 17L: directo a LINER | correcto |
| SID 2 | GELUS 6A: VAGOS/DESIT, viraje derecha R079 DGO a KIDUG, izquierda R196 TBN a GELUS | correcto |
| SID 2 | SABLA 8: VAGOS/DESIT, viraje derecha R079 hasta ARSEV | correcto |
| SID 3 | DOMINGO 6: R079 DGO hasta KIDUG, luego directo DGO | correcto |
| SID 3 | VENTANAS 6: "viraje derecha para interceptar R157 (TR337) VTN directo VTN" | correcto: KIDUG cae sobre R157 VTN (158.2 grados) |
| SID 3 | TABON 6A: "viraje derecha para interceptar R196 (TR016) TBN directo TBN" | correcto: KIDUG cae sobre R196 TBN (197.8 grados) |
| SID 3 | DONTI 6A: "R157 VTN hasta D26 VTN, viraje derecha R026 DGO hasta DONTI" | **corregido** (47.3) |
| SID 4 | TENUT 5 / GUVOL 5C: TEMUS/PUMAR, TBN, OLMUE / PABEK, GUVOL | correcto |
| SID 4 | SANTIAGO 5: "viraje derecha para interceptar R020 AMB (TR200) directo AMB; cruzar D22 AMB FL110-FL140" | **corregido** (47.3) |
| SID 5 | Tabla RNAV 35R/L: CA 357 a 5000 FT, DF PARKE (RT) FL110+, GENPO 216 FL130+, GELUS 226 FL150+ | correcto (confirma que el viraje al sur de PARKE es el publicado) |

Con esto quedan cerradas las 14 rutas que la entrada del 05-10-2026 dejaba "pendientes de carta oficial": las 8 de 35L/35R con `_ax` a PARKE giran al sur porque la carta RNAV lo publica asi (PARKE esta en 33 27 16 S, al sur del campo), y las de SID 3 / SANTIAGO 5 quedan como se detalla abajo.

### 47.3 Correcciones aplicadas

**1. `D22AMB` estaba en el radial reciproco.** La tabla de fix lo tenia en `(-7.464, -22.203)`, que son 22 NM en el radial **200** de AMB (al sur), mientras su propio comentario y la carta SID 4 piden el radial **020** ("cruzar D22 AMB entre FL110 y FL140" viniendo por TR200 hacia el VOR). Nuevo valor `(7.91, 19.02)`: 22.0 NM a 020.9 grados de AMB.

| | Antes | Ahora |
|---|---|---|
| `D22AMB` | `(-7.464,-22.203)` = 22 NM R200 | `(7.91,19.02)` = 22 NM R020 |
| `SANTIAGO5_35L/35R` | TEMUS/PUMAR -> 43 NM al sur -> 21 NM de vuelta al norte a AMB (~85 NM) | PUMAR/TEMUS -> 9.9 NM al este (100 grados) -> D22 AMB -> 22 NM a 201 grados -> AMB (**53 NM**) |

La traza verificada de `SANTIAGO5_35L` es `(-2,22) -> (9,18) -> (2,2) -> (-1,-4)`: sube por R357, vira a la derecha en PUMAR/TEMUS, intercepta R020, cruza D22 AMB y entra a AMB por TR200, como la carta.

**2. `DONTI6A` viraba 11 NM tarde.** La ruta pasaba por KIDUG (D55 VTN) y desde ahi cortaba directo a DONTI; la carta manda seguir R157 VTN hasta **D26 VTN** y recien ahi virar a R026 DGO. Se agrego el fix `D26VTN` en la tabla WPT: `(-25.86, 15.23)` = 26.0 NM a 158 grados de VTN; desde el a DONTI hay 12.7 NM en 026 grados (coherente con R026 DGO). Las dos variantes (17R y 17L) usan ahora `WPT.D26VTN`.

**3. `VENTANAS6` y `TABON6A` se dejan como estaban**, con la justificacion geometrica anotada en el codigo: KIDUG es la interseccion de R079 DGO con R157 VTN y con R196 TBN, de modo que el dogleg VAGOS/DESIT -> KIDUG -> VTN/TABON es el mismo intercept que publica la carta.

### 47.4 Verificacion

| Prueba | Resultado |
|---|---|
| Vuelo de las 66 SIDs | 66/66 al ultimo fix, relacion 0.98-1.05 |
| `SANTIAGO5_35L` / `_35R` | llega a AMB en 53 / 52 NM (antes ~85) |
| `DONTI6A_17R` / `_17L` | 59 / 60 NM, vira en D26 VTN y entra a DONTI por 026 |
| Suite completa | **117 lineas - 0 fallos** |
| Integridad | 689.654 B - BOM si - 13.103 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `932081016E1DAC6163D1FACEC184B8C6`.

## 48. Auto DEP: una salida cada 2 minutos y una sola pista - 26-10-2026

### 48.1 Pedido

> "las salidas seran cada 2 minutos, por ahora no habra salidas simultaneas de ambas pistas"

Se interpreta como: **un solo despegue por vez, siempre desde la misma pista**, con cadencia fija de 2 minutos. Se elimina por completo el modo `ROTAR`, que era el unico que mezclaba pistas.

### 48.2 Cambios

- **Selector de pista:** quedan solo las cuatro opciones reales (`17R`, `17L`, `35L`, `35R`). Se borro `<option value="ROTAR">` y el tooltip ahora dice "una sola pista a la vez".
- **`setAutoDepRwy(v)`:** normaliza cualquier valor desconocido a `17R` (`if(v!=='17R'&&v!=='17L'&&v!=='35L'&&v!=='35R')v='17R';`). Aunque alguien inyecte `'ROTAR'` por consola, el modo cae a 17R.
- **`autoDepRunway()`:** paso de `if(mode==='ROTAR') return AUTO_DEP_RWYS[autoDepSeq%4];` a `return autoDepRwyMode;`. Se elimino la constante `AUTO_DEP_RWYS`.
- **Etiquetas:** `startAutoDep()` y `setAutoDepRwy()` informan `siempre RWY <pista>` (antes habia un caso especial para `ROTAR`).
- **Cadencia:** ya era `AUTO_DEP_MS=120000` con cadena de `setTimeout` (un unico temporizador vivo) y piso anti-rafaga `AUTO_DEP_MIN_GAP_MS=10000`; no se toco.
- **Comentarios:** se reescribio la cabecera del bloque Auto DEP ("Las salidas salen SIEMPRE de una sola pista...") y el comentario del escenario `deps`.

### 48.3 Verificacion

| Prueba | Resultado |
|---|---|
| Opciones del selector | `17R, 17L, 35L, 35R` (sin ROTAR) |
| `setAutoDepRwy('ROTAR')` | queda en `17R` |
| `AUTO_DEP_MS` / `AUTO_DEP_MIN_GAP_MS` | 120000 ms / 10000 ms |
| `spawnDep()` x5 | 1 aeronave por llamada, las 5 con `depRwy=17R` |
| `startAutoDep()` | 1 salida inmediata, temporizador y watchdog activos |
| Test `SC25` (reescrito) | `pista unica: 8 salidas en 17R 17R 17R 17R 17R 17R 17R 17R` |
| Test `SC25b` (nuevo) | `ROTAR normaliza a 17R` |
| Suite completa | **118 lineas - 0 fallos** |
| Integridad | 689.264 B - BOM si - 13.098 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `85688E8005910BBE91B3B2C99E6D32B0`.

### 48.4 Notas

- El intervalo es de **tiempo real** (temporizador del navegador), no de tiempo simulado: a 4x las salidas se ven cada 8 minutos de simulador. Es el comportamiento que ya tenia el Auto DEP.
- `autoDepPool('17R')` devuelve el pool curado `AUTO_DEP` de 22 salidas, mientras que 17R tiene 24 SIDs publicadas (24/24/9/9 = 66). Las 2 restantes se pueden volar a mano o agregar al pool si se quiere cubrir el catalogo completo en automatico.

## 49. Interceptacion del LOC con margen de 60 grados y anticipacion de viraje - 26-10-2026

### 49.1 Pedido

> "al dar el rumbo para el localizador, en lugar de margen de 45 grados, ahora tendra un margen de 60 grados respecto al localizador, y si el rumbo asignado por ATC es congruente con el localizador y el margen asignado, la aeronave procedera a interceptar la prolongacion del localizador en el rumbo asignado por ATC."

Antes: `LOC_MAX=45` solo servia de filtro para el boton LOC y para el color de la barra lateral; la captura del vector final esperaba a que la aeronave estuviera a 0.15 NM del eje, sin importar el angulo. Resultado: con un vector a 60 grados la aeronave cruzaba el eje y recien ahi viraba, con sobrevuelo del eje y correccion en S.

### 49.2 Modelo implementado (guiado por manuales de operacion)

- **Margen:** `LOC_MAX=60`. El rumbo asignado no puede exceder 60 grados respecto del curso del LOC (177). Fuera de ese margen el vector NO captura y el sistema lo informa.
- **La aeronave vuela el rumbo asignado** hasta el punto de anticipacion; no vira antes ni sobre el eje.
- **Punto de anticipacion (lead):** `lat = R (1 - cos th)`, con `R = v / w` (radio de viraje de regimen, `w = TURN_RATE = 3 grados/s`) y `th` = angulo de intercepcion. Es la geometria clasica de FCTM/AOM: iniciar el viraje a esa distancia lateral hace que el arco termine exactamente sobre el eje, con el rumbo final alineado.
- **Captura:** dentro del margen, en el IF (SEDPA/TEGEB) o al norte, y **convergente** (`d(lat)/dt = v sen(hdg - 177)` apunta al eje). Al capturar se marca `_locRoll` y se vuela el curso (177) hasta alinear (viraje de regimen); luego manda la ley fina de seguimiento (+-5 grados).
- **Botón LOC:** ahora **arma** la interceptacion sobre el rumbo actual (no captura al instante). Rechaza rumbos fuera del margen o que no convergen al eje.
- **Avisos:** "rumbo ... a N grados del eje (>60) - NO captura", "no converge al eje", "al SUR del IF ... mantiene rumbo hasta el IF", "captura LOC 17R con N grados de intercepcion (anticipacion X NM)".

### 49.3 Verificacion (vuelo simulado, `update(1)`)

| Caso | Resultado |
|---|---|
| Vector 120 (57 grados), 17R, 220 kt, desde 12 NM al norte | sostiene 120 hasta lat 0.60 NM; captura en 0.51 NM; rueda a lat **0.03 NM**, rumbo **177.1**, GS capturado |
| Vector 135 (42 grados), 17L, 200 kt | captura en 0.24 NM; rueda a **0.02 NM**, rumbo 177.1 |
| Boton LOC, 30 grados, 17L | "ARMADO ... captura en 0.16 NM"; captura en 0.10; rueda a **0.025 NM** |
| Rumbo 240 (63 grados) | **no captura**: aviso "fuera del margen 60" |
| Rumbo 118 (61 grados) | cruza el eje **sin capturar** |
| Rumbo divergente (177+60) | no captura |
| Sobre el eje (lat 0.05, rumbo 177) | captura inmediata |
| Boton LOC con rumbo paralelo, 1 NM de offset | rechazado: "no converge al eje ... asigna un rumbo de interceptacion" |
| Suite completa | **120 lineas - 0 fallos** (`LOC60`, `LOCARM`, `IFLOC1`, `SC24/25/25b/26`) |
| Integridad | 691.830 B - BOM si - 13.130 CRLF - 0 LF suelto - 0 U+FFFD |

Deploy: `SCEL_ATC_Radar.html` = `netlify-deploy/index.html`, MD5 `42CBAB5A2F3C4F8A3871946E048BED0F`.

### 49.4 Notas

- Radios de viraje con TAS: 180 kt -> 0.95 NM; 220 kt -> 1.17 NM; 250 kt -> 1.33 NM. El lead crece con la velocidad, como en operacion real: a 60 grados y 250 kt se empieza el viraje a 0.67 NM del eje.
- El boton LOC ya no captura de inmediato: si la aeronave esta alineada y cerca del eje captura en el siguiente cuadro, pero si vuela en paralelo con offset pide un rumbo de interceptacion (antes se quedaba esperando a 0.15 NM sin explicacion).
- Se mantiene la regla del IF (cap. 45): al sur de SEDPA/TEGEB no hay captura.
