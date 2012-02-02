#!/bin/env python

## Author: leonardo.sala@cern.ch

import os, sys


if len(sys.argv)!=2:
    print "Creates statistics about a list containing files. It counts files per user (under /store/user) and creates a separate file for each user, cointaining his/her files"
    print "Comments to leoanrdo.sala@cern.ch\n"
    print "Usage: "+sys.argv[0]+ " filelist"
    sys.exit(1)

filelist = sys.argv[1]
print "cat "+filelist+" | grep /store/user | sed 's:.*\/store\/user\/\(.*\)\/.*:\\1:g' |cut -d/ -f1 | sort |uniq  "
usernameList = os.popen("cat "+filelist+" | grep /store/user | sed 's:.*\/store\/user\/\(.*\)\/.*:\\1:g' |cut -d/ -f1 | sort |uniq  ")

TotalFiles=0
for u in usernameList:
    u = u.strip("\n")
    uList = filelist.split(".")[0]+"_"+u+".txt"
#    print "Getting files for "+u+", output in "+uList
#    print "grep /store/user/"+u+" | cut -d\ -f2 | sort >"+uList
    os.popen("grep /store/user/"+u+" "+filelist+" | awk '{print $2}' | sort >"+uList)
    out = os.popen("cat "+uList+" | wc -l")
    filesLost = out.readline().strip("\n")
    print "User "+u+": "+filesLost
    TotalFiles += float(filesLost)

print "Total files: " + str(TotalFiles)
