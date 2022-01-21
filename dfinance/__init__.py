import time

import pandas as pd
import yfinance as yf
import alpaca_trade_api as tradeapi

class Backtest:
    """Creates a backtest instance.
    """
    def __init__(self):
        self.running_rows = []
        self.in_the_market = False


    def process_live_data(self, prefill_rows, my_alpaca_port, my_strategy, **kwargs):
        """Function to process live data. Can be used for paper or live trading.

        Args:
            prefill_rows (dataframe): dataframe containing historical data
            my_alpaca_port (AlpacaPortfolio): your Alpaca portfolio object
            my_strategy (function): function that contains your strategy
        """

        if not my_alpaca_port.is_market_open:
            print('Market is closed. No action will be taken.')
            return

        try:
            # drop the last row because it will include today's data
            prefill_rows.drop(prefill_rows.tail(1).index,inplace=True)

            # append the prefill_rows to running_rows before adding live ticker data
            # as part of the strategy
            for row in prefill_rows.iterrows():
                self.running_rows.append((row[0],
                                          row[1].values[0],  # open
                                          row[1].values[1],  # high
                                          row[1].values[2],  # low
                                          row[1].values[3],  # close
                                          row[1].values[4],  # adj close
                                          row[1].values[5])) # volume
        except:
            print('No prefill or invalid prefill.')

        # call my_strategy
        my_strategy(self, my_alpaca_port, **kwargs)



    def process_historical_data(self, df, my_port, my_strategy, **kwargs):
        """Function to process a historical data stream.
        This function serves as a wrapper to call your strategy and pass keyword arguments to it.

        Args:
            df (dataframe): dataframe of price data
            my_port (Portfolio): your portfolio object
            my_strategy (function): function that contains your strategy
        """
        my_strategy(self, df, my_port, **kwargs)


    def yield_row(self, df):
        """Yield a row of data from a dataframe.
        This is a helper function that you can call as part of a trading strategy.

        Args:
            df (dataframe): a dataframe of price data

        Yields:
            tuple: row of price data in a tuple
        """
        for row in df.iterrows():
            yield (row[0],
                    row[1].values[0], # open
                    row[1].values[1], # high
                    row[1].values[2], # low
                    row[1].values[3], # close
                    row[1].values[4], # adj close
                    row[1].values[5]) # volume


    def yield_yf(self, ticker):
        """Yield a row of data from a live feed via Yahoo! Finance.
        This is a helper function that you can call as part of a trading strategy.

        Args:
            ticker (str): ticker to retrieve data for

        Yields:
            tuple: row of price data in a tuple
        """
        data = yf.download(tickers=ticker, period='1d', interval='1m', progress=False).tail(1)
        for row in data.iterrows():
            yield (row[0],
                    row[1].values[0], # open
                    row[1].values[1], # high
                    row[1].values[2], # low
                    row[1].values[3], # close
                    row[1].values[4], # adj close
                    row[1].values[5]) # volume



class Portfolio:
    """Creates a portfolio instance.
    
    Attributes:
        cashvalue : value of cash in the account
    """
    def __init__(self):
        self.__transactions = []
        self.cashvalue = 100_000.0

    def load_transactions(self, filepath):
        """Load a list of transactions to restore a portfolio history.

        Args:
            filepath (str): filepath to load transactions file from
        """
        self.__transactions = pd.read_csv(filepath).values.tolist()

    def save_transactions(self, filepath):
        """Save a list of transactions to store a portfolio history.

        Args:
            filepath (str): filepath to save transactions file to
        """
        pd.DataFrame(self.__transactions).to_csv(filepath, index=False)
    
    def buy_stock(self, ticker, share_cnt, share_price, transaction_datetime):
        """Buy a stock. Adds the purchase to the transactions record and
        decreases the portfolio cash value by the amount of the purchase.

        Args:
            ticker (str): stock ticker
            share_cnt (float): count of shares to purchase
            share_price (float): purchase price of one share
            transaction_datetime (str): datetime of transaction
        """
        self.__transactions.append([ticker, share_cnt, share_price, share_cnt * share_price, 'buy', transaction_datetime])
        self.cashvalue -= share_cnt * share_price
        
    def sell_stock(self, ticker, share_cnt, share_price, transaction_datetime):
        """Sell a stock. Adds the sale to the transactions record and
        increases the portfolio cash value by the amount of the sale.

        Args:
            ticker (str): stock ticker
            share_cnt (float): count of shares to sell
            share_price (float): sale price of one share
            transaction_datetime (str): datetime of transaction
        """
        self.__transactions.append([ticker, -share_cnt, share_price, -(share_cnt * share_price), 'sell', transaction_datetime])
        self.cashvalue += share_cnt * share_price
        
    def ledger(self):
        """Get a dataframe ledger of all transactions.

        Returns:
            dataframe: ledger of all transactions
        """
        return pd.DataFrame(self.__transactions, columns=['Ticker', 'Shares', 'Share Price', 'Dollar Amount', 'Buy/Sell', 'Transaction Datetime'])
    
    def current_positions(self):
        """Get a printout of all current positions.

        This is really only useful if you are paper/live trading in real time,
        since it retrieves the current price of the equities in your portfolio
        at the time the function is called. However, since the Portfolio class is
        used for historical backtesting only, this function is really just for fun.

        Returns:
            dataframe: all current positions
        """
        df = self.__sum_ledger()

        # drop Totals row - we will recalculate this later
        df = df[df['Ticker'] != 'Totals']

        # Current price of tickers
        df['Current Price'] = self.__get_current_prices(list(df['Ticker'].values))

        # Current value of our shares
        df['Current Value of Shares'] = df['Sum Shares'] * df['Current Price']


        ### THIS SECTION MAY NOT FUNCTION AS INTENDED
        ### COMMENTING OUT FOR NOW
        # # Find average price per share for all buys
        # # Calculate the cost to acquire our shares
        # price_per_share_buy_avg = self.__sum_buys()['Sum Dollars'] / self.__sum_buys()['Sum Shares']
        # df['Cost to Acquire Shares'] = (df['Sum Shares'] * price_per_share_buy_avg)

        # # Calculate Unrealied Gain/Loss
        # df['Unrealized Gain/Loss'] = df['Current Value of Shares'] - df['Cost to Acquire Shares']
        # df['Unrealized Gain/Loss %'] = 100 * df['Unrealized Gain/Loss'] / df['Current Value of Shares']
        
        # # Calculate totals
        # df.loc[len(df.index)] = ['Totals', sum(df['Shares Held']), 'N/A', sum(df['Current Value of Shares']), sum(df['Cost to Acquire Shares']), \
        #                          sum(df['Unrealized Gain/Loss']), (100 * (sum(df['Unrealized Gain/Loss']) / sum(df['Current Value of Shares'])))]


        # Rename Sum Shares and drop Sum Dollars
        df = df.rename(columns={"Sum Shares": "Shares Held"})
        df = df.drop(columns=['Sum Dollars'])

        # Calculate Totals
        df.loc[len(df.index)] = ['Totals', sum(df['Shares Held']), 'N/A', sum(df['Current Value of Shares'])]

        # Remove any rows with zero shares
        df = df[df['Shares Held'] != 0]

        return df

    def value_in_market(self):
        """Get the current value of all holdings in the market.

        This is really only useful if you are paper/live trading in real time,
        since it retrieves the current price of the equities in your portfolio
        at the time the function is called. However, since the Portfolio class is
        used for historical backtesting only, this function is really just for fun.

        Returns:
            float: sum value of all holdings in the market
        """
        df = self.current_positions()
        return df['Current Value of Shares'][-1:].values[0]

#########################
### PRIVATE FUNCTIONS ###
#########################

    def __sum_ledger(self):
        total_share_cnt = 0
        total_dollar_amt = 0
        ticker_list = []
        output_list = []
        
        # Get list of all tickers
        for transaction in self.__transactions:
            if transaction[0] not in ticker_list:
                ticker_list.append(transaction[0])
        
        # Record buys and sells for each stock
        for ticker in ticker_list:
            share_cnt = 0
            dollar_amt = 0
            for transaction in self.__transactions:
                if ticker == transaction[0]:
                    share_cnt += transaction[1]
                    dollar_amt += transaction[3]
                    total_share_cnt += transaction[1]
                    total_dollar_amt += transaction[3]
            output_list.append([ticker, share_cnt, dollar_amt])
        
        # Calculate total
        output_list.append(['Totals', total_share_cnt, total_dollar_amt])

        return pd.DataFrame(output_list, columns=['Ticker', 'Sum Shares', 'Sum Dollars'])
    

    def __sum_buys(self):
        total_share_cnt = 0
        total_dollar_amt = 0
        ticker_list = []
        output_list = []
        
        # Get list of all tickers
        for transaction in self.__transactions:
            if transaction[0] not in ticker_list:
                ticker_list.append(transaction[0])
        
        # Record buys for each stock only
        for ticker in ticker_list:
            share_cnt = 0
            dollar_amt = 0
            for transaction in self.__transactions:
                if ticker == transaction[0] and transaction[4] == 'buy':
                    share_cnt += transaction[1]
                    dollar_amt += transaction[3]
                    total_share_cnt += transaction[1]
                    total_dollar_amt += transaction[3]
            output_list.append([ticker, share_cnt, dollar_amt])
        
        # Calculate total
        output_list.append(['Totals', total_share_cnt, total_dollar_amt])
        
        return pd.DataFrame(output_list, columns=['Ticker', 'Sum Shares', 'Sum Dollars'])


    def __get_current_prices(self, ticker_list):
        price_list = []
        for ticker in ticker_list:
            price_list.append(yf.download(tickers=ticker, period='1d', interval='1m', progress=False).tail(1)['Adj Close'].values[0])

        return price_list


class AlpacaPortfolio:
    """Creates an AlpacaPortfolio instance. This class can be used to interact with an Alpaca paper or live porfolio.
    
    Attributes:
        api : access the Alpaca REST api endpoint - the functions in this class exist to abstract these operations
        equity : portfolio equity
        last_equity : portfolio equity at previous close
        cash : current portfolio cash balance
    """
    def __init__(self):
        self.api = tradeapi.REST()
        self.equity = self.api.get_account().equity
        self.last_equity = self.api.get_account().last_equity
        self.cash = self.api.get_account().cash
        self.is_market_open = self.api.get_clock().is_open

    def refresh(self):
        """Refreshes the values in AlpacaPortfolio attributes.
        """
        self.equity = self.api.get_account().equity
        self.last_equity = self.api.get_account().last_equity
        self.cash = self.api.get_account().cash
        self.is_market_open = self.api.get_clock().is_open

    def buy_stock_bracket_order(self, ticker, share_cnt, profit_pct, stop_pct, limit_pct):
        """Submit a bracket buy order, which includes a market buy order, a take profit
        order, and a stop limit order.

        Args:
            ticker (str): ticker to buy
            share_cnt (float): number of shares to buy
            profit_pct (float): percent of original price at which to execute take profit order
            stop_pct (float): percent of original price at which to trigger stop limit order
            limit_pct (float): limit price as a percentage of the original price

        Returns:
            [type]: [description]
        """
        symbol = ticker
        symbol_bars = self.api.get_barset(symbol, 'minute', 1).df.iloc[0]
        symbol_price = symbol_bars[symbol]['close']

        self.api.submit_order(
            symbol=symbol,
            qty=share_cnt,
            side='buy',
            type='market',
            time_in_force='gtc',
            order_class='bracket',
            stop_loss={'stop_price': symbol_price * stop_pct,
                    'limit_price':  symbol_price * limit_pct},
            take_profit={'limit_price': symbol_price * profit_pct}
        )

        print('Submitted Order. Check https://app.alpaca.markets/paper/dashboard/overview for status.')
        return 

    def get_account_status(self):
        """Get account status.

        Returns:
            dataframe: returns a dataframe with account balances, etc.
        """
        return pd.DataFrame([[self.cash,
                              self.equity,
                              self.last_equity,
                              float(self.last_equity) - float(self.equity),
                              100 * (float(self.last_equity) - float(self.equity))]],
                              columns=['Cash', 'Equity', 'Last Equity', 'Equity Change', 'Equity Change %'])

    def current_positions(self):
        """Get current stock positions.

        Returns:
            dataframe: returns a dataframe with a summary of current stock positions.
        """
        pos_list = []
        for pos in self.api.list_positions():
            pos_list.append([pos.symbol, pos.qty, pos.cost_basis, pos.current_price, pos.unrealized_pl, f'{100 * float(pos.unrealized_plpc):.02f}'])

        return pd.DataFrame(pos_list, columns=['Ticker', 'Shares Held', 'Cost Basis', 'Current Price', 'Unrealized Gain/Loss', 'Unrealized Gain/Loss %'])
