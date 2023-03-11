from tinkoff.invest import (
    AsyncClient, 
    GetAccountsResponse,
    AccountType,
    AioRequestError
)


async def get_accounts(TOKEN: str) -> GetAccountsResponse:
    res = []

    async with AsyncClient(TOKEN) as client:
        accounts = await client.users.get_accounts()
        for acc in accounts.accounts:
            if acc.type != AccountType.ACCOUNT_TYPE_INVEST_BOX:
                res.append(acc)

    return res
	

async def cancel_orders(acc_name: str, TOKEN: str):
    async with AsyncClient(TOKEN) as client:
        accounts = await get_accounts(TOKEN)
        for account in accounts:
            if (account.name == acc_name):
                account_id = account.id
                break
        # client.cancel_all_orders(account_id=account_id)


async def is_margin_trading(acc_name: str, TOKEN: str):
	async with AsyncClient(TOKEN) as client:
		accounts = await get_accounts(TOKEN)
		for acc in accounts:
			if (acc.name == acc_name):
				account_id = acc.id
				break

		try:
			await client.users.get_margin_attributes(account_id=account_id)
			err = 1
		except AioRequestError:
			err = 0

	return err
