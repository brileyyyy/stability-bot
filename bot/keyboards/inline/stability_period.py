from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards.inline.callback_data.callback_data import acc_inter_stability_cb_data


def stability_period_buttons(acc_name: str, direct: bool, pref: str) -> InlineKeyboardMarkup:
	stability_period = InlineKeyboardMarkup(row_width=1)

	per_day = InlineKeyboardButton("Per Day", callback_data=acc_inter_stability_cb_data.new(
		acc_name=acc_name, period="per day", id=f"period{pref}"
	))
	per_week = InlineKeyboardButton("Per Week", callback_data=acc_inter_stability_cb_data.new(
		acc_name=acc_name, period="per week", id=f"period{pref}"
	))
	per_month = InlineKeyboardButton("Per Month", callback_data=acc_inter_stability_cb_data.new(
		acc_name=acc_name, period="per month", id=f"period{pref}"
	))

	stability_period.insert(per_day)
	stability_period.insert(per_week)
	stability_period.insert(per_month)
	if not direct:
		back = InlineKeyboardButton("« Back to Account", callback_data=acc_inter_stability_cb_data.new(
			acc_name=acc_name, period="", id="back"
		))
		stability_period.insert(back)

	return stability_period