import os
import random
import requests
import telebot
from telebot import types
from textblob import TextBlob
from bs4 import BeautifulSoup as SOUP

# --- Credentials & Configurations ---
# Replace with your actual credentials or load them securely via environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "YOUR_LASTFM_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
USER_AGENT = "Dataquest"

# Helper to fetch data from Last.fm API
def lastfm_get(url, payload):
    headers = {"user-agent": USER_AGENT}
    response = requests.get(url, headers=headers, params=payload)
    return response

# --- IMDb Movie Scraper Helpers ---
def get_image(image):
    try:
        return image.get("loadlate")
    except:
        return "NA"

def get_synopsis(movie):
    try:
        return movie.find_all("p", {"class": "text-muted"})[1].getText()
    except:
        return "NA"

def get_movie_title(header):
    try:
        return header[0].find("a").getText()
    except:
        return "NA"

# Lists to temporarily store movie details
movie_title_arr = []
movie_synopsis_arr = []
image_url_arr = []

def fetch_movies(emotion):
    global movie_title_arr, movie_synopsis_arr, image_url_arr
    movie_title_arr.clear()
    movie_synopsis_arr.clear()
    image_url_arr.clear()

    if emotion == "sad":
        urlhere = "http://www.imdb.com/search/title?genres=drama&title_type=feature&sort=moviemeter,asc"
    else:
        urlhere = "http://www.imdb.com/search/title?genres=comedy&title_type=feature&sort=moviemeter,asc"

    try:
        response = requests.get(urlhere)
        soup = SOUP(response.text, "html.parser")
        movies_list = soup.find_all("div", {"class": "lister-item mode-advanced"})
        for movie in movies_list:
            header = movie.find_all("h3", {"class": "lister-item-header"})
            image_div = movie.find("div", {"class": "lister-item-image float-left"})
            image = image_div.find("img", "loadlate") if image_div else None

            movie_title_arr.append(get_movie_title(header))
            movie_synopsis_arr.append(get_synopsis(movie))
            image_url_arr.append(get_image(image))
    except Exception as e:
        print(f"Error fetching movies from IMDb: {e}")

# --- Bot Handlers & Logic ---
@bot.message_handler(commands=["start", "help"])
def greet_user(message):
    sentences = [
        "Hello there! Welcome to Easy Peasy Chatbot. I'm here to help you find the perfect music and movies to suit your mood. 😊",
        "Hi! I am Easy Peasy Chatbot, your personal entertainment assistant. Let's get started on finding you some great music and movies. 🎵🎬",
        "Greetings! I am Easy Peasy Chatbot and I am here to help you discover new music and movies that you'll love. Let's get started! 🎶🎥",
    ]
    sentence = random.choice(sentences)
    bot.send_message(message.chat.id, sentence)

    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="Ok. Let's go!!!", callback_data="continue")
    keyboard.add(button)

    bot.send_message(
        message.chat.id,
        "Please press the button below to continue.",
        reply_markup=keyboard,
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "continue":
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        keyboard.add("Sunny and warm", "Rainy and humid", "Cloudy and cool", "Cold and snowy")
        question = "What is the weather like today?"
        bot.send_message(call.message.chat.id, question, reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ["Sunny and warm", "Rainy and humid", "Cloudy and cool", "Cold and snowy"])
def weather(message):
    reply = message.text
    blob = TextBlob(reply)
    emo = []

    positive_responses = ["It's a beautiful day!", "The weather is perfect.", "Wow, that's nice!"]
    negative_responses = ["Such a gloomy day.", "I see, the weather is not great.", "Ah, really!?"]

    if blob.polarity > 0:
        bot.send_message(message.chat.id, random.choice(positive_responses))
        emo.append("P")
    else:
        bot.send_message(message.chat.id, random.choice(negative_responses))
        emo.append("N")

    questions = [
        "Hey, how has your day been?",
        "How's the day been so far?",
        "How has life been treating you this fine day?"
    ]
    bot.send_message(message.chat.id, random.choice(questions))
    bot.register_next_step_handler(message, mood, emo)

def mood(message, emo):
    reply = message.text
    blob = TextBlob(reply)

    positive_responses = ["That's good to hear!", "Nice, good for you!", "Look at you living life :)", "Let's rock!!!"]
    negative_responses = ["I'm sorry to hear that.", "Hopefully everything will get better.", "You'll get through this.", "Let me light your day up :)"]

    if blob.polarity > 0:
        bot.send_message(message.chat.id, random.choice(positive_responses))
        emo.append("P")
    else:
        bot.send_message(message.chat.id, random.choice(negative_responses))
        emo.append("N")

    bot.send_message(message.chat.id, "Now, how about some music to suit your mood? Y/N")
    bot.register_next_step_handler(message, music, emo)

def music(message, emo):
    choice = message.text.strip().lower()
    dominant_emo = max(emo, key=emo.count)
    recommended_indices = []

    if choice == "y":
        bot.send_message(message.chat.id, "Who is your favorite artist? (Or type 'none')")
        bot.register_next_step_handler(message, artist_recommendation, dominant_emo, recommended_indices)
    else:
        bot.send_message(message.chat.id, "Okay, no music. How about some movies to suit your mood? Y/N")
        bot.register_next_step_handler(message, movie_recommendation, dominant_emo, recommended_indices)

def artist_recommendation(message, dominant_emo, recommended_indices):
    artist = message.text.strip()

    if artist.lower() == "none":
        tag = random.choice(["happy", "pop", "rock", "dance"]) if dominant_emo == "P" else random.choice(["sad", "blues", "indie", "metal"])
        url = f"http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={tag}&api_key={LASTFM_API_KEY}&format=json"
        r = lastfm_get(url, {"method": "tag.gettoptracks"})
    else:
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={artist}&api_key={LASTFM_API_KEY}&format=json"
        r = lastfm_get(url, {"method": "artist.gettoptracks"})

    if r.status_code == 200:
        res = r.json()
        track_key = "tracks" if artist.lower() == "none" else "toptracks"

        try:
            tracks_list = res[track_key]["track"]
            available_tracks = len(tracks_list)
            if available_tracks > 0:
                for _ in range(min(5, available_tracks)):
                    j = random.randint(0, min(49, available_tracks - 1))
                    while j in recommended_indices:
                        j = random.randint(0, min(49, available_tracks - 1))
                    recommended_indices.append(j)
                    bot.send_message(message.chat.id, f"{tracks_list[j]['name']} by {tracks_list[j]['artist']['name']} - {tracks_list[j]['url']}")
            else:
                bot.send_message(message.chat.id, "Could not find any tracks.")
        except Exception as e:
            bot.send_message(message.chat.id, "Error reading song recommendations.")
    else:
        bot.send_message(message.chat.id, "Could not fetch songs from Last.fm at this moment.")

    bot.send_message(message.chat.id, "Are you satisfied with the music recommendations? Y/N")
    bot.register_next_step_handler(message, music_feedback, dominant_emo, recommended_indices)

def music_feedback(message, dominant_emo, recommended_indices):
    choice = message.text.strip().lower()
    if choice != "y":
        bot.send_message(message.chat.id, "Do you want to continue or quit? C/Q")
        bot.register_next_step_handler(message, music_continue, dominant_emo, recommended_indices)
    else:
        bot.send_message(message.chat.id, "I am glad you enjoyed the music!")
        bot.send_message(message.chat.id, "Now, how about some movies to suit your mood? Y/N")
        bot.register_next_step_handler(message, movie_recommendation, dominant_emo, recommended_indices)

def music_continue(message, dominant_emo, recommended_indices):
    choice = message.text.strip().lower()
    if choice == "q":
        bot.send_message(message.chat.id, "Okay, let's move on. How about some movies to suit your mood? Y/N")
        bot.register_next_step_handler(message, movie_recommendation, dominant_emo, recommended_indices)
    else:
        bot.send_message(message.chat.id, "Who is your favorite artist? (Or type 'none')")
        bot.register_next_step_handler(message, artist_recommendation, dominant_emo, recommended_indices)

def movie_recommendation(message, dominant_emo, recommended_indices):
    choice = message.text.strip().lower()
    if choice == "y":
        bot.send_message(message.chat.id, "Searching movies for you on IMDb...")
        fetch_movies("happy" if dominant_emo == "P" else "sad")

        if movie_title_arr:
            selected_movies = []
            for _ in range(min(3, len(movie_title_arr))):
                j = random.randint(0, len(movie_title_arr) - 1)
                while j in selected_movies:
                    j = random.randint(0, len(movie_title_arr) - 1)
                selected_movies.append(j)
                bot.send_message(message.chat.id, f"{movie_title_arr[j]}\n\n{movie_synopsis_arr[j]}\n\nPoster: {image_url_arr[j]}")

            bot.send_message(message.chat.id, "Are you satisfied with the movie recommendations? Y/N")
            bot.register_next_step_handler(message, movie_feedback, dominant_emo, selected_movies)
        else:
            bot.send_message(message.chat.id, "Failed to parse movies. Let's head straight to feedback.")
            bot.send_message(message.chat.id, "What do you think about my performance?")
            bot.register_next_step_handler(message, user_feedback)
    else:
        bot.send_message(message.chat.id, "Okay, no movies. What do you think about my performance?")
        bot.register_next_step_handler(message, user_feedback)

def movie_feedback(message, dominant_emo, selected_movies):
    choice = message.text.strip().lower()
    if choice != "y":
        bot.send_message(message.chat.id, "Do you want to continue or quit? C/Q")
        bot.register_next_step_handler(message, movie_continue, dominant_emo, selected_movies)
    else:
        bot.send_message(message.chat.id, "I am glad you enjoyed the movie recommendations!")
        bot.send_message(message.chat.id, "What do you think about my performance?")
        bot.register_next_step_handler(message, user_feedback)

def movie_continue(message, dominant_emo, selected_movies):
    choice = message.text.strip().lower()
    if choice == "c" and movie_title_arr:
        selected = []
        for _ in range(min(3, len(movie_title_arr))):
            j = random.randint(0, len(movie_title_arr) - 1)
            while j in selected:
                j = random.randint(0, len(movie_title_arr) - 1)
            selected.append(j)
            bot.send_message(message.chat.id, f"{movie_title_arr[j]}\n\n{movie_synopsis_arr[j]}\n\nPoster: {image_url_arr[j]}")
        bot.send_message(message.chat.id, "Are you satisfied with the movie recommendations? Y/N")
        bot.register_next_step_handler(message, movie_feedback, dominant_emo, selected)
    else:
        bot.send_message(message.chat.id, "No more movies. What do you think about my performance?")
        bot.register_next_step_handler(message, user_feedback)

def user_feedback(message):
    reply = message.text
    blob = TextBlob(reply)

    positive_responses = ["Hehehe thanks! xD", "OMG THANKS!!", "You're making me blush!!"]
    negative_responses = ["I see, thanks for your feedback.", "Aww, I'll do better next time!", "Thanks for letting me know!"]

    if blob.polarity > 0:
        bot.send_message(message.chat.id, random.choice(positive_responses))
    else:
        bot.send_message(message.chat.id, random.choice(negative_responses))

    bot.send_message(message.chat.id, "Thank you for chatting with me. I hope you enjoyed it. See ya! 😊")

# --- Start Polling ---
if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
