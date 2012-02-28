#/bin/env python

from os import popen
from sys import argv,exit
from optparse import OptionParser
from simpleSrm_utils import *


### options
usage = "A simple, recursive wrapper for srmls\nUsage: "+argv[0]+" [options] SRM_DIRECTORY"
parser = OptionParser(usage = usage, version="%prog 1.0")
parser.add_option("-r",action="store", dest="MAX_REC",default="0",
                  help="Maximum recursion level (default:0)")
parser.add_option("--nocolor",action="store_true", dest="NOC",default=False,
                  help="No color output")


(options, args) = parser.parse_args()
if len(args)!=1:
    parser.print_help()
    exit(1)
DIR=args[0]
max_recursion = int(options.MAX_REC)

### polishing input directory
SE = DIR.split("/")[0]+"/"+DIR.split("/")[1]+"/"+DIR.split("/")[2]
NEW_DIR = DIR[ len(SE):]+"/"
NEW_DIR = polishDirName(NEW_DIR)

### initialization
DIR_LIST = []
#FILE_LIST=[]
#FILE_SIZE={}
LIST = {}

### recursion level is retrieved counting the "/" (stupid?)
recursion = len(NEW_DIR.split("/"))
getRecursiveList(SE,NEW_DIR,DIR_LIST,LIST,recursion,max_recursion)

DIR_LIST.sort()
#FILE_LIST.sort()
dir_counter=0
file_counter=0
dir_size=0

### the printing loop
for d in DIR_LIST:
    printDir(d, options.NOC)
    dir_counter+=1
    for f in LIST[d]:
        if d==f[0]: continue
        file_counter += 1
        dir_size += f[1]
        print "\t"+str(f[1])+"\t"+f[0]

printMessage("Directory size (only listed files): "+printHumReadSize(dir_size), options.NOC )
printMessage("Total Directories: "+str(dir_counter), options.NOC )
printMessage("Total Files: "+str(file_counter), options.NOC )

#print red+"Directory size (only listed files): "+printHumReadSize(dir_size)
#print red+"Total Directories: "+str(dir_counter)+NC
#print red+"Total Files: "+str(file_counter)+NC
