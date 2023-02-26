from aiogram import Dispatcher, types

from bot.tinkoff.api import get_accounts
from bot.tinkoff.balance import get_balance
from bot.tinkoff.yield_ import get_operations_yield
from bot.tinkoff.report import get_portfolio_report
from bot.tinkoff.utils import is_margin_trading

from bot.keyboards.inline.accounts import accounts_buttons
from bot.keyboards.inline.account_interaction_margin import account_interaction_buttons_margin
from bot.keyboards.inline.account_interaction import account_interaction_buttons
from bot.keyboards.inline.balance import balance_buttons
from bot.keyboards.inline.yield_period import yield_period_buttons
from bot.keyboards.inline.cancel_orders import cancel_orders_buttons
from bot.keyboards.inline.callback_data.callback_data import (
    acc_cb_data,
    acc_inter_cb_data,
    acc_inter_balance_cb_data,
    acc_inter_yield_cb_data,
    acc_inter_cancel_cb_data
)
from bot.filters.check_token_filter import CheckTokenFilter


# =================================   ACCOUNTS   =================================

async def accounts(message: types.Message):
    response = get_accounts()
    await message.answer(f"Choose an account from the list below:", 
                            reply_markup=accounts_buttons(response))


async def account_button(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")
    reply_markup = account_interaction_buttons_margin(acc_name) \
    if is_margin_trading(acc_name) \
    else account_interaction_buttons(acc_name)

    await call.message.edit_text(text=f"Here it is: {callback_data.get('acc_name')}\n"
                                "What do you want to do with the account?", 
                                reply_markup=reply_markup)


# ============================   ACCOUNT INTERACTIONS   ============================

async def account_interaction_balance(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get('acc_name')
    balance = get_balance(acc_name)

    await call.message.edit_text(f"Balance on Account: {callback_data.get('acc_name')}\n\n"
                                f"{balance}", reply_markup=balance_buttons(acc_name))


async def account_interaction_stability(call: types.CallbackQuery, callback_data: dict):
    await call.message.edit_text(f"Stability on Account: {callback_data.get('acc_name')}")


async def account_interaction_yield_period(call: types.CallbackQuery, callback_data: dict):
    await call.message.edit_text(f"Choose a period:\n",
                                reply_markup=yield_period_buttons(callback_data))


async def account_interaction_yield(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")
    period = callback_data.get("period")
    yield_ = get_operations_yield(acc_name, period)
    await call.message.edit_text(f"Yield on Account: {acc_name}\n\n{yield_}", 
                                 reply_markup=balance_buttons(acc_name))
    

async def account_interaction_report(call: types.CallbackQuery, callback_data: dict):
    acc_name = callback_data.get("acc_name")
    ans = get_portfolio_report(acc_name)

    await call.message.edit_text(f"Report on Account: {acc_name}\n\n{ans}",
                                 reply_markup=balance_buttons(acc_name))


# def cancel_orders():
#     with Client(TOKEN) as client:
#         response: GetAccountsResponse = get_accounts()
#         account, *_ = response.accounts
#         account_id = account.id
        # logger.info("Orders: %s", client.orders.get_orders(account_id=account_id))
        # client.cancel_all_orders(account_id=account_id)
        # logger.info("Orders: %s", client.orders.get_orders(account_id=account_id))

async def account_interaction_cancel_orders(call: types.CallbackQuery, callback_data: dict):
    await call.message.edit_text(f"Are you sure you want to cancel all orders?",
                            reply_markup=cancel_orders_buttons(callback_data))


async def account_interaction_back_button(call: types.CallbackQuery):
    response = get_accounts()
    await call.message.edit_text(f"Choose an account from the list below:", 
                                reply_markup=accounts_buttons(response))
    

# ===============================   REGISTRATION   ===============================

def register_accounts(dp: Dispatcher):
    dp.register_message_handler(accounts, CheckTokenFilter(), commands=["myaccounts", "balance", "stability", "cancelorders"])
    dp.register_callback_query_handler(account_button,
        acc_cb_data.filter(id="acc") |
        acc_inter_cancel_cb_data.filter(id="back") |
        acc_inter_balance_cb_data.filter(id="back") |
        acc_inter_yield_cb_data.filter(id="back"))
    dp.register_callback_query_handler(account_interaction_balance, acc_inter_cb_data.filter(id="balance"))
    dp.register_callback_query_handler(account_interaction_stability, acc_inter_cb_data.filter(id="stability"))
    dp.register_callback_query_handler(account_interaction_yield_period, acc_inter_cb_data.filter(id="yield"))
    dp.register_callback_query_handler(account_interaction_yield, acc_inter_yield_cb_data.filter(id="period"))
    dp.register_callback_query_handler(account_interaction_report, acc_inter_cb_data.filter(id="report"))
    dp.register_callback_query_handler(account_interaction_cancel_orders, acc_inter_cb_data.filter(id="cancel"))
    dp.register_callback_query_handler(account_interaction_back_button, acc_inter_cb_data.filter(id="back"))

