from tinkoff.invest import (
    AsyncClient,
    GetAccountsResponse,
    AccountType,
)


async def get_accounts(TOKEN: str) -> GetAccountsResponse:
    res = []

    async with AsyncClient(TOKEN) as client:
        accounts = await client.users.get_accounts()
        for acc in accounts.accounts:
            if acc.type != AccountType.ACCOUNT_TYPE_INVEST_BOX and acc.type != AccountType.ACCOUNT_TYPE_TINKOFF_IIS:
                res.append(acc)

    return res
	

async def cancel_orders(acc_name: str, TOKEN: str):
    async with AsyncClient(TOKEN) as client:
        accounts = await get_accounts(TOKEN)
        for account in accounts:
            if (account.name == acc_name):
                account_id = account.id
                break
        await client.cancel_all_orders(account_id=account_id)
