import asyncio
from telegram_bot import dp
from aiogram import executor
import functools


async def main():
    loop = asyncio.get_running_loop()
    polling = functools.partial(executor.start_polling, dp, skip_updates=True)
    await loop.run_in_executor(None, polling)


if __name__ == '__main__':
    asyncio.run(main())
