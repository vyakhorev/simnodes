###############
# Commitments are a special kind of resources that help
# to govern async. run of different parties generators.
# IDEA: there always should be a balance inside one commitment
###############

class cCommitment(simulengin.cConnToDEVS):
    comm_type = "abstract"

    # side = ["take", "give", "neutral"]
    def __init__(self, parent=None, side="give"):
        super().__init__()
        self.actor = None
        # We should do a pretty complicated commitment structure (BPMN-like)
        self.child_commitments = [] #any commitment is a tree of elementary commitments
        self.parent_commitment = parent
        self.side = side
        # Exchange network settings
        self.visited_nodes = []

    def add_visitor(self, new_visitor):
        self.visited_nodes += [new_visitor.node_id]

    def switch_side_to_give(self):
        # Passive operation
        self.side = "give"

    def switch_side_to_take(self):
        # Active operation
        self.side = "take"

    def switch_side_to_neutral(self):
        # Active-passive operation
        self.side = "neutral"

    def set_actor(self, some_node):
        self.actor = some_node

    def set_commitment_params(self, *args, **kwargs):
        raise NotImplementedError()
        
###############
# New experiment with commitments
# Now they should hold some logical
# statements and present 2 sides
# of the deal
###############

class cOffer(simulengin.cConnToDEVS):
    # offer/expectation to do a commitment
    def __init__(self):
        self.clauses = []
        
    def add_clause(self, clause):
        self.
    
class cClause:
    def __init__(self, var_name):
        self.var_name = var_name
        self.