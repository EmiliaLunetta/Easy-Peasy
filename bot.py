# ==============================================================================
# Easy Peasy Chatbot - phiên bản đã sửa lỗi
# pip install textblob pyTelegramBotAPI python-dotenv beautifulsoup4 requests nltk
#
# File .env cần có:
#   BOT_TOKEN=xxxxx
#   LASTFM_API_KEY=xxxxx
#   LASTFM_API_SECRET=xxxxx
# ==============================================================================

import os
import re
import json
import random

import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup as SOUP
from dotenv import load_dotenv
from textblob import TextBlob

# Đảm bảo corpora của TextBlob/NLTK có sẵn
try:
    import nltk

    nltk.download("punkt", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)
    nltk.download("brown", quiet=True)
except Exception:
    pass

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Thiếu BOT_TOKEN trong file .env")

bot = telebot.TeleBot(BOT_TOKEN)

API_KEY = os.getenv("LASTFM_API_KEY")
API_SECRET = os.getenv("LASTFM_API_SECRET")
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}


# ==============================================================================
# PHẦN 1: LAST.FM
# ==============================================================================
def get_tracks(method, **extra):
    """Gọi Last.fm, trả về list track (rỗng nếu lỗi / thiếu key)."""
    if not API_KEY:
        return []
    params = {
        "method": method,
        "api_key": API_KEY,
        "format": "json",
        "limit": 50,
        **extra,
    }
    try:
        res = requests.get(
            LASTFM_URL, headers=headers, params=params, timeout=10
        ).json()
    except Exception as e:
        print(f"Last.fm error: {e}")
        return []
    data = res.get("tracks") or res.get("toptracks") or {}
    tracks = data.get("track", [])
    # Last.fm trả về dict nếu chỉ có 1 bài
    return tracks if isinstance(tracks, list) else [tracks]


# ==============================================================================
# PHẦN 2: IMDb
# ==============================================================================
FALLBACK_MOVIES = [
    (
        "The Pursuit of Happyness",
        "A struggling salesman takes custody of his son.",
        "https://www.imdb.com/title/tt0454921/",
    ),
    (
        "Forrest Gump",
        "The history of the US through an Alabama man's eyes.",
        "https://www.imdb.com/title/tt0109830/",
    ),
    (
        "About Time",
        "A young man with the ability to time travel.",
        "https://www.imdb.com/title/tt2194499/",
    ),
    (
        "Soul",
        "A musician transported out of his body discovers life.",
        "https://www.imdb.com/title/tt2948372/",
    ),
]

# Lưu danh sách phim theo từng chat (không dùng global chung nữa)
user_movies = {}


def getMovieTitle(tag):
    """Lấy tên phim từ thẻ HTML, bỏ số thứ tự kiểu '1. '."""
    try:
        text = tag.get_text(" ", strip=True)
        return re.sub(r"^\d+\.\s*", "", text) or "Unknown"
    except Exception:
        return "Unknown"


def getsynopsys(movie):
    """Lấy tóm tắt phim."""
    default = "Check IMDb link for full plot and cast details."
    try:
        syn = movie.find(
            ["div", "p", "span"],
            class_=[
                "ipc-html-content-inner-div",
                "ipc-overflowText--lineClamp",
                "text-muted",
            ],
        )
        return syn.get_text().strip() if syn else default
    except Exception:
        return default


def main(emotion):
    """Scrape IMDb theo tâm trạng. Trả về list (title, synopsis, link)."""
    movies = []
    genre = "drama" if emotion == "sad" else "comedy"
    url = f"https://www.imdb.com/search/title/?genres={genre}&title_type=feature"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = SOUP(response.text, "html.parser")

        items = soup.find_all(
            ["li", "div"],
            class_=[
                "ipc-metadata-list-summary-item",
                "lister-item mode-advanced",
            ],
        )

        seen = set()
        for item in items[:15]:
            link_tag = item.find("a", href=lambda h: h and "/title/tt" in h)
            if not link_tag:
                continue
            link = "https://www.imdb.com" + link_tag["href"].split("?")[0]
            if link in seen:
                continue

            header = item.find(
                ["h3", "a"], class_=["ipc-title__text", "lister-item-header"]
            )
            title = getMovieTitle(header if header else link_tag)
            if title:
                seen.add(link)
                movies.append((title, getsynopsys(item), link))

        # Dự phòng qua __NEXT_DATA__
        if not movies:
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if script_tag and script_tag.string:
                data = json.loads(script_tag.string)
                titles = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("searchResults", {})
                    .get("titleListItems", [])
                )
                for t in titles[:10]:
                    t_id, t_name = t.get("titleId"), t.get("titleText")
                    if t_id and t_name:
                        movies.append(
                            (
                                t_name,
                                t.get(
                                    "plot",
                                    "Check IMDb link for full plot details.",
                                ),
                                f"https://www.imdb.com/title/{t_id}/",
                            )
                        )
    except Exception as e:
        print(f"Error scraping IMDb: {e}")

    return movies or FALLBACK_MOVIES


def send_movies(chat_id, movies, check):
    """Gửi tối đa 5 phim chưa gợi ý."""
    pool = [i for i in range(len(movies)) if i not in check]
    if not pool:
        bot.send_message(chat_id, "Hết phim để gợi ý rồi 😅")
        return
    for j in random.sample(pool, min(5, len(pool))):
        check.append(j)
        title, synopsis, link = movies[j]
        bot.send_message(chat_id, f"🎬 {title}\n📖 {synopsis}\n🔗 {link}")


# ==============================================================================
# PHẦN 3: BOT HANDLERS
# ==============================================================================
@bot.message_handler(commands=["start", "help"])
def greet_user(message):
    sentences = [
        "Hello there! Welcome to Easy Peasy Chatbot. I'm here to help you"
        " find the perfect music and movies to suit your mood. 😊",
        "Hi! I am Easy Peasy Chatbot, your personal entertainment assistant."
        " Let's get started on finding you some great music and movies. 🎵🎬",
        "Greetings! I am Easy Peasy Chatbot and I am here to help you"
        " discover new music and movies that you'll love. Let's get"
        " started! 🎶🎥",
    ]
    bot.send_message(message.chat.id, random.choice(sentences))

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            text="Ok. Let's go!!!", callback_data="Ok. Let's go!!!"
        )
    )
    bot.send_message(
        message.chat.id,
        "Please press the button below to continue.",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id)
    if call.data == "Ok. Let's go!!!":
        keyboard = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        for text in WEATHER_OPTIONS:
            keyboard.add(types.KeyboardButton(text))
        bot.send_message(
            call.message.chat.id,
            "What is the weather like today?",
            reply_markup=keyboard,
        )


WEATHER_OPTIONS = [
    "Sunny and warm",
    "Rainy and humid",
    "Cloudy and cool",
    "Cold and snowy",
]


@bot.message_handler(func=lambda m: m.text in WEATHER_OPTIONS)
def weather(message):
    blob = TextBlob(message.text)
    positive_responses = [
        "It's a beautiful day!",
        "The weather is perfect.",
        "Woww, that's niceee!",
    ]
    negative_responses = [
        "Such a gloomy day.",
        "I see, the weather is not great.",
        "Ahhhh, really!? ",
    ]

    emo = []
    if blob.polarity > 0:
        bot.send_message(message.chat.id, random.choice(positive_responses))
        emo.append("P")
    else:
        bot.send_message(message.chat.id, random.choice(negative_responses))
        emo.append("N")

    questions = [
        "Hey how has your day been?",
        "How's the day been so far?",
        "Ahh friend how has life been treating you this fine day?",
    ]
    bot.send_message(message.chat.id, random.choice(questions))
    # QUAN TRỌNG: đăng ký bước tiếp theo, không còn dựa vào handler bắt-mọi-tin-nhắn
    bot.register_next_step_handler(message, mood, emo)


def mood(message, emo):
    blob = TextBlob(message.text or "")
    positive_responses = [
        "That's good to hear",
        "NICEEE, good for you",
        "Look at you living the life :)",
        "Let's rock!!!",
    ]
    negative_responses = [
        "I'm sorry to hear that",
        "Hopefully everything will get better",
        "You'll get through this",
        "Let me light your day up :)",
    ]

    if blob.polarity > 0:
        bot.send_message(message.chat.id, random.choice(positive_responses))
        emo.append("P")
    else:
        bot.send_message(message.chat.id, random.choice(negative_responses))
        emo.append("N")

    bot.send_message(
        message.chat.id, "Now, how about some music to suit your mood? Y/N"
    )
    bot.register_next_step_handler(message, music, emo)


def music(message, emo):
    answer = (message.text or "").strip().lower()
    c = max(emo, key=emo.count) if emo else "P"
    check = []

    if answer == "y":
        bot.send_message(
            message.chat.id, "Who is your favorite artist? name/none"
        )
        bot.register_next_step_handler(message, artist_recommendation, c, check)
    else:
        bot.send_message(
            message.chat.id,
            "Okay, no music then. How about some movies to suit your mood? Y/N",
        )
        bot.register_next_step_handler(message, movie_recommendation, c, check)


def artist_recommendation(message, c, check):
    artist = (message.text or "").strip()

    if artist.lower() == "none":
        if c == "P":
            tag = random.choice(["happy", "pop", "rock", "dance"])
        else:
            tag = random.choice(["sad", "blues", "indie", "metal"])
        raw_tracks = get_tracks("tag.gettoptracks", tag=tag)
        not_found = "Sorry, no tracks found for this mood tag."
    else:
        raw_tracks = get_tracks("artist.gettoptracks", artist=artist)
        not_found = f"Sorry, no tracks found for artist '{artist}'."

    if not raw_tracks:
        bot.send_message(message.chat.id, not_found)
    else:
        pool = [i for i in range(len(raw_tracks)) if i not in check]
        for j in random.sample(pool, min(10, len(pool))):
            check.append(j)
            t = raw_tracks[j]
            bot.send_message(
                message.chat.id,
                f"{t.get('name', '?')} by"
                f" {t.get('artist', {}).get('name', '?')} -"
                f" {t.get('url', '')}",
            )

    bot.send_message(
        message.chat.id, "Are you satisfied with the music recommendations? Y/N"
    )
    bot.register_next_step_handler(message, music_feedback, c, check)


def music_feedback(message, c, check):
    if (message.text or "").strip().lower() != "y":
        bot.send_message(
            message.chat.id, "Do you want to continue or quit? C/Q"
        )
        bot.register_next_step_handler(message, music_continue, c, check)
    else:
        bot.send_message(message.chat.id, "I am glad you enjoyed the music")
        bot.send_message(
            message.chat.id, "Now, how about some movies to suit your mood? Y/N"
        )
        bot.register_next_step_handler(message, movie_recommendation, c, [])


def music_continue(message, c, check):
    if (message.text or "").strip().lower() == "q":
        bot.send_message(
            message.chat.id,
            "Okay, let's move on to the movie part. How about some movies to"
            " suit your mood? Y/N",
        )
        bot.register_next_step_handler(message, movie_recommendation, c, [])
    else:
        bot.send_message(
            message.chat.id, "Who is your favorite artist? name/none"
        )
        bot.register_next_step_handler(message, artist_recommendation, c, check)


def movie_recommendation(message, c, check=None):
    check = [] if check is None else check

    if (message.text or "").strip().lower() == "y":
        movies = main("happy" if c == "P" else "sad")
        user_movies[message.chat.id] = movies
        send_movies(message.chat.id, movies, check)
        bot.send_message(
            message.chat.id, "Are you satisfied with movie recommendations? Y/N"
        )
        bot.register_next_step_handler(message, movie_feedback, c, check)
    else:
        goodbye(message)  # chào luôn, không chờ thêm tin nhắn


def movie_feedback(message, c, check):
    if (message.text or "").strip().lower() != "y":
        bot.send_message(
            message.chat.id, "Do you want to continue or quit? C/Q"
        )
        bot.register_next_step_handler(message, movie_continue, c, check)
    else:
        bot.send_message(message.chat.id, "I am glad you enjoyed the movie")
        bot.send_message(message.chat.id, "What do you think about me?")
        bot.register_next_step_handler(message, user_feedback)


def movie_continue(message, c, check):
    if (message.text or "").strip().lower() == "c":
        movies = user_movies.get(message.chat.id) or main(
            "happy" if c == "P" else "sad"
        )
        user_movies[message.chat.id] = movies
        send_movies(message.chat.id, movies, check)
        bot.send_message(
            message.chat.id, "Are you satisfied with movie recommendations? Y/N"
        )
        bot.register_next_step_handler(message, movie_feedback, c, check)
    else:
        bot.send_message(message.chat.id, "Okay, there will be no movie then")
        bot.send_message(message.chat.id, "What do you think about me?")
        bot.register_next_step_handler(message, user_feedback)


def user_feedback(message):
    polarity = TextBlob(message.text or "").polarity
    positive_responses = [
        "Hehehe thankss xD",
        "OMG THANKSS!!",
        "You're making me blush!!",
    ]
    negative_responses = [
        "I see, thanks for your comments",
        "UGGGGHH HEYYYY",
        "Ahhh~~~~",
    ]
    bot.send_message(
        message.chat.id,
        random.choice(positive_responses if polarity > 0 else negative_responses),
    )
    goodbye(message)  # chào luôn


def goodbye(message):
    user_movies.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id,
        "Thank you for chatting with me. I hope you enjoyed it. See ya!!!! :)"
        "\nGõ /start để bắt đầu lại nhé.",
    )


# Handler dự phòng: PHẢI đặt cuối cùng
@bot.message_handler(content_types=["text"])
def fallback(message):
    bot.send_message(message.chat.id, "Gõ /start để bắt đầu nhé 🙂")


if __name__ == "__main__":
    print("Easy Peasy Bot is online and running 24/7...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
