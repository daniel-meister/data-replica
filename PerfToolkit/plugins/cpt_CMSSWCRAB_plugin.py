#!/usr/bin/python

### added time delay
### added lognum in data
### using "internal" prefix for internal variables (not to be used)

import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
import re
import time

from cpt_utilities import *
from cpt_SYS_plugin import *
from cpt_CMSSW_plugin import *
from cpt_CRAB_plugin import *



###parse XML produced by CMSSW
def parseDir_CMSSWCrab(LOGDIR, subdir, cmsswOutName, acceptedSummaries):
    job_output = {}
    logdir = LOGDIR+"/res/"
    lognum =  subdir[subdir.find("res/CMSSW"):].split("_")[1].split(".")[0]
    log_file =  logdir+"CMSSW_"+str(lognum)+".stdout"

    ###CRAB numberig scheme changed since 2.7.3
    tmpList = os.popen("ls "+logdir+cmsswOutName+"_"+str(lognum)+"_*.xml").readlines()
    if len(tmpList)==0:
        print "[ERROR]: no xml_file or too many files recognized, please check it"
        return 1
    else:
        xml_file_cmssw = tmpList[0].strip('\n')

    tmpList = os.popen("ls "+logdir+"cmssw_net_"+lognum+"_*.log").readlines()
    if len(tmpList)==0:
        print "[ERROR]: no net_file or too many files recognized, please check it"
        return 1
    else:
        net_file = tmpList[0].strip('\n')

    ### submission time from crab.log
    time_submit = getSubmitTime_Crab(LOGDIR)
    if float(os.stat( log_file).st_size)<1:
        print "[ERROR] "+log_file+" EMPTY!"
        return 1 #continue
    else:
        job_output["internal_jobNumber"] = int(lognum)
 ### execution time from job logfile
        time_start = getStartTime_Crab(log_file, time_submit)
                
        job_output["Time_Submission"] = time_submit
        job_output["Time_Execution"] = time_start
        job_output["Time_Delay"] = time_start - time_submit
        if job_output["Time_Delay"]<0:
            print "[WARNING]: Time_Delay negative in job "+lognum+"... a mess with timezones?"

        parseCrab_stdOut( log_file,job_output)
        cmssw_job_output = parseDir_CMSSW(xml_file_cmssw, acceptedSummaries, net_file)
        job_output.update( cmssw_job_output)

    return job_output

