from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.inline.callback_data.callback_data import acc_inter_balance_cb_data


def balance_buttons(acc_name: dict) -> InlineKeyboardMarkup:
	balance = InlineKeyboardMarkup(row_width=1)

	back = InlineKeyboardButton("« Back to Account", callback_data=acc_inter_balance_cb_data.new(
		acc_name=acc_name, id="back"
	))

	balance.insert(back)

	return balance

