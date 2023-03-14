from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import (
    abc,
    to_float, 
    get_from_period,
    buy_sell_lots,
    in_portfolio,
    count_in_portfolio,
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


async def get_stability(trades: List[OperationItem], name: str, base_comm: float, shift: int = 0, count_after_portfolio: int = 0):
	buys = []; sells = []
	prof = 0; loss = 0

	for trade in trades:
		if trade.name == name:
			if shift != 0 and count_after_portfolio == 0:
				shift -= 1
				continue

			if trade.type == OperationType.OPERATION_TYPE_BUY:
				if count_after_portfolio != 0:
					count_after_portfolio -= 1
				quantity_b = trade.quantity
				min_price = min(abc(to_float(trade.payment) / trade.quantity), to_float(trade.price))
				trade_comm = base_comm * min_price * trade.quantity / 100
				next = 0

				if sells:
					for item in sells:
						if quantity_b == 0: break

						if quantity_b >= item[0] or not next:
							if (item[1] - min_price) * trade.quantity > (abc(item[2] + trade_comm)):
								prof += 1
							else:
								loss += 1

						if item[0] == quantity_b:
							quantity_b -= item[0]
							sells = sells[sells.index(item) + 1:]
							next = 0
						elif item[0] < quantity_b:
							quantity_b -= item[0]
							sells = sells[sells.index(item) + 1:]
							if not sells:
								buys.append([quantity_b, min_price, trade_comm])
							next = 1
						else:
							item[0] -= quantity_b
							quantity_b = 0
							sells = sells[sells.index(item):]
							next = 0
				else:
					buys.append([quantity_b, min_price, trade_comm])
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				if count_after_portfolio != 0:
					count_after_portfolio -= 1
				quantity_s = trade.quantity
				min_price = min(to_float(trade.payment) / trade.quantity, to_float(trade.price))
				trade_comm = base_comm * min_price * trade.quantity / 100
				next = 0

				if buys:
					for item in buys:
						if quantity_s == 0: break

						if quantity_s >= item[0] or not next:
							if (min_price - item[1]) * trade.quantity > (abc(item[2] + trade_comm)):
								prof += 1
							else:
								loss += 1

						if item[0] == quantity_s:
							quantity_s -= item[0]
							buys = buys[buys.index(item) + 1:]
							next = 0
						elif item[0] < quantity_s:
							quantity_s -= item[0]
							buys = buys[buys.index(item) + 1:]
							if not buys:
								sells.append([quantity_s, min_price, trade_comm])
							next = 1
						else:
							item[0] -= quantity_s
							quantity_s = 0
							buys = buys[buys.index(item):]
							next = 0
				else:
					sells.append([quantity_s, min_price, trade_comm])

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

			instrument: InstrumentResponse = await client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                id=trade.figi
            )
			base_comm = await commission_by_tariff(client, instrument.instrument.instrument_type)

			buy_lots, sell_lots = buy_sell_lots(trades, name)
			lots_count = await in_portfolio(client, account_id, figi)
			count, count_after, buy_lots, sell_lots = count_in_portfolio(trades, name, lots_count, buy_lots, sell_lots)

			if lots_count and not count:
				answer += f"<b>{name}</b>\nIncorrect terminal calculations.\n\n"
			else:
				if count:
					prof, loss = await get_stability(trades, name, base_comm, count, count_after)
				else:
					if buy_lots == sell_lots:
						prof, loss = await get_stability(trades, name, base_comm)
					else:
						prof, loss = await get_stability(trades, name, base_comm, min(buy_lots, sell_lots))

				prof_trades += prof
				loss_trades += loss
				count = f"Open positions: {count}\n\n" if count else "\n"
				answer += f"<b>{name}</b>\n🟢 {prof}     🔴 {loss}\n{count}" if prof or loss else ""

	return f"Profitable trades: {prof_trades}\nLosing trades: {loss_trades}\n\n" + answer
