import os

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types


class CheckTokenFilter(BoundFilter):
	async def check(self, message: types.Message) -> bool:
		response = 0
		TOKEN = os.environ["INVEST_TOKEN"]

		if (TOKEN):
			response = 1
		else:
			await message.answer("You don't have a token!\n"
								"Send me token to unlock all options. 👾")
		
		return response