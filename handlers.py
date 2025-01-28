from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form, LogWater, LogFood, LogActivity
import aiohttp
from funcs import calculate_water_norm
from config import FOOD_ID, FOOD_TOKEN
import matplotlib.pyplot as plt
from io import BytesIO

router = Router()

profiles = {}
water_logs = {}
food_logs = {}
workout_logs = {}

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я бот для расчёта нормы воды, "
                        "калорий и трекинга активности.\n"
                        "Перед началом работы нужно создать свой профиль. Прошу честно ответить "
                        "на несколько вопросов, после которых я рассчитаю для вас нормы воды и калорий."
                        "\nДля настройки своего профиля введите /set_profile"
                        "\nВведите /help если хотите просмотреть полный список доступных команд."
                        )

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/view_profiles - Посмотреть все профили\n"
        "/set_profile - Настроить профиль\n"
        "/log_water - добавить объем выпитой воды\n"
        "/log_food - добавить количество употребленных калорий\n"
        "/log_activity - добавить физическую нагрузку\n"
        "/check_progress - показать мой прогресс\n"
        "/plot_progress - показать прогресс на графике\n"
        "/delete - отменить последний ввод данных"
    )

# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await message.reply("Как вас зовут?")
    await state.set_state(Form.name)

@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if weight <= 0:
            raise ValueError("Вес должен быть положительным числом.")
        await state.update_data(weight=weight)
        await message.reply("Введите ваш рост (в см):")
        await state.set_state(Form.height)
    except ValueError:
        await message.reply("Пожалуйста, введите корректный вес (число больше 0).")

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        if height <= 0:
            raise ValueError("Рост должен быть положительным числом.")
        await state.update_data(height=height)
        await message.reply("Введите ваш возраст:")
        await state.set_state(Form.age)
    except ValueError:
        await message.reply("Пожалуйста, введите корректный рост (число больше 0).")

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age <= 0 or age > 100:
            raise ValueError("Возраст должен быть в пределах от 1 до 100.")
        await state.update_data(age=age)
        await message.reply("Введите ваш пол одной буквой (м или ж):")
        await state.set_state(Form.sex)
    except ValueError:
        await message.reply("Пожалуйста, введите корректный возраст (целое число от 1 до 100).")

@router.message(Form.sex)
async def process_sex(message: Message, state: FSMContext):
    sex = message.text.strip().lower()
    if sex in ["м", "ж"]:
        await state.update_data(sex=sex)
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(Form.activity)
    else:
        await message.reply("Пожалуйста, введите корректный пол (м или ж).")

@router.message(Form.activity)
async def process_activity(message: Message, state: FSMContext):
    try:
        activity = float(message.text)
        if activity < 0:
            raise ValueError("Активность не может быть отрицательной.")
        await state.update_data(activity=activity)
        await message.reply("В каком городе вы находитесь?")
        await state.set_state(Form.city)
    except ValueError:
        await message.reply("Пожалуйста, введите корректное число минут активности (число 0 или больше).")

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.reply("Введите желаемый лимит калорий (опционально, "
                        "поставьте прочерк (`-`), если не определились, я посчитаю его за вас)"
                        )
    await state.set_state(Form.calories_goal)

@router.message(Form.calories_goal)
async def process_calories_goal(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if message.text.strip() == "-":
        # Если прочерк
        user_data = await state.get_data()
        sex_factor = 5 if user_data["sex"].lower() == "м" else -161
        calories = (
            10 * user_data["weight"]
            + 6.25 * user_data["height"]
            - 5 * user_data["age"]
            + sex_factor
        )
        calories *= 1.2 + (user_data["activity"] / 100)
        calories_goal = round(calories)
        await state.update_data(calories_goal=calories_goal)
        await message.reply(f"Ваш рассчитанный лимит калорий: {calories_goal} ккал.")
    else:
        #Если калории введены
        try:
            calories_goal = int(message.text)
            if calories_goal <= 0:
                raise ValueError("Лимит калорий должен быть положительным числом.")
            await state.update_data(calories_goal=calories_goal)
            await message.reply(f"Ваш лимит калорий сохранён: {calories_goal} ккал.")
        except ValueError:
            await message.reply(
                "Пожалуйста, введите корректный лимит калорий (число больше 0) или прочерк (`-`) для автоподсчёта.")
            return

    # вода
    city = user_data["city"]
    weight = user_data["weight"]
    activity = user_data["activity"]
    try:
        water_norm = await calculate_water_norm(city, weight, activity)
        await state.update_data(water_norm=water_norm)
        await message.reply(f"Ваша норма потребления воды: {water_norm} мл.")
    except Exception as e:
        await message.reply(f"Ошибка при расчёте нормы воды: {e}")

    user_id = message.from_user.id
    user_data = await state.get_data()

    profiles[user_id] = {
        "name": user_data["name"],
        "weight": user_data["weight"],
        "height": user_data["height"],
        "age": user_data["age"],
        "sex": user_data["sex"],
        "activity": user_data["activity"],
        "city": user_data["city"],
        "calories_goal": user_data["calories_goal"],
        "calories_burned_all": 0,
        "water_norm": user_data["water_norm"],
    }

    await message.reply(f"Профиль сохранён: {profiles[user_id]}")
    await state.clear()

# для просмотра созданных профилей
@router.message(Command("view_profiles"))
async def view_profiles(message: Message):
    user_id = message.from_user.id
    if user_id in profiles:
        await message.reply(f"Ваш профиль: {profiles[user_id]}")
    else:
        await message.reply("У вас ещё нет сохранённого профиля.")

# для установки активного профиля
#@router.message(Command("active_profile"))
#async def active_profile(message: Message):
#    global active_profile
#    user_id = message.text
#    if message.text not in profiles.keys():
#        await message.reply(f"Профиля {user_id} не существует!"
#                            f"Сначала создайте его через /set_profile")

#    active_profile = user_id
#    await message.reply(f"Профиль {user_id} выбран в качестве текущего.")

# логирование воды
@router.message(Command("log_water"))
async def log_water(message: Message, state: FSMContext):
    await message.reply(f"Введите количество выпитой воды (в мл)")
    await state.set_state(LogWater.volume_water)

@router.message(LogWater.volume_water)
async def process_log_water(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in profiles:
        await message.reply("У вас нет активного профиля. Создайте его командой /set_profile.")
        return
    try:
        water_amount = int(message.text)
        if water_amount <= 0:
            raise ValueError("Количество воды должно быть больше нуля.")

        if user_id not in water_logs:
            water_logs[user_id] = []
        water_logs[user_id].append(water_amount)

       # norm = profiles.get(user_id, {}).get("water_norm")
        norm = profiles[user_id]['water_norm']
        remaining = max(0, norm - sum(water_logs[user_id]))

        await message.reply(
            f"Добавлено: {water_amount} мл воды. Всего выпито: {water_logs[user_id]} мл. "
            f"Осталось выпить до достижения нормы: {remaining} мл."
        )
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите корректное количество воды (целое число больше 0).")

# логирование еды
@router.message(Command("log_food"))
async def log_water(message: Message, state: FSMContext):
    await message.reply(f"Введите название съеденного продукта (на английском языке)")
    await state.set_state(LogFood.type_food)

@router.message(LogFood.type_food)
async def process_log_food_type(message: Message, state: FSMContext):
    food_name = message.text.strip()
    await state.update_data(food_name=food_name)

    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://trackapi.nutritionix.com/v2/natural/nutrients",
                headers={
                    "x-app-id": FOOD_ID,
                    "x-app-key": FOOD_TOKEN,
                },
                json={"query": food_name},
        ) as response:
            if response.status != 200:
                await message.reply("Не удалось получить данные о продукте. "
                                    "Проверьте правильность написания названия на английском языке."
                                    )
                await state.clear()
                return

            data = await response.json()
            if "foods" not in data or not data["foods"]:
                await message.reply("Продукт не найден. Попробуйте снова.")
                await state.clear()
                return

            food_info = data["foods"][0]
            calories_per_100g = food_info["nf_calories"]
            await state.update_data(calories_per_100g=calories_per_100g)

            await message.reply(
                f"{food_info['food_name'].capitalize()} — {calories_per_100g:.2f} ккал на 100 г.\n"
                f"Сколько грамм вы съели?"
            )
            await state.set_state(LogFood.amount_food)

@router.message(LogFood.amount_food)
async def process_log_food_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError("Количество должно быть больше нуля.")

        user_data = await state.get_data()
        calories_per_100g = user_data["calories_per_100g"]
        food_name = user_data["food_name"]
        total_calories = (calories_per_100g / 100) * amount

        user_id = message.from_user.id
        if user_id not in profiles:
            await message.reply("У вас нет активного профиля. Создайте его командой /set_profile.")
            return
        if user_id not in food_logs:
            food_logs[user_id] = []
        food_logs[user_id].append(total_calories)

        await message.reply(
            f"Записано: {total_calories:.2f} ккал ({amount} г {food_name.capitalize()})."
        )
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите корректное количество (число больше 0).")

@router.message(Command("log_activity"))
async def log_activity(message: Message, state: FSMContext):
    await message.reply(f"Укажите каким видом спорта вы занимались (на английском языке)")
    await state.set_state(LogActivity.type_activity)

@router.message(LogActivity.type_activity)
async def process_log_activity_type(message: Message, state: FSMContext):
    activity_name = message.text.strip()
    await state.update_data(activity_name=activity_name)
    await message.reply("Укажите длительность тренировки (в минутах)")
    await state.set_state(LogActivity.time_activity)

@router.message(LogActivity.time_activity)
async def process_log_activity_time(message: Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError("Длительность тренировки должна быть больше нуля.")

        user_data = await state.get_data()
        activity_name = user_data["activity_name"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://trackapi.nutritionix.com/v2/natural/exercise",
                headers={
                    "x-app-id": FOOD_ID,
                    "x-app-key": FOOD_TOKEN,
                },
                json={
                    "query": f"{duration} minutes of {activity_name}",
                },
            ) as response:
                if response.status != 200:
                    await message.reply("Не удалось получить данные о тренировке. Проверьте ввод.")
                    await state.clear()
                    return

                data = await response.json()
                if "exercises" not in data or not data["exercises"]:
                    await message.reply("Тренировка не найдена. Попробуйте снова.")
                    await state.clear()
                    return

                exercise_info = data["exercises"][0]
                calories_burned = exercise_info["nf_calories"]

                user_id = message.from_user.id
                if user_id not in profiles:
                    await message.reply("У вас нет активного профиля. Создайте его командой /set_profile.")
                    return
                if user_id not in workout_logs:
                    workout_logs[user_id] = []
                workout_logs[user_id].append(calories_burned)
                profiles[user_id]["calories_burned_all"] += calories_burned

                await message.reply(
                    f"🏋️‍♂️ {activity_name.capitalize()} {duration} минут — {calories_burned:.2f} ккал истрачено."
                )
                await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, укажите корректное время тренировки (целое число больше 0).")

@router.message(Command("check_progress"))
async def check_progress(message: Message):
    user_id = message.from_user.id
    if user_id not in profiles:
        await message.reply("У вас нет активного профиля. Создайте его командой /set_profile.")
        return
    # вода
    drunk = drunk = sum(water_logs.get(user_id, 0))
    norm_water = profiles.get(user_id, {}).get("water_norm")
    to_res_water = max(0, norm_water - drunk)
    # калории
    consumed_calories = sum(food_logs.get(user_id, 0))
    norm_food = profiles.get(user_id, {}).get("calories_goal")
    burned_calories = profiles.get(user_id, {}).get("calories_burned_all")
    balance = consumed_calories - burned_calories

    result =\
    f'''
    Прогресс:
    Вода:
    - Выпито: {drunk} мл из {norm_water} мл
    - Осталось: {to_res_water} мл
    Калории:
    - Потреблено: {consumed_calories} ккал из {norm_food} ккал
    - Сожжено: {burned_calories} ккал
    - Энергетический баланс: {balance} ккал
    '''
    await message.answer(result)

@router.message(Command('delete'))
async def delete(message: Message, state: FSMContext):
    await state.clear()
    await message.reply("Отмена ввода")

@router.message(Command("plot_progress"))
async def plot_progress(message: Message):
    user_id = message.from_user.id

    if user_id not in profiles:
        await message.reply("У вас нет активного профиля. Создайте его командой /set_profile.")
        return

    if user_id not in water_logs or user_id not in food_logs:
        await message.reply("У вас ещё нет достаточных данных для построения графика.")
        return

    water_data = water_logs.get(user_id, [])
    food_data = food_logs.get(user_id, [])

    plt.figure(figsize=(10, 6))
    # вода
    plt.subplot(2, 1, 1)
    plt.plot(range(1, len(water_data) + 1), [sum(water_data[:i]) for i in range(1, len(water_data) + 1)], marker='o', label="Вода")
    plt.axhline(y=profiles[user_id]['water_norm'], color='r', linestyle='--', label="Норма воды")
    plt.title("Прогресс по воде")
    plt.xlabel("День")
    plt.ylabel("Выпито (мл)")
    plt.legend()
    # калории
    plt.subplot(2, 1, 2)
    plt.plot(range(1, len(food_data) + 1), [sum(food_data[:i]) for i in range(1, len(food_data) + 1)], marker='o', label="Калории", color="orange")
    plt.axhline(y=profiles[user_id]['calories_goal'], color='r', linestyle='--', label="Цель калорий")
    plt.title("Прогресс по калориям")
    plt.xlabel("День")
    plt.ylabel("Потреблено (ккал)")
    plt.legend()
    plt.tight_layout()

    # Для сохранения графика
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    photo = BufferedInputFile(buffer.read(), filename="progress.png")
    await message.answer_photo(photo=photo, caption="Ваш прогресс по воде и калориям 📊")