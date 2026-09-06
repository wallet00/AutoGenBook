@echo off
REM AutoGenBook — build + push na Docker Hub (Windows)
REM Předpoklad: jsi v adresari repozitare (kde je Dockerfile).
cd /d "%~dp0\.."
echo === Build image wallet007/autogenbook:latest ===
docker build -t wallet007/autogenbook:latest .
if errorlevel 1 exit /b 1
echo === Login na Docker Hub ===
docker login
echo === Push image ===
docker push wallet007/autogenbook:latest
echo === Hotovo. Image je na Docker Hubu: wallet007/autogenbook:latest ===
