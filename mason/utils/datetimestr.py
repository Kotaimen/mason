'''
Created on Sep 9, 2012

@author: Kotaimen
'''
import time

WEEKDAY_NAME = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTH_NAME = [None,
              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def date_time_string(timestamp=None):
    """ Convert a filesystem timestamp to http response time, taken
    from BaseHTTPRequestHandler.date_time_string() """

    if timestamp is None:
        timestamp = time.time()
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
    s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
            WEEKDAY_NAME[wd],
            day, MONTH_NAME[month], year,
            hh, mm, ss)
    return s
