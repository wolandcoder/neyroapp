import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from config import API_TOKEN, logger


bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class PresentationForm(StatesGroup):
    waiting_for_style_command = State()     # Выбор: "Введи стиль" или "Вернуться назад"
    waiting_for_style_input = State()       # Ожидание ввода стиля
    waiting_for_query_command = State()     # Выбор: "Введи запрос" или "Вернуться назад"
    waiting_for_query_input = State()       # Ожидание ввода запроса


def get_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Создать презентацию")]
        ],
        resize_keyboard=True
    )


def get_style_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Введи стиль"),
                types.KeyboardButton(text="Вернуться назад")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_query_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Введи запрос"),
                types.KeyboardButton(text="Вернуться назад")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    response = "Привет! Добро пожаловать в бота для генерации презентаций.\nВыберите действие:"
    logger.info(f"/start от пользователя {message.from_user.id} ({message.from_user.username})")
    await message.answer(response, reply_markup=get_main_menu_keyboard())


@dp.message(lambda message: message.text == "Создать презентацию")
async def create_presentation_handler(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) выбрал 'Создать презентацию'")
    await state.set_state(PresentationForm.waiting_for_style_command)
    await message.answer("Выберите опцию:", reply_markup=get_style_keyboard())


@dp.message(StateFilter(PresentationForm.waiting_for_style_command))
async def style_command_handler(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) вернулся в главное меню (стиль)")
        await state.clear()
        await message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu_keyboard())
    elif message.text == "Введи стиль":
        logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) выбрал ввод стиля")
        await message.answer("Пожалуйста, введите стиль:", reply_markup=types.ForceReply())
        await state.set_state(PresentationForm.waiting_for_style_input)
    else:
        await message.answer("Пожалуйста, выберите одну из опций.", reply_markup=get_style_keyboard())


@dp.message(StateFilter(PresentationForm.waiting_for_style_input))
async def style_input_handler(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) ввёл стиль: {message.text}")
    await state.update_data(style=message.text)
    await message.answer("Стиль сохранён.\nТеперь выберите действие:", reply_markup=get_query_keyboard())
    await state.set_state(PresentationForm.waiting_for_query_command)


@dp.message(StateFilter(PresentationForm.waiting_for_query_command))
async def query_command_handler(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) вернулся в главное меню (запрос)")
        await state.clear()
        await message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu_keyboard())
    elif message.text == "Введи запрос":
        logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) выбрал ввод запроса")
        await message.answer("Пожалуйста, введите запрос:", reply_markup=types.ForceReply())
        await state.set_state(PresentationForm.waiting_for_query_input)
    else:
        await message.answer("Пожалуйста, выберите одну из опций.", reply_markup=get_query_keyboard())


class PresentationGenerator:
    def __init__(self):
        self.api_url = "http://localhost:8000"

    async def create_presentation(self, request: dict) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.api_url}/v1/generate", json=request) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise Exception(f"Ошибка API: {error_data}")
                data = await response.json()
                return data["presentation_id"]

    async def check_status(self, presentation_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/v1/status/{presentation_id}") as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise Exception(f"Ошибка проверки статуса: {error_data}")
                return await response.json()

    async def get_presentation(self, presentation_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/v1/presentation/{presentation_id}") as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise Exception(f"Ошибка получения презентации: {error_data}")
                return await response.json()

    async def generate_presentation(self, request: dict) -> dict:
        presentation_id = await self.create_presentation(request)

        while True:
            status_data = await self.check_status(presentation_id)
            if status_data["status"] in ["completed", "error"]:
                break
            await asyncio.sleep(1)
        if status_data["status"] == "completed":
            presentation = await self.get_presentation(presentation_id)
            return presentation
        else:
            raise Exception(f"Ошибка генерации: {status_data.get('error_message', 'Unknown error')}")


@dp.message(StateFilter(PresentationForm.waiting_for_query_input))
async def query_input_handler(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} ({message.from_user.username}) ввёл запрос: {message.text}")
    await state.update_data(query=message.text)
    data = await state.get_data()
    style = data.get("style", "не указан")
    query = data.get("query", message.text)

    await message.answer(f"Отправка запроса на сервер...\nСтиль: {style}\nЗапрос: {query}")

    request_payload = {
        "topic": query,
        "style": style,
        "slides_count": 7
    }
    generator = PresentationGenerator()
    try:
        presentation = await generator.generate_presentation(request_payload)
        presentation_url = f"{generator.api_url}{presentation.get('url', '')}"
        await message.answer(f"Презентация сгенерирована и доступна по адресу:\n{presentation_url}")
    except Exception as e:
        await message.answer(f"Ошибка генерации презентации:\n{str(e)}")

    await state.clear()
    await message.answer("Готово. Вы вернулись в главное меню.", reply_markup=get_main_menu_keyboard())
