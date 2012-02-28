from os import popen
import subprocess
from sys import argv

### colors
red='\033[0;31m'
RED='\033[1;31m'
blue='\033[0;34m'
BLUE='\033[1;34m'
NC='\033[0m' # No Color


### conversion to MB/GB/etc
def printHumReadSize( size):
    LAB = ("","k","M","G","T")
    newSize = size
    for i in LAB:
        if newSize > 1024.:
            newSize /= 1024.
        else:
            myS = "%.2f" % (newSize)
            return myS+i

### stupid check if this is a dir
def isDir(name):
    if name[-1]=="/":        return True
    else : return False

### printing utilities
def printDir(d, NOC):
    if NOC:
        print d
    else:
        print BLUE+d+NC

def printFile(f):
    print f

def printMessage(d, NOC):
    if NOC:        print d
    else:        print RED+d+NC
                            

### clean dir name from \n and extra /'s
def polishDirName(name):
    while name.find("//")!=-1:
        name = name.replace("//","/")
    name = name.strip("\n")
    return name

### polish and format srmls output
def formatSrmLsOutput(name):
    name = name.strip("\n").strip(" ")
    size = float(name.split(" ")[0])
    dir = name.split(" ")[1]
    dir = polishDirName(dir)
    return dir, size

### get a list, with a certain recursion
### SE: the SE basename: srm://SERVER
### DIR: the directory
### DIR_LIST: an array containing the directories
### LIST: a map [DIR][FILE]
### Recursion: a parameter to decide the "level" of a directory
### max_recursion: well...
def getRecursiveList(SE,DIR,DIR_LIST,LIST, recursion, max_recursion):
    DIR = polishDirName(DIR)

    ### initialize array/map
    if DIR not in LIST.keys(): LIST[DIR] = []
    if DIR not in DIR_LIST: DIR_LIST.append(DIR)

    ### check recursion
    tmp_rec = len(DIR.split("/"))
    if( tmp_rec - recursion > max_recursion): return

    ### the listing command, takes into account also dirs with >1000 files
    attempts = 0
    out = []
    while ( len(out)==1000*attempts ):
        off = 1000*attempts
        command=['srmls','-count=1000', '-offset='+str(off),SE+DIR]
        outP = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        outL = outP.stdout.readlines()
        outE = outP.stderr.readlines()
        failed = False
        ### Error check
        for x in outE:
            if x.find("SRM_FAILURE") !=-1:  failed = True
        if failed:
            for x in outE: print x.strip("\n")
            break
        outL.remove("\n") 
        temp = outL.pop(0)
        out += outL
        attempts +=1

    ### loop over the output
    for o in out:
        o = polishDirName(o)
        if len(o)==0: continue
        oName, oSize = formatSrmLsOutput(o)
        if len(oName)==0: continue
        ### if a directory is found... go recursive!
        if isDir(oName) and oName!= DIR:
            DIR_LIST.append(oName)
            getRecursiveList(SE,oName, DIR_LIST, LIST, recursion, max_recursion)
        else: LIST[DIR].append([oName,oSize])
    return

                                            
