from datetime import datetime, timedelta
from typing import List

from tinkoff.invest import (
    AsyncClient, 
    MoneyValue, 
    OperationItem,
    OperationType,
    PortfolioResponse,
    GetInfoResponse
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


def buy_sell_equal(trades: List[OperationItem], name: str):
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


async def in_portfolio(client: AsyncClient, account_id: str, figi: str) -> int:
	quantity: int = 0
	response: PortfolioResponse = await client.operations.get_portfolio(account_id=account_id)
	
	for position in response.positions:
		if position.figi == figi:
			quantity = round(to_float(position.quantity))
			break
		
	return quantity


def count_in_portfolio(trades: List[OperationItem], name: str, quantity: int, buy: int, sell: int, buy_lots: int, sell_lots: int) -> float:
	buys = []; sells = []
	count_in_portfolio = 0
	last_operation = None

	for trade in trades:
		if trade.name == name:
			if trade.type == OperationType.OPERATION_TYPE_BUY:
				quantity_b = trade.quantity

				if sells:
					for item in sells:
						if quantity_s == 0: break

						if item == quantity_b:
							sells.pop(0)
							buy -= 1
							sell -= 1
						elif item < quantity_b:
							sells.pop(0)
							sell -= 1
							buys.append(quantity_b - item)
						else:
							item -= quantity_b
							quantity_b = 0
				else:
					buys.append(quantity_b)
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				quantity_s = trade.quantity

				if buys:
					for item in buys:
						if quantity_s == 0: break

						if item == quantity_s:
							buys.pop(0)
							buy -= 1
							sell -= 1
						elif item < quantity_s:
							buys.pop(0)
							buy -= 1
							sells.append(quantity_s - item)
						else:
							item -= quantity_s
							quantity_s = 0
				else:
					sells.append(quantity_s)

			if sum(buys) == quantity:
				count_in_portfolio = len(buys)
				buy_lots -= sum(buys)
				last_operation = OperationType.OPERATION_TYPE_BUY
				break
			elif -sum(sells) == quantity:
				count_in_portfolio = len(sells)
				sell_lots -= sum(sells)
				last_operation = OperationType.OPERATION_TYPE_SELL
				break

	return [count_in_portfolio, last_operation, buy, sell, buy_lots, sell_lots]


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


def currency_by_ticker(curr: str) -> str:
	if curr == "rub":
		res = "₽"
	if curr == "usd":
		res = "$"
	elif curr == "eur":
		res = "€"
	elif curr == "cny" or curr == "jpy":
		res = "¥"
	elif curr == "gbr":
		res = "£"

	return res


async def commission_by_tariff(client: AsyncClient, type: str) -> float:
	comm = 0.
	tariff: GetInfoResponse = await client.users.get_info()

	def investor_tariff():
		res = 0.
		if type == "share" or type == "bond" or type == "etf":
			res = 0.3
		elif type == "gold" or type == "silver":
			res = 1.9
		elif type == "currency":
			res = 0.9
		elif type == "future":
			res = 0.3
		elif type == "option":
			res = 3
		return res
	
	def trader_tariff():
		res = 0.
		if type == "share" or type == "bond" or type == "etf":
			res = 0.05
		elif type == "gold" or type == "silver":
			res = 1.5
		elif type == "currency":
			res = 0.5
		elif type == "future":
			res = 0.04
		elif type == "option":
			res = 2
		return res
	
	def premium_tariff():
		res = 0.
		if type == "share" or type == "bond" or type == "etf":
			res = 0.04
		elif type == "gold" or type == "silver":
			res = 0.9
		elif type == "currency":
			res = 0.4
		elif type == "future":
			res = 0.025
		elif type == "option":
			res = 2
		return res
	
	if tariff.tariff == "trader":
		comm = trader_tariff()
	elif tariff.tariff == "investor":
		comm = investor_tariff()
	elif tariff.tariff == "premium":
		comm = premium_tariff()

	return comm
		