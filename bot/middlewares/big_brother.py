import logging

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types

class BigBrother(BaseMiddleware):
	#1
	async def on_pre_process_update(self, update: types.Update, data: dict):
		logging.info("--------------- new update ---------------")
		
		logging.info("1. Pre Process Update")
		logging.info("Next point: Process Update")

		data["middleware_data"] = "Hello from pre_process_update"

	#2
	async def on_process_update(self, update: types.Update, data: dict):
		logging.info("2. Process Update")
		logging.info(f"Data: {data}")
		logging.info("Next point: Pre Process Message")

	#3
	async def on_pre_process_message(self, message: types.Message, data: dict):
		logging.info("3. Pre Process Message")
		logging.info("Next point: Filters")

		data["middleware_data"] = "Hello from pre_process_message!"

	#4 Filters

	#5
	async def on_process_message(self, message: types.Message, data: dict):
		logging.info("5. Process Message")
		logging.info(f"Data: {data}")
		logging.info("Next point: Handlers")

	#6 Handlers

	#7
	async def on_post_process_message(self, message: types.Message, from_handler: list, data: dict):
		logging.info("7. Post Process Message")
		logging.info(f"Data: {data}")
		logging.info(f"Data from Handler: {from_handler}")
		logging.info("Next point: Post Process Update")

	#8
	async def on_post_process_update(self, update: types.Update, from_handler: list, data: dict):
		logging.info("8. Post Process Update")
		logging.info(f"Data: {data}")
		logging.info(f"Data from Handler: {from_handler}")

		logging.info("--------------- end ---------------")

