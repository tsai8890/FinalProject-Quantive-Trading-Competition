class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 2 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.last_typPrice = 0
        self.last_MFI = 50
        self.moneyFlow = []
        self.close_price_trace = np.array([])
        self.ma_long = 400
        self.ma_short = 100
        self.ma_mini = 25
        self.UP = 1
        self.DOWN = 2


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        mini_ma = talib.SMA(self.close_price_trace, self.ma_mini)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if ( s_ma - 1 > l_ma ) and ( mini_ma - 0.5 > s_ma ):
            return self.UP
        elif (s_ma + 0.25 <= l_ma) and ( mini_ma +0.125 <= s_ma ):
            return self.DOWN
        return None


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        high_price = information['candles'][exchange][pair][0]['high']
        low_price = information['candles'][exchange][pair][0]['low']
        volume = information['candles'][exchange][pair][0]['volume']
        # for MFI calculation
        typicalPrice = ( high_price + low_price + close_price ) / 3
        curMF = typicalPrice * volume
        if typicalPrice < self.last_typPrice:
            curMF *= -1
        self.moneyFlow.append(curMF)
        self.moneyFlow = self.moneyFlow[-14:]
        self.last_typPrice = typicalPrice

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['BTC']))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        #calculate MFI
        posMF, negMF, mfiBUY, mfiSELL = 0, 0, False, False
        if len(self.moneyFlow)>=14:
            for i in range(14):
                if(self.moneyFlow[i] > 0):
                    posMF += self.moneyFlow[i]
                else:
                    negMF -= self.moneyFlow[i]
            MFR = posMF / negMF
            MFI = 100 - 100 / (1 + MFR)
            if( self.last_MFI<30 and MFI-1>=30):
                mfiBUY = True
            elif( self.last_MFI>80and MFI+1<=80):
                mfiSELL = True
            self.last_MFI = MFI

        # cross up
        if (cur_cross == self.UP and self.last_cross_status == self.DOWN and (mfiBUY or not mfiSELL)):
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 3,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif (cur_cross == self.DOWN and self.last_cross_status == self.UP and (mfiSELL or not mfiBUY)):
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -3,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []
