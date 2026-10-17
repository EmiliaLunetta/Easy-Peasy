"""
Easy Peasy Chatbot - gợi ý nhạc & phim theo cảm xúc.

Biến môi trường (đặt ở Render > Environment, KHÔNG commit lên GitHub):
    BOT_TOKEN, LASTFM_API_KEY
"""

import functools
import os
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import telebot
from bs4 import BeautifulSoup as SOUP
from telebot import types
from textblob import TextBlob

try:
    from dotenv import load_dotenv

    load_dotenv()  # chỉ có tác dụng khi chạy local có file .env
except ImportError:
    pass

# ==============================================================================
# CẤU HÌNH
# ==============================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

if not BOT_TOKEN:
    raise SystemExit("Thiếu BOT_TOKEN (đặt trong Environment của Render hoặc .env)")
if not LASTFM_API_KEY:
    print("CẢNH BÁO: thiếu LASTFM_API_KEY, phần gợi ý nhạc sẽ không hoạt động.")

bot = telebot.TeleBot(BOT_TOKEN)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"

# ==============================================================================
# PHẦN 1: PHÂN TÍCH CẢM XÚC
# ==============================================================================
# TextBlob chỉ hiểu tiếng Anh. Với câu TextBlob cho điểm ~0 (ví dụ tiếng Việt),
# bot dùng thêm từ điển nhỏ bên dưới để vẫn nhận ra được cảm xúc.
POS_WORDS = [
    "good", "great", "happy", "fine", "awesome", "amazing", "excited",
    "relaxed", "wonderful", "love", "vui", "vui vẻ", "tốt", "tuyệt",
    "hạnh phúc", "khỏe", "khoẻ", "ổn", "hào hứng", "thoải mái", "yêu đời",
    "tuyet", "hanh phuc", "thoai mai",
]
NEG_WORDS = [
    "bad", "sad", "tired", "terrible", "awful", "angry", "stressed",
    "lonely", "depressed", "anxious", "buồn", "tệ", "chán", "mệt",
    "căng thẳng", "cô đơn", "khổ", "tức", "lo lắng", "stress", "buon",
    "chan", "met", "cang thang", "co don", "lo lang",
]
NEGATORS = r"không|khong|chẳng|chả|not|never|no|don't|dont"


def _lexicon_score(text):
    t = text.lower()
    total = 0.0
    for words, sign in ((POS_WORDS, 1), (NEG_WORDS, -1)):
        for w in words:
            w_re = re.escape(w)
            if not re.search(rf"\b{w_re}\b", t):
                continue
            negated = re.search(rf"\b({NEGATORS})\s+(?:\w+\s+)?{w_re}\b", t)
            total += -sign * 0.5 if negated else sign * 0.5
    return max(-0.8, min(0.8, total))


def analyze(text):
    """Trả về điểm cảm xúc trong khoảng [-1, 1]."""
    text = (text or "").strip()
    if not text:
        return 0.0
    base = TextBlob(text).sentiment.polarity
    if abs(base) >= 0.05:
        return base
    return _lexicon_score(text)


def bucket(score):
    if score > 0.05:
        return "pos"
    if score < -0.05:
        return "neg"
    return "neu"


# Điểm cố định cho các nút thời tiết (TextBlob không đánh giá tốt cụm này)
WEATHER_SCORES = {
    "Sunny and warm": 0.6,
    "Rainy and humid": -0.4,
    "Cloudy and cool": 0.0,
    "Cold and snowy": -0.3,
}

# Mỗi câu hỏi có danh sách trả lời riêng cho tích cực / tiêu cực / trung tính.
# "weight": độ quan trọng khi tính cảm xúc tổng (cảm xúc hiện tại quan trọng nhất).
QUESTIONS = [
    {
        "prompts": ["What is the weather like today?"],
        "weight": 0.5,
        "pos": [
            "It's a beautiful day!",
            "The weather is perfect.",
            "Woww, that's niceee!",
        ],
        "neg": [
            "Such a gloomy day.",
            "I see, the weather is not great.",
            "Ahhhh, really!?",
        ],
        "neu": ["Hmm, a calm kind of day.", "Okay, not too extreme then."],
    },
    {
        "prompts": [
            "Hey how has your day been?",
            "How's the day been so far?",
            "Ahh friend how has life been treating you this fine day?",
        ],
        "weight": 1.0,
        "pos": [
            "That's good to hear",
            "NICEEE, good for you",
            "Look at you living the life :)",
        ],
        "neg": [
            "I'm sorry to hear that",
            "Hopefully everything will get better",
            "You'll get through this",
        ],
        "neu": ["Alright, a so-so day then.", "Fair enough, thanks for sharing."],
    },
    {
        "prompts": ["How are you feeling right now?"],
        "weight": 1.5,
        "pos": [
            "Love that energy!",
            "Glad you're feeling good!",
            "Let's rock!!!",
        ],
        "neg": [
            "Let me light your day up :)",
            "Thanks for being honest, I'm here for you.",
            "Hang in there, I'll try to cheer you up.",
        ],
        "neu": ["Okay, noted!", "Alright, let's see what fits you."],
    },
]


# ==============================================================================
# PHẦN 2: TIỆN ÍCH
# ==============================================================================
YES = {"y", "yes", "yeah", "yep", "ok", "okay", "có", "co", "ừ"}
NO = {"n", "no", "nope", "không", "khong"}


def parse_yn(text):
    t = (text or "").strip().lower()
    if t in YES:
        return True
    if t in NO:
        return False
    return None


def step(fn):
    """Bọc mọi handler 'bước kế tiếp': gõ /start giữa chừng sẽ khởi động lại."""

    @functools.wraps(fn)
    def wrapper(message, *args):
        text = message.text or ""
        if text.startswith("/"):
            bot.clear_step_handler_by_chat_id(message.chat.id)
            if text.startswith(("/start", "/help")):
                greet_user(message)
            return
        return fn(message, *args)

    return wrapper


def yn(message, handler, *args):
    """Đọc Y/N. Nếu trả lời lạ thì hỏi lại và trả về None."""
    ans = parse_yn(message.text)
    if ans is None:
        bot.send_message(message.chat.id, "Please answer with Y or N 🙂")
        bot.register_next_step_handler(message, handler, *args)
    return ans


# ==============================================================================
# PHẦN 3: LAST.FM
# ==============================================================================
HAPPY_TAGS = {"happy", "pop", "dance", "upbeat", "feel good", "party", "fun"}
SAD_TAGS = {"sad", "blues", "melancholy", "mellow", "emotional", "indie", "chill"}


def get_tracks(method, **extra):
    if not LASTFM_API_KEY:
        return []
    params = {
        "method": method,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 50,
        **extra,
    }
    try:
        res = requests.get(
            LASTFM_URL, headers=HEADERS, params=params, timeout=10
        ).json()
    except Exception as e:
        print(f"Last.fm error: {e}")
        return []
    tracks = (res.get("tracks") or res.get("toptracks") or {}).get("track", [])
    return tracks if isinstance(tracks, list) else [tracks]


def track_key(t):
    return (t["artist"]["name"].lower(), t["name"].lower())


def track_matches_mood(t, mood_tags):
    params = {
        "method": "track.gettoptags",
        "artist": t["artist"]["name"],
        "track": t["name"],
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }
    try:
        r = requests.get(LASTFM_URL, headers=HEADERS, params=params, timeout=5)
        tags = r.json().get("toptags", {}).get("tag", [])
    except Exception:
        return False
    return any(x["name"].lower() in mood_tags for x in tags[:10])


def pick_tracks(artist, c, heard):
    """Trả về (danh sách bài, có_khớp_cảm_xúc)."""
    mood_tags = HAPPY_TAGS if c == "P" else SAD_TAGS

    if artist.lower() == "none":
        tag = random.choice(
            ["happy", "pop", "rock", "dance"]
            if c == "P"
            else ["sad", "blues", "indie", "metal"]
        )
        tracks = get_tracks("tag.gettoptracks", tag=tag)
        fresh = [t for t in tracks if track_key(t) not in heard]
        return random.sample(fresh, min(5, len(fresh))), True

    tracks = get_tracks("artist.gettoptracks", artist=artist)
    fresh = [t for t in tracks if track_key(t) not in heard]
    candidates = random.sample(fresh, min(12, len(fresh)))
    if not candidates:
        return [], False
    with ThreadPoolExecutor(max_workers=6) as ex:
        flags = list(ex.map(lambda t: track_matches_mood(t, mood_tags), candidates))
    matched = [t for t, f in zip(candidates, flags) if f]
    if matched:
        return matched[:5], True
    return candidates[:5], False


# ==============================================================================
# PHẦN 4: IMDb
# ==============================================================================
# (title, synopsis, link, poster)
FALLBACK_MOVIES = [
    ("The Pursuit of Happyness", "A struggling salesman takes custody of his son.",
     "https://www.imdb.com/title/tt0454921/", None),
    ("Forrest Gump", "The history of the US through an Alabama man's eyes.",
     "https://www.imdb.com/title/tt0109830/", None),
    ("About Time", "A young man with the ability to time travel.",
     "https://www.imdb.com/title/tt2194499/", None),
    ("Soul", "A musician transported out of his body discovers life.",
     "https://www.imdb.com/title/tt2948372/", None),
]


def fetch_movies(c):
    genre = "comedy" if c == "P" else "drama"
    movies = []
    try:
        r = requests.get(
            f"https://www.imdb.com/search/title/?genres={genre}&title_type=feature",
            headers=HEADERS,
            timeout=10,
        )
        soup = SOUP(r.text, "html.parser")
        for item in soup.select("li.ipc-metadata-list-summary-item")[:15]:
            a = item.find("a", href=lambda h: h and "/title/tt" in h)
            t = item.select_one(".ipc-title__text")
            if not a or not t:
                continue
            title = re.sub(r"^\d+\.\s*", "", t.get_text(" ", strip=True))
            link = "https://www.imdb.com" + a["href"].split("?")[0]
            syn = item.select_one(".ipc-html-content-inner-div")
            img = item.select_one("img.ipc-image")
            movies.append(
                (
                    title,
                    syn.get_text().strip() if syn else "See the IMDb link for the plot.",
                    link,
                    img.get("src") if img else None,
                )
            )
    except Exception as e:
        print(f"IMDb error: {e}")
    return movies or FALLBACK_MOVIES


def send_movies(chat_id, movies, shown):
    pool = [i for i in range(len(movies)) if i not in shown]
    if not pool:
        return False
    for j in random.sample(pool, min(3, len(pool))):
        shown.append(j)
        title, syn, link, poster = movies[j]
        caption = f"🎬 {title}\n\n📖 {syn[:700]}\n\n🔗 {link}"
        sent = False
        if poster:
            try:
                bot.send_photo(chat_id, poster, caption=caption)
                sent = True
            except Exception as e:
                print(f"Photo error: {e}")
        if not sent:
            bot.send_message(chat_id, caption)
    return True


# ==============================================================================
# PHẦN 5: LỜI CHÀO & HỎI CẢM XÚC
# ==============================================================================
@bot.message_handler(commands=["start", "help"])
def greet_user(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    greetings = [
        "Hello, this is Easy Peasy Chatbot. I'm here to make your day better"
        " with some music and movies. 😊",
        "Greetings from Easy Peasy Chatbot. I'm a friendly bot that can suggest"
        " some music and movies for you. 😊",
        "Welcome to Easy Peasy Chatbot. I'm a smart bot that can help you find"
        " some music and movies that suit your mood. 😊",
    ]
    bot.send_message(message.chat.id, random.choice(greetings))

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Ok. Let's go!!!", callback_data="continue"))
    bot.send_message(
        message.chat.id,
        "Please press the button below to continue.",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data == "continue")
def on_continue(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    bot.clear_step_handler_by_chat_id(chat_id)
    ask_question(chat_id, 0, [])


def ask_question(chat_id, idx, scores):
    prompt = random.choice(QUESTIONS[idx]["prompts"])
    if idx == 0:
        kb = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        for option in WEATHER_SCORES:
            kb.add(types.KeyboardButton(option))
        bot.send_message(chat_id, prompt, reply_markup=kb)
    else:
        bot.send_message(chat_id, prompt, reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler_by_chat_id(chat_id, answer_question, idx, scores)


@step
def answer_question(message, idx, scores):
    q = QUESTIONS[idx]
    text = (message.text or "").strip()

    score = WEATHER_SCORES[text] if idx == 0 and text in WEATHER_SCORES else analyze(text)
    scores.append(score)
    bot.send_message(message.chat.id, random.choice(q[bucket(score)]))

    if idx + 1 < len(QUESTIONS):
        ask_question(message.chat.id, idx + 1, scores)
    else:
        finish_mood(message, scores)


def finish_mood(message, scores):
    weights = [q["weight"] for q in QUESTIONS]
    avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    c = "P" if avg >= 0 else "N"

    if avg >= 0.2:
        summary = "you're in a good mood 😊"
    elif avg <= -0.2:
        summary = "you're feeling a bit down 💙"
    else:
        summary = "you're somewhere in the middle 🙂"
    bot.send_message(
        message.chat.id,
        f"Based on your answers, I think {summary} (mood score: {avg:+.2f})",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    bot.send_message(
        message.chat.id, "How about some music to suit your mood? Y/N"
    )
    bot.register_next_step_handler(message, music, c)


# ==============================================================================
# PHẦN 6: NHẠC
# ==============================================================================
def ask_artist(message, c, heard):
    bot.send_message(message.chat.id, "Who is your favorite artist? (name / none)")
    bot.register_next_step_handler(message, artist_step, c, heard)


@step
def music(message, c):
    ans = yn(message, music, c)
    if ans is None:
        return
    if ans:
        ask_artist(message, c, set())
    else:
        ask_movies(message, c)


@step
def artist_step(message, c, heard):
    artist = (message.text or "").strip()
    if not artist:
        bot.send_message(message.chat.id, "Please type an artist name or 'none'.")
        bot.register_next_step_handler(message, artist_step, c, heard)
        return

    bot.send_message(message.chat.id, "Looking for songs for you... 🎧")
    picked, matched = pick_tracks(artist, c, heard)

    if not picked:
        bot.send_message(message.chat.id, "Could not find any (new) tracks.")
    else:
        if not matched:
            bot.send_message(
                message.chat.id,
                "I couldn't find songs matching your mood, here are some"
                " popular ones instead:",
            )
        for t in picked:
            heard.add(track_key(t))
            bot.send_message(
                message.chat.id,
                f"{t['name']} by {t['artist']['name']} - {t.get('url', '')}",
            )

    bot.send_message(
        message.chat.id, "Are you satisfied with the music recommendations? Y/N"
    )
    bot.register_next_step_handler(message, music_feedback, c, heard)


@step
def music_feedback(message, c, heard):
    ans = yn(message, music_feedback, c, heard)
    if ans is None:
        return
    if ans:
        bot.send_message(message.chat.id, "I am glad you enjoyed the music!")
        ask_movies(message, c)
    else:
        bot.send_message(
            message.chat.id, "Do you want me to continue recommending songs? Y/N"
        )
        bot.register_next_step_handler(message, music_continue, c, heard)


@step
def music_continue(message, c, heard):
    ans = yn(message, music_continue, c, heard)
    if ans is None:
        return
    if ans:
        ask_artist(message, c, heard)
    else:
        ask_movies(message, c)


# ==============================================================================
# PHẦN 7: PHIM
# ==============================================================================
def ask_movies(message, c):
    bot.send_message(message.chat.id, "How about some movies? Y/N")
    bot.register_next_step_handler(message, movie_step, c)


@step
def movie_step(message, c):
    ans = yn(message, movie_step, c)
    if ans is None:
        return
    if not ans:
        goodbye(message)
        return

    bot.send_message(message.chat.id, "Searching movies for you on IMDb... 🍿")
    movies = fetch_movies(c)
    shown = []
    send_movies(message.chat.id, movies, shown)
    bot.send_message(
        message.chat.id, "Are you satisfied with the movie recommendations? Y/N"
    )
    bot.register_next_step_handler(message, movie_feedback, c, movies, shown)


@step
def movie_feedback(message, c, movies, shown):
    ans = yn(message, movie_feedback, c, movies, shown)
    if ans is None:
        return
    if ans:
        goodbye(message)
        return

    if not send_movies(message.chat.id, movies, shown):
        bot.send_message(message.chat.id, "I've run out of movies to suggest 😅")
        goodbye(message)
        return
    bot.send_message(
        message.chat.id, "Are you satisfied with the movie recommendations? Y/N"
    )
    bot.register_next_step_handler(message, movie_feedback, c, movies, shown)


def goodbye(message):
    bot.send_message(
        message.chat.id,
        "Thank you for chatting with me. I hope you enjoyed it. See ya! 😊"
        "\nType /start to chat again.",
    )


# Handler dự phòng: PHẢI đặt cuối cùng
@bot.message_handler(content_types=["text"])
def fallback(message):
    bot.send_message(message.chat.id, "Type /start to begin 🙂")


# ==============================================================================
# CHẠY BOT
# ==============================================================================
def start_health_server():
    """Nếu deploy dạng Web Service, Render cần 1 port đang mở."""
    port = os.getenv("PORT")
    if not port:
        return

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            pass

    server = HTTPServer(("0.0.0.0", int(port)), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


if __name__ == "__main__":
    start_health_server()
    bot.remove_webhook()
    print("Easy Peasy Bot is online...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
