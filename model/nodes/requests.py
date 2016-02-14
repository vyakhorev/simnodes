# defines requests from one node to another.
# these must be easily converted to UoW after being
# done. In fact, it's better to add "proposed uows"

import simpy

class cRequest(simulengin.cConnToDEVS):
    # If I like this class, i have to add pre-sim behaviour to it
    def __init__(self):
        self.semaphore = simpy.Resource(self.devs.simpy_env)
        self.is_done = 0
        self.requester_node = None
        self.provider_node = None
        
    def try_to_block(self):
        # calls this from a node / daemon
        if self.is_done: 
            return 0
        if self.semaphore.count == 0:
            self.semaphore.request()
            return 1
        else:
            return 0
    
    def release_undone(self):
        self.semaphore.release()
        
    def release_done(self):
        self.is_done = 1
        self.semaphore.release()

class cItemRequest(cRequest):
    def __init__(self, item, qtty, due_time):
        self.item = item
        self.qtty = qtty
        self.due_time = due_time
        
class cMoneyRequest(cRequest):
    def __init__(self, ccy, qtty, due_time):
        self.ccy = ccy
        self.qtty = qtty
        self.due_time = due_time
        
class cStaticInfoRequest(cRequest):
    def __init__(self, info_key):
        self.info_key = info_key

class cForecastInfoRequest(cRequest):
    def __init__(self, horizon):
        self.horizon = horizon