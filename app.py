from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import asyncio
import logging

from bot.config import get_config

from bot.handlers.start import register_on_start
from bot.handlers.accounts import register_accounts
from bot.handlers.accounts_from_commands import register_accounts_from_commands
from bot.handlers.token import register_token_options

from bot.misc.set_commands import set_commands

from bot.filters.start_filter import StartFilter
from bot.filters.check_token_filter import CheckTokenFilter
from bot.filters.parse_token_filter import ParseTokenFilter


def register_all_filters(dp: Dispatcher):
	dp.filters_factory.bind(StartFilter)
	dp.filters_factory.bind(CheckTokenFilter)
	dp.filters_factory.bind(ParseTokenFilter)

def register_all_handlers(dp: Dispatcher):
	register_token_options(dp)
	register_on_start(dp)
	register_accounts(dp)
	register_accounts_from_commands(dp)


async def main():
	load_dotenv()

	logging.basicConfig(
		level=logging.INFO,
		format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s'
	)

	config = get_config(".env")

	bot = Bot(token=config.bot.token, parse_mode="HTML") #proxy="http://proxy.server:3128")
	storage = RedisStorage2() if config.bot.use_redis else MemoryStorage()
	dp = Dispatcher(bot, storage=storage)

	bot['config'] = config

	await set_commands(dp)
	register_all_filters(dp)
	register_all_handlers(dp)

	try:
		await dp.start_polling()
	finally:
		await dp.storage.close()
		await dp.storage.wait_closed()
		await bot.session.close()


if __name__ == "__main__":
	asyncio.run(main())