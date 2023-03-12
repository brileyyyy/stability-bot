from collections import defaultdict

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import abc, to_float, round

from tinkoff.invest import AsyncClient, PortfolioResponse


def balance_info(response: PortfolioResponse):
	result = defaultdict(float)
	ans = ""

	for position in response.positions:
		average_yield = min(abc(to_float(position.expected_yield)), abc((to_float(position.current_price) - to_float(position.average_position_price)) * to_float(position.quantity)))
		res = average_yield if to_float(position.expected_yield) > 0 else -average_yield

		result["Total"] += res
		if position.instrument_type == "share":
			result["Shares"] += res
		elif position.instrument_type == "bond":
			result["Bonds"] += res
		elif position.instrument_type == "future":
			result["Futures"] += res
		elif position.instrument_type == "option":
			result["Options"] += res
		elif position.instrument_type == "etf":
			result["Etf"] += res
		elif position.instrument_type == "sp":
			result["SP"] += res
	
	for v_position in response.virtual_positions:
		average_yield = min(abc(to_float(v_position.expected_yield)), abc((to_float(v_position.current_price) - to_float(v_position.average_position_price)) * to_float(v_position.quantity)))
		res = average_yield if to_float(v_position.expected_yield) > 0 else -average_yield

		result["Total"] += res
		result["Gifts"] += res


	for key in dict(result):
		in_portfolio = total_by_type(response, key)
	
		if result[key] < 0:
			sign = "-"
		elif result[key] == 0:
			sign = ""
		elif result[key] > 0:
			sign = "+"

		if abc(result[key]) > 0 or in_portfolio:
			percentage_yield = result[key] * 100 / in_portfolio
			ans += f"<b>{key}</b>\n{in_portfolio} ₽ ({sign}{round(result[key])} ₽ · {round(percentage_yield)}%)\n\n"

	return ans


def total_by_type(response: PortfolioResponse, type: str):
	res = 0.

	if type == "Total":
		res = to_float(response.total_amount_portfolio)
	elif type == "Shares":
		res = to_float(response.total_amount_shares)
	elif type == "Bonds":
		res = to_float(response.total_amount_bonds)
	elif type == "Futures":
		res = to_float(response.total_amount_futures)
	elif type == "Options":
		res = to_float(response.total_amount_options)
	elif type == "Etf":
		res = to_float(response.total_amount_etf)
	elif type == "SP":
		res = to_float(response.total_amount_sp)
	elif type == "Gifts":
		for position in response.virtual_positions:
			res += (position.quantity.units * to_float(position.current_price))

	return res


async def get_balance(acc_name: str, TOKEN: str):
	async with AsyncClient(TOKEN) as client:
		accounts = await get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

		response: PortfolioResponse = await client.operations.get_portfolio(account_id=account_id)
		currencies = to_float(response.total_amount_currencies)
		
		answer = (f"{balance_info(response)}"
				f"<b>Currency</b>\n{currencies} ₽")

	return answer