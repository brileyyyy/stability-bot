from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.inline.callback_data.callback_data import acc_inter_yield_cb_data


def yield_period_buttons(callback_data: dict) -> InlineKeyboardMarkup:
	yield_period = InlineKeyboardMarkup(row_width=1)

	per_day = InlineKeyboardButton("Per Day", callback_data=acc_inter_yield_cb_data.new(
		acc_name=callback_data.get("acc_name"), period="per day", id="period"
	))
	per_week = InlineKeyboardButton("Per Week", callback_data=acc_inter_yield_cb_data.new(
		acc_name=callback_data.get("acc_name"), period="per week", id="period"
	))
	per_month = InlineKeyboardButton("Per Month", callback_data=acc_inter_yield_cb_data.new(
		acc_name=callback_data.get("acc_name"), period="per month", id="period"
	))
	back = InlineKeyboardButton("« Back to Account", callback_data=acc_inter_yield_cb_data.new(
		acc_name=callback_data.get("acc_name"), period="", id="back"
	))

	yield_period.insert(per_day)
	yield_period.insert(per_week)
	yield_period.insert(per_month)
	yield_period.insert(back)

	return yield_period