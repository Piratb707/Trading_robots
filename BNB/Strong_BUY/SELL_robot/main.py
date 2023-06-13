from Trading_robots.BNB.Strong_BUY.SELL_robot.config import api_key, api_secret
from binance.client import Client
import time
from tradingview_ta import TA_Handler, Interval

# Импортирование необходимых модулей и библиотек

SYMBOL = 'BNBUSDT'  # Символ для торговли
INTERVAL = Interval.INTERVAL_30_MINUTES  # Интервал свечей
QNTY = 10  # Количество активов для торговли

client = Client(api_key, api_secret)  # Создание клиента Binance API с использованием ключа API и секретного ключа

def get_data():
    # Получение данных с помощью TradingView API
    output = TA_Handler(symbol=SYMBOL,
                        screener='Crypto',
                        exchange='Binance',
                        interval=INTERVAL)

    activiti = output.get_analysis().summary
    return activiti


def place_order(order_type):
    # Размещение ордера на покупку или продажу
    if(order_type == 'BUY'):
        order = client.create_order(symbol=SYMBOL, side=order_type, type='MARKET', quantity=QNTY)
        print(order)
    if(order_type == 'SELL'):
        order = client.create_order(symbol=SYMBOL, side=order_type, type='MARKET', quantity=QNTY)
        print(order)


def main():
    buy = False
    sell = True
    print('script running...')
    while True:
        data = get_data()
        print(data)
        if (data['RECOMMENDATION'] == 'STRONG_BUY' and not buy):
            print("_____BUY_____")
            place_order('BUY')
            buy = not buy
            sell = not sell

        if (data['RECOMMENDATION'] == 'STRONG_SELL' and not sell):
            print("_____SELL_____")
            place_order('SELL')
            buy = not buy
            sell = not sell

        time.sleep(1)


if __name__ == '__main__':
    main()
