#!/usr/bin/python
#################################################################
# crab_getJobStatistics.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_getJobStatistics.py,v 1.6 2009/12/14 15:53:07 leo Exp $
#################################################################


import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
from math import sqrt
import re
from crab_utilities import *

isRoot = True

try:
    import ROOT
except:
    print "ROOT cannot be loaded, running textual only"
    isRoot = False
    exit(1)

if len(argv)<2:
    print "USAGE: "+argv[0]+" crab_dir <outfile>"
    exit(1)

LOGDIR = argv[1]
if len(argv)==3:
    OUTFILE = argv[2]
else:
    OUTFILE = ""


### Init array of quantities
LABELS = [ ]


def parseXML(myXML, mapping):
    mapping["Success"] = False
    mapping["Error"] = {}

    XML_file = open(myXML.strip("\n"))
    
    doc = xml.dom.minidom.parse(XML_file)
 
    for node in doc.getElementsByTagName("Metric"):
        if node.attributes["Name"].value=="CpuTime":
            cpuTime =  node.attributes["Value"].value.replace('"','').split(" ")
            mapping["UserTime"] = cpuTime[0]
            mapping["SysTime"] = cpuTime[1]
            mapping["CpuPercentage"] = cpuTime[2].strip("%")
        mapping[node.attributes["Name"].value] = node.attributes["Value"].value 
        
    for node in doc.getElementsByTagName("FrameworkError"):
        mapping[node.attributes["Type"].value] = node.attributes["ExitStatus"].value

    exitCode = float(mapping["ExeExitCode"])
    if exitCode ==0:
        mapping["Success"] = True
    else:    
        if not mapping["Error"].has_key( mapping["ExeExitCode"]  ):
            mapping["Error"][ mapping["ExeExitCode"] ]=0
        mapping["Error"][ mapping["ExeExitCode"] ]+=1
    
    return mapping



def parseCrabDir(logdir, subdir, totalFiles):
    job_output = {}
    lognum =  subdir[subdir.find("res/CMSSW"):].split("_")[1].split(".")[0]

    xml_file = logdir+"crab_fjr_"+str(lognum)+".xml"
    if not os.path.isfile( xml_file ):
        print "[ERROR] "+xml_file+" NOT FOUND!"
        return 1
    else:
        if float(os.stat( xml_file ).st_size)<1:
            print "[ERROR] "+xml_file+" EMPTY!"
            return 1
        else:
            parseXML( xml_file,job_output)
            totalFiles += 1
    return job_output


    
def computeErrorStat(job_output, SUMMARY):
    #Computing err statistics
    if not job_output["Success"]:
        for err in job_output["Error"].keys():
            err = str(err)
            err = err[:err.find(".")]
            if not SUMMARY["Error"].has_key(err): SUMMARY["Error"][err] = 0
            SUMMARY["Error"][err] += 1
                #End comp error stat


def setBinEdges(job_output, label):
    binEdges={}
    #if label == "tstoragefile-read-total-msecs":
    #    lowerBin = 0.0
    #    upperBin = 1000.*1000.
    #    bins = 200
    if label.find("msecs") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 100*60000. ###6k secs 
        binEdges['bins'] = 1000 ##60 secs bin
    elif label.find("Percentage") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 100.
        binEdges['bins'] = 100 
    elif label.find("Time") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 40000. ### 40k secs=11h
        binEdges['bins'] = 4000 ### 10 secs bin 
    elif label.find("num-operations") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 100000. 
        binEdges['bins'] = 10000 
    elif label.find("Error") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 1. 
        binEdges['bins'] = 1    
    else:
        binEdges['lowerBin'] = 0
        binEdges['upperBin'] = 10000
        binEdges['bins'] = 10000    
    return binEdges
    #begin edges if
#    if not binEdges['low'].has_key(label):
#        binEdges['low'][label] = 9999999
#        binEdges['high'][label] = 0
    #end edges if

    #begin job output if
#    if job_output.has_key(label):
#        value =  float(job_output[label])
#        if value <  binEdges['low'][label]:  binEdges['low'][label] = value
#        if value >  binEdges['high'][label]: binEdges['high'][label] = value



def getJobStatistics(LOGDIR,OUTFILE):
    DIR_SUMMARY = {}
    SUMMARY = {} ###stores full stat
    SINGLE_DIR_DATA = {} ###stores single entries

    firstDir = True
    tempI=0

    
    #Begin dir analysis
    if os.path.isdir(LOGDIR)==False and os.path.islink(LOGDIR)==False:
        print "Directory not Valid"
        exit(1)


    SUMMARY = {"Success":0, "Failures":0, "Error":{}}
    spDirName = splitDirName(LOGDIR)
    #if OUTFILE=="":
    #    OUTFILE = spDirName["Site"]+"-"+spDirName["Cfg"]+"-"+spDirName['EventsJob']+"-"+spDirName['Sw']+"-"+spDirName['Date']+".root"
    OUTFILE = LOGDIR.strip('/').split("/")[-1]+'.root' 
        
    print "OutFile:",OUTFILE
    print "Analyzing "+LOGDIR

    totalFiles = 0
    ###Parsing Files
    logdir = LOGDIR+"/res/"
    LOGS = os.popen("ls "+logdir+"*.stdout")
    for x in LOGS:
        #Parse crabDir
        rValue = parseCrabDir(logdir, x, totalFiles)
        if rValue!=1: job_output = rValue
        else: continue
        #end Parse crabDir

        spName = splitDirName(LOGDIR)
        ###UserQuantities
        totalMB = 0
        totalReadTime = 0
        for quant in job_output.keys():
            if len(quant.split('-'))==4 and quant.find('readv-total-megabytes')!=-1:
                totalMB += float(job_output[quant])
            if len(quant.split('-'))==4 and quant.find('readv-total-msecs')!=-1:
                totalReadTime += float(job_output[quant])

        if job_output.has_key('tstoragefile-read-total-megabytes'):
            totalMB += float(job_output['tstoragefile-read-total-megabytes'])
            job_output['User_ReadkBEvt'] = 1024*totalMB/float(spName['EventsJob'])
        
        if job_output.has_key('tstoragefile-read-total-msecs'):
            totalReadTime += float(job_output['tstoragefile-read-total-msecs'])
            job_output['User_Wall-Read_CpuPercentage'] = 100.*( float(job_output['ExeTime']) - totalReadTime/1000.)/float(job_output['ExeTime'])


        totalFiles+=1
        computeErrorStat(job_output, SUMMARY)

        #begin label cycle
        for label in job_output.keys():
            ### checks for float values
            try: 
                float( job_output[label])
                if not label in LABELS: LABELS.append(label)
            except: 
                continue

            #begin job output if
            if job_output.has_key(label):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                SINGLE_DIR_DATA[label].append(float(job_output[label]))
            #end job output if

        #end label cycle
        if job_output["Success"]==True: SUMMARY["Success"] +=1
        else: SUMMARY["Failures"] +=1
                
    #end log cycle

    LABELS.sort()

    #Creating plots and statistics (if ROOT LOADED)
    if isRoot:
        outFile = ROOT.TFile(OUTFILE,"RECREATE")

        single_H = {}
        sampleName=OUTFILE.strip(".root")

        ### ERRORS HAVE A DIFFERENT TREATMENT
        single_H["Error"] = {}
        label="Error"
        single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName,sampleName,200,0,1)
        for err in SUMMARY[label].keys():
            single_H[label].Fill(err, SUMMARY[label][err] )

        
        if float(SUMMARY["Success"])==0:
            print LOGDIR," has no successful job"
            outFile.Write()
            outFile.Close()
            exit(0)

        for label in LABELS:
            single_H[label] = {}
            binEdges = setBinEdges(job_output,label) 
            single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName, sampleName, binEdges['bins'], binEdges['lowerBin'], binEdges['upperBin'])
            single_H[label].StatOverflows(ROOT.kTRUE)
            
            if not SINGLE_DIR_DATA.has_key(label):
                print "[WARNING]: "+label+" quantity not available"
                continue

            for entry in SINGLE_DIR_DATA[label]:
                #print entry
                single_H[label].Fill(entry)

            if label == "tstoragefile-read-total-msecs":
                nBins = single_H[label].GetNbinsX()
                single_H[label].SetBinContent( nBins , single_H[label].GetBinContent( nBins )+
                                                        single_H[label].GetBinContent( nBins+1 )) 

        outFile.Write()
        outFile.Close()





if __name__ == '__main__':
    getJobStatistics(LOGDIR,OUTFILE)
