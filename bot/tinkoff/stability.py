import os
from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import (
    abc,
    to_float, 
    get_from_period,
    buy_sell_equal,
    in_portfolio,
    count_in_portfolio,
    lots_count_equal,
)

from tinkoff.invest import (
	Client,
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
				price_b_1 = abc(to_float(trade.payment) / trade.quantity)
				price_b_2 = to_float(trade.price)
				min_price_b = min(price_b_1, price_b_2)
				comm_of_one = to_float(trade.commission) / (quantity_b / count_in_lot)

				if sells:
					for item in sells:
						if quantity_b == 0: break

						if quantity_b >= item[0]:
							if (item[1] - min_price_b) * trade.quantity > (abc(item[2] + to_float(trade.commission))):
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
								buys.append([quantity_b, min_price_b, comm_of_one * (quantity_b / count_in_lot)])
						else:
							item[0] -= quantity_b
							quantity_b = 0
							sells = sells[sells.index(item):]
				else:
					buys.append([quantity_b, min_price_b, to_float(trade.commission)])
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				quantity_s = trade.quantity
				price_s_1 = to_float(trade.payment) / trade.quantity
				price_s_2 = to_float(trade.price)
				min_price_s = min(price_s_1, price_s_2)
				comm_of_one = to_float(trade.commission) / (quantity_s / count_in_lot)

				if buys:
					for item in buys:
						if quantity_s == 0: break

						if quantity_s >= item[0]:
							if (min_price_s - item[1]) * trade.quantity > (abc(item[2] + to_float(trade.commission))):
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
								sells.append([quantity_s, min_price_s, comm_of_one * (quantity_s / count_in_lot)])
						else:
							item[0] -= quantity_s
							quantity_s = 0
							buys = buys[buys.index(item):]
				else:
					sells.append([quantity_s, min_price_s, to_float(trade.commission)])

	return [prof, loss]


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
			buy, sell, buy_lots, sell_lots = buy_sell_equal(trades, name)

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
