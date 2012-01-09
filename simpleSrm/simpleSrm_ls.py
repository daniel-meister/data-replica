#/bin/env python

from os import popen
from sys import argv

DIR=argv[1]


def printHumReadSize( size):
    LAB = ("","k","M","G","T")
    newSize = size
    for i in LAB:
        if newSize > 1024.:
            newSize /= 1024.
        else:
            myS = "%.2f" % (newSize)
            return myS+i
            

### colors
red='\033[0;31m'
RED='\033[1;31m'
blue='\033[0;34m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color

out = popen("srmls "+DIR)
DIR_LIST = []
FILE_LIST=[]
FILE_SIZE={}
for i in out:
    i = i.strip("\n").strip(" ")
    if len(i)==0: continue
    size = float(i.split(" ")[0])
    name = i.split(" ")[1]
    if name[-1]=="/": DIR_LIST.append(name)
    else:
        FILE_LIST.append(name)
        FILE_SIZE[name] = size

DIR_LIST.sort()
FILE_LIST.sort()

dir_counter=0
for d in DIR_LIST:
    print BLUE+d+NC
    dir_counter+=1
    
file_counter=0
dir_size=0
for f in FILE_LIST:
    print FILE_SIZE[f],f
    dir_size+=FILE_SIZE[f]
    file_counter+=1
    

print red+"Directory size (only files, not recursive): "+printHumReadSize(dir_size)
print red+"Total Directories: "+str(dir_counter)+NC
print red+"Total Files: "+str(file_counter)+NC
