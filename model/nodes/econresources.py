# Defines namespaces for materials \ goods \ machinery \ jobs ...

class cItemsNamespace:
    # very draft
    def __init__(self):
        # only 1 level allowed at the moment..
        self.item_tree = {}
    
    def add_item(self, new_item):
        # todo: deeper and better tree
        if new_item.parent_type is None:
            # 'parent' type - just ignore it
            return
        else:
            if new_item.parent_type in self.item_tree:
                self.item_tree[new_item.parent_type] += [new_item]
            else:
                self.item_tree[new_item.parent_type] = []
                self.item_tree[new_item.parent_type] += [new_item]
    
    def add_items(self, new_items_list):
        for item in new_items_list:
            self.add_item(item)
        
    
    def get_subitems(self, parent_item):
        if parent_item in self.item_tree:
            return self.item_tree[parent_item][:]
        else:
            return []
        
class cItem:
    # concrete or general type of items
    
    def __init__(self, name, parent_type = None):
        self.name = name
        self.parent_type = parent_type

    def __repr__(self):
        return str(self.name)

    def __eq__(x, y):
        return x.name == y.name

    def __hash__(self):
        return hash(self.name)

