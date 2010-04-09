#!/usr/bin/python

### added time delay


import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
import re

from cpt_utilities import *
from cpt_SYS_plugin import *
from cpt_CMSSW_plugin import *


def parseXML_Crab(myXML, mapping, acceptedSummaries):
    XML_file = open(myXML.strip("\n").strip(" "))
    doc = xml.dom.minidom.parse(XML_file)

    for node in doc.getElementsByTagName("Metric"):
        if not node.parentNode.attributes["Metric"].value in acceptedSummaries: continue
   
        if node.attributes["Name"].value=="CpuTime":
            cpuTime =  node.attributes["Value"].value.replace('"','').split(" ")
            mapping["TimeJob_User"] = float(cpuTime[0])
            mapping["TimeJob_Sys"] = float(cpuTime[1])
            mapping["CpuPercentage"] = float(cpuTime[2].strip("%"))
        else:
            try:
                value = float(node.attributes["Value"].value)
            except:
                value = node.attributes["Value"].value 
            quant = node.attributes["Name"].value
            index =  quant.find("Time")
            if index!=-1:
                index =  quant.find("Time")
                quant = quant[index:]+"Job_"+quant[:index]
            mapping[quant] = value #float(node.attributes["Value"].value )
        
    for node in doc.getElementsByTagName("FrameworkError"):
        mapping[node.attributes["Type"].value] = node.attributes["ExitStatus"].value

    exitCode = float(mapping["ExeExitCode"])
    return mapping



def parseCrab_stdOut(log_file,crab_stdout):
    out =  os.popen("grep ExitCode "+log_file)
    crab_stdout["Success"] = False
    crab_stdout["Error"] = {}
 
    for x in out:
        metric= x.strip("\n").split("=")[1].strip("%")
        metric = float(metric)
        if metric == 0:
            crab_stdout["Success"] = True
            break
        else:
            if not crab_stdout["Error"].has_key(metric):
                crab_stdout["Error"][metric]=0
            crab_stdout["Error"][metric]+=1
    
    return crab_stdout



def parseDir_Crab(LOGDIR, subdir, acceptedSummaries):
    job_output = {}
    logdir = LOGDIR+"/res/"
    lognum =  subdir[subdir.find("res/CMSSW"):].split("_")[1].split(".")[0]
    log_file =  logdir+"CMSSW_"+str(lognum)+".stdout"

    ### submission time from crab.log
    time_submit = os.popen("grep 'jobs submitted' "+LOGDIR+"/log/crab.log").readlines()[0]
    time_submit = time_submit[ : time_submit.find("[INFO]")]
    time_submit = float( os.popen("date -d '"+time_submit+"' +%s").readlines()[0].strip("\n") ) 

    if float(os.stat( log_file).st_size)<1:
        print "[ERROR] "+log_file+" EMPTY!"
        return 1 #continue
    else:
        ### execution time from job logfile
        time_start = os.popen("grep 'Today is ' "+log_file).readlines()[0].strip("\n")
        time_start = time_start[len("Today is "):]
        time_start = float( os.popen("date -d '"+time_start+"' +%s").readlines()[0].strip("\n"))
        
        job_output["Time_Submission"] = time_submit
        job_output["Time_Execution"] = time_start
        job_output["Time_Delay"] = time_start - time_submit

        parseCrab_stdOut( log_file,job_output)
        #totalFiles += 1

        if job_output["Success"]:
            getTimingStats(log_file, job_output)
            if "ProducerTiming" in acceptedSummaries or "ModuleTiming" in acceptedSummaries:
                getModuleTimingStats(log_file, job_output)

            xml_file = logdir+"crab_fjr_"+str(lognum)+".xml"
            if not os.path.isfile( xml_file ):
                print "[ERROR] "+xml_file+" NOT FOUND!"
                return 1
            else:
                if float(os.stat( xml_file ).st_size)<1:
                    print "[ERROR] "+xml_file+" EMPTY!"
                    return 1
                else:
                    parseXML_Crab( xml_file,job_output, acceptedSummaries)
                    #totalFiles += 1 ???? double?
    return job_output

