# MANUAL DE USUARIO — SIMULADOR ATC SCEL
## Fraseología para el controlador de tránsito aéreo

**Versión:** 1.6 · **Fecha:** 23/08/2026
**Aplicable a:** SCEL_ATC_Radar.html (simulación + LIVE) · Piloto IA NLP activo
**Novedad v1.6:** archivo `normativa.xml` con fraseología establecida (DAP-11/DAN-11);
los pilotos usan frases estandarizadas; diluciones (preguntas de confirmación) y
correcciones de fraseología; fixes se leen como palabras ("ugola" no "U G O L A").
**Novedad v1.5b:** Fix: voces empezaban en inglés, ahora español desde el inicio.
**Novedad v1.5:** voz español **Chile** para todos los vuelos (voz neural
Antonia/Raul preferida, sin modismos ni acento gallego); IBE con español neutro
(España); inglés siempre en-US; fixes/waypoints se leen como palabras ("ugola"
no "U G O L A"); velocidad +20% (+40% IBE); desbloqueo TTS más robusto.
**Novedad v1.4:** botón 🔊 TEST de audio; rate +20%; heading EN "one eight zero".
**Novedad v1.3:** rumbres SIEMPRE con 3 dígitos ("cero uno cero", "cero dos cero") y
**rumbo 000 = 360** ("tres seis cero") · niveles de vuelo también con 3 dígitos (FL090)
**Novedad v1.2:** readback con **callsign primero** · números SIEMPRE dígito a dígito
(incluido el número del vuelo: "IBERIA dos ocho cuatro") · **CMP y IBE siempre hablan español**
**Novedad v1.1:** reportes automáticos de establecimiento en localizador y en espera ·
transferencia a Santiago Torre 118.1

---

## 1. Cómo dar instrucciones

El simulador tiene **dos formas de entrada**, y ambas las entiende el piloto IA (NLP local):

| Entrada | Cómo se usa |
|---|---|
| **Voz** | Botón 🎙 **VOZ** (izquierda del radar) o tecla **Espacio**. Habla el llamado con naturalidad. |
| **Texto** | Barra inferior del radar: escribe el llamado y pulsa **Enter** (o el botón ➤). |

> **Referencia rápida en pantalla:** el botón **HELP** del panel **CONFIG** abre
> un modal con todos los comandos permitidos por voz y por texto, organizados por
> categoría (RUMBO, NIVEL, VELOCIDAD, DIRECTOS, ESPERAS, APROXIMACIÓN,
> TRANSFERENCIA, INFORMES, CONSULTAS y GLOBALES), con ejemplos en español e
> inglés y las notas de validación de cada comando.

### 1.1 Formato general del llamado

> **[CALLSIGN], [INSTRUCCIÓN] + [VALOR]**

- El **callsign** puede ir al inicio o al final ("LAN101, vire a la izquierda 240" o "vire a 240, LAN101").
- Se acepta el callsign completo (**LAN101**), con espacio (**LAN 101**) o la raíz (**LAN1**).
- Si no dices callsign pero hay una aeronave **seleccionada** (y dices "ese/usted") o hay **una sola** en pantalla, se usa esa.
- El idioma puede ser **español o inglés**, mezclados si quieres.

### 1.2 Cómo decir los números (importante)

| Tipo | Cómo decirlo | Ejemplo hablado | Ejemplo escrito |
|---|---|---|---|
| **Rumbo** | Dígito a dígito, SIEMPRE 3 dígitos, sin omitir ceros | "dos cuarenta" (240) · "**cero uno cero**" (010) · "**tres seis cero**" (360) | 240 · 010 · 360 |
| **Nivel de vuelo (FL)** | Dígito a dígito, 3 dígitos | "nivel de vuelo tres cinco cero" · FL090 = "cero nueve cero" | 350 · 090 |
| **Altitud en pies** | Palabras con "mil" | "once mil" · "ocho mil quinientos" | 11000 · 8500 |
| **Velocidad** | Dígito a dígito | "dos cinco cero nudos" | 250 |

> **Regla de rumbos:** en aviación el rumbo 000 es el rumbo **360** — se dice
> "**tres seis cero**". Los rumbos menores a 100 llevan el cero inicial:
> 010 = "**cero uno cero**", 020 = "**cero dos cero**", 005 = "**cero cero cinco**".
> Nunca se dice "diez", "veinte" o "cinco" a secas para un rumbo.

### 1.3 Voces por aerolínea

| Vuelos | Voz TTS | Variante | Velocidad |
|---|---|---|---|
| Todos (LAN, SKY, CMP, LIVE…) | Español **Chile** (es-CL) | Voz neural de Microsoft (Antonia/Raul) si está instalada | +20% (1.056) |
| **IBE (Iberia)** | Español **neutro** (es-ES/genérico) | Elvira/Laura/Pablo o voz estándar de España | +40% (1.267) |
| Vuelos en inglés | Inglés **EE.UU.** (en-US) | Nunca inglés británico salvo que no exista otra | +20% (1.044) |

> Si el sistema no tiene voces chilenas, se usa el respaldo latino (es-419)
> y como último recurso cualquier voz en español (se excluye gallego es-GA).
> Fraseología aeronáutica sin modismos regionales.

### 1.4 Callsign de Iberia

El callsign de Iberia se pronuncia **junto**, sin espacio:

| Escrito | Pronunciación |
|---|---|
| IBE111 | "**IBERIA111**" (dígito a dígito: "IBERIA uno uno uno") |
| IBE284 | "**IBERIA284**" ("IBERIA dos ocho cuatro") |

### 1.5 Diluciones y correcciones

El piloto IA puede **dilucir** (preguntar confirmación) cuando recibe una
instrucción ambigua, y el controlador puede **corregir** desviaciones de fraseología.

**Diluciones** (preguntas del piloto):
| Comando del controlador | Respuesta del piloto |
|---|---|
| "confirma autorizado a ugola patrón de espera publicado, nivel de vuelo 280" | "LAN101, ¿me confirma autorizado a ugola patrón de espera publicado, nivel de vuelo dos ocho cero?" |
| "confirma rumbo 240" | "LAN101, ¿confirma rumbo dos cuatro cero?" |
| "confirma velocidad 250" | "LAN101, ¿confirma velocidad dos cinco cero nudos?" |

**Correcciones** (el controlador corrige al piloto):
| Comando del controlador | Respuesta del piloto |
|---|---|
| "corrige rumbo 240" | "CORRECCIÓN: LAN101, rumbo dos cuatro cero, no ..." |
| "error en nivel" | "CORRECCIÓN: LAN101, nivel de vuelo ..., no ..." |

**Fixes como palabras:** todos los fixes (UGOLA, TEGEB, SEDPA, etc.) se pronuncian
como palabras ("ugola"), nunca se deletrean ("U G O L A").

> El resto de compañías (LAN, SKY, CMP…) conservan el espacio:
> "LATAM 120", "Sky 220", "Copa 450".

---

## 2. Tabla de instrucciones — fraseología recomendada

Todas las variantes de cada fila son equivalentes; el piloto las entiende igual.

### 2.1 RUMBO (viraje)

| Fraseología ES (recomendada) | Fraseología EN | Efecto |
|---|---|---|
| "LAN101, **vire a la izquierda rumbo 240**" | "LAN101, **turn left heading 240**" | Viraje por izquierda a 240° |
| "LAN101, **gire a la derecha 320**" | "LAN101, **turn right 320**" | Viraje por derecha a 320° |
| "LAN101, **rumbo 180**" | "LAN101, **fly heading 180**" | Rumbo directo (giro más corto) |
| "LAN101, **mantenga rumbo 090**" | "LAN101, **maintain heading 090**" | Fija el rumbo indicado |
| "LAN101, **mantenga rumbo**" (sin número) | "LAN101, **maintain heading**" | Fija el rumbo actual |

### 2.2 NIVEL (ascenso / descenso)

| Fraseología ES | Fraseología EN | Efecto |
|---|---|---|
| "LAN101, **ascienda a nivel de vuelo 350**" | "LAN101, **climb flight level 350**" | Asciende a FL350 |
| "LAN101, **suba a 240**" | "LAN101, **climb 240**" | Asciende a FL240 |
| "LAN101, **descienda a once mil pies**" | "LAN101, **descend to 11000 feet**" | Desciende a 11.000 ft |
| "LAN101, **descienda a mil quinientos pies**" | — | Desciende a 1.500 ft (aproximación) |

### 2.3 VELOCIDAD

| Fraseología ES | Fraseología EN | Efecto |
|---|---|---|
| "LAN101, **reduzca velocidad a 250 nudos**" | "LAN101, **reduce speed to 250 knots**" | Reduce a 250 kt |
| "LAN101, **aumente a 280**" | "LAN101, **increase speed to 280**" | Aumenta a 280 kt |
| "LAN101, **mantenga 250 nudos**" | "LAN101, **maintain 250 knots**" | Fija 250 kt |

### 2.4 DIRECTOS Y ESPERAS

| Fraseología ES | Fraseología EN | Efecto |
|---|---|---|
| "LAN101, **directo a UGOLA**" | "LAN101, **direct UGOLA**" | Vuela directo al waypoint |
| "LAN101, **espere en UGOLA**" | "LAN101, **hold at UGOLA**" | Espera (holding) en UGOLA |
| "LAN101, **espera sobre UGOLA**" | "LAN101, **hold UGOLA**" | Espera (holding) en UGOLA (preposición opcional) |
| "LAN101, **esperando en UGOLA**" | "LAN101, **holding at UGOLA**" | Espera (holding) en UGOLA |
| "LAN101, **ingrese a patrón de espera en UGOLA**" | "LAN101, **enter the holding pattern at UGOLA**" | Espera (holding) en UGOLA |
| "LAN101, **autorizado hasta UGOLA, mantenga patrón de espera publicado**" | "LAN101, **cleared to UGOLA, hold as published**" | Espera en UGOLA (el fix va ANTES de "espera") |
| "LAN101, **autorizado hasta UGOLA, mantenga patrón de espera publicado, prevea autorización de aproximación a las 15:30**" | "LAN101, **cleared to UGOLA, hold as published, expect approach clearance at 1530**" | Espera en UGOLA + hora de expectativa (se muestra en el status bar y el piloto la confirma) |
| "LAN101, **espere en UGOLA, nivel de vuelo 140**" | "LAN101, **hold at UGOLA, flight level 140**" | Espera en UGOLA asignando FL140 (si es inferior al publicado, el piloto rechaza) |
| "LAN101, **abandone la espera**" | "LAN101, **leave hold**" | Sale del holding |
| "LAN101, **reanude la STAR**" | "LAN101, **resume STAR**" | Vuelve a su ruta/STAR |
| "LAN101, **contacto Santiago Torre 118.1**" | "LAN101, **contact tower 118.1**" | Transfiere a la torre; el piloto confirma y queda traspasado |

### 2.5 APROXIMACIÓN Y OTROS

| Fraseología ES | Fraseología EN | Efecto |
|---|---|---|
| "LAN101, **intercepte localizador pista 17 derecha**" | "LAN101, **intercept ILS runway 17R**" | Captura el ILS 17R |
| "LAN101, **localizador 17 izquierda**" | "LAN101, **loc 17L**" | Captura el ILS 17L |
| "LAN101, **cambiar pista 17 derecha**" | "LAN101, **switch runway 17R**" | **Contingencia:** cambia de 17L a 17R en vuelo |
| "LAN101, **cambiar a pista 17 izquierda**" | "LAN101, **change runway 17L**" | **Contingencia:** cambia de 17R a 17L en vuelo |
| "LAN101, **identifique**" | "LAN101, **ident**" | Flash de identificación en pantalla |

### 2.6 REPORTES (la aeronave responde con sus datos)

| Fraseología ES | Fraseología EN | Respuesta esperada |
|---|---|---|
| "LAN101, **¿qué nivel tienes?**" | "LAN101, **say altitude**" | "LAN101, manteniendo nivel de vuelo dos cuatro cero" |
| "LAN101, **reporte rumbo**" | "LAN101, **say heading**" | "LAN101, rumbo dos cuatro cero" |
| "LAN101, **¿a qué velocidad?**" | "LAN101, **say speed**" | "LAN101, dos cinco cero nudos" |
| "LAN101, **al habla**" (solo llamada) | "LAN101, **call**" | "LAN101, adelante" |

### 2.7 Comandos globales (sin callsign)

| Frase | Efecto |
|---|---|
| "**pausa**" / "**pause**" / "**detener**" | Congela la simulación |
| "**reanudar**" / "**unpause**" | Reanuda la simulación |

---

## 3. Respuestas del piloto (qué debes escuchar)

El piloto IA responde hablado (TTS) y en el panel 📻. Formato: **primero el callsign,
luego la instrucción**, y TODOS los números se pronuncian **dígito a dígito**
("dos cinco cero", nunca "doscientos cincuenta"; el número del vuelo también:
"IBERIA dos ocho cuatro").

> **CMP (Copa) e IBE (Iberia) siempre responden en español**, tengan o no voz
> española instalada las otras compañías.

### 3.1 Readbacks de comandos

| Situación | Respuesta del piloto |
|---|---|
| Rumbo asignado | "LAN101, virando izquierda rumbo dos cuatro cero" — 010: "rumbo **cero uno cero**" · 360/000: "rumbo **tres seis cero**" |
| Nivel asignado | "LAN101, ascendiendo a nivel de vuelo tres cinco cero" |
| Velocidad asignada | "LAN101, reduciendo a dos cinco cero nudos" |
| Directo a fix | "LAN101, directo UGOLA" |
| Espera asignada | "LAN101, sobre UGOLA ingreso a patrón de espera publicado" |
| Abandono de espera | "LAN101, abandonando patrón de espera sobre UGOLA, reanudo SIMOK 7B o volando directo a UGOLA" |
| Interceptación ILS | "LAN101, interceptando localizador pista uno siete derecha" |
| Cambio de pista (contingencia) | "LAN101, cambio a pista uno siete izquierda" |
| Transferencia a torre | "**IBE284, contacto Santiago Torre 118.1**" / EN: "IBE284, contact tower 118.1" |

### 3.2 Reportes automáticos del piloto (sin que se los pidas)

| Momento | Reporte del piloto |
|---|---|
| Entrada al área (posición) | "IBERIA dos ocho cuatro en su frecuencia, pasando UGOLA, EROLO 7F, nivel dos ocho cero" |
| Llega al fix e inicia el patrón publicado | "LAN101, establecido en espera sobre UGOLA" |
| Captura el localizador (se establece) | "LAN101, establecido en localizador pista uno siete derecha" |

### 3.3 Aclaraciones y rechazos

| Situación | Respuesta del piloto |
|---|---|
| Llamada sola | "LAN101, adelante" |
| Falta el valor | "LAN101, ¿a qué rumbo?" · "¿a qué nivel?" · "¿a qué velocidad?" · "¿directo a qué punto?" |
| Rumbo inválido | "LAN101, repita el rumbo — no válido, LAN101" |
| Nivel bajo mínimos | "LAN101, imposible — nivel por debajo de mínimos, LAN101" |
| Nivel sobre el techo | "LAN101, nivel por encima del techo — repita, LAN101" |
| Velocidad excesiva | "LAN101, no puedo — limito a tres ocho cero nudos, LAN101" |
| Waypoint inexistente | "LAN101, XXXX no está en mi base de datos, LAN101" |
| Espera inexistente | "LAN101, no tengo espera en XXXX — disponibles: UGOLA, MORPA, DABIT, KADAK, VTN, TEGEB, SEDPA" |

> El idioma de la respuesta depende de la voz española disponible en tu navegador:
> con voz ES instalada responde en español; si no, en inglés (también válido).

---

## 4. Ejemplos rápidos de sesión real

```
Controlador:  "SKY220, vire a la derecha rumbo 280"
Piloto:       "SKY220, virando derecha rumbo dos ocho cero"

Controlador:  "SKY220, ascienda a nivel de vuelo 310"
Piloto:       "SKY220, ascendiendo a nivel de vuelo tres uno cero"

Controlador:  "SKY220, reduzca a doscientos cincuenta"
Piloto:       "SKY220, reduciendo a dos cinco cero nudos"

Controlador:  "SKY220, ¿qué nivel tienes?"
Piloto:       "SKY220, manteniendo nivel de vuelo tres uno cero"

Controlador:  "SKY220, directo a UGOLA"
Piloto:       "SKY220, directo UGOLA"

Controlador:  "SKY220, espere en UGOLA"
Piloto:       "SKY220, sobre UGOLA ingreso a patrón de espera publicado"
(luego, al llegar al fix:)  "SKY220, establecido en espera sobre UGOLA"

Controlador:  "SKY220, intercepte localizador pista 17 derecha"
Piloto:       "SKY220, interceptando localizador pista uno siete derecha"
(luego, al capturar:)       "SKY220, establecido en localizador pista uno siete derecha"

Controlador:  "IBE284, contacto Santiago Torre 118.1"
Piloto:       "IBERIA dos ocho cuatro, contacto Santiago Torre 118.1"   (siempre español)
```

---

## 5. Consejos para que funcione sin problemas

1. **Di el callsign completo** al inicio: "LAN101, ..." — evita confusiones con otras aeronaves.
2. **Separa el número de la instrucción**: "a doscientos cincuenta" funciona mejor que "adoscientos".
3. **Para rumbos, 3 dígitos con ceros**: "dos cuarenta" (240), "**cero uno cero**" (010),
   "**tres seis cero**" (360). El rumbo 000 se expresa como 360.
4. **Para niveles, di "nivel de vuelo"** si es FL, o "mil/pies" si es altitud: "once mil" = 11.000 ft.
5. Si el piloto te **pide aclaración** (¿a qué rumbo?), respóndele solo el dato: "240" — se aplica a la aeronave seleccionada.
6. **Modo LIVE**: los aviones reales tienen callsigns como "LAN533" o "JES3044"; úsalos igual.
7. La **barra de texto** escribe lo mismo que dirías por voz — útil para practicar y para equipos sin micrófono.

---

## 6. Sintaxis clásica (compatible, fallback)

El simulador también acepta la sintaxis original (funciona siempre, incluso si el NLP no entiende algo):

```
LAN101 turn left heading 180
LAN101 climb 350
LAN101 descend 110
LAN101 reduce speed 250 / increase speed 280 / speed 250
LAN101 direct UGOLA
hold UGOLA · resume STAR · maintain heading
LAN101 loc 17R · LAN101 ident
leave hold · pause · unpause
LAN101 contact tower   (transferencia a Santiago Torre 118.1)
```

**Esperas — variaciones aceptadas (voz o texto):** el fix puede ir después O antes de la palabra "espera/hold", y se acepta la fraseología completa de la normativa:

```
LAN101 hold UGOLA
LAN101 espere en UGOLA / espera sobre UGOLA / espera a UGOLA / esperando en UGOLA / hold over UGOLA
LAN101 ingrese a patrón de espera en UGOLA
LAN101 mantenga patrón de espera publicado
LAN101 autorizado hasta UGOLA, mantenga patrón de espera publicado
LAN101 autorizado hasta UGOLA, mantenga patrón de espera publicado, prevea autorización de aproximación a las 15:30
LAN101 espere en UGOLA, nivel de vuelo 140
LAN101 cleared to UGOLA, hold as published, expect approach clearance at 1530
```

La hora de expectativa ("prevea... a las HH:MM" / "expect HH:MM") se muestra en el status bar junto al patrón y el piloto la confirma en el readback. Si la instrucción incluye un nivel inferior al publicado en la STAR, el piloto **rechaza** y pide confirmación.

**Números hablados dígito a dígito (voz):** la fraseología ATC real dice los números dígito a dígito y el simulador los entiende (ES/EN, incluye fonética "niner/tree/fife/fower"):

```
LAN101 rumbo uno ocho cero          → rumbo 180
LAN101 ascienda a nivel de vuelo uno cuatro cero → climb FL140
LAN101 velocidad dos cinco cero     → velocidad 250
LAN101 hold UGOLA, expect one five three zero → expect 1530
```

Los números compuestos también funcionan ("nivel de vuelo ciento cuarenta" = FL140, "a las quince treinta" = 15:30). Si el reconocimiento no entiende una frase, el simulador muestra lo escuchado y pide repetir; ante silencio reintenta automáticamente hasta 2 veces. Un callsign mal escuchado ("LAM 101" por "LAN 101") se resuelve si la parte numérica coincide.

**Espera incompleta:** si la instrucción de espera no incluye nivel y/o hora de expectativa, el piloto **ejecuta la espera** pero pide confirmación en el readback:

```
ATC: "LAN101, hold UGOLA"                          → piloto: "LAN101, sobre UGOLA ingreso a patrón de espera publicado, confirme nivel de ingreso al patrón de espera y confirme hora prevista de abandono de la espera"
ATC: "LAN101, espere en UGOLA, nivel de vuelo 140" → piloto: "... confirme hora prevista de abandono de la espera"
ATC: "LAN101, hold UGOLA, expect 1530"             → piloto: "... confirme nivel de ingreso al patrón de espera"
ATC: "LAN101, hold UGOLA, nivel de vuelo 140, expect 1530" → piloto confirma la hora y no pide nada
```

**Desviaciones de fraseología:** el piloto se adapta a variaciones siempre que la
intención sea clara. Se toleran: sinónimos ("vire/gire/virar", "ascienda/suba",
"espera/espere/esperando/hold/holding", "proa/steer"), preposiciones opcionales
("espera a/sobre/en UGOLA"), orden de palabras ("a UGOLA directo", "nivel 140
ascienda"), números hablados ("nivel de vuelo uno cuatro cero"), palabras de
cortesía ("hold UGOLA por favor", "please hold at UGOLA"), viraje implícito
("240 a la izquierda") y "nivel NNN" sin verbo (infiere subir/bajar según la
altitud actual). También procesa **instrucciones múltiples** en una sola frase:
"vire a la izquierda rumbo 240, ascienda a nivel 140" ejecuta ambas. Si la
intención NO es clara, el piloto solicita confirmación:

```
ATC: "LAN101, zumba 350" → piloto: "LAN101, no entendí la instrucción, confirme instrucciones"
                          (EN: "LAN101, say again, confirm instructions")
```

### 6.1 Lenguaje implícito editable (CONFIG → FRASES → LENGUAJE)

Los sinónimos que el piloto usa para detectar la **intención** de una instrucción
(no el patrón exacto) se pueden editar en el panel FRASES, pestaña **LENGUAJE**, y
quedan almacenados en la sección `lenguaje` de `fraseologia_editada.json` (botón
💾 GUARDAR; en file:// se descarga el archivo para reemplazarlo y recargar).

Hay 6 grupos de sinónimos (separados por coma, se combinan con OR):

| Grupo | Detecta | Ejemplos por defecto |
|---|---|---|
| RUMBO | virajes | rumbo, heading, hdg, fly, vire, vira, gir, turn, curso, proa, steer |
| ASCENSO | subir | sub, asciend, ascend, climb, trep, subir, go up |
| DESCENSO | bajar | baj, desciend, descend, descent, go down |
| VELOCIDAD | velocidad | velocidad, speed, reduce, reduzc, disminu, slow, aument, increase, nudos, knots |
| DIRECTO | directos | directo, diríjase, dirígete, direct, proceed direct, go direct, vaya directo, ve directo, vaya, ve a, go to |
| ESPERA | esperas | espera, espere, esperando, hold, holding, patrón de espera |

Reglas:

- **Prefijos cortos cubren variantes**: `gir` → gire/gira/girar; `sub` → suba/subir;
  `baj` → baje/bajar. Para exigir la palabra completa usa el término entero.
- **Acentos opcionales**: `patrón` ≡ `patron`, `diríjase` ≡ `dirijase` (el
  simulador genera las variantes automáticamente).
- **Frases de varias palabras**: se escriben con espacios normales ("go up",
  "patrón de espera") y el simulador las convierte en coincidencia flexible.
- Tras editar, pulsa 💾 GUARDAR y **recarga la página** para aplicar.

---

## 7. Fraseología radar (nuevos comandos v1.7)

Comandos de aproximación y reportes agregados (voz o barra de texto):

```
LAN101 autorizado aproximación ILS pista 17 izquierda/derecha
LAN101 autorizado aproximación visual pista 17 izquierda/derecha
LAN101 vector para el localizador pista 17 izquierda, vire izquierda rumbo 240
LAN101 mantenga velocidad Mach punto ocho dos
LAN101 descienda a mil quinientos pies por minuto
LAN101 cruce UGOLA a nivel de vuelo 240 o superior
LAN101 tránsito a las doce
LAN101 notifique pasando UGOLA
LAN101 notifique establecido en patrón de espera
LAN101 notifique nivel
LAN101 contacto Santiago Torre 118.1   (lee "uno uno ocho coma uno")
```

Comportamiento:

- **Aproximación ILS/visual 17L/17R**: si la aeronave está al **norte** del aeropuerto (y>0) vuela directo al punto de alineación (eje de pista, FAF) y captura el localizador automáticamente. Si está al **sur** (y≤0) hace el circuito **Parque Bicentenario (8000 ft) → Cerro Renca (3500 ft) → base izquierda → alineación → aterriza** y desaparece en el umbral. Cerro Renca se dibuja como V invertida amarilla.
- **Vector final**: vira al rumbo indicado y al interceptar el localizador captura LOC/GS automáticamente.
- **Mach**: se muestra en el panel de comando (tile MACH, ej. "M.82"), no en la etiqueta radar. La TAS se recalcula según altitud. Readback comparativo: "aumentando/reduciendo/manteniendo velocidad Mach punto XX".
- **Razón vertical**: la razón indicada se mantiene hasta FL250 (ascenso) o 10000 ft (descenso); fuera de esos tramos vuelve a la razón normal de performance.
- **Cruce X a FL/altitud o superior**: solo readback de confirmación (sin lógica de cumplimiento).
- **Tránsito**: respuesta aleatoria del piloto ("tráfico a la vista" / "buscando tráfico" / "sin tráfico a la vista").
- **Notifique pasando X**: readback "notificaré pasando X" + reporte automático una sola vez al pasar el fix ("pasando X, nivel de vuelo XXX").
- **Notifique establecido en espera**: readback de confirmación (el reporte de establecido ya era automático).
- **Notifique nivel**: reporte inmediato del nivel actual que cruza la aeronave.

---

*Manual generado junto al simulador. Las variantes en negrita de las tablas son las
frases recomendadas; el resto son variantes libres que el piloto IA también comprende.*
