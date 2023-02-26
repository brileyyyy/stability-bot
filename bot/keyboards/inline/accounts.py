from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from tinkoff.invest import GetAccountsResponse

from bot.keyboards.inline.callback_data.callback_data import acc_cb_data


def accounts_buttons(response: GetAccountsResponse) -> InlineKeyboardMarkup:
	accounts = InlineKeyboardMarkup(row_width=1)

	for account in response.accounts:
		accounts.insert(
                InlineKeyboardButton(f"{account.name}", callback_data=acc_cb_data.new(
					acc_name=account.name, id="acc"
				))
            )

	return accounts