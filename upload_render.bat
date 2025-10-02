@echo off
cd /d D:\yt-dlp-render

echo ============================
echo Adding all changes...
git add .

echo ============================
echo Committing...
git commit -m "update: main.py with COOKIES_B64 support"

echo ============================
echo Pushing to GitHub...
git push origin main

echo ============================
echo Push complete! Now go to Render and Deploy latest commit.
pause
