import os

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import to_float, round

from tinkoff.invest import Client, PortfolioResponse


def balance_info(response: PortfolioResponse, value: float, header: str):
	currency_yield = 0.

	if header == "Total":
		for position in response.positions:
			currency_yield += to_float(position.expected_yield)
		for position in response.virtual_positions:
			currency_yield += to_float(position.expected_yield)

	elif header != "Gifts":
		for position in response.positions:
			if header == "Shares" and position.instrument_type == "share":
				currency_yield += to_float(position.expected_yield)
			elif header == "Bonds" and position.instrument_type == "bond":
				currency_yield += to_float(position.expected_yield)
	
	else:
		for v_position in response.virtual_positions:
			currency_yield += to_float(v_position.expected_yield)
	
	percentage_yield = currency_yield * 100 / to_float(response.total_amount_portfolio)

	if currency_yield < 0:
		sign = "-"
	elif currency_yield == 0:
		sign = ""
	elif currency_yield > 0:
		sign = "+"

	return f"<b>{header}</b>\n{value} ₽ ({sign}{round(currency_yield)} ₽ · {round(percentage_yield)}%)\n\n" \
	if currency_yield > 0 \
	else ""


def get_balance(acc_name: str):
	TOKEN = os.environ["INVEST_TOKEN"]

	def get_gift_shares(response: PortfolioResponse) -> float:
		res = 0
		for position in response.virtual_positions:
			res += (position.quantity.units * to_float(position.current_price))
		return res

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id
				break

		response = client.operations.get_portfolio(account_id=account_id)
		
		total = round(to_float(response.total_amount_portfolio))
		shares = to_float(response.total_amount_shares)
		bonds = to_float(response.total_amount_bonds)
		currencies = to_float(response.total_amount_currencies)
		gift_shares = round(get_gift_shares(response))
		
		answer = (f"{balance_info(response, total, 'Total')}"
				f"<b>Currency</b>\n{currencies} ₽\n\n"
				f"{balance_info(response, shares, 'Shares')}"
				f"{balance_info(response, bonds, 'Bonds')}"
				f"{balance_info(response, gift_shares, 'Gifts')}")

	return answer