import os
from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import (
    abc,
    to_float, 
    round, 
    get_from_period,
    buy_sell_equal,
    lots_count_equal
)

from tinkoff.invest import (
	Client,
	PortfolioResponse,
	GetOperationsByCursorRequest,
	OperationItem,
	OperationType,
	ShareResponse,
	InstrumentIdType
)


def get_stability(trades: List[OperationItem], name: str, count_in_lot: int, shift: int = 0) -> float:
	buys = []; sells = []
	prof = 0; loss = 0

	for trade in reversed(trades):
		if trade.name == name:
			if (shift > 0):
				shift -= 1
				continue

			if trade.type == OperationType.OPERATION_TYPE_BUY:
				quantity_b = trade.quantity
				price = abc(to_float(trade.payment) / trade.quantity)
				comm_of_one = to_float(trade.commission) / (quantity_b / count_in_lot)

				if sells:
					for item in sells:
						if quantity_b == 0: break

						if (item[1] - price) * trade.quantity > (abc(item[2] + to_float(trade.commission))):
							prof += 1
						else:
							loss += 1

						if item[0] == quantity_b:
							quantity_b -= item[0]
							sells = sells[sells.index(item) + 1:]
						elif item[0] < quantity_b:
							quantity_b -= item[0]
							sells = sells[sells.index(item) + 1:]
							if not sells:
								buys.append([quantity_b, price, comm_of_one * (quantity_b / count_in_lot)])
						else:
							item[0] -= quantity_b
							quantity_b = 0
							sells = sells[sells.index(item):]
				else:
					buys.append([quantity_b, price, to_float(trade.commission)])
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				quantity_s = trade.quantity
				price = to_float(trade.payment) / trade.quantity
				comm_of_one = to_float(trade.commission) / (quantity_s / count_in_lot)
				# пересчитать комиссию (1.2 != 1.02)

				if buys:
					for item in buys:
						if quantity_s == 0: break

						if (price - item[1]) * trade.quantity > (abc(item[2] + to_float(trade.commission))):
							prof += 1
						else:
							loss += 1

						if item[0] == quantity_s:
							quantity_s -= item[0]
							buys = buys[buys.index(item) + 1:]
						elif item[0] < quantity_s:
							quantity_s -= item[0]
							buys = buys[buys.index(item) + 1:]
							if not buys:
								sells.append([quantity_s, price, comm_of_one * (quantity_s / count_in_lot)])
						else:
							item[0] -= quantity_s
							quantity_s = 0
							buys = buys[buys.index(item):]
				else:
					sells.append([quantity_s, price, to_float(trade.commission)])

	return [prof, loss]


def count_in_portfolio(trades: List[OperationItem], name: str, quantity: int, buy: int, sell: int, buy_lots: int, sell_lots: int) -> float:
	buys = []; sells = []
	count_in_portfolio = 0
	last_operation = None

	i = 0
	while i < len(trades):
		if trades[i].name == name:
			if trades[i].type == OperationType.OPERATION_TYPE_BUY:
				quantity_b = trades[i].quantity

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
			elif trades[i].type == OperationType.OPERATION_TYPE_SELL:
				quantity_s = trades[i].quantity

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
		i += 1

	return [count_in_portfolio, last_operation, buy, sell, buy_lots, sell_lots]


def in_portfolio(client: Client, account_id: str, figi: str) -> int:
	quantity: int = 0
	response: PortfolioResponse = client.operations.get_portfolio(account_id=account_id)
	
	for position in response.positions:
		if position.figi == figi:
			quantity = round(to_float(position.quantity))
			break
		
	return quantity


def last_portfolio_operation_handler(trades, name, buy, sell, buy_lots, sell_lots, count, count_in_lot):
	m = buy - count

	if m == sell:
		prof, loss = get_stability(trades, name, count_in_lot)
	elif m < sell:
		if buy_lots == sell_lots:
			prof, loss = get_stability(trades, name, count_in_lot)
		else:
			mod = sell - m
			prof, loss = get_stability(trades, name, count_in_lot, mod)
	else:
		if buy_lots == sell_lots:
			prof, loss = get_stability(trades, name, count_in_lot)
		else:
			mod = m - sell
			prof, loss = get_stability(trades, name, count_in_lot, mod)

	return [prof, loss]
		

def get_operations_stability(acc_name: str, period: str):
	TOKEN = os.environ["INVEST_TOKEN"]
	trades: List[OperationItem] = []
	prof_trades = 0; loss_trades = 0
	answer = ""

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id
				break

		fr = get_from_period(period)
		def get_request(cursor=""):
			return GetOperationsByCursorRequest(
				account_id=account_id,
				from_=fr,
				cursor=cursor,
				operation_types=[OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL],
			)

		operations = client.operations.get_operations_by_cursor(get_request())
		for item in operations.items:
			if item.trades_info.trades:
				trades.append(item)

		while operations.has_next:
			request = get_request(cursor=operations.next_cursor)
			operations = client.operations.get_operations_by_cursor(request)
			for item in operations.items:
				if item.trades_info.trades:
					trades.append(item)

		unique_trades = set()
		for trade in trades:
			unique_trades.add(trade.name)

		for name in unique_trades:
			for trade in trades:
				if trade.name == name:
					figi = trade.figi
					break

			quantity = in_portfolio(client, account_id, figi)
			instrument: ShareResponse = client.instruments.share_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                id=trade.figi
            )
			count_in_lot = instrument.instrument.lot
			buy, sell, buy_lots, sell_lots = buy_sell_equal(trades, name, client)

			count, last_operation, buy, sell, buy_lots, sell_lots = count_in_portfolio(trades, name, quantity, buy, sell, buy_lots, sell_lots)

			if count:
				if count > 0 and last_operation == OperationType.OPERATION_TYPE_SELL:
					last_operation = OperationType.OPERATION_TYPE_BUY
				elif count < 0 and last_operation == OperationType.OPERATION_TYPE_BUY:
					last_operation = OperationType.OPERATION_TYPE_SELL

				if last_operation == OperationType.OPERATION_TYPE_BUY:
					prof, loss = last_portfolio_operation_handler(trades, name, buy, sell, buy_lots, sell_lots, count, count_in_lot)
				elif last_operation == OperationType.OPERATION_TYPE_SELL:
					prof, loss = last_portfolio_operation_handler(trades, name, sell, buy, buy_lots, sell_lots, count, count_in_lot)
			else:
				if buy_lots == sell_lots:
					prof, loss = get_stability(trades, name, count_in_lot)
				else:
					c = lots_count_equal(trades, name)
					mod = (buy + sell) - c
					prof, loss = get_stability(trades, name, count_in_lot, mod)

			prof_trades += prof
			loss_trades += loss
			answer += f"<b>{name}</b>\n🟢 {prof}     🔴 {loss}\n\n" if prof or loss else ""

	return f"Profitable trades: {prof_trades}\nLosing trades: {loss_trades}\n\n" + answer
