from typing import List

from bot.tinkoff.api import get_accounts
from bot.tinkoff.utils import to_float, round, currency_by_ticker

from tinkoff.invest import (
    AsyncClient,
    GetOperationsByCursorRequest,
    OperationType,
    OperationItem,
    InstrumentIdType,
    InstrumentResponse
)


async def get_operations_history(acc_name: str, TOKEN: str):
    trades: List[OperationItem] = []
    ans = {}
    answer = ""
    
    async with AsyncClient(TOKEN) as client:
        accounts = await get_accounts(TOKEN)
        for acc in accounts:
            if (acc.name == acc_name):
                account_id = acc.id
                break

        def get_request(cursor=""):
            return GetOperationsByCursorRequest(
				account_id=account_id,
				cursor=cursor,
				operation_types=[OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL],
			)

        operations = await client.operations.get_operations_by_cursor(get_request())
        for item in operations.items:
            if item.trades_info.trades:
                trades.append(item)

        while operations.has_next:
            request = get_request(cursor=operations.next_cursor)
            operations = await client.operations.get_operations_by_cursor(request)
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

            instrument: InstrumentResponse = await client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=trade.figi
            )
            curr_symbol = currency_by_ticker(instrument.instrument.currency)
            if trade.type == OperationType.OPERATION_TYPE_BUY:
                trade_type = "B"
            elif trade.type == OperationType.OPERATION_TYPE_SELL:
                trade_type = "S"
            
            ans[date] += f"({trade_type}) {trade.name} - {trade.quantity} шт - {round(price)} {curr_symbol}\n"

        for item in ans:
            answer += f"<b>{item}</b>\n{ans[item]}\n"

    return answer
