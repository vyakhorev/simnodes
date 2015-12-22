from collections import OrderedDict
import simpy
from random import randint

def tally():
    sent = 0
    while True:
        rec = yield sent
        rand = randint(0, 100)
        print('a rand : ', rand)
        sent = rec + rand
        print('a sent : ', sent)


def molly():
    sent = 0
    while True:
        rec = yield sent
        rand = randint(0, 99)
        print('b rand : ', rand)
        print('b rec : ', rec)
        sent = rec - rand
        print('b sent : ', sent)

def tally2():
    sent = 0
    while True:
        rec = yield sent
        sent += rec + 5
        print('a sent : ', sent)


def molly2():
    sent = 0
    while True:
        rec = yield sent
        sent -= rec - 5
        print('b sent : ', sent)

# Exporting for Gui

if __name__ == '__main__':

    a = tally2()
    b = molly2()

    next(a)
    next(b)

    signal = 0

    for i in range(100):
        signal = a.send(signal)
        print('signal from a : ', signal)
        signal = b.send(signal)
        print('signal from b : ', signal)


