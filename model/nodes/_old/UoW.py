class cUnitOfWork(object):
    job_type = ""

    def __init__(self):
        self.trace = [] # a log

    def __repr__(self):
        return self.job_type

    def add_trace(self, when, who, do_what):
        self.trace += [(when, who, do_what)]


class cEconomicUoW(cUnitOfWork):
    """
        Supports CF and GF interfaces
    """
    def __init__(self):
        super(cEconomicUoW, self).__init__()
        self.cf = {} # Key is a currency
        self.gf = {} # Key is an item

    def add_to_cf(self, what, when, howmuch):
        if not(what in self.cf):
            self.cf[what] = cCashFlow()
        self.cf[what].add_flow(when, howmuch)

    def add_to_gf(self, what, when, howmuch):
        if not(what in self.gf):
            self.gf[what] = cGoodsFlow()
        self.gf[what].add_flow(when, howmuch)


class cFlow(object):
    """
        Howmuch and when for a single what.
    """
    #TODO: add some algebra with CF, iterations, zero checking (would be important)
    def __init__(self):
        self.flow = {} #Ordered dict?...
        self.active_whens = []
        self.is_sorted = 0

    def add_flow(self, when, howmuch):
        self.flow[when] = howmuch
        self.active_whens += [when]

    def wipe(self):
        self.flow = {} #Ordered dict?...
        self.active_whens = []
        self.is_sorted = 0


class cCashFlow(cFlow):
    pass


class cGoodsFlow(cFlow):
    pass

# *****************************
# Actual implementations are below
# *****************************

class cBuyGoodsUoW(cEconomicUoW):
    """
        Instruction to buy some goods
    """
    job_type = "buy_goods"

    def __init__(self, what, howmuch, price):
        super().__init__()
        self.what = what
        self.howmuch = howmuch
        self.price = price

    def __repr__(self):
        return self.job_type + " " + str(round(self.howmuch, 2)) + " of " + self.what + " for " + str(round(self.get_value(), 2))

    def get_value(self):
        return self.price * self.howmuch

class cSellGoodsUoW(cEconomicUoW):
    """
        Instruction to sell some goods
    """
    job_type = "sell_goods"

    def __init__(self, what, howmuch, price):
        super().__init__()
        self.what = what
        self.howmuch = howmuch
        self.price = price

    def __repr__(self):
        return self.job_type + " " + str(round(self.howmuch, 2)) + " of " + self.what + " for " + str(round(self.get_value(), 2))

    def get_value(self):
        return self.price * self.howmuch

class cShipmentUoW(cEconomicUoW):
    """
        Instruction to buy some goods
    """
    job_type = "shipment"

    def __init__(self, what, howmuch, price):
        super().__init__()
        self.what = what
        self.howmuch = howmuch
        self.price = price

    def __repr__(self):
        return self.job_type + " " + str(round(self.howmuch, 2)) + " of " + self.what + " for " + str(round(self.get_value(), 2))

    def get_value(self):
        return self.price * self.howmuch

class cPaymentUoW(cEconomicUoW):
    """
        Instruction to buy some goods
    """
    job_type = "payment"

    def __init__(self, what, howmuch):
        super().__init__()
        self.what = what
        self.howmuch = howmuch

    def __repr__(self):
        return self.job_type + " " + str(round(self.howmuch, 2)) + " of " + self.what

    def get_value(self):
        return self.howmuch