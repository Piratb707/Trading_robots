from config import api_key, api_secret  # Импортируем ключи API из файла config | Import API keys from config file
from binance.client import Client  # Импортируем класс Client из библиотеки binance | Importing the Client class from the binance library
import time  # Импортируем модуль time для задержки времени | Importing the time module to delay time
from tradingview_ta import TA_Handler, Interval, Exchange  # Импортируем необходимые классы из библиотеки tradingview_ta | We import the necessary classes from the tradingview_ta library

SYMBOL = 'BNBUSDT'  # Устанавливаем символ торговой пары | Setting the trading pair symbol
INTERVAL = Interval.INTERVAL_30_MINUTES  # Устанавливаем интервал свечей | Set the interval of candles
QNTY = 10  # Устанавливаем количество для ордера | Setting the order quantity

client = Client(api_key, api_secret)  # Создаем экземпляр класса Client с использованием ключей API | Create an instance of the Client class using API keys

def get_data():
    # Получаем данные анализа торговой пары | Getting trading pair analysis data
    output = TA_Handler(symbol=SYMBOL,
                        screener='Crypto',
                        exchange='Binance',
                        interval=INTERVAL)

    activiti = output.get_analysis().summary  # Получаем сводку активности торговой пары | Getting a summary of the activity of a trading pair
    return activiti


def place_order(order_type):
    if(order_type == 'BUY'):
        # Создаем ордер на покупку | Creating a buy order
        order = client.create_order(symbol=SYMBOL, side=order_type, type='MARKET', quantity=QNTY)
        print(order)
    if(order_type == 'SELL'):
        # Создаем ордер на продажу | Creating a sell order
        order = client.create_order(symbol=SYMBOL, side=order_type, type='MARKET', quantity=QNTY)
        print(order)


def main():
    buy = False  # Переменная для отслеживания состояния покупки | Purchase status tracking variable
    sell = True  # Переменная для отслеживания состояния продажи | Variable to track the state of the sale
    print('script running...')  # Выводим сообщение о запуске скрипта | Displaying a message about running the script
    while True:
        data = get_data()  # Получаем данные анализа торговой пары | Getting trading pair analysis data
        print(data)  # Выводим данные анализа | Displaying analysis data
        if (data['RECOMMENDATION'] == 'STRONG_BUY' and not buy):
            # Если рекомендация - сильная покупка и еще не было покупки, выполняем следующие действия:
            # If the recommendation is a strong buy and there hasn't been a buy yet, perform the following actions:
            print("_____BUY_____")  # Выводим сообщение о покупке | Displaying a purchase message
            place_order('BUY')  # Выполняем ордер на покупку | Execute a buy order
            buy = not buy  # Обновляем состояние покупки | Update purchase status
            sell = not sell  # Обновляем состояние продажи | Update the sale status

        if (data['RECOMMENDATION'] == 'STRONG_SELL' and not sell):
            # Если рекомендация - сильная продажа и еще не было продажи, выполняем следующие действия:
            # If the recommendation is a strong sale and there has not yet been a sale, perform the following actions:
            print("_____SELL_____")  # Выводим сообщение о продаже | Displaying a sell message
            place_order('SELL')  # Выполняем ордер на продажу | Execute a sell order
            buy = not buy  # Обновляем состояние покупки | Update purchase status
            sell = not sell  # Обновляем состояние продажи | Update the sale status

        time.sleep(1)  # Задержка на 1 секунду | 1 second delay


if __name__ == '__main__':
    main()
