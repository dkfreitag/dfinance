import pandas as pd
from statistics import mean

def strategy(self, df, my_port, sma_short, sma_long, share_num, ticker):
    """Simple Moving Average Crossover Strategy
    Given as an example of how to write a strategy.

    Args:
        df (dataframe): dataframe of price data
        my_port (Portfolio): your portfolio object
        sma_short (int): number of periods for short moving average
        sma_long (int): number of periods for long moving average
        share_num (float): number of shares to buy/sell on each crossover
        ticker (str): ticker to trade
    """
    row_iterable = iter(self.yield_row(df))
    for row in row_iterable:
        self.running_rows.append(row)

        # CHANGE CODE HERE AND BELOW

        # self.running_rows[-1] is the most recent row in time
        # self.running_rows[-2] is the row before that one in time
        # self.running_rows[0] is the first point in time
        
        # if we have enough periods to get both short and long moving averages
        if len(self.running_rows) >= sma_long:
            sma_short_avg = mean(pd.DataFrame(self.running_rows[-1:-(sma_short+1):-1])[3].values)
            sma_long_avg = mean(pd.DataFrame(self.running_rows[-1:-(sma_long+1):-1])[3].values)

            if sma_short_avg < sma_long_avg:
                print(f'{self.running_rows[-1][0]} | Short: {sma_short_avg:.02f} | Long: {sma_long_avg:.02f} | Short < Long')
                
                # if the short moving average goes below the long moving average
                # and we are in the market
                # sell a share at close price
                if self.in_the_market:
                    my_port.sell_stock(ticker, share_num, self.running_rows[-1][3], self.running_rows[-1][0])
                    print(f'\nSelling {share_num} shares of {ticker} for {share_num * self.running_rows[-1][3]}\n')
                    self.in_the_market = False

            elif sma_short_avg > sma_long_avg:
                print(f'{self.running_rows[-1][0]} | Short: {sma_short_avg:.02f} | Long: {sma_long_avg:.02f} | Short > Long')
                
                # if the short moving average goes above the long moving average
                # and we are not in the market
                # buy a share at close price
                if not self.in_the_market:
                    my_port.buy_stock(ticker, share_num, self.running_rows[-1][3], self.running_rows[-1][0])
                    print(f'\nBuying {share_num} shares of {ticker} for {share_num * self.running_rows[-1][3]}\n')
                    self.in_the_market = True
                
            elif sma_short_avg == sma_long_avg:
                print(f'{self.running_rows[-1][0]} | Short: {sma_short_avg:.02f} | Long: {sma_long_avg:.02f} | Short == Long')

    # close our position if we happen to still be in the market
    if self.in_the_market:
        my_port.sell_stock(ticker, share_num, self.running_rows[-1][3], self.running_rows[-1][0])
        print('Closing position.')
        print(f'\nSelling {share_num} shares of {ticker} for {share_num * self.running_rows[-1][3]}\n')
        self.in_the_market = False