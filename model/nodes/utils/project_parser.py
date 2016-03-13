import json
from pprint import pprint

from model.nodes.classes.Node_func_v2 import node_types, cAgentNode, cHubNode, cNodeBase, cFuncNode, node_types_dict
from model.model import cNodeFieldModel
from model.nodes.classes.Task import cTask, cDelivery

# string = 'G:/Cable/Git/Simnodes/simnodes/new_way/proj_file.json'
string = 'G:/Cable/Git/Simnodes/simnodes/new_way/proj_file_2_agents.json'


Bool_dict = {'true': True,
             'True': True,
             'false': False,
             'False': False
             }

def parse_json(filepath):
    with open(string) as data_file:
        data = json.load(data_file)
    return data


class CodeGenerator:
    def __init__(self, data):
        self.data_dict = data
        self.model = None
        self.nodes_alias_dict = {}

    def set_model(self, model):
        self.model = model

    def make_objects(self):
        print(node_types_dict)
        nodes = []
        for nodetype, vals in self.data_dict.items():
            # JSON doesn't let you have identical field names,
            # this is workaround to cut index after nodetype : AgentType1 -> AgentType etc.
            nodetype = ''.join(char for char in nodetype if not char.isdigit())

            # we know such type ?
            if nodetype in {'AgentType', 'HubType', 'FuncType'}:
                # check node types and create objects
                for n_type_i in node_types:
                    if nodetype == str(n_type_i):
                        print('Cool {} == {}'.format(nodetype, n_type_i))
                        # create new node
                        # NODE BIRTH
                        node = node_types_dict[nodetype](name='None')
                        nodes += [node]
                        # looping for attributes
                        for attr_i, val_i in vals.items():
                            print(attr_i, val_i)
                            if attr_i == 'tasks':
                                # unpacking tasks
                                tasks_list = []
                                for task_class_name_i, attrs_dict_i in val_i.items():
                                    task_class_name_i = \
                                        ''.join(char for char in task_class_name_i if not char.isdigit())
                                    # Looking for task type
                                    if task_class_name_i == 'cDelivery':
                                        new_task = cDelivery(name='None')
                                        # loop for task attributes
                                        for task_attr_name, task_attr_val in attrs_dict_i.items():
                                            if task_attr_val in ['true', 'True', 'false', 'False']:
                                                task_attr_val = Bool_dict[task_attr_val]
                                            setattr(new_task, task_attr_name, task_attr_val)

                                    if task_class_name_i == 'cTask':
                                        new_task = cTask(name='None')
                                        # loop for task attributes
                                        for task_attr_name, task_attr_val in attrs_dict_i.items():
                                            if task_attr_val in ['true', 'True', 'false', 'False']:
                                                task_attr_val = Bool_dict[task_attr_val]
                                            setattr(new_task, task_attr_name, task_attr_val)

                                    # filling tasks list
                                    tasks_list += [new_task]

                                # setting tasks to current node
                                node.set_tasks(tasks_list)
                            else:
                                setattr(node, attr_i, val_i)

                        # filling nodes_alias_dict
                        self.nodes_alias_dict[node.id] = node
                    else:
                        print('Fail {} <> {}'.format(nodetype, n_type_i))
                    print('=========================================')

            else:
                print('Unknown node type')

        return nodes

    def connect_between(self, nodes):
        for nd_i in nodes:
            if isinstance(nd_i, cAgentNode):
                for node_neigh in nd_i.buddies:
                    nd_i.connect_buddies([self.nodes_alias_dict[node_neigh]])
                    nd_i.parent = self.nodes_alias_dict[node_neigh]
            elif isinstance(nd_i, cHubNode):
                for node_neigh in nd_i.inp_nodes:
                    nd_i.connect_nodes(inp_nodes=[self.nodes_alias_dict[node_neigh]], out_nodes=[])
                    nd_i.parent = self.nodes_alias_dict[node_neigh]
                for node_neigh in nd_i.out_nodes:
                    nd_i.connect_nodes(inp_nodes=[], out_nodes=[self.nodes_alias_dict[node_neigh]])
                    nd_i.parent = self.nodes_alias_dict[node_neigh]
            elif isinstance(nd_i, cFuncNode):
                for node_neigh in nd_i.buddies:
                    nd_i.connect_nodes(inp_node=self.nodes_alias_dict[node_neigh], out_node=None)
                    nd_i.parent = self.nodes_alias_dict[node_neigh]
            else:
                print('WRONG')

    def setup_conditions(self, nodes):
        for nd_i in nodes:
            if isinstance(nd_i, cHubNode):
                temp_dict = {}
                print('im hub Node!')
                print(nd_i.conditions)
                for nodeid_alias, expression in nd_i.conditions.items():
                    temp_dict[self.nodes_alias_dict[nodeid_alias]] = expression

                nd_i.condition(temp_dict)

    def color_maping(self, nodes):
        for nd_i in nodes:
            if isinstance(nd_i, cHubNode):
                nd_i.color = 'Green'
            elif isinstance(nd_i, cAgentNode):
                nd_i.color = 'Blue'
            elif isinstance(nd_i, cFuncNode):
                nd_i.color = 'Orange'
        """
        # TODO refactor this wrong function
        for nd_i in nodes:
            for node_neigh in nd_i.buddies:
                # TODO make one abst method ... this ugly
                print(node_neigh)
                if isinstance(nd_i, cAgentNode):
                    # searching for buddy by node id
                    for nd in nodes:
                        if nd.nodeid == node_neigh:
                            print('HELL YES')
                            nd_i.connect_buddies([nd])
                            nd_i.parent = nd


                elif isinstance(nd_i, cHubNode):
                    # FIXME inputs - outputs
                    for nd in nodes:
                        if nd.nodeid == node_neigh:
                            print('HELL YES')
                            nd_i.connect_nodes(inp_nodes=[nd], out_nodes=[])
                            nd_i.parent = nd
                else:
                    print('WRONG')
        """


if __name__ == '__main__':
    with open(string) as data_file:
        data = json.load(data_file)
    pprint(data)

    cg = CodeGenerator(data)
    the_model = cNodeFieldModel()
    # the_model.addNodes()
    cg.set_model(the_model)
    objects = cg.make_objects()
    print('objects', objects)
    print('cg.nodes_alias_dict', cg.nodes_alias_dict)
    cg.connect_between(objects)
    cg.setup_conditions(objects)
    cg.color_maping(objects)
    [print((nd.name, nd.connected_buddies)) for nd in objects]
    print(' -------- ')
    [pprint(vars(nd)) for nd in objects]



