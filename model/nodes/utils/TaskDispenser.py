__author__ = 'ILUA'
from model.nodes.classes.Task import cTask, cDelivery, make_task_from_str


class cTaskDispenser:

    def __init__(self):
        self.glossary = {'t_DELIVER': cDelivery,
                         't_PUSH': cTask,
                         't_REQUEST': cTask,
                         't_ALERT': cTask
                         }

    def items(self):
        return self.glossary