from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.inline.callback_data.callback_data import acc_inter_cancel_cb_data


def cancel_orders_buttons(callback_data: dict) -> InlineKeyboardMarkup:
	cancel_choice = InlineKeyboardMarkup(row_width=1)

	yes = InlineKeyboardButton("Yes", callback_data=acc_inter_cancel_cb_data.new(
		acc_name=callback_data.get("acc_name"),id="yes"
	))
	back = InlineKeyboardButton("« Back to Account", callback_data=acc_inter_cancel_cb_data.new(
		acc_name=callback_data.get("acc_name"), id="back"
	))

	cancel_choice.insert(yes)
	cancel_choice.insert(back)

	return cancel_choice