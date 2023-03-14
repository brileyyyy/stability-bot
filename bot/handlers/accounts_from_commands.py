from aiogram import Dispatcher, types

from bot.tinkoff.api import get_accounts
from bot.tinkoff.balance import get_balance
from bot.tinkoff.yieldd import get_operations_yield
from bot.tinkoff.stability import get_operations_stability
from bot.tinkoff.report import get_portfolio_report
from bot.tinkoff.history import get_operations_history
from bot.tinkoff.utils import get_trades_by_period

from bot.keyboards.inline.accounts import accounts_buttons
from bot.keyboards.inline.yield_period import yield_period_buttons
from bot.keyboards.inline.stability_period import stability_period_buttons
from bot.keyboards.inline.callback_data.callback_data import (
    acc_cb_data,
    acc_inter_yield_cb_data,
    acc_inter_stability_cb_data,
)
from bot.filters.check_token_filter import CheckTokenFilter
from bot.misc.database.db import db

from tinkoff.invest import GetAccountsResponse


# =================================   ACCOUNTS   =================================

async def accounts(message: types.Message):
    TOKEN = db.get_token(message.from_user.id)
    command = message.get_command()
    response: GetAccountsResponse = await get_accounts(TOKEN)
    margin_accounts = []
    accounts = []

    for account in response:
        if len(await get_trades_by_period(account.name, TOKEN, "per month")) > 40:
            margin_accounts.append(account)
        else:
            accounts.append(account)

    if command == "/yield" or command == "/stability":
        res = margin_accounts
    elif command == "/report" or command == "/history":
        res = accounts
    else:
        res = response

    await message.answer(f"Choose an account from the list below:", 
						reply_markup=accounts_buttons(res, command[1:]))


# ============================   ACCOUNT INTERACTIONS   ============================

async def account_interaction_balance(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get('acc_name')
    balance = await get_balance(acc_name, TOKEN)

    await call.message.edit_text(f"Balance on Account: {callback_data.get('acc_name')}\n\n"
                                 f"{balance}")


async def account_interaction_stability_period(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")

    await call.message.edit_text(f"Choose a period:\n",
                                reply_markup=stability_period_buttons(acc_name, True, "_direct"))
    

async def account_interaction_stability(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    period = callback_data.get("period")
    stability = await get_operations_stability(acc_name, TOKEN, period)

    await call.message.edit_text(f"Stability on Account: {acc_name}\n\n{stability}", reply_markup=None)


async def account_interaction_yield_period(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")

    await call.message.edit_text(f"Choose a period:\n",
                                reply_markup=yield_period_buttons(acc_name, True, "_direct"))
    

async def account_interaction_yield(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    period = callback_data.get("period")
    yieldd = await get_operations_yield(acc_name, TOKEN, period)

    await call.message.edit_text(f"Yield on Account: {acc_name}\n\n{yieldd}")
    

async def account_interaction_report(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    ans = await get_portfolio_report(acc_name, TOKEN)

    await call.message.edit_text(f"Report on Account: {acc_name}\n\n{ans}")
    

async def account_interaction_history(call: types.CallbackQuery, callback_data: dict):
    TOKEN = db.get_token(call.from_user.id)
    acc_name = callback_data.get("acc_name")
    ans = await get_operations_history(acc_name, TOKEN)

    await call.message.edit_text(f"History on Account: {acc_name}\n\n{ans}")
    

# ===============================   REGISTRATION   ===============================

def register_accounts_from_commands(dp: Dispatcher):
    dp.register_message_handler(accounts, CheckTokenFilter(), commands=["balance", "stability", "yield", "report", "history"])
    dp.register_callback_query_handler(account_interaction_balance, acc_cb_data.filter(id="balance"))
    dp.register_callback_query_handler(account_interaction_stability_period, acc_cb_data.filter(id="stability"))
    dp.register_callback_query_handler(account_interaction_stability, acc_inter_stability_cb_data.filter(id="period_direct"))
    dp.register_callback_query_handler(account_interaction_yield_period, acc_cb_data.filter(id="yield"))
    dp.register_callback_query_handler(account_interaction_yield, acc_inter_yield_cb_data.filter(id="period_direct"))
    dp.register_callback_query_handler(account_interaction_report, acc_cb_data.filter(id="report"))
    dp.register_callback_query_handler(account_interaction_history, acc_cb_data.filter(id="history"))
