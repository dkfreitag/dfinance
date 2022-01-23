import pandas as pd
import numpy as np
import time
import pickle

import talib
from talib.abstract import *

def strategy(self, my_alpaca_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct, pkl_filename):
    # only get new data if the market is open
    while my_alpaca_port.is_market_open:
        # recursive try except block to restart in case of failure
        try:
            # initialize blank running_df
            running_df = pd.DataFrame()

            row_iterable = iter(self.yield_yf(ticker))
            for row in row_iterable:
                
                # For every iteration, save the prefill data in data_rows, then attach the newly
                # fetched row. This way, we only have all historical data but the most recent row
                # is always the newest data point. Must use copy() to ensure running_rows retains
                # original values.
                data_rows = self.running_rows.copy()
                data_rows.append(row)

                # turn data_rows into a dataframe
                running_df = pd.DataFrame(data_rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
                running_df.index = running_df['Date']
                running_df.drop(columns=['Date'], inplace=True)

                ###########################
                ##### ADDING FEATURES #####
                ###########################

                # add column names
                running_df['sma_10'] = np.NaN
                running_df['sma_20'] = np.NaN
                running_df['sma_30'] = np.NaN

                # calculate SMA for various time periods
                # if we have at least 10 rows in running_df, add the 10 day SMA
                # repeat same process for sma_20 and sma_30
                if len(running_df) > 10:
                    running_df.iloc[-1:-2:-1, 6] = SMA(running_df.iloc[-1:-11:-1]['Close'].values, timeperiod=10)[-1]

                if len(running_df) > 20:
                    running_df.iloc[-1:-2:-1, 7] = SMA(running_df.iloc[-1:-21:-1]['Close'].values, timeperiod=20)[-1]

                if len(running_df) > 30:
                    running_df.iloc[-1:-2:-1, 8] = SMA(running_df.iloc[-1:-31:-1]['Close'].values, timeperiod=30)[-1]



                # load the model
                with open(pkl_filename, 'rb') as file:  
                    model = pickle.load(file)

                # get a prediction based on the most recent row in running_df
                model_pred = model.predict(running_df.iloc[-1:-2:-1])[0]


                ###########################################
                ##### REMOVE THIS TO DO PAPER TRADING #####
                # set the model prediction to 0 so no action is taken
                model_pred = 0
                ##### REMOVE THIS TO DO PAPER TRADING #####
                ###########################################


                # If we aren't in the market (i.e. list_positions() == []),
                # and if our model prediction = 1, submit our bracket order
                if my_alpaca_port.api.list_positions() == [] and model_pred == 1:
                    my_alpaca_port.buy_stock_bracket_order(ticker=ticker,
                                                           share_cnt=share_cnt,
                                                           profit_pct=profit_pct,
                                                           stop_pct=stop_pct,
                                                           limit_pct=limit_pct)
                
                # sleep for a time before iterating on the next row
                time.sleep(600)

        except:
            strategy(self, my_alpaca_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct, pkl_filename)