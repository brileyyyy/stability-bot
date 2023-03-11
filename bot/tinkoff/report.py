from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import to_float, round, currency_by_ticker

from tinkoff.invest import (
    AsyncClient,
    PortfolioResponse, 
    InstrumentIdType,
    InstrumentResponse
)
        

async def get_portfolio_report(acc_name: str, TOKEN: str):
	answer = ""

	async with AsyncClient(TOKEN) as client:
		accounts = await get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

		response: PortfolioResponse = await client.operations.get_portfolio(account_id=account_id)

		for position in response.positions:
			if position.instrument_type != "currency":
				curr_price = to_float(position.current_price)
				quantity = to_float(position.quantity)
				exp_yield = to_float(position.expected_yield)
				total = curr_price * quantity
				
				instrument: InstrumentResponse = await client.instruments.get_instrument_by(
					id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                	id=position.figi
				)
				curr_symbol = currency_by_ticker(instrument.instrument.currency)

				answer += f"<b>{instrument.instrument.name}</b>\nTotal: {round(total)} {curr_symbol}\nNet: {round(exp_yield)} {curr_symbol}\nOpen positions: {round(quantity)}\n\n"
		
		for position in response.virtual_positions:
			curr_price = to_float(position.current_price)
			quantity = to_float(position.quantity)
			exp_yield = to_float(position.expected_yield)
			total = curr_price * quantity

			instrument: InstrumentResponse = await client.instruments.get_instrument_by(
				id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
				id=position.figi
			)

			answer += f"{instrument.instrument.name}\nTotal: {round(total)} ₽\nNet: {round(exp_yield)} ₽\nOpen positions: {round(quantity)}\n\n"

	return f"<b>Total</b>\n{to_float(response.total_amount_portfolio)} ₽\n\n<b>Currency</b>\n{round(to_float(response.total_amount_currencies))} ₽\n\n" + answer
