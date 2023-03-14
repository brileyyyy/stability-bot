from aiogram import Dispatcher, types

from bot.tinkoff.api import get_accounts
from bot.tinkoff.api import cancel_orders
from bot.tinkoff.balance import get_balance
from bot.tinkoff.yieldd import get_operations_yield
from bot.tinkoff.stability import get_operations_stability
from bot.tinkoff.report import get_portfolio_report
from bot.tinkoff.history import get_operations_history
from bot.tinkoff.utils import get_trades_by_period

from bot.keyboards.inline.accounts import accounts_buttons
from bot.keyboards.inline.account_interaction_margin import account_interaction_buttons_margin
from bot.keyboards.inline.account_interaction import account_interaction_buttons
from bot.keyboards.inline.back import back_button
from bot.keyboards.inline.yield_period import yield_period_buttons
from bot.keyboards.inline.stability_period import stability_period_buttons
from bot.keyboards.inline.cancel_orders import cancel_orders_buttons
from bot.keyboards.inline.callback_data.callback_data import (
    acc_cb_data,
    acc_inter_cb_data,
    acc_inter_balance_cb_data,
    acc_inter_yield_cb_data,
    acc_inter_stability_cb_data,
    acc_inter_cancel_cb_data
)
from bot.filters.check_token_filter import CheckTokenFilter
from bot.misc.database.db import db

from tinkoff.invest import AioRequestError


# =================================   ACCOUNTS   =================================

async def accounts(message: types.Message):
    TOKEN = db.get_token(message.from_user.id)
    response = await get_accounts(TOKEN)

    await message.answer(f"Choose an account from the list below:", 
                        reply_markup=accounts_buttons(response, ""))


async def account_button(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")

    trades_count = len(await get_trades_by_period(acc_name, TOKEN, "per month"))
    
    reply_markup = account_interaction_buttons_margin(acc_name) \
    if trades_count > 40 \
    else account_interaction_buttons(acc_name)

    await call.message.edit_text(text=f"Here it is: {callback_data.get('acc_name')}\n"
                                "What do you want to do with the account?", 
                                reply_markup=reply_markup)


# ============================   ACCOUNT INTERACTIONS   ============================

async def account_interaction_balance(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get('acc_name')
    balance = await get_balance(acc_name, TOKEN)

    await call.message.edit_text(f"Balance on Account: {callback_data.get('acc_name')}\n\n"
                                f"{balance}", reply_markup=back_button(acc_name))


async def account_interaction_stability_period(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")

    await call.message.edit_text(f"Choose a period:\n",
                                reply_markup=stability_period_buttons(acc_name, False, ""))
    

async def account_interaction_stability(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    period = callback_data.get("period")
    stability = await get_operations_stability(acc_name, TOKEN, period)

    await call.message.edit_text(f"Stability on Account: {acc_name}\n\n{stability}",
                                 reply_markup=back_button(acc_name))


async def account_interaction_yield_period(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")

    await call.message.edit_text(f"Choose a period:\n",
                                reply_markup=yield_period_buttons(acc_name, False, ""))
    

async def account_interaction_yield(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    period = callback_data.get("period")
    yieldd = await get_operations_yield(acc_name, TOKEN, period)

    await call.message.edit_text(f"Yield on Account: {acc_name}\n\n{yieldd}", 
                                 reply_markup=back_button(acc_name))
    

async def account_interaction_report(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    ans = await get_portfolio_report(acc_name, TOKEN)

    await call.message.edit_text(f"Report on Account: {acc_name}\n\n{ans}",
                                 reply_markup=back_button(acc_name))
    

async def account_interaction_history(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    ans = await get_operations_history(acc_name, TOKEN)

    await call.message.edit_text(f"History on Account: {acc_name}\n\n{ans}",
                                 reply_markup=back_button(acc_name))


async def account_interaction_cancel_orders(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")

    await call.message.edit_text(f"You are about to cancel all orders on account: {acc_name}. Is that correct?",
                            reply_markup=cancel_orders_buttons(acc_name))

    
async def account_interaction_cancel_orders_confirm(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    try:
        await cancel_orders(acc_name, TOKEN)
        await call.answer("All orders have been cancelled.", show_alert=True)
    except AioRequestError as err:
        await call.answer(f"{err.metadata.message}. Maybe your token have read-only properties", 
                          show_alert=True)



async def account_interaction_back_button(call: types.CallbackQuery):
    TOKEN = db.get_token(call.from_user.id)
    response = await get_accounts(TOKEN)
    await call.message.edit_text(f"Choose an account from the list below:", 
                                reply_markup=accounts_buttons(response, ""))
    

# ===============================   REGISTRATION   ===============================

def register_accounts(dp: Dispatcher):
    dp.register_message_handler(accounts, CheckTokenFilter(), commands=["myaccounts"])
    dp.register_callback_query_handler(account_button,
        acc_cb_data.filter(id="acc") |
        acc_inter_balance_cb_data.filter(id="back") |
        acc_inter_stability_cb_data.filter(id="back") |
        acc_inter_yield_cb_data.filter(id="back") |
        acc_inter_cancel_cb_data.filter(id="back"))
    dp.register_callback_query_handler(account_interaction_balance, acc_inter_cb_data.filter(id="balance"))
    dp.register_callback_query_handler(account_interaction_stability_period, acc_inter_cb_data.filter(id="stability"))
    dp.register_callback_query_handler(account_interaction_stability, acc_inter_stability_cb_data.filter(id="period"))
    dp.register_callback_query_handler(account_interaction_yield_period, acc_inter_cb_data.filter(id="yield"))
    dp.register_callback_query_handler(account_interaction_yield, acc_inter_yield_cb_data.filter(id="period"))
    dp.register_callback_query_handler(account_interaction_report, acc_inter_cb_data.filter(id="report"))
    dp.register_callback_query_handler(account_interaction_history, acc_inter_cb_data.filter(id="history"))
    dp.register_callback_query_handler(account_interaction_cancel_orders, acc_inter_cb_data.filter(id="cancel"))
    dp.register_callback_query_handler(account_interaction_cancel_orders_confirm, acc_inter_cancel_cb_data.filter(id="yes"))
    dp.register_callback_query_handler(account_interaction_back_button, acc_inter_cb_data.filter(id="back"))


