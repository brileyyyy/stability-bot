from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import (
    abc,
    to_float,
    round,
    get_trades_by_period,
    get_fee_by_period,
    buy_sell_lots,
    in_portfolio,
    count_in_portfolio,
    commission_by_tariff
)

from tinkoff.invest import (
	AsyncClient,
	OperationItem,
	OperationType,
	InstrumentResponse,
	InstrumentIdType
)


def get_yield(trades: List[OperationItem], name: str, base_comm: float, m: int = 0, shift: int = 0, count_after_portfolio: int = 0):
	net: float = 0; comm: float = 0

	if m or shift:
		b = 0; s = 0;
		for trade in trades:
			if trade.name == name:
				if shift != 0 and count_after_portfolio == 0:
					shift -= 1
					continue

				if trade.type == OperationType.OPERATION_TYPE_BUY:
					if count_after_portfolio != 0:
						count_after_portfolio -= 1
					b += trade.quantity
					min_payment = min(abc(to_float(trade.payment)), to_float(trade.price) * trade.quantity)
					trade_comm = round(base_comm * min_payment / 100)

					if m:
						if b <= m:
							comm += trade_comm
							net -= min_payment
							net -= trade_comm
					else:
						comm += trade_comm
						net -= (min_payment + trade_comm)
				elif trade.type == OperationType.OPERATION_TYPE_SELL:
					if count_after_portfolio != 0:
						count_after_portfolio -= 1
					s += trade.quantity
					min_payment = min(to_float(trade.payment), to_float(trade.price) * trade.quantity)
					trade_comm = round(base_comm * min_payment / 100)
					
					if m:
						if s <= m:
							comm += trade_comm
							net += (min_payment - trade_comm)
					else:
						comm += trade_comm
						net += (min_payment - trade_comm)

				if b == s == m:
					break
	else:
		for trade in trades:
			if trade.name == name:
				min_pay = min(abc(to_float(trade.payment)), to_float(trade.price) * trade.quantity)
				if trade.type == OperationType.OPERATION_TYPE_BUY:
					res = -min_pay
				elif trade.type == OperationType.OPERATION_TYPE_SELL:
					res = min_pay

				trade_comm = round(base_comm * abc(res) / 100)
				
				net += (res - trade_comm)
				comm += trade_comm

	return [round(net), round(comm)]
		

async def get_operations_yield(acc_name: str, TOKEN: str, period: str):
	trades: List[OperationItem] = await get_trades_by_period(acc_name, TOKEN, period)
	service_fee, margin_fee = await get_fee_by_period(acc_name, TOKEN, period)

	total_net = 0; total_comm = 0
	answer = ""

	async with AsyncClient(TOKEN) as client:
		accounts = await get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

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
				id=figi
			)
			base_comm = await commission_by_tariff(client, instrument.instrument.instrument_type)

			buy_lots, sell_lots = buy_sell_lots(trades, name)
			lots_count = await in_portfolio(client, account_id, figi)
			count, count_after, buy_lots, sell_lots = count_in_portfolio(trades, name, lots_count, buy_lots, sell_lots)

			if lots_count and not count:
				answer += f"<b>{name}</b>\nDelays in terminal calculations.\n\n"
			else:
				if count:
					if buy_lots == sell_lots:
						net, comm = get_yield(trades, name, base_comm, buy_lots, shift=count, count_after_portfolio=count_after)
					else:
						net, comm = get_yield(trades, name, base_comm, min(buy_lots, sell_lots), count, count_after)
				else:
					if buy_lots == sell_lots:
						net, comm = get_yield(trades, name, base_comm)
					else:
						net, comm = get_yield(trades, name, base_comm, min(buy_lots, sell_lots))

				if buy_lots == 0 or sell_lots == 0:
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
