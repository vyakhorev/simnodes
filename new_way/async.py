import asyncio
import functools

@asyncio.coroutine
def consumer(n, q):
    print('consumer {}: starting'.format(n))
    while True:
        print('consumer {}: waiting for item'.format(n))
        item = yield from q.get()
        print('consumer {}: has item {}'.format(n, item))
        if item is None:
            # None is the signal to stop.
            q.task_done()
            break
        else:
            yield from asyncio.sleep(0.01 * item)
            q.task_done()
    print('consumer {}: ending'.format(n))

@asyncio.coroutine
def producer(q, num_workers):
    print('producer: starting')
    # Add some numbers to the queue to simulate jobs
    for i in range(num_workers * 3):
        yield from q.put(i)
        print('producer: added task {} to the queue'.format(i))
    # Add None entries in the queue
    # to signal the consumers to exit
    print('producer: adding stop signals to the queue')
    for i in range(num_workers):
        yield from q.put(None)
    print('producer: waiting for queue to empty')
    yield from q.join()
    print('producer: ending')


event_loop = asyncio.get_event_loop()
try:
    num_consumers = 2

    # Create the queue with a fixed size so the producer
    # will block until the consumers pull some items out.
    q = asyncio.Queue(maxsize=num_consumers)

    # Scheduled the consumer tasks.
    consumers = [
        event_loop.create_task(consumer(i, q))
        for i in range(num_consumers)
    ]

    # Schedule the producer task.
    prod = event_loop.create_task(producer(q, num_consumers))

    # Wait for all of the coroutines to finish.
    result = event_loop.run_until_complete(
        asyncio.wait(consumers + [prod])
    )
finally:
    event_loop.close()