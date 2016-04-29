# coding:utf-8

from model.nodes.classes.Node_func_v2 import cNodeBase
from model.nodes.classes.SimBase import cSimNode
import model.nodes.classes.Ports_v2 as ports
import model.nodes.simulengin.simulengin as simulengin
from model.nodes.wallet import cWallet

class cBaseBlueAgent(cNodeBase, cSimNode):
    """
    Нода с одним входом 1:1 и одним выходом 1:1
    """

    def __init__(self, name):
        super().__init__(name)

        self.in_orders = ports.cOnetoOneInpQueue(self)
        self.out_orders = ports.cOnetoOneOutQueue(self)
        self.ports = [self.in_port, self.out_port]
        for p_i in self.ports:
            self.register_port(p_i)

        self.daemons = []

        self.item_wallet = cWallet()

    def iter_item_wallets(self):
        # Интерфейс для выдачи всех кошелей - для проверки условий
        yield self.item_wallet

    def register_daemon(self, new_daemon):
        self.daemons += [new_daemon]

    def connect_to_input(self, port_to_connect):
        self.in_orders.connect_to_port(port_to_connect)

    def connect_to_output(self, port_to_connect):
        self.out_orders.connect_to_port(port_to_connect)


class cNodeTradeContract(cNodeBase, cSimNode):
    """
    Нода, взаимодействующая с двумя другими по поводу купли-продажи
    Демон в ней обеспечивает выполнение паттерна "контракт" для
    каждого запроса.
    """
    def __init__(self, name):
        super().__init__(name)

        self.out_party_buyer = ports.cOnetoOneOutQueue(self)
        self.in_party_buyer = ports.cOnetoOneInpQueue(self)
        self.out_party_seller = ports.cOnetoOneOutQueue(self)
        self.in_party_seller = ports.cOnetoOneInpQueue(self)
        self.ports = [self.out_party_buyer, self.in_party_buyer, self.out_party_seller, self.in_party_seller]

        for p_i in self.ports:
            self.register_port(p_i)

        self.contracts_demon = cContractListDaemon()
        self.daemons = []

    def connect_inout_buyer(self, in_port, out_port):
        # Этот метод для тестирования. По-хорошему, должна быть гибкость,
        # куда коннектить in порт и out порт. Так что один порт сделать низя.
        self.out_party_buyer.connect_to_port(in_port)
        self.in_party_buyer.connect_to_port(out_port)

    def connect_inout_seller(self, in_port, out_port):
        # Этот метод для тестирования. По-хорошему, должна быть гибкость,
        # куда коннектить in порт и out порт. Так что один порт сделать низя.
        self.out_party_seller.connect_to_port(in_port)
        self.in_party_seller.connect_to_port(out_port)

    def my_generator(self):
        pass


class cNodeAgentTrader(cBaseBlueAgent):
    """
    1:1 input, 1:1 output
    И покупатель, и продавец (зависимо от настройки)
    """
    def __init__(self, name):
        super().__init__(name)

    def my_generator(self):
        # пока по минимуму демонов
        pass


class cContractListDaemon(simulengin.cConnToDEVS):
    """
    Отслеживает несколько контрактов и создает
    новые по необходимости
    """
    def __init__(self, name):
        super().__init__(name)
        self.price_list = {}
        self.requests = metatypes.mtQueue(self)
        self.active_contracts = [] #активные демоны

    def add_conditions(self, item, price):
        # Для товара назначим цену.
        self.price_list[item] = price

    def my_generator(self):
        pass

    def gen_get_request(self):
        while 1:
            next_req = yield self.requests.get()
            # стартуем нового демона


class cContractTradeDaemon(simulengin.cConnToDEVS):
    """
    Отвечает за исполнение конкретного контракта
    """
    def __init__(self, name):
        super().__init__(name)


class cStateExecutor(simulengin.cConnToDEVS):
    """
    Фактически переход из стейта в стейт - команда одной
    ноды другой. Команды должны выполняться универсально,
    поэтому можно поробовать в отдельном классе реализовать
    логику выполнения команды за ноду. Потом это можно
    подмешать к ноде (фабрикой, например).
    """

    def __init__(self, parent_node):
        self.parent_node = parent_node

    def do_task(self):
        pass



def new_task_request_get_item(item, price, qtty):
    # Так нода требует себе товар
    new_task = cTask()
    state_start = cTaskState("start")
    state_get_item = cTaskState("get_item")
    state_cancel = cTaskState("cancel")

def new_task_push_take_item(item, price, qtty):
    # Так нода насильно отдаёт товар
    # Ожидается в ответ на new_task_request_get_item
    new_task = cTask()
    state_start = cTaskState("start")
    state_get_item = cTaskState("get_item")
    state_cancel = cTaskState("cancel")


class cTask:
    """
    Что-то, что имеет стейты, и его можно переводить из стейта в стейт.
    При этом, каждый стейт имеет событие начала и конца работы над ним.
    Ноды умеют передвигать таск из стейта в стейт.

    При этом, в таске указываются ресурсы, необходимые для перехода
    в следующиие стейты. Так, нода может попробовать "подогнать"
    что ей нужно, чтобы сделать стейт. Ну или просто попытаться сделать
    и зафейлиться в случае нехватки.
    """
    def __init__(self):
        # Чтобы задать таск нужно задать текущий стейт.
        # Из него уже можно всё дерево вытащить.
        self.previous_state = None
        self.active_state = None
        self.expanded_states = [] # Пополняется по мере выполнения

    def set_state(self, start_state):
        # Все последующие переходы заданы в стейте
        self.active_state = start_state

    def peek_next_states(self):
        # Для выбора следующего стейта нода может получить
        # следующие стейты и переходы.
        for trans_i, state_i in self.active_state.peek_next_states():
            yield trans_i, state_i


class cTaskTransition:
    """
    Связь между двумя стейтами. Может содержать необходимые условия перехода.
    """
    def __init__(self, state0, state1):
        self.requerments = []
        self.state0 = state0
        self.state1 = state1

    def add_req(self, a_req):
        self.requerments += [a_req]

    def get_start(self):
        return self.state0

    def get_end(self):
        return self.state1

class cTaskState:
    """
    Стейт таска. Может содержать (и публиковать) ивенты о том, что со стейтом
    что-то случилось.
    """

    def __init__(self, name):
        self.transitions = []
        self.start_event = None
        self.done_event = None

    def connect(self, other, req_list):
        # from self to other
        next_transition = cTaskTransition(self, other)
        # what is needed for this transition
        for req_i in req_list:
            next_transition.add_req(req_i)
        # write it down
        self.transitions += [next_transition]

    def peek_next_states(self):
        for trans in self.transitions:
            yield (trans, trans.get_end())

    # get event
    def subscribe_start(self):
        if self.start_event is None:
            self.start_event = simulengin.simpy.Event()
        return self.start_event

    # get event
    def subscribe_done(self):
        if self.done_event is None:
            self.done_event = simulengin.simpy.Event()
        return self.done_event

class cRequerment:
    """
    Условие для перехода из стейта в стейт. Нужен универсальный механизм проверки,
    удовлетворяет ли нода этим условиям.
    """
    def __init__(self):
        pass

    def check_req(self, node_i):
        # Так можно проверить, есть ли у ноды что нужно
        raise NotImplementedError

class cItemRequerment(cRequerment):
    """
    Наличие товара
    """
    def __init__(self, item, qtty):
        super().__init__()
        self.item = item
        self.qtty = qtty

    def check_req(self, node_i):
        # Так можно проверить, есть ли у ноды товары
        # ! Одной проверки недостаточно. Для нормальной
        # асинхронной работы надо ещё зарезервировать.
        # Так что это не заменеяет обработку на стороне
        # ноды.
        qtty_avail = 0
        for wallet_i in node_i.iter_wallets():
            qtty_avail += wallet_i.check_qtty(self.item)
        if self.qtty <= qtty_avail:
            return True
        else:
            return False

















