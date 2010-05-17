#!/usr/bin/python

import os
import re

### same name for quatities read by different programs (dstat, proc)?
### option for naming xml files?

##Retrieve network stats from proc
def getNetworkStats(logfile, mapping):
    log = open(logfile)
    isFirstData = True
    startingEpoch = 0
    prevEpoch = 0
    prevTX=0
    prevRX=0
    divider = 1024.
    totalRX = 0
    totalTX = 0

    for x in log:
        x = x.strip("\n")
        m_init = re.match(r"\[NET\]\ +(\d+) RX:\ +(\d+)\ +TX:\ +(\d+).*",x)
        if m_init!=None:
            epoch = float(m_init.group(1))
            if isFirstData: 
                startingEpoch = epoch
                prevEpoch = epoch
                prevTX = float(m_init.group(3))/divider
                prevRX = float(m_init.group(2))/divider
                isFirstData = False
                if not mapping.has_key("WN_net-Seconds"):  mapping["WN_net-Seconds"]=[]
                if not mapping.has_key("WN_net-RX_kBs"):  mapping["WN_net-RX_kBs"]=[]
                if not mapping.has_key("WN_net-TX_kBs"):  mapping["WN_net-TX_kBs"]=[]
                totalRX = prevRX 
                totalTX = prevTX
                continue

            timeInterval = epoch - prevEpoch

            RX =  (float(m_init.group(2))/divider) - prevRX
            RX = RX/timeInterval
            TX =  (float(m_init.group(3))/divider) - prevTX
            TX = TX/timeInterval
            
  
            mapping["WN_net-Seconds"].append(epoch - startingEpoch)
            mapping["WN_net-RX_kBs"].append( RX )
            mapping["WN_net-TX_kBs"].append( TX )
            prevEpoch = epoch
            prevTX = float(m_init.group(3))/divider
            prevRX = float(m_init.group(2))/divider
    
    mapping["WN_net-totalRX_MB"] =  (prevRX - totalRX)/(1024)
    mapping["WN_net-totalTX_MB"] =  (prevTX - totalTX)/(1024)


### vmstatInterval is the interval set in dstat, need to think sth better
def getData_vmstat(logfile, mapping, vmstatInterval=10):
    #this dictionary translates the quantity names of dstat in humar readable names
    translator = {"us":"WN_vmstat-CPU_User", "sy":"WN_vmstat-CPU_Sys", "id":"WN_vmstat-CPU_Idle","wa":"WN_vmstat-CPU_Wait",
                  "bi":"WN_vmstat-DISK_Read","bo":"WN_vmstat-DISK_Write",
                  "buff":"WN_vmstat-MEM_Buff", "cache":"WN_vmstat-MEM_Cached", "free":"WN_vmstat-MEM_Free"
                  }

    myFile = open(logfile)
    isFirstData=True
    startingEpoch = 0
    evt = 0
    labels = []
    for line in myFile:
        line = line.strip("\n")
        if line.strip()=="": continue
        ### this is vmstat output format
        if line[0]==" " and line[1]=="r": 
            labels = line.split()
        else:
            i=0
            data = line.split()
            for l in labels: 
                l = l.strip('"')
                if translator.has_key(l): translatedLabel = translator[l]
                else: translatedLabel = "WN_vmstat-"+l
                if not mapping.has_key( translatedLabel ): mapping[ translatedLabel ] = []
                divider = 1.
                if translatedLabel.find("NET")!=-1 or translatedLabel.find("DISK")!=-1:  divider=(1024)
                mapping[ translatedLabel ].append( float(data[i])/divider )
    
                ### translating into kB
                i += 1
            if not mapping.has_key("WN_vmstat-Seconds"):  mapping["WN_vmstat-Seconds"]=[]
            secInterval = float(vmstatInterval)*float(evt)
            mapping["WN_vmstat-Seconds"].append( secInterval )
            isFirstData=False
            evt+=1
               
    


### dstatInterval is the interval set in dstat, need to think sth better
def getData_dstat(logfile, mapping):
    print "Getting dstat data"
    #this dictionary translates the quantity names of dstat in humar readable names
    translator = {"usr":"WN_dstat-CPU_User", "sys":"WN_dstat-CPU_Sys", "idl":"WN_dstat-CPU_Idle","wai":"WN_dstat-CPU_Wait",
                  "read":"WN_dstat-DISK_Read","write":"WN_dstat-DISK_Write",
                  "used":"WN_dstat-MEM_Used", "buff":"WN_dstat-MEM_Buff", "cach":"WN_dstat-MEM_Cached", "free":"WN_dstat-MEM_Free",
                  "recv":"WN_dstat-NET_Rx", "send":"WN_dstat-NET_Tx"}

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
               
    
