import os
from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import to_float, round, get_from_period

from tinkoff.invest import (
	Client,
	PortfolioResponse,
	GetOperationsByCursorRequest,
	OperationItem,
	OperationsResponse,
	OperationType
)


def get_yield(trades: List[OperationItem], name: str, direction: str, min: int = 0, shift: int = 0) -> float:
	net: float = 0
	comm: float = 0

	if (direction == "left"):
		trades.reverse()

	if min:
		for trade in trades:
			if trade.name == name:
				comm -= to_float(trade.commission)
				
		b = 0; s = 0
		for trade in trades:
			if shift != 0:
				shift -= 1
				continue
			if trade.name == name:
				if trade.type == OperationType.OPERATION_TYPE_BUY:
					b += trade.quantity
					if b <= min:
						net += (to_float(trade.payment) + to_float(trade.commission))
				elif trade.type == OperationType.OPERATION_TYPE_SELL:
					s += trade.quantity
					if s <= min:
						net += (to_float(trade.payment) + to_float(trade.commission))

				if (b == s == min):
					break
	else:
		for trade in trades:
			if trade.name == name:
				net += (to_float(trade.payment) + to_float(trade.commission))
				comm -= to_float(trade.commission)

	return [round(net), round(comm)]


def buy_sell_equal(trades: List[OperationItem], name: str):
	buy = 0; sell = 0

	for trade in trades:
		if trade.name == name:
			if trade.type == OperationType.OPERATION_TYPE_BUY:
				buy += trade.quantity
			elif trade.type == OperationType.OPERATION_TYPE_SELL:
				sell += trade.quantity
	
	return [buy, sell]


def in_portfolio(client: Client, account_id: str, figi: str) -> int:
	quantity: int = 0
	response: PortfolioResponse = client.operations.get_portfolio(account_id=account_id)
	
	for position in response.positions:
		if position.figi == figi:
			quantity = to_float(position.quantity)
		
	return quantity

def last_portfolio_operation_handler(trades, name, buy, sell, quantity):
	m = buy - quantity
	if m == sell:
		direction = "left"
		net, comm = get_yield(trades, name, direction, m)
	elif m < sell:
		mod = sell - m
		if mod < quantity:
			direction = "left"
			net, comm = get_yield(trades, name, direction, m + mod)
		elif mod > quantity:
			net, comm = get_yield(trades, name, direction, m + mod)
	else:
		net, comm = get_yield(trades, name, direction, sell, quantity)

	open_pos = (buy + sell) - 2 * m

	return [net, comm, open_pos]
		

def get_operations_yield(acc_name: str, period: str):
	TOKEN = os.environ["INVEST_TOKEN"]
	trades: List[OperationItem] = []
	service_fee = 0; total_net = 0; total_comm = 0
	response = ""

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id

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

		direction = "right"
		for name in unique_trades:
			buy, sell = buy_sell_equal(trades, name)

			for trade in trades:
				if trade.name == name:
					figi = trade.figi
					break

			if buy == sell:
				net, comm = get_yield(trades, name, direction)
				open_pos = 0
			elif in_portfolio(client, account_id, figi):
				quantity = in_portfolio(client, account_id, figi)
				last_operation = trades[0].type

				if last_operation == OperationType.OPERATION_TYPE_BUY:
					net, comm, open_pos = last_portfolio_operation_handler(trades, name, buy, sell, quantity)
				elif last_operation == OperationType.OPERATION_TYPE_SELL:
					net, comm, open_pos = last_portfolio_operation_handler(trades, name, sell, buy, quantity)
			else:
				m = min(buy, sell)
				net, comm = get_yield(trades, name, direction, m)
				open_pos = (buy + sell) - 2 * m

			total_net += float(net)
			total_comm += float(comm)
			open_pos = f"Open positions: {round(open_pos)}\n\n" if open_pos else "\n"
			response += f"<b>{name}</b>\nNet: {net}\nComm: {comm}\n{open_pos}"

	if service_fee:
		total_net += service_fee

	service_fee = f"<b>Additional Comm:</b> {-round(service_fee)} ₽\n" if service_fee else ""
	return f"<b>Net:</b> {round(total_net)} ₽\n<b>Comm:</b> {round(total_comm)} ₽\n{service_fee}\n" + response