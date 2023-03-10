from tinkoff.invest import (
    Client, 
    GetAccountsResponse,
    AccountType,
    RequestError
)


def get_accounts(TOKEN: str) -> GetAccountsResponse:
    res = []

    with Client(TOKEN) as client:
        accounts = client.users.get_accounts()
        for acc in accounts.accounts:
            if acc.type != AccountType.ACCOUNT_TYPE_INVEST_BOX:
                res.append(acc)

    return res
	

def cancel_orders(acc_name: str, TOKEN: str):
    with Client(TOKEN) as client:
        accounts = get_accounts(TOKEN)
        for account in accounts:
            if (account.name == acc_name):
                account_id = account.id
                break
        # client.cancel_all_orders(account_id=account_id)


def is_margin_trading(acc_name: str, TOKEN: str):
	with Client(TOKEN) as client:
		accounts = get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

		try:
			client.users.get_margin_attributes(account_id=account_id)
			err = 1
		except RequestError:
			err = 0

	return err
