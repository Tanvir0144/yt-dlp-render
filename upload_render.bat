@echo off
cd /d D:\yt-dlp-render

:: সব ফাইল add করো
git add .

:: কমিট করো
git commit -m "fix: update requirements and runtime for Render"

:: GitHub এ push করো
git push origin main

echo ==============================
echo Push complete! Now redeploy on Render.
echo ==============================
pause
