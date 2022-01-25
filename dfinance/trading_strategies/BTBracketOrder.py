import pandas as pd
import numpy as np
import pickle

import talib
from talib.abstract import *

def strategy(self, df, my_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct, pkl_filename):
    # initialize blank running_df
    running_df = pd.DataFrame()

    row_iterable = iter(self.yield_row(df))
    for row in row_iterable:
        self.running_rows.append(row)

        # turn self.running_rows into a dataframe
        running_df = pd.DataFrame(self.running_rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
        running_df.index = running_df['Date']
        running_df.drop(columns=['Date'], inplace=True)

        ###########################
        ##### ADDING FEATURES #####
        ###########################

        # add column names
        running_df['sma_10'] = np.NaN
        running_df['sma_20'] = np.NaN
        running_df['sma_30'] = np.NaN
        running_df['macd'] = np.NaN
        running_df['macdsignal'] = np.NaN
        running_df['macdhist'] = np.NaN
        running_df['rsi'] = np.NaN

        # calculate SMA for various time periods
        # if we have at least 10 rows in running_df, add the 10 day SMA
        # repeat same process for sma_20 and sma_30
        if len(running_df) > 10:
            running_df.iloc[-1:-2:-1, 6] = SMA(running_df.iloc[-1:-11:-1]['Close'].values, timeperiod=10)[-1]

        if len(running_df) > 20:
            running_df.iloc[-1:-2:-1, 7] = SMA(running_df.iloc[-1:-21:-1]['Close'].values, timeperiod=20)[-1]

        if len(running_df) > 30:
            running_df.iloc[-1:-2:-1, 8] = SMA(running_df.iloc[-1:-31:-1]['Close'].values, timeperiod=30)[-1]

        if len(running_df) > 33:
            macd, macdsignal, macdhist = MACD(running_df['Close'].values, fastperiod=12, slowperiod=26, signalperiod=9)
            running_df.iloc[-1:-2:-1, 9] = macd[-1]
            running_df.iloc[-1:-2:-1, 10] = macdsignal[-1]
            running_df.iloc[-1:-2:-1, 11] = macdhist[-1]
        
        if len(running_df) > 14:
            real = RSI(running_df['Close'].values, timeperiod=14)
            running_df.iloc[-1:-2:-1, 12] = real[-1]

        # load the model
        with open(pkl_filename, 'rb') as file:  
            model = pickle.load(file)

        # get a prediction based on the most recent row in running_df
        model_pred = model.predict(running_df.iloc[-1:-2:-1])[0]

        # initialize buy_price
        buy_price = 0

        # if the model predicts we should buy, then buy at the close price on the close date
        if model_pred == 1 and self.in_the_market == False:
            my_port.buy_stock(ticker, share_cnt, self.running_rows[-1][3], self.running_rows[-1][0])
            print(f'Buying {share_cnt} shares of {ticker} for {share_cnt * self.running_rows[-1][3]}')
            buy_price = self.running_rows[-1][3]
            self.in_the_market = True

        # if we are in the market and the close price is at/above buy_price * profit_pct, take profit
        if self.running_rows[-1][3] >= buy_price * profit_pct and self.in_the_market == True:
            my_port.sell_stock(ticker, share_cnt, self.running_rows[-1][3], self.running_rows[-1][0])
            print(f'Selling {share_cnt} shares of {ticker} for {share_cnt * self.running_rows[-1][3]}')
            self.in_the_market = False

        # if we are in the market and the close price is at/below buy_price * limit_pct, stop loss
        if self.running_rows[-1][3] <= buy_price * limit_pct and self.in_the_market == True:
            my_port.sell_stock(ticker, share_cnt, self.running_rows[-1][3], self.running_rows[-1][0])
            print(f'Selling {share_cnt} shares of {ticker} for {share_cnt * self.running_rows[-1][3]}')
            self.in_the_market = False

    # close our position if we happen to still be in the market once we have iterated
    # through all rows in the backtest data
    if self.in_the_market:
        my_port.sell_stock(ticker, share_cnt, self.running_rows[-1][3], self.running_rows[-1][0])
        print('\nClosing position.')
        print(f'\nSelling {share_cnt} shares of {ticker} for {share_cnt * self.running_rows[-1][3]}\n')
        self.in_the_market = False
