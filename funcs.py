import aiohttp
from config import WEATHER_TOKEN

WEATHER_TOKEN = WEATHER_TOKEN

async def calculate_water_norm(city: str, weight: float, activity: float) -> int:
    base_water = weight * 30
    add_water_activity = (activity // 30) * 500
    add_water_weather = 0

    # Получаем данные о погоде через OpenWeatherMap API
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": WEATHER_TOKEN, "units": "metric"},
        ) as response:
            if response.status != 200:
                raise Exception(f"Не удалось получить данные о погоде. Статус: {response.status}")
            weather_data = await response.json()
            temperature = weather_data["main"]["temp"]

            if temperature > 25:
                add_water_weather = 500 if temperature <= 30 else 1000

    water = base_water + add_water_activity + add_water_weather
    return round(water)