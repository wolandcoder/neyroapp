from telegram_bot import dp, bot
import asyncio


async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())