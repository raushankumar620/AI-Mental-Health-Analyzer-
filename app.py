# Required Libraries
import os
import openai
import requests
import pyttsx3
import threading
import speech_recognition as sr
from flask import Flask, request, jsonify, render_template
from transformers import pipeline
import sqlite3
import webbrowser

# Initialize Flask App
app = Flask(__name__)

# Initialize Text-to-Speech Engine
def init_tts_engine():
    engine = pyttsx3.init()
    return engine

engine = init_tts_engine()

# Function for Speech-to-Text
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print("You said: " + text)
            return text
        except sr.UnknownValueError:
            print("Sorry, I did not get that.")
            return None
        except sr.RequestError:
            print("Speech Recognition service is down.")
            return None

# Function for Text-to-Speech
def speak(text):
    def tts_run():
        engine.say(text)
        engine.runAndWait()

    tts_thread = threading.Thread(target=tts_run)
    tts_thread.start()

# API Integration Examples
def sentiment_analysis_huggingface(text):
    try:
        sentiment_pipeline = pipeline("sentiment-analysis")
        result = sentiment_pipeline(text)
        return result
    except Exception as e:
        return str(e)

def weather_info(city):
    api_key = "de7b9fc5e928f4bde1818e4febd0b148"
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"]
        }
    else:
        return {"error": "City not found"}

def chatgpt_response(prompt):
    openai.api_key = "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"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# Database Functions
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY, user_input TEXT, response TEXT)")
    conn.commit()
    conn.close()

def log_interaction(user_input, response):
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO interactions (user_input, response) VALUES (?, ?)", (user_input, response))
    conn.commit()
    conn.close()

# Flask Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        if user_input:
            sentiment = sentiment_analysis_huggingface(user_input)
            if sentiment[0]["label"] == "NEGATIVE":
                response_text = "I'm sorry to hear that. A devotional song has been provided for you."
                song_url = "https://youtu.be/VgdAcENXy84?si=twIxLjyPZd6Nwdox"
                speak(response_text)
                webbrowser.open(song_url)
            else:
                response_text = "Great to hear! A beautiful Hindi song has been provided for you."
                song_url = ""
                speak(response_text)
                webbrowser.open(song_url)

            log_interaction(user_input, response_text)
            return render_template("index.html", user_input=user_input, response=response_text)
    return render_template("index.html")

@app.route("/weather", methods=["POST"])
def get_weather():
    city = request.form.get("city")
    if city:
        weather = weather_info(city)
        if "error" in weather:
            weather_text = weather["error"]
        else:
            weather_text = f"Temperature: {weather['temperature']}°C, Description: {weather['description']}"
        return render_template("index.html", weather=weather_text, user_input=None, response=None, chat_response=None)
    return render_template("index.html", weather="City not provided", user_input=None, response=None, chat_response=None)

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.form.get("prompt")
    if prompt:
        try:
            response = chatgpt_response(prompt)
            return render_template("index.html", chat_response=response, user_input=None, response=None, weather=None)
        except Exception as e:
            return render_template("index.html", chat_response=f"Error: {str(e)}", user_input=None, response=None, weather=None)
    return render_template("index.html", chat_response="Please enter a valid prompt.", user_input=None, response=None, weather=None)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
