import os
from datetime import datetime, timedelta

from bot.tinkoff.api import get_accounts

from tinkoff.invest import Client, MoneyValue, RequestError


def abc(nano):
	return nano if nano >= 0 else -nano


def to_float(amount: MoneyValue) -> float:
	if amount.units <= 0 and amount.nano < 0:
		return amount.units - float(f"0.{abc(amount.nano)}")
	else:
		return amount.units + float(f"0.{abc(amount.nano)}")


def round(value: float) -> float:
	return int(value) if value - int(value) == 0 else "{:.2f}".format(value)


def get_from_period(period: str) -> datetime:
	to = datetime.now()
	if period == "per day":
		fr = datetime.replace(to, hour=0, minute=0, second=0, microsecond=0)
	elif period == "per week":
		fr = to - timedelta(days=6)
		fr = fr.replace(hour=0, minute=0, second=0, microsecond=0)
	elif period == "per month":
		fr = to - timedelta(days=29)
		fr = fr.replace(hour=0, minute=0, second=0, microsecond=0)

	return fr


def is_margin_trading(acc_name: str):
	TOKEN = os.environ["INVEST_TOKEN"]

	with Client(TOKEN) as client:
		accounts = get_accounts()
		for account in accounts.accounts:
			if (account.name == acc_name):
				account_id = account.id

		try:
			client.users.get_margin_attributes(account_id=account_id)
			err = 1
		except RequestError:
			err = 0

	return err
		