# Sonora

Sonora is a standalone Telegram music search bot. This repository currently contains the initial production-ready foundation and Telegram layer.

## Current status

- Bot starts with Telegram Bot API using aiogram 3.x
- Handles `/start`
- Accepts normal text messages as music search queries
- Returns a temporary "search received" response
- Includes a provider abstraction for future music sources

## Setup

1. Create and activate a virtual environment (if not already active).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create your local environment file:
   ```bash
   copy .env.example .env
   ```
4. Put your real Telegram token into `.env`:
   ```env
   BOT_TOKEN=your_real_token_here
   ```

## Run

```bash
python main.py
```

## Project structure

```text
Sonora_Bot/
??? bot/
?   ??? __init__.py
?   ??? handlers/
?   ?   ??? __init__.py
?   ?   ??? start.py
?   ?   ??? search.py
?   ??? providers/
?       ??? __init__.py
?       ??? base.py
??? config.py
??? main.py
??? requirements.txt
??? .env.example
??? .gitignore
??? README.md
```
