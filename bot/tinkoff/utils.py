from datetime import datetime, timedelta
from typing import List

from bot.tinkoff.api import get_accounts

from tinkoff.invest import (
    AsyncClient, 
    MoneyValue,
    GetOperationsByCursorRequest,
    GetOperationsByCursorResponse,
    OperationsResponse,
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


async def get_trades_by_period(acc_name: str, TOKEN: str, period: str):
	trades: List[OperationItem] = []

	async with AsyncClient(TOKEN) as client:
		accounts = await get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

		fr = get_from_period(period)
		def get_request(cursor=""):
			return GetOperationsByCursorRequest(
				account_id=account_id,
				from_=fr,
				cursor=cursor,
				operation_types=[OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL],
			)

		operations: GetOperationsByCursorResponse = await client.operations.get_operations_by_cursor(get_request())
		for item in operations.items:
			if item.trades_info.trades:
				trades.append(item)

		while operations.has_next:
			request = get_request(cursor=operations.next_cursor)
			operations = await client.operations.get_operations_by_cursor(request)
			for item in operations.items:
				if item.trades_info.trades:
					trades.append(item)

	return trades


async def get_fee_by_period(acc_name: str, TOKEN: str, period: str):
	service_fee = 0; margin_fee = 0
	
	async with AsyncClient(TOKEN) as client:
		accounts = await get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

		fr = get_from_period(period)
		operations: OperationsResponse = await client.operations.get_operations(
			account_id=account_id,
			from_=fr,
		)
		for op in operations.operations:
			if op.operation_type == OperationType.OPERATION_TYPE_SERVICE_FEE:
				service_fee = to_float(op.payment)
			elif op.operation_type == OperationType.OPERATION_TYPE_MARGIN_FEE:
				margin_fee = to_float(op.payment)

			if service_fee and margin_fee:
				break

	return [service_fee, margin_fee]


def buy_sell_lots(trades: List[OperationItem], name: str):
	buy_lots = 0; sell_lots = 0

	for trade in trades:
		if trade.name == name:
			if trade.type == OperationType.OPERATION_TYPE_BUY:
				buy_lots += trade.quantity
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				sell_lots += trade.quantity
	
	return [buy_lots, sell_lots]


async def in_portfolio(client: AsyncClient, account_id: str, figi: str) -> int:
	quantity: int = 0
	response: PortfolioResponse = await client.operations.get_portfolio(account_id=account_id)
	
	for position in response.positions:
		if position.figi == figi:
			quantity = round(to_float(position.quantity))
			break
		
	return quantity


def count_in_portfolio(trades: List[OperationItem], name: str, quantity: int, buy_lots: int, sell_lots: int) -> float:
	buys = []; sells = []
	count_in_portfolio = 0; count_after_portfolio = 0
	i = 0

	for trade in trades:
		if trade.name == name:
			i += 1
			if trade.type == OperationType.OPERATION_TYPE_BUY:
				quantity_b = trade.quantity
				count_after_portfolio += 1

				if sells:
					for item in sells:
						if quantity_s == 0: break

						if item == quantity_b:
							sells.pop(0)
						elif item < quantity_b:
							sells.pop(0)
							buys.append(quantity_b - item)
						else:
							item -= quantity_b
							quantity_b = 0
				else:
					buys.append(quantity_b)
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				quantity_s = trade.quantity
				count_after_portfolio += 1

				if buys:
					for item in buys:
						if quantity_s == 0: break

						if item == quantity_s:
							buys.pop(0)
						elif item < quantity_s:
							buys.pop(0)
							sells.append(quantity_s - item)
						else:
							item -= quantity_s
							quantity_s = 0
				else:
					sells.append(quantity_s)

			if sum(buys) == quantity:
				count_in_portfolio = len(buys)
				buy_lots -= sum(buys)
				if i == len(buys):
					count_after_portfolio = 0
				break
			elif -sum(sells) == quantity:
				count_in_portfolio = len(sells)
				sell_lots -= sum(sells)
				if i == len(sells):
					count_after_portfolio = 0
				break

	return [count_in_portfolio, count_after_portfolio, buy_lots, sell_lots]


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
		