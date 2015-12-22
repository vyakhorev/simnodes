import simpy
from random import choice
import textwrap


class Eater:
    def __init__(self, env1, store):
        self.name = 'Eater'
        self.env = env1
        self.store = store
        self.env.process(self.eat())

    def eat(self):
        while True:
            print(self)
            got = yield self.store.get()
            print('{} got {}'.format(self.name, got))
            if got[1] in ['apples', 'oranges']:
                print('nyam nyam')
            else:
                print('dont eat it')
                yield self.store.put(got)

            # print(self.store.items)
            yield env.timeout(1)


class Engineer:
    def __init__(self, env1, store):
        self.name = 'Engineer'
        self.env = env1
        self.store = store
        self.env.process(self.build())

    def build(self):
        while True:
            print(self)
            got = yield self.store.get()
            print('{} got {}'.format(self.name, got))

            yield env.timeout(1)


def debug(env1, store):
    while True:
        yield env1.timeout(3)
        print(env1.now, store.items)


if __name__ == '__main__':
    env = simpy.Environment()
    res1 = simpy.Store(env, capacity=60)
    prods = ['apples', 'oranges', 'bricks']
    for i in range(60):
        res1.put([i, choice(prods)])
    env.process(debug(env, res1))

    a = (textwrap.wrap(str(res1.items), width=100))
    for i in a:
        print(i)

    eater1 = Eater(env, res1)
    builder1 = Engineer(env, res1)

    env.run(60)



