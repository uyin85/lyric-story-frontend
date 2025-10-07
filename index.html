<!DOCTYPE html>
<html>
<head>
  <title>Lyric Story Video</title>
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 20px auto; line-height: 1.6; }
    .section { background: #fff; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    input, textarea, select, button { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; }
    button { background: #3b82f6; color: white; border: none; cursor: pointer; font-weight: bold; }
    button:hover { background: #2563eb; }
    .hidden { display: none; }
    .video-item { border: 1px solid #eee; padding: 15px; margin: 10px 0; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>Lyric Story Video</h1>

  <!-- Login -->
  <div id="login" class="section">
    <h2>Sign In</h2>
    <input type="email" id="email" placeholder="Email" required>
    <input type="password" id="password" placeholder="Password" required>
    <button onclick="login()">Login</button>
    <button onclick="signup()">Sign Up</button>
    <p id="msg"></p>
  </div>

  <!-- Dashboard -->
  <div id="dashboard" class="section hidden">
    <h2>Create Video</h2>
    <textarea id="lyrics" placeholder="Paste lyrics here..." rows="4"></textarea>
    <input type="file" id="mp3" accept=".mp3" required>
    <select id="style">
      <option value="cinematic">Cinematic</option>
      <option value="anime">Anime</option>
      <option value="pixar">Pixar</option>
      <option value="realistic">Realistic</option>
    </select>
    <button onclick="generate()">Generate Video</button>
    <p id="status"></p>

    <h2>My Videos</h2>
    <div id="videos">Loading...</div>
    <button onclick="logout()" style="background:#ef4444;">Logout</button>
  </div>

  <script>
    // ===== CONFIGURE THESE =====
    const SUPABASE_URL = 'https://zxepddzcdsovshhdezea.supabase.co';
    const SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp4ZXBkZHpjZHNvdnNoaGRlemVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk4MDE2MTMsImV4cCI6MjA3NTM3NzYxM30.yI6kVkBIZgdIHov09hFwDNoGCmqiWVxDmFx7tg93Gak';
    const BACKEND_URL = 'https://lyric-story-frontend.onrender.com';
    // ==========================

    const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

    async function login() {
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      
      if (!email || !password) {
        document.getElementById('msg').innerText = 'Fill email and password';
        return;
      }

      try {
        const {  } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          document.getElementById('msg').innerText = error.message;
        } else {
          init();
        }
      } catch (err) {
        document.getElementById('msg').innerText = 'Error: ' + err.message;
      }
    }

    async function signup() {
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      
      if (!email || !password) {
        document.getElementById('msg').innerText = 'Fill email and password';
        return;
      }

      try {
        const {  } = await supabase.auth.signUp({ email, password });
        if (error) {
          document.getElementById('msg').innerText = error.message;
        } else {
          document.getElementById('msg').innerText = '✅ Check your email to confirm!';
        }
      } catch (err) {
        document.getElementById('msg').innerText = 'Error: ' + err.message;
      }
    }

    async function logout() {
      await supabase.auth.signOut();
      document.getElementById('login').classList.remove('hidden');
      document.getElementById('dashboard').classList.add('hidden');
    }

    async function generate() {
      const lyrics = document.getElementById('lyrics').value;
      const mp3 = document.getElementById('mp3').files[0];
      const style = document.getElementById('style').value;
      if (!lyrics || !mp3) return alert('Fill all fields');

      const formData = new FormData();
      formData.append('lyrics', lyrics);
      formData.append('song', mp3);
      formData.append('style', style);

      const {  { session } } = await supabase.auth.getSession();
      document.getElementById('status').innerText = 'Processing... (1-2 min)';

      try {
        const res = await fetch(BACKEND_URL + '/generate', {
          method: 'POST',
          headers: { Authorization: 'Bearer ' + session.access_token },
          body: formData
        });

        const data = await res.json();
        if (res.ok) {
          document.getElementById('status').innerText = '✅ Done! Video in "My Videos"';
          loadVideos();
        } else {
          document.getElementById('status').innerText = '❌ ' + (data.error || 'Error');
        }
      } catch (err) {
        document.getElementById('status').innerText = 'Network error: ' + err.message;
      }
    }

    async function loadVideos() {
      const {  { user } } = await supabase.auth.getUser();
      if (!user) return;
      
      const {  } = await supabase
        .from('videos')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      document.getElementById('videos').innerHTML = data?.map(v => 
        `<div class="video-item">
          <b>${v.lyrics_preview.substring(0, 40)}...</b> (${v.language})<br>
          <a href="${v.video_url}" download>Download Video</a>
        </div>`
      ).join('') || 'No videos';
    }

    async function init() {
      const {  { user } } = await supabase.auth.getUser();
      if (user) {
        document.getElementById('login').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
        loadVideos();
      }
    }

    init();
  </script>
</body>
</html>