import pandas as pd
import time

def strategy(self, my_alpaca_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct):
    # only get new data if the market is open
    while my_alpaca_port.is_market_open:
        # recursive try except block to restart in case of failure
        try:
            row_iterable = iter(self.yield_yf(ticker))
            for row in row_iterable:
                
                # For every iteration, save the prefill data in data_rows, then attach the newly
                # fetched row. This way, we only have all historical data but the most recent row
                # is always the newest data point. Must use copy() to ensure running_rows retains
                # original values.
                data_rows = self.running_rows.copy()
                data_rows.append(row)

                # CHANGE CODE HERE AND BELOW

                # data_rows[-1] is the most recent row in time
                # data_rows[-2] is the row before that one in time
                # data_rows[0] is the first point in time
                

                #####
                ##### Commenting out the model strategy for now
                ##### Current model is trained on RXMD, which cannot be purchased through Alpaca
                #####

                # # load the model
                # with open(pkl_filename, 'rb') as file:  
                #     model = pickle.load(file)

                # # prepare the data in the format needed by the model
                # temp_row = pd.DataFrame([data_rows[-1]], columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
                # temp_row.index = temp_row['Date']
                # temp_row.drop(columns=['Date'], inplace=True)

                # # get a prediction based on the row data
                # model_pred = model.predict(temp_row)[0]
                


                model_pred = 1

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
            self.strategy(my_alpaca_port, ticker, share_cnt, profit_pct, stop_pct, limit_pct)