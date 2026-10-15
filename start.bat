@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating AURA-Flood environment with Python 3.14...
    py -3.14 -m venv .venv
    if errorlevel 1 goto setup_failed
)

".venv\Scripts\python.exe" -c "import fastapi, uvicorn, pandas, numpy, geopandas, shapely, rasterio, sklearn" >nul 2>nul
if errorlevel 1 (
    echo Installing AURA-Flood dependencies. This may take a few minutes...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_failed
)

echo.
echo AURA-Flood will be available at http://127.0.0.1:8000
echo Keep this window open while using the website.
echo.
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
if errorlevel 1 goto server_failed
goto end

:setup_failed
echo.
echo Setup failed. Read the error above, check your internet connection, then run start.bat again.
pause
goto end

:server_failed
echo.
echo The server stopped. Read the error above.
pause

:end
endlocal
