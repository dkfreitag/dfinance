import time

import pandas as pd
import yfinance as yf

class Backtest:
    """Creates a backtest instance.
    """
    def __init__(self):
        self.running_rows = []
        self.in_the_market = False


    def process_live_data(self, ticker):
        """Function to process a live data stream.
        Under Construction.

        Args:
            ticker (str): ticker to process
        """
        while True:
            try:
                row_iterable = iter(self.__yield_yf(ticker))
                for row in row_iterable:
                    # DO STUFF HERE
                    print(row)
                    # ADJUST THE SLEEP TIME AS NEEDED FOR DELAY BETWEEN NOW AND NEXT ROW
                    time.sleep(3)
            except:
                self.process_live_data(self, ticker)


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
                    row[1].values[4]) # volume


    def yield_yf(self, ticker):
        """Yield a row of data from a live feed via Yahoo! Finance.
        This is a helper function that you can call as part of a trading strategy.

        Args:
            ticker (str): ticker to retrieve data for

        Yields:
            tuple: row of price data in a tuple
        """
        data = yf.download(tickers=ticker, period='1d', interval='1m', progress=False).tail(1)
        yield (data.index.values[0],
                data.values[0][0], # open
                data.values[0][1], # high
                data.values[0][2], # low
                data.values[0][3], # close
                data.values[0][4], # adj close
                data.values[0][5]) # volume



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
        at the time the function is called.

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

        Returns:
            float: sum value of all holdings in the market
        """
        df = self.summary_of_transactions()
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
