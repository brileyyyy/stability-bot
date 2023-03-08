from aiogram import Dispatcher, types


async def set_commands(dp: Dispatcher):
	await dp.bot.set_my_commands(
		[
			types.BotCommand("start", "start a dialog"),
			types.BotCommand("myaccounts", "your accounts"),
			types.BotCommand("balance", "account balance"),
			types.BotCommand("stability", "account stability"),
			types.BotCommand("yield", "account yield"),
			types.BotCommand("report", "account report"),
			types.BotCommand("history", "account history"),
			types.BotCommand("settoken", "register your TI token"),
			types.BotCommand("gettoken", "your TI token")
		]
	)