#!/usr/bin/python
#################################################################
# phedex_getMissingBlocks.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id$
#################################################################


from sys import argv, exit
from os import popen

from optparse import OptionParser

usage = """This program outputs the blocks with missing files taking as input the output of
PHEDEX/Utilities/BlockConsistencyCheck -verbose

USAGE: %prog list

"""
parser = OptionParser(usage=usage)

if len(argv)<2:
    print usage
    exit(1)
    
INPUT = argv[1]

myFile = open(INPUT)

lines = myFile.readlines()
start = False
line=0
for l in lines:
    l = l.strip(' ').strip('\n')
    if l=='': continue
    
    if l=='==> summarising Blocks':
        start = True
    if start and l=='#------------------------------------------------------------------':
        start = False

    if start:

        if l[0]=="/":
            if lines[line+1].find('Missing')!=-1:
                print l
            
    line += 1        
