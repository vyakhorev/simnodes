import operator


def get_operator_fn(op):
    return {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '%': operator.mod,
        '^': operator.xor,
        '=': operator.eq,
        '>': operator.gt,
        '<': operator.lt,
    }[op]


def do_expression(op1, operator, op2):
    if isinstance(op1, str):
        op1 = int(op1)
    if isinstance(op2, str):
        op2 = int(op2)
    return get_operator_fn(operator)(op1, op2)