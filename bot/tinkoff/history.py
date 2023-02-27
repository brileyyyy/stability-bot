import os
from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import to_float, round

from tinkoff.invest import (
    Client,
    GetOperationsByCursorRequest,
    OperationType,
    OperationItem,
    ShareResponse,
    InstrumentIdType
)


def get_operations_history(acc_name: str):
    TOKEN = os.environ["INVEST_TOKEN"]
    trades: List[OperationItem] = []
    ans = {}
    answer = ""
    
    with Client(TOKEN) as client:
        accounts = get_accounts()
        for account in accounts.accounts:
            if (account.name == acc_name):
                account_id = account.id
                break

        def get_request(cursor=""):
            return GetOperationsByCursorRequest(
				account_id=account_id,
				cursor=cursor,
				limit=3,
				operation_types=[OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL],
			)

        operations = client.operations.get_operations_by_cursor(get_request())
        for item in operations.items:
            if item.trades_info.trades:
                trades.append(item)

        while operations.has_next:
            request = get_request(cursor=operations.next_cursor)
            operations = client.operations.get_operations_by_cursor(request)
            for item in operations.items:
                if item.trades_info.trades:
                    trades.append(item)
                    
        for trade in trades:
            day = f"0{trade.date.day}" if trade.date.day < 10 else trade.date.day
            month = f"0{trade.date.month}" if trade.date.month < 10 else trade.date.month
            date = f"{day}.{month}.{trade.date.year}"
            ans[date] = ""

        for trade in trades:
            day = f"0{trade.date.day}" if trade.date.day < 10 else trade.date.day
            month = f"0{trade.date.month}" if trade.date.month < 10 else trade.date.month
            date = f"{day}.{month}.{trade.date.year}"
            price = to_float(trade.price)

            instrument: ShareResponse = client.instruments.share_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, 
                id=trade.figi
            )
            ans[date] += f"{instrument.instrument.ticker} - {trade.quantity} шт - {round(price)} ₽\n"

        for item in ans:
            answer += f"<b>{item}</b>\n{ans[item]}\n"

    return answer
