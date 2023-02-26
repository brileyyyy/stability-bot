import os

from aiogram import Dispatcher, types

from bot.filters.check_token_filter import CheckTokenFilter
from bot.filters.parse_token_filter import ParseTokenFilter

from tinkoff.invest import RequestError

from bot.tinkoff.api import get_accounts


async def get_option(message: types.Message):
	TOKEN = os.environ["INVEST_TOKEN"]
	await message.answer(f"Here is your TI token:\n\n<code>{TOKEN}</code>")


async def set_option(message: types.Message):
	TOKEN = os.environ["INVEST_TOKEN"]
	if TOKEN:
		await message.answer("You are already register a token.")
	else:
		await message.answer("Send me a token string.")


async def parse_token(message: types.Message):
	os.environ["INVEST_TOKEN"] = message.text
	try:
		get_accounts()
		ans = "You have registered a TI token! 🔥\nNow you have access to all options of Stability."
	except RequestError:
		os.environ["INVEST_TOKEN"] = ""
		ans = "Invalid token string."

	await message.answer(ans)


def register_token_options(dp: Dispatcher):
	dp.register_message_handler(get_option, CheckTokenFilter(), commands="gettoken")
	dp.register_message_handler(set_option, commands="settoken")
	dp.register_message_handler(parse_token, ParseTokenFilter())