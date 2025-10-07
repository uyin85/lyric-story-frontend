import os
import subprocess
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
import replicate
import requests
from pydub import AudioSegment
from langdetect import detect
from supabase import create_client

app = Flask(__name__)
CORS(app)

OPENROUTER_KEY = os.environ["OPENROUTER_KEY"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

STYLE_PROMPTS = {
    "cinematic": "cinematic, film still, 35mm",
    "anime": "anime style, Studio Ghibli",
    "pixar": "3D render, Pixar animation style",
    "realistic": "photorealistic, 85mm portrait"
}

def verify_token(token):
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        return None

def get_story(lyrics):
    try:
        lang = detect(lyrics)
    except:
        lang = "en"
    
    prompt = f"Analyze these lyrics. Respond in the same language. Lyrics: {lyrics}. Meaning and 4 scenes:"
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={"model": "mistralai/mistral-7b-instruct", "messages": [{"role": "user", "content": prompt}]}
    )
    return resp.json()["choices"][0]["message"]["content"], lang

def generate_image(prompt):
    output = replicate.run(
        "stabilityai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712102b35068c41f509e5c31e15550e2c6",
        input={"prompt": prompt, "seed": 42, "num_inference_steps": 4}
    )
    return output[0]

@app.route('/generate', methods=['POST'])
def generate():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401
    token = auth_header.split(" ")[1]
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401

    lyrics = request.form.get('lyrics', '')
    mp3_file = request.files.get('song')
    style = request.form.get('style', 'cinematic')
    if not lyrics or not mp3_file:
        return jsonify({"error": "Lyrics and MP3 required"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        mp3_file.save(tmp.name)
        mp3_path = tmp.name

    audio = AudioSegment.from_mp3(mp3_path)
    duration_sec = len(audio) / 1000.0
    num_scenes = 4

    story, lang = get_story(lyrics)
    scenes = [f"scene {i+1} of emotional story" for i in range(num_scenes)]
    char_desc = "main character"

    style_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["cinematic"])
    image_paths = []
    for i, scene in enumerate(scenes):
        full_prompt = f"{char_desc}, {scene}, {style_prompt}, 4k"
        img_url = generate_image(full_prompt)
        img_data = requests.get(img_url).content
        img_path = f"/tmp/scene_{i}.jpg"
        with open(img_path, "wb") as f:
            f.write(img_data)
        image_paths.append(img_path)

    clip_paths = []
    scene_duration = duration_sec / len(image_paths)
    for i, img in enumerate(image_paths):
        clip = f"/tmp/clip_{i}.mp4"
        subprocess.run(["ffmpeg", "-loop", "1", "-i", img, "-c:v", "libx264", "-t", str(scene_duration), "-pix_fmt", "yuv420p", "-y", clip])
        clip_paths.append(clip)

    with open("/tmp/list.txt", "w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip}'\n")
    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "/tmp/list.txt", "-c:v", "libx264", "-y", "/tmp/video.mp4"])
    subprocess.run(["ffmpeg", "-i", "/tmp/video.mp4", "-i", mp3_path, "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-y", "/tmp/final.mp4"])

    job_id = f"{user_id}_{int(duration_sec)}"
    with open("/tmp/final.mp4", "rb") as f:
        supabase.storage.from_("videos").upload(f"{user_id}/{job_id}.mp4", f.read())
    video_url = supabase.storage.from_("videos").get_public_url(f"{user_id}/{job_id}.mp4")

    supabase.table("videos").insert({
        "user_id": user_id,
        "lyrics_preview": lyrics[:50],
        "duration_sec": duration_sec,
        "video_url": video_url,
        "language": lang
    }).execute()

    return jsonify({"video_url": video_url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)