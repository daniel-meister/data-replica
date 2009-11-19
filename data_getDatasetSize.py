#!/bin/env python
#################################################################
# data_getDatasetSize.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id$
#################################################################

from os import popen
from sys import argv

usage = """This scripts takes as input a list of datasets and outputs their size.
It needs dbssql in the path.

USAGE: """+argv[0]+""" file.list"""

if len(argv)<2:
    print usage
    exit(1)

total = 0
sizes = popen("cat "+argv[1])
for i in sizes:
    i = i.strip("\n")
    command = """dbssql --input=\'find dataset,sum(block.size) where dataset="""+i.strip('\n')+"""\' | grep \'/\' | awk {\'print $2\'}"""
    pipe = popen(command)
    size = pipe.readlines()[0].strip('\n')
    size = float(size) /(1024*1024*1024) #GB
    total += size
    print "%s %.1f GB" %(i,size)

print "TOTAL: %.1f GB" %total

        
