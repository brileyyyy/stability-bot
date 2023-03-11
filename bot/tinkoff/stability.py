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
    commission_by_tariff
)

from tinkoff.invest import (
	AsyncClient,
	GetOperationsByCursorRequest,
	OperationItem,
	OperationType,
	InstrumentResponse,
	InstrumentIdType
)


async def get_stability(client: AsyncClient, trades: List[OperationItem], name: str, count_in_lot: int, shift: int = 0) -> float:
	buys = []; sells = []
	prof = 0; loss = 0

	for trade in reversed(trades):
		if trade.name == name:
			if (shift > 0):
				shift -= 1
				continue

			if trade.type == OperationType.OPERATION_TYPE_BUY:
				quantity_b = trade.quantity
				# price_b_1 = abc(to_float(trade.payment) / trade.quantity)
				# price_b_2 = to_float(trade.price)
				min_price = min(abc(to_float(trade.payment) / trade.quantity), to_float(trade.price))
				comm_of_one = await commission_by_tariff(client, trade.instrument_type) * (min_price * (trade.quantity / count_in_lot))

				if sells:
					for item in sells:
						if quantity_b == 0: break

						if quantity_b >= item[0]:
							if (item[1] - min_price) * trade.quantity > (abc(item[2] + to_float(trade.commission))):
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
								buys.append([quantity_b, min_price, comm_of_one * (quantity_b / count_in_lot)])
						else:
							item[0] -= quantity_b
							quantity_b = 0
							sells = sells[sells.index(item):]
				else:
					buys.append([quantity_b, min_price, to_float(trade.commission)])
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				quantity_s = trade.quantity
				# price_s_1 = to_float(trade.payment) / trade.quantity
				# price_s_2 = to_float(trade.price)
				min_price = min(to_float(trade.payment) / trade.quantity, to_float(trade.price))
				comm_of_one = await commission_by_tariff(client, trade.instrument_type) * (min_price * (trade.quantity / count_in_lot))

				if buys:
					for item in buys:
						if quantity_s == 0: break

						if quantity_s >= item[0]:
							if (min_price - item[1]) * trade.quantity > (abc(item[2] + to_float(trade.commission))):
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
								sells.append([quantity_s, min_price, comm_of_one * (quantity_s / count_in_lot)])
						else:
							item[0] -= quantity_s
							quantity_s = 0
							buys = buys[buys.index(item):]
				else:
					sells.append([quantity_s, min_price, to_float(trade.commission)])

	return [prof, loss]


async def last_portfolio_operation_handler(client, trades, name, buy, sell, buy_lots, sell_lots, count, count_in_lot):
	m = buy - count

	if m == sell:
		prof, loss = await get_stability(client, trades, name, count_in_lot)
	elif m < sell:
		if buy_lots == sell_lots:
			prof, loss = await get_stability(client, trades, name, count_in_lot)
		else:
			mod = sell - m
			prof, loss = await get_stability(client, trades, name, count_in_lot, mod)
	else:
		if buy_lots == sell_lots:
			prof, loss = await get_stability(client, trades, name, count_in_lot)
		else:
			mod = m - sell
			prof, loss = await get_stability(client, trades, name, count_in_lot, mod)

	return [prof, loss]
		

async def get_operations_stability(acc_name: str, TOKEN: str, period: str):
	trades: List[OperationItem] = []
	prof_trades = 0; loss_trades = 0
	answer = ""

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

		operations = await client.operations.get_operations_by_cursor(get_request())
		for item in operations.items:
			if item.trades_info.trades:
				trades.append(item)

		while operations.has_next:
			request = get_request(cursor=operations.next_cursor)
			operations = await client.operations.get_operations_by_cursor(request)
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

			quantity = await in_portfolio(client, account_id, figi)
			instrument: InstrumentResponse = await client.instruments.get_instrument_by(
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
					prof, loss = await last_portfolio_operation_handler(client, trades, name, buy, sell, buy_lots, sell_lots, count, count_in_lot)
				elif last_operation == OperationType.OPERATION_TYPE_SELL:
					prof, loss = await last_portfolio_operation_handler(client, trades, name, sell, buy, buy_lots, sell_lots, count, count_in_lot)
			else:
				if buy_lots == sell_lots:
					prof, loss = await get_stability(client, trades, name, count_in_lot)
				else:
					c = lots_count_equal(trades, name)
					mod = (buy + sell) - c
					prof, loss = await get_stability(client, trades, name, count_in_lot, mod)

			prof_trades += prof
			loss_trades += loss
			answer += f"<b>{name}</b>\n🟢 {prof}     🔴 {loss}\n\n" if prof or loss else ""

	return f"Profitable trades: {prof_trades}\nLosing trades: {loss_trades}\n\n" + answer
