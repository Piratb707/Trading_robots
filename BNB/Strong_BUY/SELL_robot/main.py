from Trading_robots.BNB.Strong_BUY.SELL_robot.config import api_key, api_secret
from binance.client import Client
import time
from tradingview_ta import TA_Handler, Interval

SYMBOL = 'BNBUSDT'  # Symbol for trading
INTERVAL = Interval.INTERVAL_30_MINUTES  # Candlestick interval
QNTY = 10  # Quantity of assets to trade

client = Client(api_key, api_secret)

def get_data():
    """
    Get data using the TradingView API.
    
    Returns:
        dict: Analysis summary of the activity.
    """
    output = TA_Handler(symbol=SYMBOL,
                        screener='Crypto',
                        exchange='Binance',
                        interval=INTERVAL)
    activity_summary = output.get_analysis().summary
    return activity_summary

def place_order(order_type):
    """
    Place a market order for buying or selling.
    
    Args:
        order_type (str): Type of order, either 'BUY' or 'SELL'.
    """
    if order_type == 'BUY':
        # Place a market order to buy the specified quantity of the symbol
        order = client.create_order(symbol=SYMBOL, side=order_type, type='MARKET', quantity=QNTY)
        print(order)
    if order_type == 'SELL':
        # Place a market order to sell the specified quantity of the symbol
        order = client.create_order(symbol=SYMBOL, side=order_type, type='MARKET', quantity=QNTY)
        print(order)

def calculate_profit():
    """
    Calculate the total profit based on executed trades.
    
    Returns:
        float: Total profit.
    """
    trades = client.get_my_trades(symbol=SYMBOL)
    total_profit = 0
    for trade in trades:
        if trade['isBuyer']:
            # Deduct the quote quantity from the total profit if it was a buy trade
            total_profit -= float(trade['quoteQty'])
        else:
            # Add the quote quantity to the total profit if it was a sell trade
            total_profit += float(trade['quoteQty'])
    return total_profit

def main():
    """
    Main function to execute trading operations.
    """
    buy = False
    sell = True
    print('Script running...')
    start_time = time.time()
    total_deals = 0
    total_profit = 0
    while True:
        data = get_data()
        print(data)
        if data['RECOMMENDATION'] == 'STRONG_BUY' and not buy:
            print("_____BUY_____")
            # Place a buy order if the recommendation is 'STRONG_BUY'
            place_order('BUY')
            buy = not buy
            sell = not sell
            total_deals += 1

        if data['RECOMMENDATION'] == 'STRONG_SELL' and not sell:
            print("_____SELL_____")
            # Place a sell order if the recommendation is 'STRONG_SELL'
            place_order('SELL')
            buy = not buy
            sell = not sell
            total_deals += 1

        elapsed_time = time.time() - start_time
        if elapsed_time >= 3600:  # If 1 hour has passed (3600 seconds)
            total_profit = calculate_profit()
            print(f"Total Deals: {total_deals}")
            print(f"Total Profit: {total_profit}")
            start_time = time.time()
            total_deals = 0
            total_profit = 0

        time.sleep(1)

if __name__ == '__main__':
    main()
