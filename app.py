import datetime
import requests
from flask import Flask, render_template, request, jsonify
import os
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai
import threading
import subprocess
import re
from serpapi import GoogleSearch

app = Flask(__name__)

# Set your API keys
os.environ["GOOGLE_API_KEY"] = "Enter Your apikey"
os.environ["OPENWEATHERMAP_API_KEY"] = "Enter Your apikey"
os.environ["ALPHA_VANTAGE_API_KEY"] = "QHWOM39HU20P7HL7"
os.environ["SERPAPI_API_KEY"] = "Enter Your apikey"
os.environ["TMDB_API_KEY"] = "Enter Your apikey"

# Configure the SDK
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    safety_settings=safety_settings,
    generation_config=generation_config,
)

# Initialize the TTS engine
engine = pyttsx3.init()
# Set properties (optional)
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

# Start a chat session
chat_session = model.start_chat(history=[])

# Initialize the speech recognizer
recognizer = sr.Recognizer()

# Flag to track whether the engine is speaking
is_speaking = False
stop_flag = False

def speak(text):
    global is_speaking, stop_flag
    is_speaking = True
    stop_flag = False

    def run_speak():
        for word in text.split():
            if stop_flag:
                break
            engine.say(word)
            engine.runAndWait()
        is_speaking = False

    threading.Thread(target=run_speak).start()

def get_weather(city):
    api_key = os.environ["OPENWEATHERMAP_API_KEY"]
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}q={city}&appid={api_key}&units=metric"

    response = requests.get(complete_url)
    data = response.json()

    if data["cod"] != "404":
        main = data["main"]
        weather = data["weather"][0]
        wind = data["wind"]
        temperature = main["temp"]
        pressure = main["pressure"]
        humidity = main["humidity"]
        description = weather["description"]
        wind_speed = wind["speed"]

        response_text = (
            f"Weather details for {city}:\n"
            f"Temperature: {temperature}°C\n"
            f"Humidity: {humidity}%\n"
            f"Pressure: {pressure} hPa\n"
            f"Weather: {description}\n"
            f"Wind Speed: {wind_speed} m/s"
        )
    else:
        response_text = "City not found."

    return response_text

def get_stock_price(symbol):
    api_key = os.environ["ALPHA_VANTAGE_API_KEY"]
    base_url = "https://www.alphavantage.co/query?"
    complete_url = f"{base_url}function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}"

    response = requests.get(complete_url)
    data = response.json()

    try:
        latest_time = list(data["Time Series (5min)"].keys())[0]
        latest_data = data["Time Series (5min)"][latest_time]
        price = latest_data["1. open"]
        response_text = f"The latest stock price for {symbol} is ${price}."
    except KeyError:
        response_text = "Stock symbol not found or API limit reached."

    return response_text

def get_google_image(query):
    params = {
        "q": query,
        "tbm": "isch",
        "ijn": "0",
        "api_key": os.environ["SERPAPI_API_KEY"]
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    image_url = results["images_results"][0]["thumbnail"]
    return image_url

def get_movie_info(movie_title):
    api_key = os.environ["TMDB_API_KEY"]
    base_url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": api_key,
        "query": movie_title
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if data['results']:
        movie = data['results'][0]
        title = movie['title']
        overview = movie['overview']
        release_date = movie['release_date']
        rating = movie['vote_average']
        response_text = (
            f"Title: {title}\n"
            f"Overview: {overview}\n"
            f"Release Date: {release_date}\n"
            f"Rating: {rating}/10"
        )
    else:
        response_text = "Movie not found."
    return response_text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    global is_speaking, stop_flag
    user_input = request.json.get('user_input', '').upper()
    response_text = ""
    image_url = ""

    if "SPARK" in user_input:
        response_text = "Hello Jagadeesh, how can I assist you?"
    elif "HOW ARE YOU" in user_input:
        response_text = "I'm just a program, so I don't have feelings, but I'm here to help you!"
    elif "EXIT" in user_input:
        if is_speaking:
            print("Stopping the engine...")
            stop_flag = True
        response_text = "Voice assistance stopped."
    elif "TIME" in user_input:
        now = datetime.datetime.now()
        time = now.strftime("%I:%M %p")  # 12-hour format with AM/PM
        response_text = f"The current time is {time}."
    elif "DATE" in user_input:
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        response_text = f"Today's date is {date}."
    elif "WEATHER" in user_input:
        match = re.search(r'\b(?:WEATHER\sIN\s|WEATHER\s)(\w+)\b', user_input, re.IGNORECASE)
        city = match.group(1).title() if match else "London"  # Default city
        response_text = get_weather(city)
    elif "STOCK PRICE" in user_input:
        match = re.search(r'\b(?:STOCK PRICE OF\s|STOCK PRICE\s)(\w+)\b', user_input, re.IGNORECASE)
        symbol = match.group(1).upper() if match else "AAPL"  # Default stock symbol
        response_text = get_stock_price(symbol)
    elif "MOVIE" in user_input:
        match = re.search(r'\b(?:MOVIE\s)(.+)', user_input, re.IGNORECASE)
        movie_title = match.group(1).title() if match else None
        response_text = get_movie_info(movie_title) if movie_title else "Please provide a movie title."
    else:
        try:
            response = chat_session.send_message(user_input)
            response_text = response.text
            image_url = get_google_image(user_input)  # Fetch image based on user query
        except Exception as e:
            response_text = f"An error occurred: {str(e)}"

    if not is_speaking and "EXIT" not in user_input:
        speak(response_text)

    print("Response Text:", response_text)

    return jsonify({'response': response_text, 'image_url': image_url})

@app.route('/open_notepad', methods=['POST'])
def open_notepad():
    try:
        subprocess.Popen(['notepad.exe'])
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
