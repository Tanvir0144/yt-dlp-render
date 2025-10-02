from fastapi import FastAPI
import yt_dlp
import os

app = FastAPI()

def get_ydl_opts(extra_opts=None):
    """Common YDL options with cookies support"""
    opts = {"quiet": True}
    cookies = os.getenv("COOKIES")

    # যদি Render environment এ cookies থাকে → ফাইলে লিখে দাও
    if cookies:
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(cookies)
        opts["cookiefile"] = "cookies.txt"

    if extra_opts:
        opts.update(extra_opts)
    return opts

@app.get("/")
def home():
    return {"message": "YT-DLP Super API Running on Render with Cookies!"}

@app.get("/download")
def download(url: str):
    ydl_opts = get_ydl_opts({"skip_download": True})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "views": info.get("view_count"),
            "thumbnail": info.get("thumbnail"),
            "formats": info.get("formats")[:5],
            "url": info.get("webpage_url"),
        }

@app.get("/search")
def search(q: str, limit: int = 5):
    url = f"ytsearch{limit}:{q}"
    ydl_opts = get_ydl_opts({"extract_flat": True})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"results": info["entries"]}

@app.get("/trending")
def trending(region: str = "US"):
    url = f"https://www.youtube.com/feed/trending?gl={region}"
    ydl_opts = get_ydl_opts({"extract_flat": True})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"trending": info["entries"][:10]}

@app.get("/play")
def play(url: str):
    ydl_opts = get_ydl_opts({"format": "best"})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "stream_url": info["url"]
        }
