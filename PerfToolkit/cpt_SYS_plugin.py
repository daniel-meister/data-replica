#!/usr/bin/python

import os
import re


##Retrieve statistics not available through FJR
def getNetworkStats(logfile, mapping):
    pipe = os.popen("grep -E 'Network start|Network stop' "+logfile)
    list = pipe.readlines()
    if len(list)==2:
        date = [0,0]
        bytes = [0,0]
        i=0
        while i<2:
            m_init = re.match(r"Network st.*\ +(\d+) RX bytes:(\d+).*", list[i])
            if m_init!=None:
                date[i] = float(m_init.group(1))
                bytes[i] = float(m_init.group(2))
            i+=1

        mapping["Ifconfig_MB"] = (bytes[1]-bytes[0])/(1024*1024)
        mapping["Ifconfig_MBoverS"] =  mapping["Ifconfig_MB"]/(date[1]-date[0])



### dstatInterval is the interval set in dstat, need to think sth better
def getData_dstat(logfile, mapping):
    print "Getting dstat data"
    #this dictionary translates the quantity names of dstat in humar readable names
    translator = {"usr":"dstat-CPU_User", "sys":"dstat-CPU_Sys", "idl":"dstat-CPU_Idle","wai":"dstat-CPU_Wait",
                  "read":"dstat-DISK_Read","write":"dstat-DISK_Write",
                  "used":"dstat-MEM_Used", "buff":"dstat-MEM_Buff", "cach":"dstat-MEM_Cached", "free":"dstat-MEM_Free",
                  "recv":"dstat-NET_Rx", "send":"dstat-NET_Tx"}

    myFile = open(logfile)
    isFirstData=True
    startingEpoch = 0
    evt = 0
    for line in myFile:
        line = line.strip("\n")
        if line.strip()=="": continue
        if line[0]=="\"": labels = line.split(",")
        else:
            i=0
            data = line.split(",")
            for l in labels: 
                l = l.strip('"')
                if isFirstData and l=="epoch": startingEpoch = float(data[i])
                if translator.has_key(l): translatedLabel = translator[l]
                else: translatedLabel = "dstat-"+l
                if not mapping.has_key( translatedLabel ): mapping[ translatedLabel ] = []
                divider = 1.
                if translatedLabel.find("NET")!=-1 or translatedLabel.find("DISK")!=-1:  divider=(1024)
                mapping[ translatedLabel ].append( float(data[i])/divider )
                ### translating into kB/s
                i += 1
            if not mapping.has_key("dstat-Seconds"):  mapping["dstat-Seconds"]=[]
            secInterval = round(mapping["dstat-epoch"][evt] - startingEpoch)
            mapping["dstat-Seconds"].append( secInterval )
            isFirstData=False
            evt+=1
               
    
