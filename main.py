from fastapi import FastAPI
import yt_dlp
import os, base64

app = FastAPI()

def get_ydl_opts(extra_opts=None):
    """Common YDL options with cookies support"""
    opts = {"quiet": True}

    # Render environment এ COOKIES_B64 থাকলে ডিকোড করে cookies.txt বানাও
    cookies_b64 = os.getenv("COOKIES_B64")
    if cookies_b64:
        try:
            cookies_data = base64.b64decode(cookies_b64).decode("utf-8")
            with open("cookies.txt", "w", encoding="utf-8") as f:
                f.write(cookies_data)
            opts["cookiefile"] = "cookies.txt"
        except Exception as e:
            print("Cookie decode error:", e)

    if extra_opts:
        opts.update(extra_opts)
    return opts

@app.get("/")
def home():
    return {"message": "✅ YT-DLP Super API Running on Render with Cookies!"}

# ------------------ DOWNLOAD ------------------
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

# ------------------ SEARCH ------------------
@app.get("/search")
def search(q: str, limit: int = 5):
    url = f"ytsearch{limit}:{q}"
    ydl_opts = get_ydl_opts({"extract_flat": True})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"results": info.get("entries", [])}

# ------------------ TRENDING (FIXED) ------------------
@app.get("/trending")
def trending(region: str = "BD", limit: int = 10):
    # feed/trending এর বদলে ytsearch ব্যবহার করলাম
    query = f"ytsearch{limit}:trending in {region}"
    ydl_opts = get_ydl_opts({"extract_flat": True})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return {"trending": info.get("entries", [])}

# ------------------ PLAY STREAM ------------------
@app.get("/play")
def play(url: str):
    ydl_opts = get_ydl_opts({"format": "best"})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "stream_url": info.get("url")
        }
