#!/usr/bin/python

from sys import argv, exit
from os import popen
from optparse import OptionParser


usage = """This script is just a simple wrapper for some useful BDII queries,
not included in lcginfo and too complex to be remembered (thx, GLUE!).

usage: %prog info-type [--select=value]

info-type can be:

[SE]
    - se-technology: it outputs a list of SE and their technologies. If --select=<technology> is given
    only SEs with that technology are listed. E.g.:

    %prog se-technology

    %prog se-technology --select=bestman
         

"""

parser = OptionParser(usage = usage, version="%prog 0.1")
parser.add_option("--select",action="store", dest="select",default="",
help="selects a value for an info-type")

(options, args) = parser.parse_args()

if len(args)<1:
    print usage
    exit(1)

INFO_TYPE = args[0]

if INFO_TYPE == "se-technology":
    if options.select!="":
        print options.select
    else:
        command = """ldapsearch -x -h lcg-bdii.cern.ch:2170 -p 2170 -b o=grid \'(&(objectClass=GlueSE))\' | grep -E \'dn|GlueSEImplementationName\' """ 

else:
    print "not available"


pipe = popen(command)
output = ""
for l in pipe.readlines():
    l = l.strip('\n')
    if INFO_TYPE == "se-technology":
        if options.select!="":
            print options.select
        else:
            test = l.find("GlueSEUniqueID=")
            if test!=-1:
                output_temp = l[test+len("GlueSEUniqueID="):].replace('Mds-Vo-name=','').split(',')
                output += output_temp[1]+" ("+output_temp[0]+")"
            else:
                output += l.replace('GlueSEImplementationName:',' ')
                output +='\n'
                

print output
