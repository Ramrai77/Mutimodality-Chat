Multimodality Chat Application (Powered by Google Gemini API)
Project Overview

Multimodality Chat is an advanced AI-powered Streamlit application built using the Google Gemini API.
It supports text, image, document, audio, video, and YouTube-based interactions in a single unified chat interface.

All user and AI conversations are stored persistently in MongoDB, enabling chat history tracking and future analysis.

This project showcases real-world usage of Google Gemini multimodal models, backend database integration, and scalable Python application development.

🚀Key Features

💬 Conversational AI using Google Gemini API

🖼 Image understanding with Gemini Vision

📄 PDF / DOCX / TXT document summarization

▶️ YouTube video transcript summarization

🎧 Audio upload → Speech-to-Text (Whisper)

🎥 Video upload → AI-based video summarization

🔊 Text-to-Speech audio responses

🗂 Chat export as PDF

🗄 MongoDB chat history storage

🎨 Light / Dark theme toggle

👤 User & AI avatars with styled chat bubbles

🛠️ Tech Stack
🔹 Programming & Framework

Python

Streamlit

🔹 AI & APIs

Google Gemini API

gemini-1.5-flash

gemini-2.0-flash-lite

Phi Agent Framework

Whisper (Speech-to-Text)

gTTS (Text-to-Speech)

🔹 File & Media Processing

PIL (Images)

PyPDF2 (PDF)

python-docx (DOCX)

youtube-transcript-api

pydub (Audio)

🔹 Database

MongoDB

PyMongo

🗄️ Database Design (MongoDB)

Database Name

multimodal_chat_db


Collection

chat_responses


Stored Fields

role (user / assistant)

text (message content)

timestamp (message time)

Install Dependencies
pip install -r requirements.txt

Configure Google Gemini API & MongoDB

Create a .env file:

GOOGLE_API_KEY=your_google_gemini_api_key
MONGO_URI=your_mongodb_connection_string

Run Application
streamlit run app.py

📂 Project Structure
Multimodality-Chat/
├── app.py
├── README.md
├── requirements.txt
├── .env
