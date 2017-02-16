#!/usr/bin/env python

from operator import itemgetter
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

current_word = None
current_count = 0
word = None

# input comes from STDIN
for line in sys.stdin:
    print "".join(line)
