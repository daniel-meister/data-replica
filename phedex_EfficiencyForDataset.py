#!/bin/env python

from os import popen
from sys import argv, exit
from optparse import OptionParser

usage = """This program computes the transfer efficiency divided by datasets using PhEDEx logfiles

USAGE: %prog [options] logfile(2)

"""
parser = OptionParser(usage=usage)
parser.add_option("--sel", dest="selection", help="select datasets")
parser.add_option("-v", dest="verbose", help="dump errors",action="store_true",default=False)


(options, args) = parser.parse_args()

if len(argv)<2:
    print """USAGE: """+argv[0]+""" [--help] [--sel DATASET] [-v] logfile(s) """
    exit(1)

if not options.selection:
    options.selection = ""

print options

def fillLogEntry(mylog, log_entry, dataset,LOGS,options):
    entry_start=0
    entry_delimiter = mylog[entry_start:].find("=")
    entry_end = mylog[entry_start:].find(" ")
    newLog = mylog[entry_start:]

    while entry_end != -1 and entry_delimiter != -1:
        label = newLog[:entry_delimiter]
        entry = newLog[entry_delimiter+1:entry_end]

        if len(label)<2:
            continue
        
        log_entry[label] = entry
        if label == "lfn":
            dataset = "/"+entry.split("/")[3]+"/"+entry.split("/")[4]+"/"+entry.split("/")[5]+"/"+entry.split("/")[6]
                        
        entry_start = entry_end+1
        newLog = newLog[entry_start:]
        entry_delimiter = newLog.find("=")
        if entry_delimiter!=-1:
            if newLog[entry_delimiter+1] == "(" :
                entry_end = newLog.find(")")+1
            else:
                entry_end = newLog.find(" ")

                
    if options.selection=='' or dataset.find(options.selection)!=-1:
        if not LOGS.has_key(dataset):
            LOGS[dataset] = {}
        if not LOGS[dataset].has_key(log_entry["from"]):
            LOGS[dataset][log_entry["from"]] ={'failed':0,'success':0,'total':0,'errors':{}}


        failed = 1
        if log_entry["detail"].find("error during phase: []") != -1:
            failed = 0
        else:
            if not LOGS[dataset][log_entry["from"]]["errors"].has_key( log_entry["detail"] ):
                LOGS[dataset][log_entry["from"]]["errors"][log_entry["detail"]]=0
            LOGS[dataset][log_entry["from"]]["errors"][log_entry["detail"]] += 1
                    
        
                
        if failed==1:
            LOGS[dataset][log_entry["from"]]["failed"]+=1
        else:
            LOGS[dataset][log_entry["from"]]["success"]+=1
        LOGS[dataset][log_entry["from"]]["total"]+=1
        
    return



def printWiki(LOGS):
    grand_total = 0
    grand_success = 0
    
    print "|*DATASET*|*SITE*|*SUCCESS*|*FAILED*|*TOTAL*|*EFFICIENCY*|"
    
    for dataset in LOGS.keys():
        total = 0
        success = 0
        print "|*"+dataset+"*| | | | | |"
        for site in LOGS[dataset].keys():
            
            grand_total += LOGS[dataset][site]["total"]
            grand_success += LOGS[dataset][site]["success"]
            total += LOGS[dataset][site]["total"]
            success += LOGS[dataset][site]["success"]
            
            print "| |"+site+" | "+str(LOGS[dataset][site]["success"])+"| "+str(LOGS[dataset][site]["failed"])+"| "+str(LOGS[dataset][site]["total"])+"| %.1f| " %(100*float(LOGS[dataset][site]["success"])/float(LOGS[dataset][site]["total"]))
        print "| | | | | | *%.1f*|" %(100*float(success)/float(total))
            
    print "| | | | | *TOTAL EFFICIENCY* | *%.1f*|" %(100*float(grand_success)/float(grand_total))
    return



def main(args):

#    LOGFILE = argv[1]

    f = []
    i = 0
    for LOGFILE in args:
        f.append(open(LOGFILE,"r"))
        i+=1
    LOGS = {}
    
    header = 0

    j=0
    while j in range(0,i):
        for stat in f[j]:
            
            if stat.find("xstats")==-1:
                continue
            
            if header == 0:
                print "\n----- STATISTICS FROM "+stat[:stat.find("FileDownload")]
                header = 1
            
            log_start = stat.find("xstats: ")+len("xstats: ")
            mylog = stat[log_start:]
            
            log_entry = {}
            dataset = ""
            
            fillLogEntry(mylog, log_entry,dataset,LOGS,options)
        j+=1

    printWiki(LOGS)

    if options.verbose:
        for dataset in LOGS:
            print "\n----------"+dataset
            for site in LOGS[dataset]:
                print "+++"+site
                for x in LOGS[dataset][site]["errors"].keys():
                    print LOGS[dataset][site]["errors"][x], ': ',x
    return


print __name__
if __name__ == '__main__':
    main(args)
        
