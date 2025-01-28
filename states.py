from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    name = State()
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    calories_goal = State()
    sex = State()

class LogWater(StatesGroup):
    volume_water = State()

class LogFood(StatesGroup):
    type_food = State()
    amount_food = State()

class LogActivity(StatesGroup):
    type_activity = State()
    time_activity = State()