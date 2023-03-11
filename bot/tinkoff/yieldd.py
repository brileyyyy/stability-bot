from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import (
    abc,
    to_float,
    round,
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
	GetOperationsByCursorResponse,
	OperationsResponse,
	OperationItem,
	OperationType
)


async def get_yield(client: AsyncClient, trades: List[OperationItem], name: str, direction: str = "right", m: int = 0, shift: int = 0) -> float:
	net: float = 0; comm: float = 0
	step = 1

	if direction == "left":
		step = -1

	if m:
		for trade in trades:
			if trade.name == name:
				comm -= to_float(trade.commission)
				
		b = 0; s = 0
		for trade in trades[::step]:
			if shift != 0:
				shift -= 1
				continue
			if trade.name == name:
				if trade.type == OperationType.OPERATION_TYPE_BUY:
					b += trade.quantity
					min_payment = min(abc(to_float(trade.payment)), to_float(trade.price) * trade.quantity)
					trade_comm = round(await commission_by_tariff(client, trade.instrument_type) * to_float(trade.price) / 100 * trade.quantity)

					if b <= m:
						net -= min_payment
						net -= trade_comm
				elif trade.type == OperationType.OPERATION_TYPE_SELL:
					s += trade.quantity
					min_payment = min(to_float(trade.payment), to_float(trade.price) * trade.quantity)
					trade_comm = round(await commission_by_tariff(client, trade.instrument_type) * to_float(trade.price) / 100 * trade.quantity)
					
					if s <= m:
						net += (min_payment - trade_comm)

				if (b == s == m):
					break
	else:
		for trade in trades:
			if trade.name == name:
				min_pay = min(abc(to_float(trade.payment)), to_float(trade.price) * trade.quantity)
				if trade.type == OperationType.OPERATION_TYPE_BUY:
					res = -min_pay
				elif trade.type == OperationType.OPERATION_TYPE_SELL:
					res = min_pay

				trade_comm = round(await commission_by_tariff(client, trade.instrument_type) * to_float(trade.price) / 100 * trade.quantity)
				
				net += (res - trade_comm)
				comm += trade_comm

	return [round(net), round(comm)]


async def last_portfolio_operation_handler(client, trades, name, buy, sell, buy_lots, sell_lots, count):
	m = buy - count

	if m == sell:
		net, comm = await get_yield(client, trades, name, "left", m)
	elif m < sell:
		if buy_lots == sell_lots:
			net, comm = await get_yield(client, trades, name)
		else:
			mod = sell - m
			if mod < count:
				net, comm = await get_yield(client, trades, name, "left", m + mod)
			elif mod > count:
				net, comm = await get_yield(client, trades, name, "right", m + mod)
	else:
		if buy_lots == sell_lots:
			net, comm = await get_yield(client, trades, name, "right", shift=count)
		else:
			net, comm = await get_yield(client, trades, name, "right", sell, count)

	return [net, comm]
		

async def get_operations_yield(acc_name: str, TOKEN: str, period: str):
	trades: List[OperationItem] = []
	service_fee = 0; margin_fee = 0; total_net = 0; total_comm = 0
	answer = ""

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

		unique_trades = set()
		for trade in trades:
			unique_trades.add(trade.name)

		for name in unique_trades:
			for trade in trades:
				if trade.name == name:
					figi = trade.figi
					break

			quantity = await in_portfolio(client, account_id, figi)
			buy, sell, buy_lots, sell_lots = buy_sell_equal(trades, name)
			count, last_operation, buy, sell, buy_lots, sell_lots = count_in_portfolio(trades, name, quantity, buy, sell, buy_lots, sell_lots)

			if count:
				if count > 0 and last_operation == OperationType.OPERATION_TYPE_SELL:
					last_operation = OperationType.OPERATION_TYPE_BUY
				elif count < 0 and last_operation == OperationType.OPERATION_TYPE_BUY:
					last_operation = OperationType.OPERATION_TYPE_SELL

				if last_operation == OperationType.OPERATION_TYPE_BUY:
					net, comm = last_portfolio_operation_handler(client, trades, name, buy, sell, buy_lots, sell_lots, count)
				elif last_operation == OperationType.OPERATION_TYPE_SELL:
					net, comm = last_portfolio_operation_handler(client, trades, name, sell, buy, buy_lots, sell_lots, count)
			else:
				if buy_lots == sell_lots:
					net, comm = await get_yield(client, trades, name)
				else:
					c = lots_count_equal(trades, name)
					mod = (buy + sell) - c
					net, comm = await get_yield(client, trades, name, shift=mod)

			if buy == 0 or sell == 0:
				net = 0

			total_net += float(net)
			total_comm += float(comm)
			count = f"Open positions: {count}\n\n" if count else "\n"
			answer += f"<b>{name}</b>\nNet: {net}\nComm: {comm}\n{count}"

	if service_fee:
		total_net += service_fee
	if margin_fee:
		total_net += margin_fee

	add_comm = f"<b>Additional Comm:</b> {-round(service_fee) - round(margin_fee)} ₽\n" if service_fee or margin_fee else ""
	return f"<b>Net:</b> {round(total_net)} ₽\n<b>Comm:</b> {round(total_comm)} ₽\n{add_comm}\n" + answer
