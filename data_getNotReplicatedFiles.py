#!/bin/env python

from sys import argv,exit
from os import popen
from optparse import OptionParser

usage = """This program finds the files with no replicas around the world, and outputs one file with these files
and another one with list of files with replicas. It requires dbssql in the PATH

USAGE: %prog  listOfLfn

"""
parser = OptionParser(usage=usage)

if len(argv)<2:
    print usage
    exit(1)

MY_SITE="T2_CH_CSCS"

INPUT = argv[1]
OUTFILE_U = INPUT[:INPUT.find('.')]+'_noReplicas.lst'
OUTFILE_R = INPUT[:INPUT.find('.')]+'_withReplicas.lst'

f_r = open(OUTFILE_R, 'w')
f_ur = open(OUTFILE_U, 'w')

list = open(INPUT)

for f in list:
    f = f.strip('\n')
    command = """dbssql --input='find file,count(site) where file="""+f+""" and site!="""+MY_SITE+"""' | grep -v -e###"""
    
    nReplicas = 0
    pipe = popen(command)
    for l in pipe.readlines():
        l=l.strip('\n').strip(' ')
        if l!='':
            l = l.split(" ")[1]
            nReplicas = float(l)

    if nReplicas==0:
        f_ur.write(f+'\n')
    else:
        f_r.write(f+'\n')
   
