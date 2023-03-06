from aiogram.utils.callback_data import CallbackData


acc_cb_data = CallbackData("acc", "acc_name", "id")
acc_inter_cb_data = CallbackData("acc_inter", "acc_name", "id")
acc_inter_balance_cb_data = CallbackData("acc_inter_balance", "acc_name", "id")
acc_inter_yield_cb_data = CallbackData("acc_inter_yield", "acc_name", "period", "id")
acc_inter_stability_cb_data = CallbackData("acc_inter_stability", "acc_name", "period", "id")
acc_inter_cancel_cb_data = CallbackData("acc_inter_cancel", "acc_name", "id")