# Class name must be Strategy
class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property needed
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['MIOTA-USDT'],
            },
        }
        self.period = 10 * 60 #10分鐘線
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 200  #定義20個週期，用以計算長均線
        self.ma_short = 50  #定義5個週期，用以計算短均線
        self.UP = 1
        self.DOWN = 2

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN

    # called every self.period
    def trade(self, information):
        exchange = 'Binance'
        pair = 'MIOTA-USDT'
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['MIOTA']))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        
        # cross up 黃金交叉
        if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 100,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down 死亡交叉
        #elif amount = self['assets'][exchange]['ETH'] >0:
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -100,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif close_price > l_ma and close_price > s_ma:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 100,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif close_price < l_ma and close_price < s_ma:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -100,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]

        self.last_cross_status = cur_cross
        return []
