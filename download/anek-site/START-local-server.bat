@echo off
cd /d "%~dp0site"
echo Serving the Anak website at http://localhost:8000
echo Press Ctrl+C to stop.
start "" http://localhost:8000
python -m http.server 8000 || py -m http.server 8000
pause
