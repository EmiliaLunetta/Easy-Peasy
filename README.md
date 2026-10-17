# Easy Peasy Chatbot

> A mood-based music and movie recommendation bot on Telegram, powered by **Sentiment Analysis**, the **Last.fm API**, and **IMDb web scraping**.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![pyTelegramBotAPI](https://img.shields.io/badge/pyTelegramBotAPI-4.12.0-blue)](https://github.com/eternnoir/pyTelegramBotAPI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## About The Project

**Easy Peasy Chatbot** is designed to lift your spirits and brighten your day. By chatting with you and asking about your day, weather, and feelings, the bot analyzes your current mood using Natural Language Processing (NLP) and delivers personalized entertainment:

- **Music Recommendations:** Fetches tracks via the **Last.fm API** based on your favorite artists and emotional tags.
- **Movie Recommendations:** Scrapes **IMDb** to suggest suitable movies along with titles, synopses, and posters.

---

## Key Features

- **Mood Detection:** Uses `TextBlob` to perform sentiment polarity analysis on user replies (classifying mood as positive or negative).
- **Interactive Conversation Flow:** Built using `pyTelegramBotAPI`'s `register_next_step_handler` and custom interactive keyboards (`ReplyKeyboardMarkup`).
- **Dynamic Music Suggestions:** Supports artist-based lookups and random emotion-tagged songs.
- **Rich Movie Previews:** Web scraping with `BeautifulSoup` to display posters and plot introductions directly inside Telegram.
- **Feedback Loop:** Asks if you are satisfied with the suggestions, repeating the search until you find something you like.

---

## Built With (Tech Stack)

- **Language:** Python
- **Bot Framework:** `pyTelegramBotAPI` (telebot)
- **Sentiment Analysis:** `TextBlob`
- **Web Scraping & APIs:** `BeautifulSoup4`, `requests`
- **Environment Management:** `python-dotenv`

---

## Chatbot Logic & Workflow

```text
[Greeting] ──> [Ask Mood/Weather/Day Questions] ──> [Sentiment Analysis (TextBlob)]
                                                              │
                                                        [User Mood: +/-]
                                                              │
                    ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
                    ▼                                                                                   ▼
      [Music Recommendation (Y/N)]                                                        [Movie Recommendation (Y/N)]
        ├── No  ──> Go to Movies                                                            ├── No  ──> Goodbye!
        └── Yes ──> Ask Favorite Artist                                                     └── Yes ──> Scrape IMDb based on mood
                     ├── Specific Artist: Recommend tracks                                               ├── Send Title, Poster & Synopsis
                     └── "None": Recommend by emotion tag                                                └── Satisfied?
                           └── Satisfied?                                                                     ├── Yes ──> Goodbye!
                                 ├── Yes ──> Go to Movies                                                     └── No  ──> Suggest other movies
                                 └── No  ──> Recommend more songs
```

---

## Getting Started

### Prerequisites

- Python 3.8 or higher installed on your machine.
- A Telegram account to get a bot token from [@BotFather](https://t.me/botfather).
- A [Last.fm API Account](https://www.last.fm/api) to get your API Key & Secret.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/easy-peasy-chatbot.git
   cd easy-peasy-chatbot
   ```

2. **Create and activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download TextBlob NLTK corpora:**
   ```bash
   python -m textblob.download_corpora
   ```

---

## Configuration

1. Create a `.env` file in the root directory by copying the example file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your credentials:
   ```env
   BOT_TOKEN="your_telegram_bot_token_here"
   LASTFM_API_KEY="your_lastfm_api_key_here"
   LASTFM_API_SECRET="your_lastfm_api_secret_here"
   ```

---

## Usage

Start the chatbot by running:

```bash
python bot.py
```

Now open Telegram, search for your bot, and send `/start` or a greeting to begin chatting!

---

## References & Acknowledgments

This project was built with inspiration and references from:
- [Vecna Telegram Bot](https://github.com/ananyathomas/Vecna)
- [Dataquest: How to Connect to the Last.fm API](https://www.dataquest.io/blog/last-fm-api-python/)
- [Habr: Creating Telegram Bots with pyTelegramBotAPI](https://habr.com/ru/articles/580408/)

---
