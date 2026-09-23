import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    spotify_client_id: str
    spotify_client_secret: str


def get_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "BOT_TOKEN is missing. Create a .env file based on .env.example."
        )

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID is missing. Create a .env file based on .env.example."
        )
    if not client_secret:
        raise RuntimeError(
            "SPOTIFY_CLIENT_SECRET is missing. Create a .env file based on .env.example."
        )

    return Settings(
        bot_token=token,
        spotify_client_id=client_id,
        spotify_client_secret=client_secret,
    )
