from aiogram import Dispatcher, types

from bot.filters.check_token_filter import CheckTokenFilter
from bot.filters.parse_token_filter import ParseTokenFilter
from bot.misc.database.db import db

from tinkoff.invest import RequestError, Client


async def get_option(message: types.Message):
	TOKEN = db.get_token(message.from_user.id)

	await message.answer(f"Here is your TI token:\n\n<code>{TOKEN}</code>")


async def set_option(message: types.Message):
	await message.answer("Send me a token string.")


async def parse_token(message: types.Message):
	TOKEN = db.get_token(message.from_user.id)

	try:
		with Client(message.text):
			pass

		db.set_token(message.from_user.id, message.text)
		if TOKEN == "notoken":
			ans = "You have registered a TI token! 🔥\nNow you have access to all options of Stability."
		else:
			ans = "You have updated a TI token!"
			
	except RequestError:
		ans = "Invalid token string."

	await message.answer(ans)


def register_token_options(dp: Dispatcher):
	dp.register_message_handler(get_option, CheckTokenFilter(), commands="gettoken")
	dp.register_message_handler(set_option, commands="settoken")
	dp.register_message_handler(parse_token, ParseTokenFilter())