import os

from tinkoff.invest import Client, GetAccountsResponse


def get_accounts() -> GetAccountsResponse:
	TOKEN = os.environ["INVEST_TOKEN"]
	
	with Client(TOKEN) as client:
		return client.users.get_accounts()
	

def cancel_orders(acc_name: str):
    TOKEN = os.environ["INVEST_TOKEN"]
    
    with Client(TOKEN) as client:
        accounts = get_accounts()
        for account in accounts.accounts:
            if (account.name == acc_name):
                account_id = account.id
                break
        # client.cancel_all_orders(account_id=account_id)	
