from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


class StartFilter(BoundFilter):
	async def check(self, message: types.Message) -> bool:
		return message.text == "/start" or message.text[0] != '/'