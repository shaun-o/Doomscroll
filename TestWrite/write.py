#!/usr/bin/env python

import redis
import sys

if __name__ == "__main__":

    r = redis.Redis(host='localhost', port=6379, db=0)

    arg1 = sys.argv[1]
    arg2 = sys.argv[2]

    if arg1 == 'add':
        r.set(arg2, sys.argv[3])
        r.expire(arg2, 60)
    else:
        r.delete(arg2)