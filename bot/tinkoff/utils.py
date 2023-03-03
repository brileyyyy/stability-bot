import os
from datetime import datetime, timedelta
from typing import List

from bot.tinkoff.api import get_accounts

from tinkoff.invest import (
    Client, 
    MoneyValue, 
    RequestError,
    OperationItem,
    OperationType,
)


def abc(nano):
	return nano if nano >= 0 else -nano


def to_float(amount: MoneyValue) -> float:
	if amount.units <= 0 and amount.nano < 0:
		return amount.units - float(f"0.{abc(amount.nano)}")
	else:
		return amount.units + float(f"0.{abc(amount.nano)}")


def round(value: float) -> float:
	return int(value) if value - int(value) == 0 else float("{:.2f}".format(value))


def get_from_period(period: str) -> datetime:
	to = datetime.now()
	fr = datetime.now()
	if period == "per day":
		fr = datetime.replace(to, hour=0, minute=0, second=0, microsecond=0)
	elif period == "per week":
		fr = to - timedelta(days=6)
		fr = fr.replace(hour=0, minute=0, second=0, microsecond=0)
	elif period == "per month":
		fr = to - timedelta(days=29)
		fr = fr.replace(hour=0, minute=0, second=0, microsecond=0)

	return fr


def is_margin_trading(acc_name: str):
	TOKEN = os.environ["INVEST_TOKEN"]

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id
				break

		try:
			client.users.get_margin_attributes(account_id=account_id)
			err = 1
		except RequestError:
			err = 0

	return err


def buy_sell_equal(trades: List[OperationItem], name: str, client: Client):
	buy = 0; sell = 0
	buy_lots = 0; sell_lots = 0

	for trade in trades:
		if trade.name == name:
			if trade.type == OperationType.OPERATION_TYPE_BUY:
				buy += 1
				buy_lots += trade.quantity
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				sell += 1
				sell_lots += trade.quantity
	
	return [buy, sell, buy_lots, sell_lots]


def lots_count_equal(trades: List[OperationItem], name: str):
	b = 0; s = 0
	c = 0; max = 0

	for trade in trades:
		if trade.name == name:
			if trade.type == OperationType.OPERATION_TYPE_BUY:
				b += trade.quantity
				c += 1
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				s += trade.quantity
				c += 1

			if b == s:
				max = c

	return max
		