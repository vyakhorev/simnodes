import model.nodes.metatypes as metatypes
from model.nodes.meta import MetaStruct

class cMessage(MetaStruct):
    """
        Message container class, which hold all flowing data , receivers and senders .

        :attr:'uows' - holding units of work
        :attr:'sender' - link to :class:'sender'
        :attr:'receivers' list of  :classes:'receivers'

        :method:'add_receiver': provides adding of receivers
    """
    def __init__(self, uows, sender, receivers):
        super().__init__()
        self._uows = uows
        self._sender = sender
        self._receivers = receivers

    @property
    def uows(self):
        return self._uows

    @property
    def sender(self):
        return self._sender

    @property
    def receivers(self):
        return self._receivers

    @property
    def mesid(self):
        """ Unique message id """
        return self.nodeid

    def add_receiver(self):
        pass

    def __repr__(self):
        return "{} '{}' from {} to {} ".format(self.mesid, self.uows, self.sender, self.receivers)