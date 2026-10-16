@echo off
rem ============================================================
rem  ACTUALIZAR DEPLOY NETLIFY
rem  Copia el simulador y TODOS sus archivos de apoyo a la
rem  carpeta netlify-deploy\ con el nombre CORRECTO index.html.
rem
rem  IMPORTANTE:
rem  - Netlify sirve como pagina principal SOLO index.html.
rem    No renombres a mano en Windows (con extensiones ocultas
rem    el archivo queda como index.html.html y Netlify lo ignora
rem    en la raiz). Este bat hace el renombrado automatico.
rem  - SIN coast_xy_smooth.js y border_xy.js el radar aparece
rem    NEGRO (la interfaz carga pero no dibuja nada).
rem
rem  Uso: ejecutar este .bat y arrastrar la carpeta
rem  netlify-deploy COMPLETA a https://app.netlify.com/drop
rem ============================================================
set SRC=%~dp0
set DST=%~dp0netlify-deploy
if not exist "%DST%" mkdir "%DST%"

rem -- Pagina principal con nombre index.html (renombrado automatico) --
copy /Y "%SRC%SCEL_ATC_Radar.html" "%DST%\index.html" >nul

rem -- REQUERIDOS: sin estos dos el radar queda en negro --
copy /Y "%SRC%coast_xy_smooth.js" "%DST%\" >nul
copy /Y "%SRC%border_xy.js" "%DST%\" >nul

rem -- Datos BADA, callsigns y fraseologia (funcionalidad completa) --
copy /Y "%SRC%performance.xml" "%DST%\" >nul
copy /Y "%SRC%callsign.xml" "%DST%\" >nul
copy /Y "%SRC%fraseologia_editada.json" "%DST%\" >nul
copy /Y "%SRC%normativa.xml" "%DST%\" >nul
copy /Y "%SRC%datos_offline.json" "%DST%\" >nul
copy /Y "%SRC%ejercicio1_ejemplo.xml" "%DST%\" >nul

echo.
echo  Deploy actualizado: %DST%
echo.
echo  1. Arrastra la CARPETA netlify-deploy completa a
echo     https://app.netlify.com/drop
echo  2. NO subas solo el HTML: faltarian coast_xy_smooth.js
echo     y border_xy.js y el radar quedaria negro.
echo.
pause
