@echo off
title SCEL ATC Radar — Servidor
echo ============================================
echo  SCEL ATC Radar — Servidor Local
echo ============================================
echo.
echo  Abre el radar en tu navegador:
echo  http://localhost:8000/SCEL_ATC_Radar.html
echo.
echo  Fuentes ADS-B:
echo    - Flightradar24 (/live/fr24)
echo    - adsb.lol (/live/chile) -- recomendado
echo.
echo  Ctrl+C para detener
echo ============================================
echo.
python server.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python no encontrado.
    echo Instala Python desde https://www.python.org/
    echo o abre el HTML directo (sin tráfico en vivo).
    pause
)
exit /b %errorlevel%
