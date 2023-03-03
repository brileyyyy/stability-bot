import os
from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import (
    abc,
    to_float, 
    round, 
    get_from_period,
    buy_sell_equal
)

from tinkoff.invest import (
	Client,
	PortfolioResponse,
	GetOperationsByCursorRequest,
	OperationItem,
	OperationsResponse,
	OperationType
)


def get_yield(trades: List[OperationItem], name: str, direction: str, m: int = 0, shift: int = 0) -> float:
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

					pay_b = round(to_float(trade.payment))
					pay_price_b = round(to_float(trade.price) * trade.quantity)
					min_pay_b = min(abc(pay_b), pay_price_b)
					res = pay_b if min_pay_b == abc(pay_b) else -pay_price_b
					if b <= m:
						net += res + to_float(trade.commission)
				elif trade.type == OperationType.OPERATION_TYPE_SELL:
					s += trade.quantity

					pay_s = round(to_float(trade.payment))
					pay_price_s = round(to_float(trade.price) * trade.quantity)
					if s <= m:
						net += min(pay_s, pay_price_s) + to_float(trade.commission)

				if (b == s == m):
					break
	else:
		for trade in trades:
			if trade.name == name:
				net += (to_float(trade.payment) + to_float(trade.commission))
				comm -= to_float(trade.commission)

	return [round(net), round(comm)]


def in_portfolio(client: Client, account_id: str, figi: str) -> int:
	quantity: int = 0
	response: PortfolioResponse = client.operations.get_portfolio(account_id=account_id)
	
	for position in response.positions:
		if position.figi == figi:
			quantity = abc(round(to_float(position.quantity)))
			break
		
	return quantity

def last_portfolio_operation_handler(trades, name, buy, sell, quantity):
	m = buy - quantity
	if m == sell:
		net, comm = get_yield(trades, name, "left", m)
	elif m < sell:
		mod = sell - m
		if mod < quantity:
			net, comm = get_yield(trades, name, "left", m + mod)
		elif mod > quantity:
			net, comm = get_yield(trades, name, "right", m + mod)
	else:
		net, comm = get_yield(trades, name, "right", sell, quantity)

	open_pos = (buy + sell) - 2 * m

	return [net, comm, open_pos]
		

def get_operations_yield(acc_name: str, period: str):
	TOKEN = os.environ["INVEST_TOKEN"]
	trades: List[OperationItem] = []
	service_fee = 0; total_net = 0; total_comm = 0
	answer = ""

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id
				break

		fr = get_from_period(period)
		operations: OperationsResponse = client.operations.get_operations(
			account_id=account_id,
			from_=fr,
		)
		for op in operations.operations:
			if op.operation_type == OperationType.OPERATION_TYPE_SERVICE_FEE:
				service_fee = to_float(op.payment)
				break

		def get_request(cursor=""):
			return GetOperationsByCursorRequest(
				account_id=account_id,
				from_=fr,
				cursor=cursor,
				limit=3,
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
			buy, sell = buy_sell_equal(trades, name)

			for trade in trades:
				if trade.name == name:
					comm = -to_float(trade.commission)
					figi = trade.figi
					last_operation = trade.type
					break
			
			if buy == 0 or sell == 0:
				net = 0
				open_pos = max(buy, sell)
			elif buy == sell:
				net, comm = get_yield(trades, name, "right")
				open_pos = 0
			elif in_portfolio(client, account_id, figi):
				quantity = in_portfolio(client, account_id, figi)

				if last_operation == OperationType.OPERATION_TYPE_BUY:
					net, comm, open_pos = last_portfolio_operation_handler(trades, name, buy, sell, quantity)
				elif last_operation == OperationType.OPERATION_TYPE_SELL:
					net, comm, open_pos = last_portfolio_operation_handler(trades, name, sell, buy, quantity)
			else:
				m = min(buy, sell)
				net, comm = get_yield(trades, name, "right", m)
				open_pos = (buy + sell) - 2 * m

			total_net += float(net)
			total_comm += float(comm)
			open_pos = f"Open positions: {round(open_pos)}\n\n" if open_pos else "\n"
			answer += f"<b>{name}</b>\nNet: {net}\nComm: {comm}\n{open_pos}"

	if service_fee:
		total_net += service_fee

	service_fee = f"<b>Additional Comm:</b> {-round(service_fee)} ₽\n" if service_fee else ""
	return f"<b>Net:</b> {round(total_net)} ₽\n<b>Comm:</b> {round(total_comm)} ₽\n{service_fee}\n" + answer
