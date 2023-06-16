#!/usr/bin/env python
# coding: utf-8

# In[ ]:


get_ipython().system('pip install textblob')

# Import requests library
import os
import requests
import telebot
get_ipython().system('pip install pyTelegramBotAPI')
bot = telebot.TeleBot('6210560812:AAHH6M5daoJKYqA1PtekQN_vKQ5PmsZTyVk')
from telebot import types
# Define API key, secret, and user agent as constants
API_KEY = '7bc65c1d5adf30658bff0b4a827e7446'
API_SECRET = '65fc37b601ee1c26deca3e78df718db6'
USER_AGENT = 'Dataquest'

# Define headers and payload for the API request
headers = {
    'user-agent': USER_AGENT
}
payload = {
    'api_key': API_KEY,
    'method': 'tag.gettoptracks',
    'format': 'json',
    "tracks": 
    {
        "track": [
                  {...},{...}
                 ],
        "@attr": 
        {
            "page": "1",
            "perPage": "5",
            "totalPages": "1",
            "total": "2"
        }
    }
}

# Define a function to make the API request and return the response
def lastfm_get(url: str, payload: dict) -> requests.Response:
    response = requests.get(url, headers = headers, params = payload)
    return response

# Import TextBlob library
from textblob import TextBlob

# Import random library
import random

# Interact with users
#Greeting
@bot.message_handler(commands=['start', 'help'])
def greet_user(message): # Choose a random greeting sentence
    sentences = ["Hello there! Welcome to Easy Peasy Chatbot. I'm here to help you find the perfect music and movies to suit your mood. 😊",
                 "Hi! I'm Easy Peasy Chatbot, your personal entertainment assistant. Let's get started on finding you some great music and movies. 🎵🎬",
                 "Greetings! I'm Easy Peasy Chatbot and I'm here to help you discover new music and movies that you'll love. Let's get started! 🎶🎥"]

    sentence = random.choice(sentences)
    bot.send_message(message.chat.id, sentence)

@bot.message_handler(commands=['ok', 'continue','yes'])
def button_message(message):
    # Asking question 1
    keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True) 
    item1 = types.KeyboardButton('Sunny and warm') 
    item2 = types.KeyboardButton('Rainy and humid')
    item3 = types.KeyboardButton('Cloudy and coolll')
    item4 = types.KeyboardButton('Cold and snowy')
    keyboard1.add(item1)
    keyboard1.add(item2)
    keyboard1.add(item3)
    keyboard1.add(item4)
    question1 = "What is the weather like today?"
    bot.send_message(message.chat.id, question1, reply_markup=keyboard1)
    
@bot.message_handler(func=lambda message: message.text in ['Sunny and warm', 'Rainy and humid', 'Cloudy and coolll', 'Cold and snowy'])
def weather(message):
    reply = message.text 
    blob = TextBlob(reply)
    positive_responses = ["It's a beautiful day!", "The weather is perfect.", "Woww, that's niceee!"]

    negative_responses = ["Such a gloomy day.", "I see, the weather is not great.", "Ahhhh, really!? "]

    emo =[]

    if blob.polarity > 0:
        sentence = random.choice(positive_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("P")
    else:
        sentence = random.choice(negative_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("N")
    questions = ["Hey how has your day been?",
                 "How's the day been so far?",
                 "Ahh friend how has life been treating you this fine day?"]
    question2 = random.choice(questions)
    bot.send_message(message.chat.id, question2)
    
@bot.message_handler(content_types = ['text'])
def mood(message):  
    reply = message.text 
    blob = TextBlob(reply)
    positive_responses = ["That's good to hear",
                          "NICEEE, good for you",
                          "Look at you living the life :)",
                          "Let's rock!!!"]

    negative_responses = ["I'm sorry to hear that",
                          "Hopefully everything will get better",
                          "You'll get through this",
                          "Let me light your day up :)"]
    emo = []

    if blob.polarity > 0:
        sentence = random.choice(positive_responses)
        bot.send_message(message.chat.id, sentence)
        emo.append("P")
    else:
        sentence = random.choice(negative_responses)           
        bot.send_message(message.chat.id, sentence)
        emo.append("N")

    bot.send_message(message.chat.id, 'Now, how about some music to suit your mood? Y/N') 
    
@bot.message_handler(func=lambda message: message.text in ['Y', 'N']) 
def music(message, emo): 
    a = message.text
    # Find the most common emotion in the user's replies
    c = max(emo, key = emo.count)
    
    # Define an empty list to store the indices of the recommended songs
    check= []
        
    # If the user wants music recommendations, make an API request based on their emotion and tag
    if a.lower() == "y":
        # Ask the user for their favorite artist
        bot.send_message(message.chat.id, "Who is your favorite artist? name/none")
        artist = message.text
        # If the user has no preference, choose a random tag based on their emotion
        if artist.lower() == "none":
            if c == "P":
                tag = random.choice(["happy", "pop", "rock", "dance"])
            else:
                tag = random.choice(["sad", "blues", "indie", "metal"])
            # Make an API request with the tag and print the results
            url = f'http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={tag}&api_key=' + API_KEY + '&format=json'
            r = lastfm_get(url,{'method': 'tag.gettoptracks'})
            print(r.status_code)
            res = r.json()
            for i in range(10):
                j = random.choice(range(0, 50))
                for k in range(0,len(check)):
                    if (check[k]==j):
                        j = random.choice(range(0, 50))
                        k = 0
                check.append(j)
                # Use f-strings to format the output
                bot.send_message(message.chat.id, f"{res['tracks']['track'][j]['name']} by {res['tracks']['track'][j]['artist']['name']} - {res['tracks']['track'][j]['url']}")
        # If the user has a preference, make an API request with the artist and print the results
        else:
            url = f'http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={artist}&api_key=' + API_KEY + '&format=json'                    
            r = lastfm_get(url,{'method': 'artist.gettoptracks'})
            print(r.status_code)
            res = r.json()
            for i in range(10):
                j = random.choice(range(0, 50))
                for k in range(0,len(check)):
                    if (check[k]==j):
                        j = random.choice(range(0, 50))
                        k = 0
                check.append(j)
                # Use f-strings to format the output
                bot.send_message(message.chat.id, f"{res['toptracks']['track'][j]['name']} by {res['toptracks']['track'][j]['artist']['name']} - {res['toptracks']['track'][j]['url']}")
        # Ask the user if they are satisfied with the music recommendations
        bot.send_message(message.chat.id, "Are you satisfied with the music recommendations? Y/N")
        b = message.text
        # If the user is not satisfied, repeat the process until they are
        while b.lower() != "y":
            # Ask the user if they want to continue or quit
            bot.send_message(message.chat.id, "Do you want to continue or quit? C/Q")
            d = message.text
            # If the user wants to quit, break the loop
            if d.lower() == "q":
                break
            # If the user wants to continue, ask them for their favorite artist again
            else:
                bot.send_message(message.chat.id, "Who is your favorite artist? name/none")
                artist = message.text
                # If the user has no preference, choose a random tag based on their emotion
                if artist.lower() == "none":
                    if c == "P":
                        tag = random.choice(["happy", "pop", "rock", "dance"])
                    else:
                        tag = random.choice(["sad", "blues", "indie", "metal"])
                    # Make an API request with the tag and print the results
                    url = f'http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag={tag}&api_key=' + API_KEY + '&format=json'
                    r = lastfm_get(url,{'method': 'tag.gettoptracks'})
                    print(r.status_code)
                    res = r.json()
                    for i in range(10):
                        j = random.choice(range(0, 50))
                        for k in range(0,len(check)):
                            if (check[k]==j):
                                j = random.choice(range(0, 50))                                        
                                k = 0
                        check.append(j)
                        # Use f-strings to format the output
                        bot.send_message(message.chat.id, f"{res['tracks']['track'][j]['name']} by {res['tracks']['track'][j]['artist']['name']} - {res['tracks']['track'][j]['url']}")
                # If the user has a preference, make an API request with the artist and print the results
                else:
                    url = f'http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={artist}&api_key=' + API_KEY + '&format=json'
                    r = lastfm_get(url,{'method': 'artist.gettoptracks'})
                    print(r.status_code)
                    res = r.json()
                    for i in range(10):
                        j = random.choice(range(0, 50))
                        for k in range(0,len(check)):
                            if (check[k]==j):
                                j = random.choice(range(0, 50))
                                k = 0
                        check.append(j)
                        # Use f-strings to format the output
                        bot.send_message(message.chat.id, f"{res['toptracks']['track'][j]['name']} by {res['toptracks']['track'][j]['artist']['name']} - {res['toptracks']['track'][j]['url']}")
                # Ask the user if they are satisfied with the music recommendations again
                bot.send_message(message.chat.id, "Are you satisfied with the music recommendations? Y/N")
                b = message.text
    else:
        return
bot.infinity_polling()


# In[ ]:




