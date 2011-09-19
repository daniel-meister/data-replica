#!/usr/bin/python
#################################################################
# grid_queryBDII.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: grid_queryBDII.py,v 1.4 2009/12/03 23:23:44 leo Exp $
#################################################################


from sys import argv, exit
from os import popen
from optparse import OptionParser


usage = """This script is just a simple wrapper for some useful BDII queries,
not included in lcginfo and too complex to be remembered (thx, GLUE!).

usage: %prog info-type 

info-type can be:

[SE]
    - se-technology: it outputs a list of SE and their technologies. 
    - ce-status: outputs CE status for a site

         

"""

parser = OptionParser(usage = usage, version="%prog 0.1")
parser.add_option("--select",action="store", dest="select",default="",
help="selects a value for an info-type")
parser.add_option("--site",action="store", dest="site",default="", help="selects a site")


(options, args) = parser.parse_args()

if len(args)<1:
    print usage
    exit(1)

INFO_TYPE = args[0]

command = """ldapsearch -x -h lcg-bdii.cern.ch -p 2170 -b """

if INFO_TYPE == "se-technology":
    if options.select!="":
        print options.select
    else:
        command += """ o=grid \'(&(objectClass=GlueSE))\' | grep -E \'dn|GlueSEImplementationName|GlueSEImplementationVersion\' """ 

elif INFO_TYPE=="ce-status":
    if options.site == "":
        print "PLEASE SELECT A SITE"
        exit(1)
    else:
        command += """ mds-vo-name="""+options.site+""",mds-vo-name=local,o=grid  'objectClass=GlueCE' GlueCEStateStatus GlueCEStateWaitingJobs GlueCEStateRunningJobs GlueCEStateTotalJobs GlueCEStateFreeJobSlots GlueCEStateWorstResponseTime GlueCEStateEstimatedResponseTime | grep -A 9 cms"""
else:
    print "not available"

#print command

pipe = popen(command)
output = ""
site = {}

for l in pipe.readlines():
    l = l.strip('\n')
    if INFO_TYPE == "se-technology":
        test = l.find("GlueSEUniqueID=")
        if test!=-1:
            output_temp = l[test+len("GlueSEUniqueID="):].replace('Mds-Vo-name=','').split(',')
            siteName = output_temp[1]+" ("+output_temp[0]+")"
            site[siteName]={}
        else:
            tech = l
            tech = tech.replace('GlueSEImplementationName:',' ')
            tech = tech.replace('GlueSEImplementationVersion:',' ')
            #tech.lower()
            
            if l.find("GlueSEImplementationName")!=-1: site[siteName]["tech"] = tech
            elif l.find("GlueSEImplementationVersion:")!=-1: site[siteName]["version"] = tech

    else:
        print l

for s in site.keys():
    if site[s]!="":
        line = s
        for l in site[s].values():
            line += l+" "  
        print line    


