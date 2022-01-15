"""
A Ledger class that can accept trades as input
and will maintain accounting and finance statistics for the portfolio.

    ledger = Ledger()

    ledger.add_transaction({ticker='AAPL', shares=100, price=100.00, trade_time='2019-01-01 00:00:00'})

    ledger.get_balances (as_of: datetime.datetime)
    # returns a dataframe with the balances of the portfolio

    ledger._trans -> pd.DataFrame
    # returns a dataframe with the transactions of the portfolio

    ledger.return_at(as_of: datetime.datetime, prices_at: dict) -> pd.DataFrame
    # returns the return
"""
import datetime

import pandas as pd

test_transactions = [
    ["AAPL", 100, 100.00, pd.to_datetime("2019-01-01 00:00:00")],
    ["AAPL", -100, 125.00, pd.to_datetime("2019-01-02 00:00:00")],
    ["AAPL", 100, 130.00, pd.to_datetime("2019-01-03 00:00:00")],
    ["AAPL", -100, 129.00, pd.to_datetime("2019-01-04 00:00:00")],
    ["AAPL", 100, 185.00, pd.to_datetime("2019-02-01 00:00:00")],
    ["AAPL", -100, 192.00, pd.to_datetime("2019-02-13 00:00:00")],
]
test_transactions = [
    {"ticker": i[0], "shares": i[1], "price": i[2], "trade_time": i[3]}
    for i in test_transactions
]

print(test_transactions)


class Ledger:
    # Ledger attemps to do things functionally at the time a user asks for it.
    # Do not implement state past transactions.
    def __init__(self):
        self.tx = []

    def add_transaction(
        self, ticker: str, shares: int, price: float, trade_time: datetime
    ):
        self.tx.append(
            {
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "trade_time": trade_time,
            }
        )

    def get_balances(self, as_of: datetime.datetime = None):
        # returns a dataframe with the balances of the portfolio at timestamp
        # uses average
        tx_asof = self._trans[self._trans["trade_time"] <= as_of]
        tx_asof["usd_equity_change"] = tx_asof["price"] * tx_asof["shares"]
        _sorted = tx_asof.sort_values("trade_time", ascending=True)
        gb = _sorted.groupby("ticker")
        _sorted["current_position_usd_value"] = gb.cumsum()["shares"]
        print(_sorted)
        _sorted["net_value_at_timestamp"] = gb.cumsum()["usd_equity_change"]
        # filter to most reecnt row
        idx = gb["trade_time"].transform(max) == _sorted["trade_time"]
        return _sorted[idx]

    def return_at(self, as_of: datetime.datetime = None, prices_at: dict = None):
        """
        # TODO: make this accurately calculate returns
        """
        bals = self.get_balances(as_of)
        for i in bals.ticker.unique():
            if i not in list(prices_at.keys()):
                raise Exception(
                    f"ticker {i} missing from prices_at passed in at timestamp {as_of}"
                )
        # append asset value at balance
        bals["current_asset_value"] = bals["ticker"].apply(lambda x: prices_at.get(x))
        bals["current_position_usd_value"] = (
            bals["current_asset_value"] * bals["current_position_usd_value"]
        )

        return bals.rename(
            columns={
                "shares": "last_trade_share_movement",
                "price": "last_trade_price",
                "trade_time": "last_trade_time",
            }
        )

    @property
    def _trans(self):
        return pd.DataFrame(self.tx)


if __name__ == "__main__":
    ledger = Ledger()
    # *i syntax passes the list items
    [ledger.add_transaction(**i) for i in test_transactions]
    print(ledger.get_balances(as_of=datetime.datetime(2019, 5, 1)))
    print(
        ledger.return_at(as_of=datetime.datetime(2019, 5, 1), prices_at={"AAPL": 130}).T
    )
