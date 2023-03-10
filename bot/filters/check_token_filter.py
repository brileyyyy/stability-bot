from aiogram.dispatcher.filters import BoundFilter
from aiogram import types

from bot.misc.database.db import db


class CheckTokenFilter(BoundFilter):
	async def check(self, message: types.Message) -> bool:
		response = 0
		TOKEN = db.get_token(message.from_user.id)

		if TOKEN == "notoken":
			await message.answer("You don't have a token!\n"
								"Send me token to unlock all options. 👾")
		else:
			response = 1
		
		return response