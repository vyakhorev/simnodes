
import model.nodes.meta
import model.nodes.metatypes as metatypes
import model.nodes.simulengin.simulengin as simulengin
import simpy


class cSimNode(simulengin.cConnToDEVS, model.nodes.meta.MetaStruct):
    """
        This class covers simulation behaviour of every Node.
    """
    # node_id = metatypes.Integer()
    # FIXME reimplement naming system
    name = metatypes.String('cSimNode')

    # TODO ports = metatypes.PortDict()
    # or each port by it's name

    def __init__(self, name):
        super().__init__()
        # Do I have to state it here?...
        self.node_id = self.nodeid
        self.name = name
        self.ports = {}

    def __repr__(self):
        return str(self.name) + " (node id " + str(self.node_id) + ")"

    def register_port(self, new_port):
        # print('registering {} {}'.format(new_port.port_id, self.ports))
        if new_port.port_id in self.ports:
            pass
            # raise KeyError("already in the list!")

        self.ports[new_port.port_id] = new_port
        setattr(self, str(new_port.port_id), new_port)

    def get_connections(self):
        # todo make compr
        conn_list = []
        for port_i in self.ports.values():
            conn_list += port_i.get_conections()
        return conn_list

    def my_generator(self):
        raise NotImplemented()

class cSimPort(simulengin.cConnToDEVS, model.nodes.meta.MetaStruct):
    # port_id = metatypes.Integer()
    name = metatypes.String('cSimPort')
    # TODO parent_node = metatypes.SimNode()
    # TODO connected_to_port = metatypes.SimPort()

    def __init__(self, parent_node):
        super().__init__()
        # self._name = name
        self.port_id = self.nodeid
        self.parent_node = parent_node
        self.connected_ports = {}
        self.simple_repr = True

    def __repr__(self):
        rpr = "port " + str(self.nodeid) + " @ " + str(self.parent_node)
        if self.simple_repr == True:
            return rpr
        if self.is_connected:
            # print(self.connected_ports)
            rpr += ' connected to '
            for k, v in self.connected_ports.items():
                rpr += ' ' + str(k)
        else:
            print('Not connected yet')
        return rpr

    def connect_to_port(self, another_port):
        if another_port.port_id in self.connected_ports:
            print('Failed to connect !! ')
            # Already connected
            return
        print('connecting {} with {} port_id to {} with {} port_id '.format(self, self.port_id, another_port,
                                                                            another_port.port_id))
        self.connected_ports[another_port.port_id] = another_port
        another_port.connected_ports[self.port_id] = self

        # print(self.connected_ports)

    def is_connected(self):
        if len(self.connected_ports) == 0:
            return False
        return True

    def disconnect_port(self, another_port):
        if another_port.nodeid in self.connected_ports:
            self.connected_ports.pop(another_port.nodeid)
            another_port.connected_ports.pop(self.nodeid)

    def get_connections(self):
        # todo make compr
        conn_list = []
        for port_i in self.connected_ports.values():
            conn_list += [[port_i, port_i.parent_node]]
        return conn_list

    def get_connections_iter(self):
        # generator!!
        return ([port_i, port_i.parent_node] for port_i in self.connected_ports.values())


    def my_generator(self):
        raise NotImplemented()

class cSimObserver(simulengin.cAbstObserver):
    def __init__(self, name, obj_i, attr_name, period):
        super().__init__(name, period)
        self.sim_obj = obj_i
        self.obs_attr = attr_name
        if hasattr(obj_i, 'name'):
            self.owner_name = obj_i.name
        else:
            self.owner_name = str(obj_i.__class__)
        self.ts_name = self.obs_attr + "@" + self.owner_name

    def observe_data(self):

        if hasattr(self.sim_obj, self.obs_attr):
            ts_value = getattr(self.sim_obj, self.obs_attr).level
        else:
            ts_value = getattr(self.sim_obj, self.obs_attr)

        ts_value = getattr(self.sim_obj, self.obs_attr).level #todo type checking

        self.record_data(self.ts_name, ts_value)
