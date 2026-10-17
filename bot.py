# ==============================================================================
# PART 1: PREPARATION & INITIALIZATION
# ==============================================================================

import json
import os
import random
import re
from bs4 import BeautifulSoup as SOUP
from dotenv import load_dotenv
import requests
import requests as HTTP
import telebot
from telebot import types
from textblob import TextBlob

# Ensure TextBlob corpora is available
try:
    import nltk

    nltk.download("punkt", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)
    nltk.download("brown", quiet=True)
except Exception:
    pass

load_dotenv()

BOT_TOKEN = os.getenv(
    "BOT_TOKEN", "6210560812:AAHH6M5daoJKYqA1PtekQN_vKQ5PmsZTyVk"
)
bot = telebot.TeleBot(BOT_TOKEN)

API_KEY = os.getenv("LASTFM_API_KEY", "7bc65c1d5adf30658bff0b4a827e7446")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
headers = {"user-agent": USER_AGENT}


def lastfm_get(url: str, payload: dict) -> requests.Response:
    return requests.get(url, headers=headers, params=payload)


def getImage(image):
    try:
        if not image:
            return "NA"
        return image.get("src") or image.get("loadlate") or "NA"
    except Exception:
        return "NA"


def getsynopsys(movie):
    try:
        syn = movie.find(
            ["div", "p", "span"],
            class_=[
                "ipc-html-content-inner-div",
                "ipc-overflowText--lineClamp",
                "text-muted",
            ],
        )
        if syn:
            return syn.getText().strip()
        return "Check IMDb link for full plot details."
    except Exception:
        return "Check IMDb link for full plot details."


def getMovieTitle(header):
    try:
        if not header:
            return "Unknown Movie"
        tag = header[0] if isinstance(header, list) else header
        return re.sub(r"^\d+\.\s*", "", tag.getText().strip())
    except Exception:
        return "Unknown Movie"


movie_title_arr = []
movie_synopsis_arr = []
image_url_arr = []


def main(emotion):
    global movie_title_arr, movie_synopsis_arr, image_url_arr
    movie_title_arr.clear()
    movie_synopsis_arr.clear()
    image_url_arr.clear()

    genre = "drama" if emotion == "sad" else "comedy"
    urlhere = (
        f"https://www.imdb.com/search/title/?genres={genre}&title_type=feature"
    )
    headers_browser = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = HTTP.get(urlhere, headers=headers_browser, timeout=10)
        soup = SOUP(response.text, "html.parser")
        items = soup.find_all(
            ["li", "div"],
            class_=[
                "ipc-metadata-list-summary-item",
                "lister-item mode-advanced",
            ],
        )

        for item in items[:15]:
            link_tag = item.find("a", href=lambda h: h and "/title/tt" in h)
            if link_tag and link_tag.get("href"):
                raw_href = link_tag["href"].split("?")[0]
                movie_link = f"https://www.imdb.com{raw_href}"
                header = item.find(
                    ["h3", "a"],
                    class_=["ipc-title__text", "lister-item-header"],
                )
                title = getMovieTitle(header if header else link_tag)
                synopsis = getsynopsys(item)

                if title and movie_link not in image_url_arr:
                    movie_title_arr.append(title)
                    movie_synopsis_arr.append(synopsis)
                    image_url_arr.append(movie_link)
    except Exception as e:
        print(f"Error IMDb: {e}")

    # Fallback with real working IMDb URLs if blocked
    if not movie_title_arr:
        if emotion == "sad":
            movie_title_arr.extend(
                ["The Pursuit of Happyness", "Forrest Gump", "Good Will Hunting"]
            )
            movie_synopsis_arr.extend([
                "A struggling salesman takes custody of his son.",
                "The history of the US through an Alabama man's eyes.",
                "A janitor at M.I.T. has a gift for mathematics.",
            ])
            image_url_arr.extend([
                "https://www.imdb.com/title/tt0454921/",
                "https://www.imdb.com/title/tt0109830/",
                "https://www.imdb.com/title/tt0119217/",
            ])
        else:
            movie_title_arr.extend(
                ["About Time", "The Grand Budapest Hotel", "Soul"]
            )
            movie_synopsis_arr.extend([
                "Tim discovers he can travel in time and change his life.",
                "Adventures of a legendary concierge at a famous hotel.",
                "A jazz musician discovers what it really means to have soul.",
            ])
            image_url_arr.extend([
                "https://www.imdb.com/title/tt2194499/",
                "https://www.imdb.com/title/tt2278388/",
                "https://www.imdb.com/title/tt2948372/",
            ])


# ==============================================================================
# PART 2: STRICT STEP-BY-STEP CONVERSATION FLOW
# ==============================================================================


# 1. Start & Greeting
@bot.message_handler(commands=["start", "help"])
def greet_user(message):
    sentences = [
        (
            "Hello there! Welcome to Easy Peasy Chatbot. I'm here to help you"
            " find the perfect music and movies to suit your mood. 😊"
        ),
        (
            "Hi! I am Easy Peasy Chatbot, your personal entertainment"
            " assistant. Let's get started on finding you some great music and"
            " movies. 🎵🎬"
        ),
        (
            "Greetings! I am Easy Peasy Chatbot and I am here to help you"
            " discover new music and movies that you'll love. Let's get"
            " started! 🎶🎥"
        ),
    ]
    bot.send_message(message.chat.id, random.choice(sentences))

    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(
        text="Ok. Let's go!!!", callback_data="start_flow"
    )
    keyboard.add(button)
    bot.send_message(
        message.chat.id,
        "Please press the button below to continue.",
        reply_markup=keyboard,
    )


# 2. Callback -> Question 1 (Weather)
@bot.callback_query_handler(func=lambda call: call.data == "start_flow")
def callback_query(call):
    keyboard1 = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    keyboard1.add("Sunny and warm", "Rainy and humid")
    keyboard1.add("Cloudy and coolll", "Cold and snowy")
    msg = bot.send_message(
        call.message.chat.id,
        "What is the weather like today?",
        reply_markup=keyboard1,
    )
    bot.register_next_step_handler(msg, step_weather)


# 3. Handle Weather -> Question 2 (Day/Mood)
def step_weather(message):
    reply = message.text
    blob = TextBlob(reply)
    emo = ["P" if blob.polarity > 0 else "N"]

    if blob.polarity > 0:
        bot.send_message(
            message.chat.id, "It's a beautiful day! The weather is perfect. ☀️"
        )
    else:
        bot.send_message(
            message.chat.id, "Such a gloomy day. I see the weather isn't great."
        )

    questions = [
        "Hey, how has your day been?",
        "How's your day been so far?",
        "How has life been treating you this fine day?",
    ]
    msg = bot.send_message(
        message.chat.id,
        random.choice(questions),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(msg, step_mood, emo)


# 4. Handle Mood -> Ask Music Decision (Y/N)
def step_mood(message):
    reply = message.text
    blob = TextBlob(reply)
    emo = "P" if blob.polarity >= 0 else "N"

    if emo == "P":
        bot.send_message(
            message.chat.id, "That's good to hear! Look at you living life :)"
        )
    else:
        bot.send_message(
            message.chat.id,
            "I'm sorry to hear that. Hopefully everything gets better soon!",
        )

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add("Y", "N")
    msg = bot.send_message(
        message.chat.id,
        "Now, how about some music to suit your mood? (Y/N)",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, step_music_decision, emo)


# 5. Music Decision Handler
def step_music_decision(message, emo):
    choice = message.text.strip().upper()
    if choice == "Y":
        msg = bot.send_message(
            message.chat.id,
            "Who is your favorite artist? (Type your favorite artist's name, or"
            " type 'none'):",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(msg, step_artist_recommend, emo)
    else:
        # User doesn't want music -> Go directly to movie intro
        ask_movie_intro(message, emo)


# 6. Recommend Songs from Last.fm
def step_artist_recommend(message, emo):
    artist = message.text.strip()
    check = []

    if artist.lower() == "none":
        tag = (
            random.choice(["happy", "pop", "dance"])
            if emo == "P"
            else random.choice(["sad", "blues", "indie"])
        )
        url = f"http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={tag}&api_key={API_KEY}&format=json"
        r = lastfm_get(url, {"method": "tag.gettoptracks"})
        try:
            raw_tracks = r.json().get("tracks", {}).get("track", [])
        except Exception:
            raw_tracks = []
    else:
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={artist}&api_key={API_KEY}&format=json"
        r = lastfm_get(url, {"method": "artist.gettoptracks"})
        try:
            raw_tracks = r.json().get("toptracks", {}).get("track", [])
        except Exception:
            raw_tracks = []

    if not raw_tracks:
        bot.send_message(
            message.chat.id,
            "Could not find matching tracks for that choice.",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    else:
        limit = min(5, len(raw_tracks))
        bot.send_message(
            message.chat.id,
            "🎵 Here are some songs for you:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        for i in range(limit):
            j = random.choice(range(len(raw_tracks)))
            if j not in check:
                check.append(j)
                track = raw_tracks[j]
                bot.send_message(
                    message.chat.id,
                    f"• {track['name']} by {track['artist']['name']} -\n{track.get('url', '')}",
                )

    # Ask satisfaction for Music
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add("Y", "N")
    msg = bot.send_message(
        message.chat.id,
        "Are you satisfied with the music recommendations? (Y/N)",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, step_music_feedback, emo)


# 7. Check Music Satisfaction
def step_music_feedback(message, emo):
    choice = message.text.strip().upper()
    if choice == "Y":
        bot.send_message(message.chat.id, "Awesome! Glad you enjoyed the music.")
        ask_movie_intro(message, emo)
    else:
        # Not satisfied -> Ask if they want other songs
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        markup.add("Y", "N")
        msg = bot.send_message(
            message.chat.id,
            "Do you want me to recommend different songs? (Y/N)",
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, step_music_retry_decision, emo)


def step_music_retry_decision(message, emo):
    choice = message.text.strip().upper()
    if choice == "Y":
        msg = bot.send_message(
            message.chat.id,
            "Tell me an artist name (or 'none'):",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(msg, step_artist_recommend, emo)
    else:
        # Move on to movies
        ask_movie_intro(message, emo)


# ==============================================================================
# MOVIE SECTION (STRICTLY ISOLATED)
# ==============================================================================


def ask_movie_intro(message, emo):
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add("Y", "N")
    msg = bot.send_message(
        message.chat.id,
        "Now, how about some movies to suit your mood? (Y/N)",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, step_movie_decision, emo)


def step_movie_decision(message, emo):
    choice = message.text.strip().upper()
    if choice == "Y":
        bot.send_message(
            message.chat.id,
            "Fetching movie recommendations from IMDb...",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        main("happy" if emo == "P" else "sad")
        send_movies_to_user(message, emo)
    else:
        # User says NO to movies -> Say goodbye immediately, do not hang!
        bot.send_message(
            message.chat.id,
            "Okay, no movies! What did you think about chatting with me today?",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(message, step_user_feedback)


def send_movies_to_user(message, emo):
    num_movies = len(movie_title_arr)
    count = min(3, num_movies)
    check = []

    for _ in range(count):
        j = random.choice(range(num_movies))
        if j not in check:
            check.append(j)
            bot.send_message(
                message.chat.id,
                f"🎬 {movie_title_arr[j]}\n📖 {movie_synopsis_arr[j]}\n🔗 {image_url_arr[j]}",
            )

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add("Y", "N")
    msg = bot.send_message(
        message.chat.id,
        "Are you satisfied with these movie recommendations? (Y/N)",
        reply_markup=markup,
    )
    bot.register_next_step_handler(msg, step_movie_satisfaction, emo)


def step_movie_satisfaction(message, emo):
    choice = message.text.strip().upper()
    if choice == "Y":
        bot.send_message(
            message.chat.id, "I'm so glad you liked the movie picks! 🍿"
        )
        msg = bot.send_message(
            message.chat.id,
            "Before we say goodbye, what do you think about me?",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        bot.register_next_step_handler(msg, step_user_feedback)
    else:
        # User says NO (Not satisfied) -> Ask if they want other movies
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        markup.add("Y", "N")
        msg = bot.send_message(
            message.chat.id,
            "Would you like to see other movie suggestions? (Y/N)",
            reply_markup=markup,
        )
        bot.register_next_step_handler(msg, step_movie_retry_decision, emo)


def step_movie_retry_decision(message, emo):
    choice = message.text.strip().upper()
    if choice == "Y":
        bot.send_message(
            message.chat.id,
            "Here are some other picks for you:",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        send_movies_to_user(message, emo)
    else:
        # Doesn't want more movies -> Go to farewell
        bot.send_message(
            message.chat.id,
            "Okay, no more movies for now!",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        msg = bot.send_message(
            message.chat.id, "What do you think about chatting with me today?"
        )
        bot.register_next_step_handler(msg, step_user_feedback)


# ==============================================================================
# FAREWELL & FEEDBACK
# ==============================================================================


def step_user_feedback(message):
    reply = message.text
    blob = TextBlob(reply)

    if blob.polarity > 0:
        bot.send_message(message.chat.id, "OMG THANKSS!! You're making me blush!! 🥰")
    else:
        bot.send_message(
            message.chat.id,
            "I see, thanks for your feedback! I will try to do better next"
            " time. 🥺",
        )

    bot.send_message(
        message.chat.id,
        "Thank you for chatting with me. I hope you enjoyed it! Type /start"
        " whenever you want to hang out again. See ya!!!! 😊👋",
        reply_markup=types.ReplyKeyboardRemove(),
    )


# Fallback for unexpected messages: Guide user back to /start
@bot.message_handler(func=lambda msg: True)
def fallback_handler(message):
    bot.send_message(
        message.chat.id,
        "I'm waiting for your commands! Type /start to start a fresh"
        " conversation. 😊",
    )


if __name__ == "__main__":
    print("Easy Peasy Bot is online and running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
