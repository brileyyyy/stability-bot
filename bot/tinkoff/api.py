import os

from tinkoff.invest import Client, GetAccountsResponse


def get_accounts() -> GetAccountsResponse:
	TOKEN = os.environ["INVEST_TOKEN"]
	
	with Client(TOKEN) as client:
		return client.users.get_accounts()
	
