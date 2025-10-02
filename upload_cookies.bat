@echo off
REM ==============================
REM Upload all_cookies.txt to Render as Env Variable
REM ==============================

:: তোমার Render API Key
set RENDER_API_KEY=rnd_6wMKfKsMycrMluIqpZFj5fifp9Ji

:: তোমার Service ID
set SERVICE_ID=srv-d3f67ljipnbc739vssc0

:: ফাইল পড়ে কনটেন্ট variable এ রাখো
setlocal enabledelayedexpansion
set "COOKIES_CONTENT="
for /f "usebackq delims=" %%A in ("all_cookies.txt") do (
    set "line=%%A"
    set "COOKIES_CONTENT=!COOKIES_CONTENT!!line!^^n"
)

:: JSON payload তৈরি করে API তে পাঠানো
echo {"envVars":[{"key":"COOKIES","value":"%COOKIES_CONTENT%"}]} > payload.json

curl -X PATCH "https://api.render.com/v1/services/%SERVICE_ID%" ^
     -H "Accept: application/json" ^
     -H "Authorization: Bearer %RENDER_API_KEY%" ^
     -H "Content-Type: application/json" ^
     --data-binary @payload.json

del payload.json

echo ==============================
echo ✅ Cookies uploaded to Render as Environment Variable
echo ==============================
pause
