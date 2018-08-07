import ccxt
import time 


def logtrades(pair):

    hour_ago = int(time.time() * 1000) - 60 * 1000 
    exchange = getattr(ccxt, "bcex")()

    last_time = int(time.time() * 1000) - (60 * 1000  * 1000)

    with open('trades.txt', 'a') as my_log:

        while True:

            trades = exchange.fetch_trades(pair, since = last_time)

            for trade in trades:

                my_log.write(trade['timestamp'])
                my_log.write(",")
                my_log.write(trade['datetime'])
                my_log.write(",")
                my_log.write(trade['price'])
                my_log.write(",")
                my_log.write(trade['amount'])
                my_log.write("\n")
                my_log.flush()

                last_time = trade['timestamp']

                time.sleep(60) #sleep one minute

if __name__ == "__main__":
    logtrades("XLM/CKUSD");