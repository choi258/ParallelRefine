#!/usr/bin/python
#/usr/lib/python2.6/site-packages/pip/_vendor/requests/packages/

import sys
import subprocess
import os
from google.refine import refine

reload(sys)
sys.setdefaultencoding('utf-8')

DATA = os.path.join(os.path.dirname(__file__), 'data', 'test_6000_21.csv')
HEADER = os.path.join(os.path.dirname(__file__), 'data', 'header.csv')
PROCESSED = os.path.join(os.path.dirname(__file__), 'data', 'input.csv')
SAMPLED = os.path.join(os.path.dirname(__file__), 'data', 'sampled.csv')

_format = 'text/line-based/*sv'
_options = {}

# Read the first line, save it in a header file
with open(DATA, 'rb') as inp:
    header = inp.readline()
    with open(HEADER, 'wb') as head:
        head.write(header)

# Count total number of lines in the input file
# Use shell for this
no_of_lines, _ = subprocess.Popen(['wc', '-l', DATA], \
        stdout=subprocess.PIPE).communicate()
no_of_lines = int(no_of_lines.split()[0])

# Format the data into new csv so that hadoop processing is easier
first, count, record = True, 0, ''
with open(DATA, 'rb') as inp:
    with open(PROCESSED, 'wb') as out:
        for line in inp:
            if first:
                first = False
                continue
            if count == 50:
                out.write(record.rstrip('#####')+'\n')
                count, record = 0, ''
            record += line.strip() + '#####'
            count += 1
        if record:
            out.write(record.rstrip('#####')+'\n')

# Now create the sample project using sampled data
sampling_ratio = 0.1
no_of_sampled_lines = int(sampling_ratio * no_of_lines)
subprocess.Popen(['cp', HEADER, SAMPLED]).communicate()
with open(SAMPLED, 'ab') as out:
    subprocess.Popen(['shuf', '-n {0}'.format(no_of_sampled_lines), \
        DATA], stdout=out).communicate()

server = refine.RefineServer()
refine = refine.Refine(server)
project = refine.new_project(project_file=SAMPLED, \
                             project_format=_format,\
                             project_options=_options)
print "Done"
print "Open: " +  project.project_url()
