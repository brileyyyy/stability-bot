import os

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


class ParseTokenFilter(BoundFilter):
	async def check(self, message: types.Message) -> bool:
		TOKEN = os.environ["INVEST_TOKEN"]
		
		return message.text.startswith("t.") and not TOKEN