# David's Finance Package (dfinance) README

The goal of this package is to provide all the functionality necessary for creating, backtesting, and executing live algorithmic trading strategies.

Done:
* Data feed for historical price data
* Data feed for live price data
* Porfolio class to provide buy/sell helper functions and track transactions, cash account value, and current market positions
* Backtest class to provide the ability to backtest a trading strategy on historical data
* Sample historical data trading function (strategy) that operates on a Porfolio object

To do:
* Write a sample live data trading function that operates with API calls to Alpaca instead of using a Porfolio object
* Build additional data feeds for alternative data
* Write documentation on htpeter's utils.ledger class


## Import the library

`import dfinance as dfin`

## Import a strategy

`from dfinance.trading_strategies import Strategy_SMA_Crossover`

---

## Backtest Class

### Initialize the backtest object

`my_back = dfin.Backtest()`


### Run a strategy on historical data
```
my_back.process_historical_data(historical_df,                      # dataframe with price data
                                my_port,                            # portfolio object
                                Strategy_SMA_Crossover.strategy,    # strategy function name
                                sma_short=10,                       # keyword arg for this strategy
                                sma_long=15,                        # keyword arg for this strategy
                                share_num=50,                       # keyword arg for this strategy
                                ticker='AAPL')                      # keyword arg for this strategy
```

### Run a strategy on live data

`Under construction.`

---

## Portfolio Class

#### Initialize the portfolio object

`my_port = dfin.Portfolio()`

#### Set the cash value

`my_port.cashvalue = 133_700.00`

#### Get ledger of transactions or summary of transactions

`my_port.ledger()`

`my_port.summary_of_transactions()`

#### Get balance of cash in the account and value in the market

`my_port.cashvalue`

`my_port.value_in_market()`

#### Save transactions or load transactions

`my_port.save_transactions('myport.csv')`

`my_port.load_transactions('myport.csv')`

#### Buy or sell stock

Arguments: ticker, share count, share price, transaction datetime (as a string)

`my_port.buy_stock('GME', 2, 10, '2021-01-01 00:00:00')`

`my_port.sell_stock('GME', 1, 20, '2022-01-01 00:12:00')`