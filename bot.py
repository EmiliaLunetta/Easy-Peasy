# ==============================================================================
# PART 1: PREPARATION & INITIALIZATION
# ==============================================================================

# Note: Install required libraries via terminal:
# pip install textblob pyTelegramBotAPI python-dotenv beautifulsoup4 requests

# Import required libraries
import os
import random
from bs4 import BeautifulSoup as SOUP
from dotenv import load_dotenv
import requests
import requests as HTTP
import telebot
from telebot import types
from textblob import TextBlob

# These lines are importing the required libraries for the code.
# os is a library for interacting with the operating system, requests is a library for making HTTP requests,
# telebot is a library for creating Telegram bots,
# types is a module from telebot that provides various types of objects for bots,
# TextBlob is a class from textblob that represents a text object, and random is a library for generating random answers.

# Ensure TextBlob corpora is available (prevents LookupError on 24/7 servers)
try:
    import nltk

    nltk.download("punkt", quiet=True)
    nltk.download("averaged_perceptron_tagger", quiet=True)
    nltk.download("brown", quiet=True)
except Exception:
    pass

#Load environment variables securely from .env file
load_dotenv()

# Initialization bot
BOT_TOKEN = os.getenv(
    "BOT_TOKEN", "[TOKEN]" # Fill your token from @Botfather
)
bot = telebot.TeleBot(BOT_TOKEN)

# Define API key, secret, and user agent as constants
API_KEY = os.getenv("LASTFM_API_KEY")
API_SECRET = os.getenv("LASTFM_API_SECRET")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"

# Define headers for the API and HTTP requests
headers = {"user-agent": USER_AGENT}


# Define a function to make the API request and return the response
def lastfm_get(url: str, payload: dict) -> requests.Response:
    response = requests.get(url, headers=headers, params=payload)
    return response


# This line is defining a function named lastfm_get that takes two arguments: url and payload.
# The url is a string that represents the endpoint of the Last.fm API,
# and the payload is a dictionary that contains the parameters for the request.
# The function uses the requests.get method to make a GET request to the url with the headers and payload as arguments,
# and assigns the response object to the variable response. The function returns the response object.


# Prepare for movie recommendation
def getImage(image):
    try:
        url = image.get("loadlate")
        if not url:
            url = image.get("src")
        return url if url else "NA"
    except Exception:
        return "NA"


def getsynopsys(movie):
    try:
        return movie.find_all("p", {"class": "text-muted"})[1].getText().strip()
    except Exception:
        return "Plot synopsis not available."


def getMovieTitle(header):
    try:
        return header[0].find("a").getText().strip()
    except Exception:
        return "Unknown Movie"


# Initialize empty lists to store scraped data
movie_title_arr = []
movie_synopsis_arr = []
image_url_arr = []

# These lines are preparing for movie recommendation based on scraping data from IMDb, a movie database website.
# The code defines three functions: getImage, getsynopsys, and getMovieTitle.
# Each function takes an argument that represents an element from the IMDb webpage,
# and tries to extract some information from it using methods from BeautifulSoup, a library for parsing HTML documents.
# If the extraction succeeds, the function returns the information as a string; otherwise, it returns 'NA' as a placeholder.
# The code also imports BeautifulSoup as SOUP and requests as HTTP for convenience.
# The code also initializes three empty lists: movie_title_arr, movie_synopsis_arr, and image_url_arr.
# These lists will store the movie titles, synopses, and image URLs scraped from IMDb.


# ==============================================================================
# PART 2: MAIN BOT LOGIC & HANDLERS
# ==============================================================================


# Greeting
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
    # This part of the code defines a function named greet_user that takes an argument named message.
    # The message is an object that represents the user's input to the bot.
    # The function is decorated with the @bot.message_handler decorator, which registers the function as a handler for messages that match certain criteria. In this case, the criteria are commands=['start', 'help'],
    # which means that the function will handle messages that start with /start or /help. These are common commands for Telegram bots to initiate or get help from the bot.
    # The function body consists of two statements. The first statement defines a list named sentences that contains three strings. Each string is a possible greeting sentence that the bot can send to the user.
    # The second statement uses the random.choice function to select a random element from the sentences list and assign it to the variable sentence. Then, the bot.send_message method is used to send the sentence as a message to the user's chat id, which is an attribute of the message object.
    sentence = random.choice(sentences)
    bot.send_message(message.chat.id, sentence)

    # Create an inline keyboard with a button to continue
    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(
        text="Ok. Let's go!!!", callback_data="Ok. Let's go!!!"
    )
    keyboard.add(button)

    # Send a message with the inline keyboard
    bot.send_message(
        message.chat.id,
        "Please press the button below to continue.",
        reply_markup=keyboard,
    )
    # This part of the code is modified to use an inline keyboard instead of commands for continuing the conversation.
    # An inline keyboard is a set of buttons that appear within a message and can trigger a callback when pressed.
    # The code creates an inline keyboard with a single button named "Continue" using the types.InlineKeyboardMarkup
    # and types.InlineKeyboardButton classes. The button has a callback_data attribute that contains a string that
    # identifies the button. The code then sends a message with the inline keyboard using the reply_markup argument.
    # The code also defines a function named callback_query that handles the callbacks from the inline keyboard using the
    # @bot.callback_query_handler decorator. The function takes an argument named call, which is an object that represents
    # the callback data. The function checks if the call.data attribute matches the string "continue", which means that
    # the user pressed the continue button. If so, the function proceeds to ask the first question about the weather
    # using the same code as before.


# Define a function to handle the callback from the inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # If the user pressed the continue button
    if call.data == "Ok. Let's go!!!":
        # Asking question 1
        keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        item1 = types.KeyboardButton("Sunny and warm")
        item2 = types.KeyboardButton("Rainy and humid")
        item3 = types.KeyboardButton("Cloudy and coolll")
        item4 = types.KeyboardButton("Cold and snowy")
        keyboard1.add(item1)
        keyboard1.add(item2)
        keyboard1.add(item3)
        keyboard1.add(item4)
        question1 = "What is the weather like today?"
        bot.send_message(
            call.message.chat.id, question1, reply_markup=keyboard1
        )
        # The function body consists of an if statement that checks if the call.data attribute matches the string "continue",
        # which means that the user pressed the continue button on the inline keyboard.
        # If so, the function proceeds to ask the first question about the weather using the same code as before.
        # The code creates a custom keyboard with four buttons that represent possible answers to the question
        # The code then sends a message with the question and the custom keyboard using the reply_markup argument.
        # The user can choose one of the buttons as their answer.


# This part of the code defines a function named weather that takes an argument named message.
# The message is an object that represents the user's input to the bot.
# The function is decorated with the @bot.message_handler decorator, which registers the function as a handler
# for messages that match certain criteria. In this case, the criteria are func=lambda message: message.text
# in the possible answers to the first question about the weather.
@bot.message_handler(
    func=lambda message: message.text
    in [
        "Sunny and warm",
        "Rainy and humid",
        "Cloudy and coolll",
        "Cold and snowy",
    ]
)
def weather(message):
    reply = (
        message.text
    )  # The message.text attribute to the variable reply. This is the user's answer to the question.
    blob = TextBlob(
        reply
    )  # The second statement creates an object named blob using the TextBlob class from the textblob
    # library. This class represents a text object that can be analyzed for natural language processing tasks.
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
    # The third and fourth statements define two lists named positive_responses and negative_responses that contain
    # three strings each. These are possible responses that the bot can send to the user based on their answer
    # to the weather question.
    emo = (
        []
    )  # This list will store a letter that indicates the sentiment of the user's answer: 'P' for positive or 'N' for negative.

    if blob.polarity > 0:
        sentence = random.choice(positive_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("P")
    else:
        sentence = random.choice(negative_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("N")

    questions = [
        "Hey how has your day been?",
        "How's the day been so far?",
        "Ahh friend how has life been treating you this fine day?",
    ]
    question2 = random.choice(questions)
    bot.send_message(message.chat.id, question2)

    ### The next block of statements consists of an if-else statement that checks the polarity attribute of the blob object.
    # The polarity is a value between -1 and 1 that indicates how positive or negative the text is. If the polarity is
    # greater than 0, it means that the text is positive. In this case, the code uses the random.choice function to
    # select a random element from the positive_responses list and assign it to the variable sentence.
    # Then, the bot.send_message method is used to send the sentence as a message to the user's chat id. The code
    # also appends 'P' to the emo list. Otherwise, if the polarity is less than or equal to 0, it means that the text
    # is negative or neutral. In this case, the code uses the random.choice function to select a random element from the
    # negative_responses list and assign it to the variable sentence. Then, the bot.send_message method is used to send the
    # sentence as a message to the user's chat id. The code also appends 'N' to the emo list.

    ### The last block of statements defines another list named questions that contains three strings.
    # These are possible questions that the bot can ask the user about their day. The code uses the random.choice function
    # to select a random element from the questions list and assign it to the variable question2. Then, the bot.send_message
    # method is used to send question2 as a message to the user's chat id. This is the second question that the bot will ask the user.


@bot.message_handler(content_types=["text"])
def mood(message):
    reply = message.text
    blob = TextBlob(reply)
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
    emo = []

    if blob.polarity > 0:
        sentence = random.choice(positive_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("P")
    else:
        sentence = random.choice(negative_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("N")

    bot.send_message(
        message.chat.id, "Now, how about some music to suit your mood? Y/N"
    )
    bot.register_next_step_handler(message, music, emo)


# This part of the code defines a function named mood that takes an argument named message. The message is an object
# that represents the user's input to the bot. The function is decorated with the @bot.message_handler decorator,
# which registers the function as a handler for messages that match certain criteria. In this case, the criteria are
# content_types=["text"], which means that the function will handle messages that have text content. These are the possible
# answers to the second question about the user's day.
# The body part of the function is similar to the weather function
# In the end I use the bot.register_next_step_handler method to register a function named music as a handler for the
# next message from the user. This function will handle messages that indicate whether or not they want music recommendations.
# The method also passes two arguments: message and emo. These are objects that represent the current message and sentiment
# list respectively and will be available in the music function.


def music(message, emo):
    a = message.text  # User's input
    # Find the most common emotion in the user's replies
    c = max(emo, key=emo.count) if emo else "P"

    # Define an empty list to store the indices of the recommended songs
    check = []

    # If the user wants music recommendations, make an API request based on their emotion and tag
    if a.lower() == "y":
        # Ask the user for their favorite artist
        bot.send_message(
            message.chat.id, "Who is your favorite artist? name/none"
        )
        bot.register_next_step_handler(message, artist_recommendation, c, check)
        # If the user wants music recommendations, ask for their favorite artist and register artist_recommendation as
        # the next handler
    else:
        bot.send_message(
            message.chat.id,
            "Okay, no music then. How about some movies to suit your mood? Y/N",
        )
        bot.register_next_step_handler(message, movie_recommendation, c, check)
        # This part of the code defines a function named music that takes two arguments: message and emo. The message is
        # the user's input and the emo is the user's sentiment. The function handles messages that indicate if the user
        # wants music recommendations. The function body assigns the message text to a, finds the dominant emotion in emo
        # and assigns it to c, and initializes an empty list named check. The function then checks if the user wants music
        # recommendations by comparing a.lower() to 'y'. If yes, the function asks for their favorite artist and registers
        # artist_recommendation as the next handler. If no, the function asks for movie recommendations and registers
        # movie_recommendation as the next handler.


def artist_recommendation(message, c, check):
    artist = message.text.strip()
    # This part of the code defines a function named artist_recommendation that takes three arguments: message, c and check.
    # The message is an object that represents the user's input to the bot. The c is a letter that indicates the dominant
    # emotion of the user. The check is a list that contains the indices of the songs that are recommended to the user.
    # The function is registered as a handler for messages that indicate the user's favorite artist.

    # If the user has no preference, choose a random tag based on their emotion
    if artist.lower() == "none":
        if c == "P":
            tag = random.choice(["happy", "pop", "rock", "dance"])
        else:
            tag = random.choice(["sad", "blues", "indie", "metal"])
        # Make an API request with the tag and print the results
        url = (
            "http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag="
            + tag
            + "&api_key="
            + API_KEY
            + "&format=json"
        )
        r = lastfm_get(url, {"method": "tag.gettoptracks"})
        try:
            res = r.json()
            raw_tracks = res.get("tracks", {}).get("track", [])
        except Exception:
            raw_tracks = []

        if not raw_tracks:
            bot.send_message(
                message.chat.id, "Sorry, no tracks found for this mood tag."
            )
        else:
            max_limit = min(50, len(raw_tracks))
            count = min(10, max_limit)
            for i in range(count):
                j = random.choice(range(0, max_limit))
                for k in range(0, len(check)):
                    if check[k] == j:
                        j = random.choice(range(0, max_limit))
                        k = 0
                check.append(j)
                bot.send_message(
                    message.chat.id,
                    f"{raw_tracks[j]['name']} by"
                    f" {raw_tracks[j]['artist']['name']} -"
                    f" {raw_tracks[j].get('url', '')}",
                )

    # If the user has a preference, make an API request with the artist and print the results
    else:
        url = (
            "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist="
            + artist
            + "&api_key="
            + API_KEY
            + "&format=json"
        )
        r = lastfm_get(url, {"method": "artist.gettoptracks"})
        try:
            res = r.json()
            raw_tracks = res.get("toptracks", {}).get("track", [])
        except Exception:
            raw_tracks = []

        if not raw_tracks:
            bot.send_message(
                message.chat.id,
                f"Sorry, no tracks found for artist '{artist}'.",
            )
        else:
            max_limit = min(50, len(raw_tracks))
            count = min(10, max_limit)
            for i in range(count):
                j = random.choice(range(0, max_limit))
                for k in range(0, len(check)):
                    if check[k] == j:
                        j = random.choice(range(0, max_limit))
                        k = 0
                check.append(j)
                bot.send_message(
                    message.chat.id,
                    f"{raw_tracks[j]['name']} by"
                    f" {raw_tracks[j]['artist']['name']} -"
                    f" {raw_tracks[j].get('url', '')}",
                )

    bot.send_message(
        message.chat.id, "Are you satisfied with the music recommendations? Y/N"
    )
    bot.register_next_step_handler(message, music_feedback, c, check)


def music_feedback(message, c, check):
    b = message.text.strip()
    if b.lower() != "y":
        bot.send_message(
            message.chat.id, "Do you want to continue or quit? C/Q"
        )
        bot.register_next_step_handler(message, music_continue, c, check)
    else:
        bot.send_message(message.chat.id, "I am glad you enjoyed the music")
        bot.send_message(
            message.chat.id, "Now, how about some movies to suit your mood? Y/N"
        )
        bot.register_next_step_handler(message, movie_recommendation, c, check)


def music_continue(message, c, check):
    d = message.text.strip()
    if d.lower() == "q":
        bot.send_message(
            message.chat.id,
            "Okay, let's move on to the movie part. How about some movies to"
            " suit your mood?",
        )
        bot.register_next_step_handler(message, movie_recommendation, c, check)
    else:
        bot.send_message(
            message.chat.id, "Who is your favorite artist? name/none"
        )
        bot.register_next_step_handler(message, artist_recommendation, c, check)


def main(emotion):
    # Clear arrays at each search so memory stays clean across multiple users
    global movie_title_arr, movie_synopsis_arr, image_url_arr
    movie_title_arr.clear()
    movie_synopsis_arr.clear()
    image_url_arr.clear()

    if emotion == "sad":
        urlhere = "https://www.imdb.com/search/title/?genres=drama&title_type=feature"
    else:
        urlhere = "https://www.imdb.com/search/title/?genres=comedy&title_type=feature"

    # Use browser user-agent header to avoid 403 Forbidden
    response = HTTP.get(urlhere, headers=headers)
    data = response.text
    soup = SOUP(data, "html.parser")
    movies_list = soup.find_all("div", {"class": "lister-item mode-advanced"})

    for movie in movies_list:
        header = movie.find_all("h3", {"class": "lister-item-header"})
        imageDiv = movie.find("div", {"class": "lister-item-image float-left"})
        image = (
            imageDiv.find("img") if imageDiv else None
        )  # safe image extraction

        movie_title = getMovieTitle(header)
        movie_title_arr.append(movie_title)

        synopsis = getsynopsys(movie)
        movie_synopsis_arr.append(synopsis)

        img_url = getImage(image)
        image_url_arr.append(img_url)

    # Fallback to prevent crash if IMDb changes layout
    if not movie_title_arr:
        movie_title_arr.extend(
            ["The Pursuit of Happyness", "Forrest Gump", "About Time", "Soul"]
        )
        movie_synopsis_arr.extend(
            [
                "A struggling salesman takes custody of his son.",
                "The history of the US through an Alabama man's eyes.",
                "A young man with the ability to time travel.",
                "A musician transported out of his body discovers life.",
            ]
        )
        image_url_arr.extend(["NA", "NA", "NA", "NA"])


# Continue recommending movies
def movie_recommendation(message, c, check=None):
    if check is None:
        check = []
    b = message.text.strip()
    check = []

    if b.lower() == "y":
        if c == "P":
            main("happy")
        else:
            main("sad")

        num_movies = len(movie_title_arr)
        count = min(5, num_movies)

        for i in range(count):
            j = random.choice(range(0, num_movies))
            for k in range(0, len(check)):
                if check[k] == j:
                    j = random.choice(range(0, num_movies))
                    k = 0
            check.append(j)

            # Send movie information safely
            bot.send_message(
                message.chat.id,
                f"🎬 {movie_title_arr[j]}\n📖 {movie_synopsis_arr[j]}\n🔗 {image_url_arr[j]}\n",
            )

        bot.send_message(
            message.chat.id, "Are you satisfied with movie recommendations? Y/N"
        )
        bot.register_next_step_handler(message, movie_feedback, c, check)
    else:
        bot.register_next_step_handler(message, goodbye)


def movie_feedback(message, c, check):
    d = message.text.strip()
    if d.lower() != "y":
        bot.send_message(
            message.chat.id, "Do you want to continue or quit? C/Q"
        )
        bot.register_next_step_handler(message, movie_continue, c, check)
    else:
        bot.send_message(message.chat.id, "I am glad you enjoyed the movie")
        bot.send_message(message.chat.id, "What do you think about me?")
        bot.register_next_step_handler(message, user_feedback)


def movie_continue(message, c, check):
    e = message.text.strip()
    if e.lower() == "c":
        num_movies = len(movie_title_arr)
        count = min(5, num_movies)

        for i in range(count):
            j = random.choice(range(0, num_movies))
            for k in range(0, len(check)):
                if check[k] == j:
                    j = random.choice(range(0, num_movies))
                    k = 0
            check.append(j)

            bot.send_message(
                message.chat.id,
                f"🎬 {movie_title_arr[j]}\n📖 {movie_synopsis_arr[j]}\n🔗 {image_url_arr[j]}\n",
            )

        bot.send_message(
            message.chat.id, "Are you satisfied with movie recommendations? Y/N"
        )
        bot.register_next_step_handler(message, movie_feedback, c, check)
    else:
        bot.send_message(message.chat.id, "Okay, there will be no movie then")
        bot.send_message(message.chat.id, "What do you think about me?")
        bot.register_next_step_handler(message, user_feedback)


def user_feedback(message):
    reply = message.text
    blob = TextBlob(reply)
    polarity = blob.polarity

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

    if polarity > 0:
        sentence = random.choice(positive_responses)
        bot.send_message(message.chat.id, sentence)
    else:
        sentence = random.choice(negative_responses)
        bot.send_message(message.chat.id, sentence)
    bot.register_next_step_handler(message, goodbye)


def goodbye(message):
    bot.send_message(
        message.chat.id,
        "Thank you for chatting with me. I hope you enjoyed it. See ya!!!! :)",
    )


# Run bot indefinitely without crashing upon network drops
if __name__ == "__main__":
    print("Easy Peasy Bot is online and running 24/7...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
