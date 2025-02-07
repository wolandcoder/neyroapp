from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN, logger

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


class PresentationForm(StatesGroup):
    waiting_for_style_command = State()
    waiting_for_style_input = State()
    waiting_for_query_command = State()
    waiting_for_query_input = State()


def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Создать презентацию")
    return keyboard


def get_style_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Введи стиль", "Вернуться назад")
    return keyboard


def get_query_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add("Введи запрос", "Вернуться назад")
    return keyboard


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    response = "Привет! Добро пожаловать в бота для генерации презентаций.\nВыберите действие:"
    logger.info(f"Запуск /start от пользователя {message.from_user.id}")
    await message.reply(response, reply_markup=get_main_menu_keyboard())


@dp.message_handler(lambda message: message.text == "Создать презентацию", state="*")
async def create_presentation_handler(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Создать презентацию'")
    await PresentationForm.waiting_for_style_command.set()
    await message.reply("Выберите опцию:", reply_markup=get_style_keyboard())


@dp.message_handler(state=PresentationForm.waiting_for_style_command)
async def style_command_handler(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню (стиль)")
        await state.finish()
        await message.reply("Вы вернулись в главное меню.", reply_markup=get_main_menu_keyboard())
    elif message.text == "Введи стиль":
        logger.info(f"Пользователь {message.from_user.id} выбрал ввод стиля")

        await message.reply("Пожалуйста, введите стиль:", reply_markup=types.ForceReply())
        await PresentationForm.waiting_for_style_input.set()
    else:
        await message.reply("Пожалуйста, выберите одну из опций.", reply_markup=get_style_keyboard())


@dp.message_handler(state=PresentationForm.waiting_for_style_input)
async def style_input_handler(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} ввёл стиль: {message.text}")

    await state.update_data(style=message.text)
    await message.reply("Стиль сохранён.\nТеперь выберите действие:", reply_markup=get_query_keyboard())
    await PresentationForm.waiting_for_query_command.set()


@dp.message_handler(state=PresentationForm.waiting_for_query_command)
async def query_command_handler(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню (запрос)")
        await state.finish()
        await message.reply("Вы вернулись в главное меню.", reply_markup=get_main_menu_keyboard())
    elif message.text == "Введи запрос":
        logger.info(f"Пользователь {message.from_user.id} выбрал ввод запроса")

        await message.reply("Пожалуйста, введите запрос:", reply_markup=types.ForceReply())
        await PresentationForm.waiting_for_query_input.set()
    else:
        await message.reply("Пожалуйста, выберите одну из опций.", reply_markup=get_query_keyboard())


@dp.message_handler(state=PresentationForm.waiting_for_query_input)
async def query_input_handler(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} ввёл запрос: {message.text}")

    await state.update_data(query=message.text)
    data = await state.get_data()
    style = data.get("style", "не указан")
    query = data.get("query", message.text)

    await message.reply(f"Отправка запроса на сервер...\nСтиль: {style}\nЗапрос: {query}")

    # TODO json

    await state.finish()

    await message.reply("Готово. Вы вернулись в главное меню.", reply_markup=get_main_menu_keyboard())