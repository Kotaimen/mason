'''
Created on May 7, 2012

@author: Kotaimen
'''
import time
import sys


class Timer(object):

    """ A tic-tac clock

    Usage::

        with Timer('time taken: %(time)s') as timer:
            ... do something ...

    """

    def __init__(self,
                message='Time taken: %(time)s',
                 writer=sys.stderr.write,
                 newline=True):
        self._message = message
        self._writer = writer
        self._tic = 0.
        self._newline = newline
        # On win32, time.clock() has higher resolution
        if sys.platform == 'win32':
            self.timer = time.clock
        else:
            self.timer = time.time

    def tic(self):
        self._tic = self.timer()

    def tac(self):
        self._tac = self.timer()

    def get_timestr(self):
        diff = self._tac - self._tic
        if diff > 3600:
            return '%dh%.2fm' % (diff // 3600, diff % 3600 / 60.)
        if diff > 60:
            return '%.2fm' % (diff / 60.)
        elif diff > 0.1:
            return '%.4fs' % diff
        else:
            return '%.2fms' % (diff * 1000.)

    def get_message(self):
        return self._message % {'time':self.get_timestr()}

    def get_time(self):
        """ Get elapsed time in seconds """
        return self._tac - self._tic

    def __enter__(self):
        self.tic()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.tac()
        self._writer(self.get_message())
        if self._newline:
            self._writer('\n')

if __name__ == '__main__':
    with Timer('Slept for %(time)s') as timer:
        time.sleep(0.001)
    with Timer('Slept for %(time)s') as timer:
        time.sleep(0.01)
    with Timer('Slept for %(time)s') as timer:
        time.sleep(0.1)
