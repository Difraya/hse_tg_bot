from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")
FOOD_TOKEN = os.getenv("FOOD_TOKEN")
FOOD_ID = os.getenv("FOOD_ID")

