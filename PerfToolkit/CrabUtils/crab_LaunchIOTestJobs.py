#!/bin/env python

from os import popen
from sys import argv, exit

if len(argv)<6:
    print "Usage: "+argv[0]+" SITE VERSION CFG EVENTS_JOB DATASET"
    exit(1)

MYSITE=argv[1]
MYVERSION=argv[2]
MYCFG=argv[3][:argv[3].find('.py')]
MYDATE=popen("date +'%Y%m%d%k%M'").readlines()[0].strip('\n').replace(" ","0")
EVENTS_JOB=argv[4]
#LABEL=argv[5]
DATASET=argv[5]
DATASET_REDUCED=argv[5].replace("/","+").strip("+").replace("-",".")
print DATASET_REDUCED


command = """cat crab.template"""
command += """| sed 's:MYSITE:"""+MYSITE+""":g'"""
command += """| sed 's:MYDIR:'`pwd`':g'"""
command += """| sed 's:MYVERSION:"""+MYVERSION+""":g'"""
command += """| sed 's:MYCFG:"""+MYCFG+""":g'"""
command += """| sed 's:MYDATE:"""+MYDATE+""":g'"""
command += """| sed 's:EVENTS_JOB:"""+EVENTS_JOB+""":g'"""
#command += """| sed 's:DATASET:"""+DATASET+""":g'"""
command += """| sed 's:DATASET_REDUCED:"""+DATASET_REDUCED+""":g'"""
command += """| sed 's:DATASET:"""+DATASET+""":g'"""

command += """> crab.cfg"""

popen(command)
pipe=popen("crab -create -submit 1-20")
for l in pipe.readlines():
    print l.strip('\n')

#popen("rm crab.cfg")        
