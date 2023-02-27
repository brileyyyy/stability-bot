import os

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import to_float, round

from tinkoff.invest import Client, PortfolioResponse, ShareResponse, InstrumentIdType
        

def get_portfolio_report(acc_name: str):
	TOKEN = os.environ["INVEST_TOKEN"]
	answer = ""

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id
				break

		response: PortfolioResponse = client.operations.get_portfolio(account_id=account_id)

		for position in response.positions:
			if position.instrument_type != "currency":
				curr_price = to_float(position.current_price)
				quantity = to_float(position.quantity)
				exp_yield = to_float(position.expected_yield)
				total = curr_price * quantity

				instrument: ShareResponse = client.instruments.share_by(
					id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
					id=position.figi
				)

				answer += f"<b>{instrument.instrument.name}</b>\nTotal: {round(total)} ₽\nNet: {round(exp_yield)} ₽\nOpen positions: {round(quantity)}\n\n"
		
		for position in response.virtual_positions:
			curr_price = to_float(position.current_price)
			quantity = to_float(position.quantity)
			exp_yield = to_float(position.expected_yield)
			total = curr_price * quantity

			instrument: ShareResponse = client.instruments.share_by(
				id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
				id=position.figi
			)

			answer += f"{instrument.instrument.name}\nTotal: {round(total)} ₽\nNet: {round(exp_yield)} ₽\nOpen positions: {round(quantity)}\n\n"

	return f"<b>Total</b>\n{to_float(response.total_amount_portfolio)} ₽\n\n<b>Currency</b>\n{round(to_float(response.total_amount_currencies))} ₽\n\n" + answer
