import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import os
import time
import tempfile
from PIL import Image
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from google.generativeai import upload_file, get_file
from PyPDF2 import PdfReader
from docx import Document
import whisper
from gtts import gTTS
from pydub import AudioSegment
import base64
from fpdf import FPDF
import google.generativeai as genai
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from pymongo import MongoClient

# --- Load Environment ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- MongoDB Setup ---
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["multimodal_chat_db"]
collection = db["chat_responses"]

def save_message_to_db(role, text, timestamp):
    try:
        collection.insert_one({"role": role, "text": text, "timestamp": timestamp})
    except Exception as e:
        st.warning(f"\u26a0\ufe0f Failed to log message to DB: {e}")

# --- Initialize Gemini models ---
chat_model = genai.GenerativeModel("gemini-1.5-flash")
vision_model = genai.GenerativeModel("gemini-2.0-flash-lite")

@st.cache_resource
def initialize_agent():
    return Agent(
        name="Video AI Summarizer",
        model=Gemini(id="gemini-2.0-flash-lite"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_agent = initialize_agent()

# --- Page Config ---
st.set_page_config(page_title="🎛️ Multimodality Chat", layout="wide")

# --- CSS Styling (Slider, Theme, Avatars, Bubbles) ---
st.markdown("""
<style>
.slider-container {
  width: 100%;
  overflow: hidden;
  border-radius: 12px;
  margin-bottom: 20px;
}
.slider-track {
  display: flex;
  width: calc(420px * 10);
  animation: scroll 40s linear infinite;
  position: sticky;
}
.slider-track img {
  width: 400px;
  height: 200px;
  object-fit: cover;
  margin-right: 20px;
  border-radius: 12px;
}
@keyframes scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.chat-container {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  display: inline-block;
  margin-right: 10px;
  border: 2px solid #00bfff;
}
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.chat-bubble {
  border-radius: 18px;
  padding: 12px 16px;
  max-width: 80%;
  line-height: 1.5;
  font-size: 16px;
}
.chat-bubble.user {
  background-color: #e9ecef;
  color: #000;
  margin-left: auto;
  margin-right: 0;
}
.chat-bubble.bot {
  background-color: #d0ebff;
  color: #004085;
  margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# --- Auto-sliding header ---
st.markdown("""
<div class="slider-container">
  <div class="slider-track">
   <img src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1499951360447-b19be8fe80f5?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1472214103451-9374bd1c798e?auto=format&fit=crop&w=400&h=200&q=80" />
   <img src="https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=400&h=200&q=80" />
  </div>
</div>
""", unsafe_allow_html=True)

# (The rest of your chatbot code continues here...)

# --- Title ---
st.title("🎛️ Multimodality Chat")

# --- Sidebar ---
with st.sidebar:
    st.image("https://i.imgur.com/yW2W9SC.png", use_container_width=True)
    st.markdown("## 🎨 Theme & Features")
    theme = st.radio("Choose theme", ["Light", "Dark"], index=0)
    audio_toggle = st.toggle("Enable Text-to-Audio", value=True)

    if st.button("🔁 Reset Chat"):
        st.session_state.chat_history = []
        st.rerun()

# --- Theme switch ---
if theme == "Dark":
    st.markdown("""
        <style>
        body, .stApp { background-color: #0e1117; color: #fafafa; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body, .stApp { background-color: #ffffff; color: #000000; }
        </style>
    """, unsafe_allow_html=True)

# --- Avatars ---
USER_AVATAR_URL = "https://api.dicebear.com/7.x/adventurer-neutral/svg?seed=User123"
BOT_AVATAR_URL = "https://api.dicebear.com/7.x/bottts-neutral/svg?seed=GeminiAI"

# --- Chat State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Display Chat Bubbles ---
for msg in st.session_state.chat_history:
    is_user = msg["role"] == "user"
    avatar_url = USER_AVATAR_URL if is_user else BOT_AVATAR_URL
    role_class = "user" if is_user else "bot"

    st.markdown(f"""
    <div class="chat-container">
        <div class="avatar"><img src="{avatar_url}"></div>
        <div class="chat-bubble {role_class}">{msg["text"]}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Input & Upload ---
user_input = st.chat_input("Type a message or command...")
uploaded_file = st.file_uploader("Upload media", type=["jpg", "jpeg", "png", "bmp", "gif", "pdf", "docx", "txt", "mp3", "wav", "mp4", "mov", "avi"], label_visibility="collapsed")

if user_input or uploaded_file:
    now = datetime.now().strftime("%H:%M")
    user_msg = user_input or f"📎 Uploaded: {uploaded_file.name}"
    st.session_state.chat_history.append({"role": "user", "text": user_msg, "time": now})
    save_message_to_db("user", user_msg, now)  # ✅ Save to DB
    with st.spinner("🤖 Gemini is processing..."):
        try:
            if user_input and "youtube.com" in user_input:
                video_id = user_input.split("v=")[-1]
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                text = " ".join([t["text"] for t in transcript])
                response = chat_model.generate_content(f"Summarize and explain this YouTube video:\n{text}")

            elif uploaded_file and uploaded_file.name.endswith((".pdf", ".docx", ".txt")):
                if uploaded_file.name.endswith(".pdf"):
                    text = " ".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
                elif uploaded_file.name.endswith(".docx"):
                    doc = Document(uploaded_file)
                    text = "\n".join(p.text for p in doc.paragraphs)
                else:
                    text = uploaded_file.read().decode("utf-8")
                response = chat_model.generate_content(f"Summarize this document:\n{text}")

            elif uploaded_file and uploaded_file.type.startswith("image/"):
                image = Image.open(uploaded_file)
                response = vision_model.generate_content([user_input or "Describe this image", image])

            elif uploaded_file and uploaded_file.type.startswith("audio/"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
                    audio = AudioSegment.from_file(uploaded_file)
                    audio.export(temp.name, format="wav")
                    model = whisper.load_model("base")
                    result = model.transcribe(temp.name)
                    transcript = result["text"]
                    response = chat_model.generate_content(f"Summarize or respond to this transcript:\n{transcript}")

            elif uploaded_file and uploaded_file.name.endswith((".mp4", "mov", "avi")):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
                    temp.write(uploaded_file.read())
                    video_path = temp.name
                uploaded = upload_file(video_path)
                while uploaded.state.name == "PROCESSING":
                    time.sleep(1)
                    uploaded = get_file(uploaded.name)
                response = multimodal_agent.run("Summarize this uploaded video", videos=[uploaded])

            else:
                response = chat_model.generate_content(user_input)

            ai_reply = response.text if hasattr(response, 'text') else response.content
            st.session_state.chat_history.append({"role": "assistant", "text": ai_reply, "time": now})
            save_message_to_db("assistant", ai_reply, now)  # ✅ Save to DB 
            # Audio response
            if audio_toggle:
                tts = gTTS(text=ai_reply, lang='en')
                audio_path = os.path.join(tempfile.gettempdir(), "gemini_reply.mp3")
                tts.save(audio_path)
                st.audio(audio_path)
                with open(audio_path, "rb") as file:
                    audio_bytes = file.read()
                    b64 = base64.b64encode(audio_bytes).decode()
                    download_link = f'<a href="data:audio/mp3;base64,{b64}" download="gemini_reply.mp3">🔊 Download Audio</a>'
                    st.markdown(download_link, unsafe_allow_html=True)

            # # Export chat as PDF
            # if st.button("📄 Export Chat to PDF"):
            #     pdf = FPDF()
            #     pdf.add_page()
            #     pdf.set_font("Arial", size=12)
            #     for m in st.session_state.chat_history:
            #         role = "You" if m["role"] == "user" else "Gemini"
            #         pdf.multi_cell(0, 10, f"{role}: {m['text']}\n")
            #     chat_file = os.path.join(tempfile.gettempdir(), "chat_history.pdf")
            #     pdf.output(chat_file)
            #     with open(chat_file, "rb") as f:
            #         st.download_button("Download Chat PDF", f, file_name="chat_history.pdf")

        except Exception as e:
            error_msg = f"\u274c Error: {str(e)}"
            st.session_state.chat_history.append({"role": "assistant", "text": error_msg, "time": now})
            st.error(error_msg)
            save_message_to_db("assistant", error_msg, now)


# Export chat PDF button outside spinner block
if st.button("📄 Export Chat to PDF"):

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for m in st.session_state.chat_history:
            role = "You" if m["role"] == "user" else "Gemini"
            pdf.multi_cell(0, 10, f"{role}: {m['text']}\n")
        chat_file = os.path.join(tempfile.gettempdir(), "chat_history.pdf")
        pdf.output(chat_file)
        with open(chat_file, "rb") as f:
            st.download_button("Download Chat PDF", f, file_name="chat_history.pdf")
    except Exception as e:
        st.error(f"\u274c Failed to export chat: {e}")

           
