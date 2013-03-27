'''
Created on May 24, 2012

@author: ray
'''
import time
import logging
import Queue
import traceback
from multiprocessing import Process, JoinableQueue, cpu_count

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

BLOCK_TIMEOUT = 0.01


#==============================================================================
# Producer Proxy
#==============================================================================
class ProducerProxy(Process):

    """ Producer Proxy

    Producer Proxy act as a broker for producer in Producer-Consumer Pattern.
    It deals with the process model for the real producer.
    """

    def __init__(self, queue, producer):
        Process.__init__(self)
        self._queue = queue
        self._producer = producer
        self.daemon = True

    def items(self):
        return self._producer.items()

    def run(self):
        for item in self.items():

            while True:
                try:
                    self._queue.put(item, timeout=BLOCK_TIMEOUT)
                except Queue.Full:
                    continue
                else:
                    break


#==============================================================================
# Consumer
#==============================================================================
class ConsumerProxy(Process):

    """ Consumer Proxy

    Consumer Proxy act as a broker for consumer in Producer-Consumer Pattern.
    It deals with the process model for the real consumer.
    """

    def __init__(self, queue, consumer):
        Process.__init__(self)
        self._queue = queue
        self._consumer = consumer
        self.daemon = True

    def consume(self, task):
        self._consumer.consume(task)

    def run(self):
        while True:
            try:
                task = self._queue.get(timeout=BLOCK_TIMEOUT)
            except Queue.Empty:
                continue

            try:
                self.consume(task)
            except Exception:
                traceback.print_exc()
            finally:
                self._queue.task_done()


#==============================================================================
# Master and Slaver
#==============================================================================
class Producer(object):

    """ Producer Interface """

    def items(self):
        """ Returns a iterable of task object """
        yield
        return


class Consumer(object):

    """ Consumer Interface """

    def consume(self, task):
        """ Deals with the task """
        raise NotImplementedError


#==============================================================================
# Monitor
#==============================================================================
class Mothership(object):

    """ Monitor of producer and consumers """

    def __init__(self, producer, consumers):
        self._queue = JoinableQueue()

        self._producer_proxy = ProducerProxy(self._queue, producer)
        self._consumer_pool = list(ConsumerProxy(self._queue, consumer) \
                                   for consumer in consumers)

    def start(self):
        """ Start working """
        logger.info('Starting Producers'.center(20, '='))
        self._producer_proxy.start()

        logger.info('Starting Consumers'.center(20, '='))
        for consumer in self._consumer_pool:
            consumer.start()

        self._producer_proxy.join()
        self._queue.join()

    def __enter__(self):
        return self

    def __exit__(self, types, value, tb):
        return


#==============================================================================
# Test
#==============================================================================
class TestTask(object):

    def __init__(self, num):
        self._num = num

    @property
    def num(self):
        return self._num


class TestMaster(Producer):

    def items(self):
        for i in range(100):
            yield TestTask(i)


class TestSlaver(Consumer):

    def __init__(self, tag):
        self._tag = tag

    def consume(self, task):
        logger.info('%s-%d' % (self._tag, task.num))
        time.sleep(0.1)


def main():

    master = TestMaster()
    slavers = [TestSlaver('test1'), TestSlaver('test2'), TestSlaver('test3')]

    with Mothership(master, slavers) as m:
        m.start()

if __name__ == "__main__":
    main()
