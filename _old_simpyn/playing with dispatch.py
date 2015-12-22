import functools


class SnareDrum(object):
    pass


class Cymbal(object):
    pass


class Stick(object):
    pass


class Brushes(object):
    pass


@functools.singledispatch
def play(instrument, accessory):
    raise NotImplementedError("Cannot play these")


@play.register(SnareDrum)
def _(instrument, accessory):
    if isinstance(accessory, Stick):
        return "POC!"
    if isinstance(accessory, Brushes):
        return "SHHHH!"
    raise NotImplementedError("Cannot play these")

if __name__ == '__main__':
    print(play(SnareDrum(), Stick()))
    print(play(SnareDrum(), Brushes()))
    print(play(Cymbal(), Stick()))
    # play(Cymbal(), Brushes())