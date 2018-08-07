import sys
import websocket
import threading
import ssl
import json
import time
from datetime import datetime
from datetime import timedelta
from time import sleep


class BCEXWebsocket():

    def __init__(self):
        self.__reset()

    def __del__(self):
        self.exit()

    def connect(self, endpoint, symbol):
        '''Connect to the websocket.'''
        self.symbol = symbol
        filename = 'orderbook_' + symbol + '.txt'
        self.my_log = open(filename, 'a')
        self.__connect(endpoint)
        print('Connected to WS. Waiting for data images, this may take a moment...')

    def error(self, err):
        self._error = err
        self.exit()

    def exit(self):
        self.exited = True
        self.my_log.close()
        self.ws.close()


    def __connect(self, wsURL):
        '''Connect to the websocket in a thread.'''

        ssl_defaults = ssl.get_default_verify_paths()
        sslopt_ca_certs = {'ca_certs': ssl_defaults.cafile}
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         header=[],
                                         cookie='__jsluid=a3718fd232c1901c0400e3a9a63ea216; USER_UNI=e7ef627cd9bb4c1f41611cce71b3675c; PHPSESSID=34f3eea0ac392475f8f5faf651a504dc; COINTYPE=btc2ckusd; lang=us_EN; UNIQUEID=f4c56f83ff9427fa3f173bebbd5afa4e'
                                         )

        self.lastConnect = datetime.utcnow()
        self.wst = threading.Thread(target=lambda: self.ws.run_forever(sslopt=sslopt_ca_certs))
        self.wst.daemon = True
        self.wst.start()

        # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
            sleep(2)
            conn_timeout -= 1

        if not conn_timeout or self._error:
            print("Couldn't connect to WS! Exiting.")
            self.exit()
            sys.exit(1)

    def __wait_for_symbol(self, symbol):
        '''On subscribe, this data will come down. Wait for it.'''
        while not {'instrument', 'trade', 'quote'} <= set(self.data):
            sleep(0.1)

    def __index_of_first_non_digit(self, message):
        index = 0;
        for i in message:
            if not i.isdigit():
                return index
            index = index + 1

        return -1

    def __on_message(self, ws, message):
        '''Handler for parsing WS messages.'''

        firstNonDigit = self.__index_of_first_non_digit(message)
        if firstNonDigit == -1:
            #Various status messages seem to be returned as single digits. We ignore them.
            return
        message = json.loads(message[firstNonDigit:])

        if len(message) != 2:
            print(message)
            return

        header = message[0]
        body = message[1]

        order = json.loads(body['order']) if 'order' in body else None
        orderbook = json.loads(body['sum']) if 'sum' in body else None

        bestAsk = orderbook['sale'][0]
        bestBid = orderbook['buy'][0]

        #Log orderbook info
        currentTime = int(time.time() * 1000);
        self.my_log.write(str(currentTime))
        self.my_log.write(',')
        self.my_log.write(str(bestAsk))
        self.my_log.write(',')
        self.my_log.write(str(bestBid))
        self.my_log.write(',')
        self.my_log.write(str(orderbook))
        self.my_log.write('\n')

        #Occasionally send keep-alive back to server
        delta = currentDate - self.lastConnect
        if delta > timedelta(seconds=30):
            self.lastConnect = currentDate
            self.ws.send('2')

    def __on_open(self, ws):
        print("Websocket Opened.")

    def __on_close(self, ws):
        print('Websocket Closed')
        self.exit()

    def __on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __reset(self):
        self.exited = False
        self._error = None

if __name__ == "__main__":

    ws = BCEXWebsocket()
    url = 'wss://sha.bcex.ca:9443/socket.io/?EIO=3&transport=websocket'
    ws.connect(url, "xml2ckusd")
    while(ws.ws.sock.connected):
        sleep(1)

