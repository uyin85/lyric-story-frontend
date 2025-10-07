import os
import subprocess
import tempfile
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import replicate
import requests
from langdetect import detect
from supabase import create_client

app = Flask(__name__)
CORS(app)

# Load environment variables
OPENROUTER_KEY = os.environ["OPENROUTER_KEY"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Style prompts
STYLE_PROMPTS = {
    "cinematic": "cinematic, film still, 35mm, dramatic lighting",
    "anime": "anime style, Studio Ghibli, detailed background",
    "pixar": "3D render, Pixar animation style, soft lighting",
    "realistic": "photorealistic, 85mm portrait, natural lighting",
    "oil": "oil painting, Van Gogh style, visible brush strokes"
}

def verify_token(token):
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except:
        return None

def get_mp3_duration(mp3_path):
    """Get MP3 duration using ffprobe (preinstalled on Render)"""
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "json", mp3_path
    ], capture_output=True, text=True)
    
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])

def get_story_in_language(lyrics):
    try:
        lang = detect(lyrics)
    except:
        lang = "en"
    
    prompt = f"""
    Analyze these song lyrics. IMPORTANT: Respond in the same language as the lyrics.

    Lyrics:
    {lyrics}

    Instructions:
    1. Meaning: Explain emotional core.
    2. Storyline: Write a short narrative (5 sentences).
    3. Character: Describe main character (appearance, mood).

    Format:
    Meaning: [text]
    Storyline: [text]
    Character: [text]
    """
    
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    
    output = resp.json()["choices"][0]["message"]["content"]
    return output, lang

def parse_llm_output(output):
    lines = output.split('\n')
    meaning = storyline = character = ""
    current = None
    
    for line in lines:
        if line.startswith("Meaning:"):
            current = "meaning"
            meaning = line.replace("Meaning:", "").strip()
        elif line.startswith("Storyline:"):
            current = "storyline"
            storyline = line.replace("Storyline:", "").strip()
        elif line.startswith("Character:"):
            current = "character"
            character = line.replace("Character:", "").strip()
        elif current == "meaning":
            meaning += " " + line.strip()
        elif current == "storyline":
            storyline += " " + line.strip()
        elif current == "character":
            character += " " + line.strip()
    
    if not character:
        character = "mysterious person, cinematic style"
    if not storyline:
        storyline = "A emotional journey through the lyrics."
    
    scenes = [s.strip() for s in storyline.split('.') if s.strip()][:6]
    return meaning, scenes, character

def generate_image(prompt, seed=42):
    output = replicate.run(
        "stabilityai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712102b35068c41f509e5c31e15550e2c6",
        input={
            "prompt": prompt,
            "negative_prompt": "deformed, blurry, text, watermark, cartoon",
            "seed": seed,
            "num_inference_steps": 4,
            "guidance_scale": 1.0
        }
    )
    return output[0]

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Auth
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header.split(" ")[1]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid token"}), 401

        # Get data
        lyrics = request.form.get('lyrics', '')
        mp3_file = request.files.get('song')
        style = request.form.get('style', 'cinematic')
        
        if not lyrics or not mp3_file:
            return jsonify({"error": "Lyrics and MP3 required"}), 400

        # Save MP3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            mp3_file.save(tmp_mp3.name)
            mp3_path = tmp_mp3.name

        # Get duration (using ffprobe)
        duration_sec = get_mp3_duration(mp3_path)
        num_scenes = min(6, max(3, int(duration_sec // 30)))

        # Get story & language
        llm_output, lang = get_story_in_language(lyrics)
        meaning, scenes, character_desc = parse_llm_output(llm_output)
        if len(scenes) < num_scenes:
            scenes = (scenes * (num_scenes // len(scenes) + 1))[:num_scenes]

        # Add cultural hint
        culture_hint = CULTURE_HINTS.get(lang, "cinematic, global style")

        # Generate images
        image_paths = []
        for i, scene in enumerate(scenes[:num_scenes]):
            full_prompt = f"{character_desc}, {scene}, {culture_hint}, {STYLE_PROMPTS[style]}, 4k, film still"
            img_url = generate_image(full_prompt, seed=42)
            
            img_resp = requests.get(img_url)
            img_path = f"/tmp/scene_{i}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_resp.content)
            image_paths.append(img_path)

        # Create video clips (with zoom effect)
        clip_paths = []
        scene_duration = duration_sec / len(image_paths)
        for i, img_path in enumerate(image_paths):
            clip_path = f"/tmp/clip_{i}.mp4"
            subprocess.run([
                "ffmpeg", "-loop", "1", "-i", img_path,
                "-c:v", "libx264", "-t", str(scene_duration),
                "-vf", "zoompan=z='min(zoom+0.001,1.2)':d=120",  # subtle zoom
                "-pix_fmt", "yuv420p", "-y", clip_path
            ], check=True)
            clip_paths.append(clip_path)

        # Concat clips
        list_file = "/tmp/list.txt"
        with open(list_file, "w") as f:
            for clip in clip_paths:
                f.write(f"file '{clip}'\n")

        video_no_audio = "/tmp/video_no_audio.mp4"
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c:v", "libx264", "-y", video_no_audio
        ], check=True)

        # Add user audio
        final_video = "/tmp/final_video.mp4"
        subprocess.run([
            "ffmpeg", "-i", video_no_audio, "-i", mp3_path,
            "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", "-y", final_video
        ], check=True)

        # Upload to Supabase Storage
        job_id = f"{user_id}_{int(duration_sec)}"
        with open(final_video, "rb") as f:
            supabase.storage.from_("videos").upload(
                f"{user_id}/{job_id}.mp4",
                f.read(),
                file_options={"content-type": "video/mp4"}
            )

        video_url = supabase.storage.from_("videos").get_public_url(f"{user_id}/{job_id}.mp4")

        # Save to DB
        supabase.table("videos").insert({
            "user_id": user_id,
            "lyrics_preview": lyrics[:100],
            "duration_sec": duration_sec,
            "video_url": video_url,
            "language": lang,
            "style": style
        }).execute()

        return jsonify({
            "video_url": video_url,
            "language": lang,
            "style": style,
            "duration_sec": duration_sec
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)