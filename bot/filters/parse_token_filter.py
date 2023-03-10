from aiogram.dispatcher.filters import BoundFilter
from aiogram import types

from bot.misc.database.db import db


class ParseTokenFilter(BoundFilter):
	async def check(self, message: types.Message) -> bool:
		TOKEN = db.get_token(message.from_user.id)
		
		return message.text.startswith("t.") and TOKEN == "notoken"