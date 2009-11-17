#!/bin/env python

from os import popen
from sys import argv, exit
from optparse import OptionParser

usage = """This program divided a list of files into categories. If a second list
of files is given, this is subtracted from the first

USAGE: %prog fileList [secondFileList]

"""
parser = OptionParser(usage=usage)

if len(argv)< 2:
    print "Usage: "+argv[0]+" lostFilesList [phedexLostFileList]"
    exit(1)

FILELIST = argv[1]
if len(argv)==3:
    FILELIST2 = argv[2]
else:
    FILELIST2=""
    
LOGNAME = FILELIST[:FILELIST.find(".")]

OUTFILE = {}
OUTFILE['USER'] = LOGNAME+"_User.lst"
OUTFILE['UNMERGED'] = LOGNAME+"_Unmerged.lst"
OUTFILE['LT07'] = LOGNAME+"_LT07.lst"
OUTFILE['OTHER'] = LOGNAME+"_Other.lst"

SEARCH={}
SEARCH['USER'] = "/user"
SEARCH['UNMERGED'] = "/unmerged"
SEARCH['LT07'] = "/phedex_monarctest/"


FILES = {}
for x in OUTFILE.keys():
    FILES[x] = open(OUTFILE[x],"w")

if FILELIST2!='':
    command = "cat "+FILELIST+" | sort > "+FILELIST+"-sorted.lst "
    command += "&& cat "+FILELIST2+" | sort > "+FILELIST2+"-sorted.lst "
    command += "&& comm -23 "+FILELIST+"-sorted.lst "+FILELIST2+"-sorted.lst > "+LOGNAME+"_common.lst"
    popen(command)

mylist = popen("cat "+LOGNAME+"-common.lst") 

for f in mylist:
    found = False
    for x in OUTFILE.keys():
        if x=="OTHER": continue
        if f.find( SEARCH[x] ) != -1:
            FILES[x].write(f)
            found=True
    if not found:
        FILES['OTHER'].write(f)
                
for x in OUTFILE.keys():
    FILES[x].close()

popen("rm "+FILELIST+"-sorted.lst "+FILELIST2+"-sorted.lst ")
