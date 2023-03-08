from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tinkoff.invest import GetAccountsResponse

from bot.keyboards.inline.callback_data.callback_data import acc_cb_data


def accounts_buttons(response: GetAccountsResponse, command: str) -> InlineKeyboardMarkup:
	accounts = InlineKeyboardMarkup(row_width=1)

	if command:
		for account in response:
			accounts.insert(
					InlineKeyboardButton(f"{account.name}", callback_data=acc_cb_data.new(
						acc_name=account.name, id=command
					))
				)
	else:
		for account in response:
			accounts.insert(
					InlineKeyboardButton(f"{account.name}", callback_data=acc_cb_data.new(
						acc_name=account.name, id="acc"
					))
				)

	return accounts