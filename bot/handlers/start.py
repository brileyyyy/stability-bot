from aiogram import Dispatcher, types

from bot.filters.start_filter import StartFilter

from bot.misc.database.db import db


async def on_start(message: types.Message):
	if not db.user_exists(message.from_user.id):
		db.add_user(message.from_user.id)

	await message.answer("Hi!\n"
						"My name is Stability and I'm only friends with account holders in Tinkoff Investments. 👾\n\n"
						"You can control me by sending these commands:\n\n"
						"/myaccounts - your accounts\n\n"
						"<b>Interaction</b>\n"
						"/balance - account balance\n"
						"/stability - account stability\n"
						"/yield - account yield\n"
						"/report - account report\n"
						"/history - account history\n\n"
						"<b>Tokens</b>\n"
						"/settoken - register your TI token\n"
						"/gettoken - your TI token")


def register_on_start(dp: Dispatcher):
	dp.register_message_handler(on_start, StartFilter())
	