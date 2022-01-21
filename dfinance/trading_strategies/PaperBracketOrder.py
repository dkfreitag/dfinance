import pandas as pd
import time

def strategy(self, my_alpaca_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct):
    # only get new data if the market is open
    while my_alpaca_port.is_market_open:
        # recursive try except block to restart in case of failure
        try:
            row_iterable = iter(self.yield_yf(ticker))
            for row in row_iterable:
                self.running_rows.append(row)

                # sleep for an hour before getting new data
                #time.sleep(360)

                # CHANGE CODE HERE AND BELOW

                # self.running_rows[-1] is the most recent row in time
                # self.running_rows[-2] is the row before that one in time
                # self.running_rows[0] is the first point in time
                
                
                # TO DO HERE: feed the model the data from running_rows
                # Get the prediction from the model
                # If the prediction from the model is 1, then proceed with the following:


                # If we aren't in the market (i.e. list_positions returns []), submit our bracket order
                if my_alpaca_port.api.list_positions() == []:
                    my_alpaca_port.buy_stock_bracket_order(ticker=ticker,
                                                           share_cnt=share_cnt,
                                                           profit_pct=profit_pct,
                                                           stop_pct=stop_pct,
                                                           limit_pct=limit_pct)
                else:
                    return

        except:
            self.strategy(my_alpaca_port, ticker)