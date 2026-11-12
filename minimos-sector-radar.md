# Mínimos de sector radar — SCEL (base MRVAC)

Fuente de mínimos: carta **ALTMIN/MRVAC SCEL** (AIP Chile, INFO SUP AIP S9 · AMDT 86 · 03-dic-2020).
Estado de geometría: verificado contra `SECTOR_MIN` del simulador (`SCEL_ATC_Radar.html`).
Total: **44** cajas · OK **24** · falta geometría **18** · mínimo no numérico **2**

| # | Sector | Mínimo cartilla | ft | Geometría | Estado | Nota |
|---:|---|---|---:|---|---|---|
| 1 | QUINTAY1 | 2000' | 2000 | NO | FALTA geometria |  |
| 2 | (4000') circulo junto AMB | 4000' | 4000 | NO | FALTA geometria | sin nombre en cartilla |
| 3 | QUINTAY2 | 4500' | 4500 | NO | FALTA geometria |  |
| 4 | (5000') caja sur CHAPE | 5000' | 5000 | NO | FALTA geometria | sin nombre en cartilla |
| 5 | (5200') caja sobre AMB | 5200' | 5200 | NO | FALTA geometria | sin nombre en cartilla |
| 6 | MONTE | 5500' | 5500 | SI | OK |  |
| 7 | PIL1 | 5500' | 5500 | SI | OK |  |
| 8 | PIL3 | FL55 | 5500 | SI | OK |  |
| 9 | PAPUDO | FL60 | 6000 | SI | OK |  |
| 10 | PIL2 | 6000' | 6000 | SI | OK |  |
| 11 | CHAPE | 7000' | 7000 | SI | OK |  |
| 12 | PELDEHUE | 7000' | 7000 | NO | FALTA geometria |  |
| 13 | MAIPO | 8000' | 8000 | SI | OK |  |
| 14 | TBN | 8000' | 8000 | NO | FALTA geometria |  |
| 15 | CASABLANCA | 8500' | 8500 | NO | FALTA geometria |  |
| 16 | PLOMO1 | 8500' | 8500 | SI | OK |  |
| 17 | TANGO1 | FL90 | 9000 | SI | OK |  |
| 18 | ANDES1 | FL100 | 10000 | SI | OK |  |
| 19 | ANGOD1 | FL100 | 10000 | SI | OK |  |
| 20 | TANGO2 | FL100 | 10000 | SI | OK |  |
| 21 | UKL1 | FL110 | 11000 | SI | OK |  |
| 22 | ANDES2 | FL120 | 12000 | SI | OK |  |
| 23 | ANGOD2 | FL120 | 12000 | SI | OK |  |
| 24 | PAINE | FL130 | 13000 | NO | FALTA geometria |  |
| 25 | ANDES3 | FL140 | 14000 | SI | OK |  |
| 26 | UKL2 | FL150 | 15000 | SI | OK |  |
| 27 | ALBAL1 | FL160 | 16000 | NO | FALTA geometria |  |
| 28 | NEBEG1 | FL160 | 16000 | SI | OK |  |
| 29 | PLOMO2 | FL160 | 16000 | SI | OK |  |
| 30 | COBRE1 | FL165 | 16500 | NO | FALTA geometria |  |
| 31 | PIRQUE | FL180 | 18000 | SI | OK |  |
| 32 | UKL3 | FL180 | 18000 | SI | OK |  |
| 33 | ACONCAGUA | FL190 | 19000 | NO | FALTA geometria |  |
| 34 | ALBAL2 | FL190 | 19000 | NO | FALTA geometria |  |
| 35 | COBRE2 | FL190 | 19000 | NO | FALTA geometria |  |
| 36 | ALBAL3 | FL200 | 20000 | NO | FALTA geometria |  |
| 37 | PLOMO3 | FL210 | 21000 | SI | OK |  |
| 38 | UKL4 | FL210 | 21000 | SI | OK |  |
| 39 | NEBEG2 | FL230 | 23000 | SI | OK |  |
| 40 | (FL250) circulo sup. | FL250 | 25000 | NO | FALTA geometria | sin nombre en cartilla |
| 41 | (FL260) circulo sup. A | FL260 | 26000 | NO | FALTA geometria | sin nombre en cartilla |
| 42 | (FL260) circulo sup. B | FL260 | 26000 | NO | FALTA geometria | sin nombre en cartilla |
| 43 | OUTER_BOUNDARY | FL100-FL070 | — | SI | CORREGIR: minimo no numerico | compuesto: falta valor unico |
| 44 | OUTER_CHAPE | FL100-FL070 | — | SI | CORREGIR: minimo no numerico | compuesto: falta valor unico |

## Qué falta corregir

1. **OUTER_BOUNDARY y OUTER_CHAPE** — mínimo compuesto `FL100-FL070` (no utilizable por MSAW). Necesitan un valor único y su MRVAC.
2. **12 sectores con mínima en cartilla pero sin polígono** en el simulador: ACONCAGUA, QUINTAY1, QUINTAY2, CASABLANCA, TBN, PELDEHUE, PAINE, ALBAL1-3, COBRE1-2.
3. **6 cajas sin nombre** de la cartilla (5000', 5200', 4000', FL260 ×2, FL250): solo tienen altitud; requieren nombre y coordenadas si deben entrar a MSAW.
