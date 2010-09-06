#!/usr/bin/python

import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
import re


from cpt_utilities import *
from cpt_SYS_plugin import *


###put accepted summaries also here!
def parseXML_CMSSW(myXML, mapping, acceptedSummaries):
    mapping["Success"] = True ###WorkAround
    mapping["Error"] = {}

    XML_file = open(myXML.strip("\n"))
    
    doc = xml.dom.minidom.parse(XML_file)
    for node in doc.getElementsByTagName("FrameworkError"):
        metric = node.attributes["ExitStatus"].value
        
        try :
            mapping["Error"][metric]+=1
        except KeyError:
            mapping["Error"][metric]=1

        mapping["Success"] = False

    for node in doc.getElementsByTagName("Metric"):
        if not node.parentNode.attributes["Metric"].value in acceptedSummaries: continue
        perfType = node.parentNode.attributes["Metric"].value
        try:
            value = float(node.attributes["Value"].value)
        except:
            value = node.attributes["Value"].value
        mapping["CMSSW_"+node.attributes["Name"].value] = value
        
    for node in doc.getElementsByTagName("counter-value"):
        perfType = node.parentNode.localName
        if perfType == "storage-timing-summary":
            subsystem =  node.attributes["subsystem"].value
            type = node.attributes["counter-name"].value
            for attr in node.attributes.keys():
                if attr== "subsystem" or  attr== "counter-name": continue
                try:
                    value = float( node.attributes[attr].value)
                except:
                    value = node.attributes[attr].value
                mapping[subsystem+"-"+type+"-"+ attr] = value
        
    ### Custom quantities
    if mapping.has_key("tstoragefile-read-actual-num-successful-operations") and  mapping.has_key("tstoragefile-read-actual-total-megabytes"):
        mapping["custom-read-actual-MB_per_operation"] = float(mapping["tstoragefile-read-actual-total-megabytes"])/float(mapping["tstoragefile-read-actual-num-successful-operations"])

    return mapping






def getTimingStats(logfile, mapping):
    pipe = os.popen("grep -E 'TimeEvent|Begin processing the|TimeModule' "+logfile)
    record = -1
    mapping["TimeEvent_record"] = []
    mapping["TimeEvent_event"] = []
    mapping["TimeEvent_secs"] = []
    mapping["TimeEvent_cpuSecs"] = []
    mapping["TimeEvent_cpuPercentage"] = []
    #mapping["TimeEvent_eleIsoDepositTk-CandIsoDepositProducer_secs"] = []

    for x in pipe:
        find1 =  x.find("Begin processing the")
        find2 = x.find("TimeEvent> ")
        find3 = x.find("TimeModule> ")
        if find1 !=-1 :
            record = float( x[len("Begin processing the"): x.find("record")-3]) ##-3 is to cut away st,nd, rd,th
        elif find2 != -1: 
            mapping["TimeEvent_record"].append(record)
            data = x[len("TimeEvent> "):].split(" ")
            mapping["TimeEvent_event"].append(float(data[0]))
            
            secs =  round(float( data[2]),3)
            cpuSecs =  round(float( data[3]),3)
            mapping["TimeEvent_secs"].append( secs)
            mapping["TimeEvent_cpuSecs"].append( cpuSecs )
            if secs!=0: mapping["TimeEvent_cpuPercentage"].append(100*cpuSecs/secs )
            else: mapping["TimeEvent_cpuPercentage"].append(0 )

    pipe.close()





def getModuleTimingStats(logfile, mapping):
    pipe = os.popen("grep -E 'Begin processing the|TimeModule' "+logfile)
    mapping["TimeModule-record"] = []
    mapping["TimeModule-event"] = []
    prevRecord = 0
    record=0
    for x in pipe:
        find1 =  x.find("Begin processing the")
        find2 = x.find("TimeModule> ")
    
        if find1 !=-1 :
            prevRecord=record
            record = float( x[len("Begin processing the"): x.find("record")-3])
        elif find2 != -1: 
            mapping["TimeModule-record"].append(record)
            splitX =  x.strip('\n').split(" ")
            event = float(splitX[1])
            producer = splitX[4]
            module = splitX[3]
            secs = float(splitX[5])
            mapping["TimeModule-event"].append(event)

            if not mapping.has_key("TimeModule-"+producer): 
                mapping["TimeModule-"+producer] = {}
                try:
                    mapping["TimeModule-"+producer][module].append(secs)
                except KeyError:
                    mapping["TimeModule-"+producer][module] = []
                    mapping["TimeModule-"+producer][module].append(secs)

            #if not mapping.has_key("TimeModule-"+producer): 
            #    mapping["TimeModule-"+producer] = {}
            #    #mapping["TimeModule_"+producer]['TOTAL'] = []
            #if not mapping["TimeModule-"+producer].has_key(module): mapping["TimeModule-"+producer][module] = []
            #mapping["TimeModule-"+producer][module].append(secs)
            
    for x in mapping.keys():
        if x.find('TimeModule')!=-1 and x.find('record')==-1 and x.find('event')==-1:
            mapping[x]['TOTAL'] = []
            for y in mapping[x].keys():
                if y=="TOTAL": continue
                i = 0
                if len(mapping[x]['TOTAL'])==0:
                    j=0
                    while j<len(mapping[x][y]):
                        mapping[x]['TOTAL'].append(0)
                        j+=1
                while i<len(mapping[x][y]):
                    mapping[x]['TOTAL'][i]+= mapping[x][y][i]
                    i+=1
                



###time information using /usr/bin/time
###grep user test.txt | sed 's/\(.*\)user \(.*\)system \(.*\)elapsed \(.*\)\%CPU.*/\1 \2 \3 \4 /'
def parseCMSSW_stdOut(log_file, job_output):
    rule = re.compile(r"""(.*)user (.*)system (.*)elapsed (.*)%CPU.*""")
    #rule = re.compile(r"""\(.*\)""")
        
    lines = os.popen("grep elapsed "+log_file)
    for x in lines:
        result = rule.search( x )
        if result!=None:
            timing = result.groups()
            job_output['TimeJob_User'] = float(translateTime(timing[0]))
            job_output['TimeJob_Sys'] = float(translateTime(timing[1]))
            job_output['TimeJob_Exe'] = float(translateTime(timing[2]))
            job_output['TimeJob_CpuPercentage'] = float(timing[3])

    return job_output



def parseDir_CMSSW(logname, acceptedSummaries,netLogFile=""):
    job_output = {}
    
    xmlFile = logname
    logFile = xmlFile.replace(".xml",".stdout")

    if not os.path.isfile( xmlFile ):
        print "[ERROR] "+xmlFile+" NOT FOUND!"
        return 1
    elif float(os.stat( xmlFile ).st_size)<1:
        print "[ERROR] "+xmlFile+" EMPTY!"
        return 1
    else:
        parseXML_CMSSW( xmlFile,job_output, acceptedSummaries)
        if job_output["Success"]:
            parseCMSSW_stdOut(logFile, job_output)
            getTimingStats(logFile, job_output)
            base_logname = xmlFile.split("/")[-1].split(".")[0].split("_")[0]
            
            ### is different from "" when called from another plugin
            if netLogFile=="": 
                lognum = logFile.split("/")[-1].split("_")[1].split(".")[0]
                job_output["internal_jobNumber"] = int(lognum)
                netLogFile = xmlFile.replace(".xml",".log")
                netLogFile = netLogFile.replace( base_logname, base_logname+"_net"  )
            getNetworkStats(netLogFile, job_output)
            
            dstat_logfile = xmlFile.replace(".xml","_dstat.csv")
            if os.path.isfile( dstat_logfile ): getData_dstat( dstat_logfile, job_output)
            vmstat_logfile = xmlFile.replace(".xml",".log")
            #base_logname = vmstat_logfile.split("/")[-1].split(".")[0].split("_")[0]
            vmstat_logfile = vmstat_logfile.replace( base_logname, base_logname+"_vmstat"  )
            if os.path.isfile( vmstat_logfile ): getData_vmstat(vmstat_logfile, job_output, 10)
            
            #This one to take into account also the 60 seconds of sleep o tests (or whatever)
            job_output["CMSSW_CpuPercentage"] = 100*job_output['TimeJob_User']/job_output['CMSSW_TotalJobTime']

            #getModuleTimingStats(logFile, job_output)
        #totalFiles += 1
    
    #print job_output
    #print job_output["TimeEvent_secs"]

    return job_output
