from binance.client import Client
import keys
import pandas as pd
import time
from datetime import datetime, timedelta

# Create a Binance API client instance
# Создаем экземпляр клиента Binance API
client = Client(keys.api_key, keys.api_secret)

# Get Binance server time
# Получение времени сервера Binance
server_time = client.get_server_time()
server_timestamp = server_time['serverTime']

# Variables for tracking transaction statistics
# Переменные для отслеживания статистики сделок
total_deals = 0  # Счетчик суммы сделок | Transaction amount counter
profit = 0  # Переменная для отслеживания заработка | Variable for tracking earnings
loss = 0  # Переменная для отслеживания потерь | Variable for loss tracking
successful_deals = 0  # Счетчик успешных сделок | Successful transactions counter
unsuccessful_deals = 0  # Счетчик неуспешных сделок | Unsuccessful transactions counter
open_position = False  # Флаг, указывающий, открыта ли позиция | Flag indicating whether the position is open or not
last_open_time = None  # Время открытия последнего ордера | Time of opening of the last order

# Decoder for API error handling
# Декоратор для обработки ошибок API
def handle_api_error(func):
    """
    Декоратор для обработки ошибок API.

    Args:
        func: Функция, которую нужно обернуть.

    Returns:
        Обернутая функция.

    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"API Error: {e}")
            if isinstance(e, Client.APIError) and e.code == -1013:
                print("Filter failure: NOTIONAL")
                print("Retrying to close the order...")
                retry_close_order(*args, **kwargs)
            else:
                print("Restarting after 1 minute...")
                time.sleep(60)
                return func(*args, **kwargs)
    return wrapper

# Function for attempting to close an order
# Функция для попытки закрытия ордера
def retry_close_order(*args, **kwargs):
    """
    Попытка закрыть ордер после ошибки NOTIONAL.

    Args:
        *args: Позиционные аргументы.
        **kwargs: Именованные аргументы.

    """
    max_attempts = 3  # Максимальное количество попыток закрытия ордера | Maximum number of attempts to close an order
    attempt = 1  # Текущая попытка |  Current attempt

    while attempt <= max_attempts:
        try:
            strategy(*args, **kwargs)
            break
        except Exception as e:
            print(f"Error occurred during closing the order: {e}")
            print(f"Retrying to close the order. Attempt {attempt}/{max_attempts}...")
            attempt += 1
            time.sleep(10)

    if attempt > max_attempts:
        print("Max attempts reached. Skipping the order closing.")

# Function to get the most successful currency pair
# Функция для получения самой успешной валютной пары
@handle_api_error
def top_coin():
    """
    Получает самую успешную валютную пару на основе изменения цены.

    Returns:
        Строка с символом валютной пары.

    """
    all_tickers = pd.DataFrame(client.get_ticker())
    usdt = all_tickers[all_tickers.symbol.str.contains('USDT')]
    work = usdt[~((usdt.symbol.str.contains('UP')) | (usdt.symbol.str.contains('DOWN')))]
    top_coin = work[work.priceChangePercent.astype(float) == work.priceChangePercent.astype(float).max()]
    top_coin = top_coin.symbol.values[0]
    return top_coin

# Функция для получения последних данных свечей
@handle_api_error
def last_data(symbol, interval, lookback):
    """
    Получает последние данные свечей для заданной валютной пары.

    Args:
        symbol: Символ валютной пары.
        interval: Интервал времени свечей.
        lookback: Количество прошедших свечей, которые нужно получить.

    Returns:
        DataFrame с данными свечей.

    """
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + "min ago UTC"))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

# Function to close an open position
@handle_api_error
def close_position(asset):
    """
    Closes the open position for the given asset.

    Args:
        asset: Symbol of the currency pair to close the position.

    """
    global open_position

    try:
        positions = client.get_account()['positions']
        for position in positions:
            if position['symbol'] == asset:
                if float(position['positionAmt']) > 0:
                    qty = float(position['positionAmt'])
                    order = client.create_order(symbol=asset, side='SELL', type='MARKET', quantity=qty)
                    print("Closing position:", order)
                    open_position = False
                    break
    except Exception as e:
        print(f"Error occurred during closing the position: {e}")

# Основная стратегия
@handle_api_error
def strategy(buy_amt, SL=0.100, Target=1.01):
    """
    Основная стратегия торговли.

    Args:
        buy_amt: Сумма для покупки валюты.
        SL: Уровень стоп-лимита для продажи.
        Target: Уровень цели для продажи.

    """
    global total_deals, profit, loss, successful_deals, unsuccessful_deals, open_position, last_open_time

    if not open_position or (open_position and datetime.now() - last_open_time > timedelta(hours=1)):
        try:
            asset = top_coin()
            df = last_data(asset, '1m', '120')

        except:
            time.sleep(61)
            asset = top_coin()
            df = last_data(asset, '1m', '120')

        qty = round(buy_amt / df.Close.iloc[-1], 1)

        if ((df.Close.pct_change() + 1).cumprod()).iloc[-1] > 1:
            print(asset)
            print(df.Close.iloc[-1])
            print(qty)

            # Получение информации о лоте для валютной пары
            lot_size_info = [f for f in client.get_symbol_info(asset)["filters"] if f["filterType"] == "LOT_SIZE"][0]
            step_size = float(lot_size_info['stepSize'])
            min_qty = float(lot_size_info['minQty'])

            qty = max(min_qty, round(qty / step_size) * step_size)

            # Ожидание падения цены на 0,025% или движения цены ниже целевой цены
            target_price = df.Close.iloc[-1] * 0.99
            while df.Close.iloc[-1] > target_price:
                try:
                    df = last_data(asset, '1m', '2')
                except:
                    print('Restart after 1 min')
                    time.sleep(61)
                    df = last_data(asset, '1m', '2')

                print(time.strftime("|%H.%M.%S|"), f"{asset} Price: {df.Close.iloc[-1]}, Target: {target_price}")
                time.sleep(5)

            # Close the open position before opening a new one
            if open_position:
                close_position(asset)

            order = client.create_order(symbol=asset, side='BUY', type='MARKET', quantity=qty)
            print(order)
            buyprice = float(order['fills'][0]['price'])
            open_position = True
            last_open_time = datetime.now()

            while open_position:
                try:
                    df = last_data(asset, '1m', '2')
                except:
                    print('Restart after 1 min')
                    time.sleep(61)
                    df = last_data(asset, '1m', '2')

                print(time.strftime("|%H.%M.%S|"), f"Price: {df.Close.iloc[-1]}, Target: {buyprice * Target}, Stop: {buyprice * SL}")
                if df.Close.iloc[-1] <= buyprice * SL or df.Close.iloc[-1] >= buyprice * Target:
                    # Обновленная часть кода, чтобы проверить, что цена открытия ордера не ниже фактической цены
                    if df.Close.iloc[-1] <= buyprice:
                        print("Order not found within the specified range. Restarting...")
                        break

                    # Используем параметр quoteOrderQty для установки номинала ордера в USDT
                    quote_qty = qty * buyprice
                    order = client.create_order(symbol=asset, side="SELL", type="MARKET", quoteOrderQty=quote_qty)
                    print(order)
                    total_deals += 1  # Увеличиваем счетчик суммы сделок на 1

                    if df.Close.iloc[-1] >= buyprice * Target:
                        profit += buyprice * Target - buyprice  # Вычисляем заработок и добавляем его к переменной profit
                        successful_deals += 1  # Увеличиваем счетчик успешных сделок на 1
                    else:
                        loss += buyprice - buyprice * SL  # Вычисляем потери и добавляем их к переменной loss
                        unsuccessful_deals += 1  # Увеличиваем счетчик неуспешных сделок на 1

                    open_position = False  # Закрытие позиции
                    time.sleep(300)  # Пауза в 5 минут после закрытия сделки

        else:
            print(time.strftime("|%H.%M.%S|"), "Searching...")
            time.sleep(1)
    else:
        print(time.strftime("|%H.%M.%S|"), "Waiting for the current position to be closed...")

# Бесконечный цикл для выполнения стратегии
while True:
    try:
        strategy(15)
    except:
        print("Not enough funds. Restarting...")
        time.sleep(1)
    print("------------------------")
    print(time.strftime("|%H:%M:%S|"))
    print("Total Deals:", total_deals)
    print("Profit (USDT):", profit)
    print("Loss (USDT):", loss)
    print("Successful Deals:", successful_deals)
    print("Unsuccessful Deals:", unsuccessful_deals)
    print("------------------------")
    time.sleep(60)
