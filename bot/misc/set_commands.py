from aiogram import Dispatcher, types


async def set_commands(dp: Dispatcher):
	await dp.bot.set_my_commands(
		[
			types.BotCommand("start", "start a dialog"),
			types.BotCommand("myaccounts", "your accounts")
		]
	)