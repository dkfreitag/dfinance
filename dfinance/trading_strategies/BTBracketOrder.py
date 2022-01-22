import pandas as pd
import time
import pickle

def strategy(self, df, my_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct, pkl_filename):
    row_iterable = iter(self.yield_row(df))
    for row in row_iterable:
        self.running_rows.append(row)

        # CHANGE CODE HERE AND BELOW

        # self.running_rows[-1] is the most recent row in time
        # self.running_rows[-2] is the row before that one in time
        # self.running_rows[0] is the first point in time
        
        # load the model
        with open(pkl_filename, 'rb') as file:  
            model = pickle.load(file)

        # prepare the data in the format needed by the model
        temp_row = pd.DataFrame([self.running_rows[-1]], columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
        temp_row.index = temp_row['Date']
        temp_row.drop(columns=['Date'], inplace=True)

        # get a prediction based on the row data
        model_pred = model.predict(temp_row)[0]

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
