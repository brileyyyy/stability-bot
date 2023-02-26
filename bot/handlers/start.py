from aiogram import Dispatcher, types

from bot.filters.start_filter import StartFilter


async def on_start(message: types.Message):
	await message.answer("Hi!\n"
						"My name is Stability and I'm only friends with account holders in Tinkoff Investments. 👾\n\n"
						"You can control me by sending these commands:\n\n"
						"/myaccounts - your accounts\n\n"
						"<b>Interaction</b>\n"
						"/balance - your balance\n"
						"/stability - your stability\n"
						"/cancelorders - cancel all orders\n\n"
						"<b>Tokens</b>\n"
						"/settoken - register your TI token\n"
						"/gettoken - your TI token")


def register_on_start(dp: Dispatcher):
	dp.register_message_handler(on_start, StartFilter())
	