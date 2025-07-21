import os, random, requests, subprocess, time
from datetime import datetime
from pydub.generators import Sine
from pydub import AudioSegment

# ---------- ENV VARIABLES ----------
LONG_LIVED_TOKEN = os.environ.get("LONG_LIVED_TOKEN")
APP_ID = os.environ.get("APP_ID")
APP_SECRET = os.environ.get("APP_SECRET")
IG_USER_ID = os.environ.get("IG_USER_ID")  # Manual IG User ID

# ---------- CLEAN OR CREATE GENERATED FOLDER ONCE ----------
def prepare_generated_folder():
    if os.path.isfile("generated"):  # If it's a file, delete it
        os.remove("generated")
    if not os.path.isdir("generated"):
        os.makedirs("generated")

# ---------- SAFE TOKEN REFRESH ----------
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
        return (random.choice(filtered) if filtered else random.choice(res)["q"])[:80]
    except:
        fallback = {
            "space": ["The stars don’t answer, they only listen."],
            "dark_poetry": ["Hearts bleed quietly under smiling faces."],
            "psychedelic": ["Reality melts when the mind starts to wander."]
        }
        return random.choice(fallback[mode])

# ---------- IMAGE GENERATION ----------
def generate_image(mode):
    placeholder_images = {
        "space": "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3",
        "dark_poetry": "https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0",
        "psychedelic": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29"
    }
    img_url = placeholder_images[mode]
    img_path = f"generated/{mode}_{int(time.time())}.jpg"
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
    duration = 10000
    if mode == "space":
        tone1 = Sine(80).to_audio_segment(duration=duration).fade_in(2000).fade_out(2000)
        tone2 = Sine(160).to_audio_segment(duration=duration).fade_in(2000).fade_out(2000)
        audio = tone1.overlay(tone2 - 10)
    elif mode == "dark_poetry":
        tone1 = Sine(220).to_audio_segment(duration=duration).fade_in(1000).fade_out(2000)
        tone2 = Sine(440).to_audio_segment(duration=duration).fade_in(1000).fade_out(2000)
        audio = tone1.overlay(tone2 - 20)
    else:
        tone1 = Sine(300).to_audio_segment(duration=duration).fade_in(500).fade_out(1500)
        tone2 = Sine(600).to_audio_segment(duration=duration).fade_in(500).fade_out(1500)
        tone3 = Sine(900).to_audio_segment(duration=duration).fade_in(500).fade_out(1500)
        audio = tone1.overlay(tone2 - 15).overlay(tone3 - 25)
    audio.export(output_path, format="mp3")
    return output_path

# ---------- ADD AUDIO TO VIDEO ----------
def add_audio(video_path, mode, output_path="generated/final_audio.mp4"):
    audio_path = generate_audio(mode)
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-shortest", "-c:v", "copy", "-c:a", "aac", output_path
    ]
    subprocess.run(cmd)
    return output_path

# ---------- HASHTAGS ----------
def generate_hashtags(mode):
    hashtags = {
        "space": ["#spacevibes", "#universe", "#cosmic", "#stars", "#deepthoughts"],
        "dark_poetry": ["#darkpoetry", "#sadquotes", "#gloomcore", "#emoaesthetic", "#brokenhearts"],
        "psychedelic": ["#psychedelicart", "#trippyvibes", "#surreal", "#mindtrip", "#aesthetic"]
    }
    random.shuffle(hashtags[mode])
    return " ".join(hashtags[mode][:5])

# ---------- RAILWAY STATIC URL ----------
def upload_to_railway(video_path):
    return f"https://{os.environ.get('RAILWAY_STATIC_URL')}/{os.path.basename(video_path)}"

# ---------- POST TO INSTAGRAM ----------
def upload_instagram_reel(video_path, caption):
    video_url = upload_to_railway(video_path)
    url = f"https://graph.facebook.com/v17.0/{IG_USER_ID}/media"
    params = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": LONG_LIVED_TOKEN
    }
    res = requests.post(url, data=params).json()
    creation_id = res.get("id")
    publish_url = f"https://graph.facebook.com/v17.0/{IG_USER_ID}/media_publish"
    publish_res = requests.post(publish_url, data={
        "creation_id": creation_id,
        "access_token": LONG_LIVED_TOKEN
    }).json()
    print("✅ Posted to Instagram:", publish_res)

# ---------- MAIN BOT RUN ----------
def run_bot():
    prepare_generated_folder()

    if datetime.now().day % 50 == 0:
        refresh_long_lived_token()

    mode = random.choice(["space", "dark_poetry", "psychedelic"])
    print(f"Posting mode: {mode}")
    quote = generate_quote(mode)
    img = generate_image(mode)
    video = create_video_ffmpeg(img, quote)
    final_video = add_audio(video, mode)
    caption = f"{quote}\n\n{generate_hashtags(mode)}"
    upload_instagram_reel(final_video, caption)

if __name__ == "__main__":
    run_bot()
