import os, random, requests, subprocess, time
from datetime import datetime
from pydub.generators import Sine
from pydub import AudioSegment

# ---------- ENV VARIABLES ----------
LONG_LIVED_TOKEN = os.environ.get("LONG_LIVED_TOKEN")
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
IG_USER_ID = os.environ.get("IG_USER_ID")  # Manual IG User ID

# ---------- SAFE TOKEN REFRESH (Every 50 Days) ----------
def refresh_long_lived_token():
    global LONG_LIVED_TOKEN
    url = (
        f"https://graph.facebook.com/v17.0/oauth/access_token?"
        f"grant_type=fb_exchange_token&client_id={APP_ID}"
        f"&client_secret={APP_SECRET}&fb_exchange_token={LONG_LIVED_TOKEN}"
    )
    res = requests.get(url).json()
    if "access_token" in res:
        LONG_LIVED_TOKEN = res["access_token"]
        print("✅ Long-lived token refreshed.")
    else:
        print("⚠️ Token refresh failed:", res)

# ---------- FREE QUOTE GENERATION ----------
def generate_quote(mode):
    keywords = {
        "space": ["dream", "stars", "universe", "infinite", "mystery"],
        "dark_poetry": ["sad", "love", "pain", "heart", "tears", "lonely"],
        "psychedelic": ["dream", "mind", "reality", "vision", "trip"]
    }
    selected_keywords = keywords[mode]

    try:
        res = requests.get("https://zenquotes.io/api/quotes").json()
        filtered = [
            q["q"] for q in res
            if any(word.lower() in q["q"].lower() for word in selected_keywords)
        ]
        if filtered:
            return random.choice(filtered)[:80]
        else:
            return random.choice(res)["q"][:80]
    except Exception as e:
        print("⚠️ Quote API error, fallback to default:", e)
        fallback = {
            "space": ["The stars don’t answer, they only listen."],
            "dark_poetry": ["Hearts bleed quietly under smiling faces."],
            "psychedelic": ["Reality melts when the mind starts to wander."]
        }
        return random.choice(fallback[mode])

# ---------- IMAGE GENERATION (Placeholder Images) ----------
def generate_image(mode):
    placeholder_images = {
        "space": "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3",
        "dark_poetry": "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0",
        "psychedelic": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29"
    }
    img_url = placeholder_images[mode]
    timestamp = int(time.time())
    img_path = f"generated/{mode}_{timestamp}.jpg"
    with open(img_path, "wb") as f:
        f.write(requests.get(img_url).content)
    return img_path

# ---------- CREATE VIDEO ----------
def create_video_ffmpeg(image_path, text, output_path="generated/final.mp4"):
    cmd = [
        "ffmpeg", "-y", "-loop", "1",
        "-i", image_path,
        "-vf", f"scale=1080:1920,drawtext=text='{text}':x=(w-text_w)/2:y=h-200:fontsize=48:fontcolor=white",
        "-t", "10", "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path
    ]
    subprocess.run(cmd)
    return output_path

# ---------- GENERATE AMBIENT AUDIO ----------
def generate_audio(mode, output_path="generated/audio_track.mp3"):
    duration = 10000  # 10s
    if mode == "space":
        tone1 = Sine(80).to_audio_segment(duration=duration).fade_in(2000).fade_out(2000)
        tone2 = Sine(160).to_audio_segment(duration=duration).fade_in(2000).fade_out(2000)
        audio = tone1.overlay(tone2 - 10)
    elif mode == "dark_poetry":
        tone1 = Sine(220)
