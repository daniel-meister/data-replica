#!/usr/bin/python
#################################################################
# cpt_getJobInfo.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: cpt_getJobInfo.py,v 1.6 2010/04/09 12:23:15 leo Exp $
#################################################################

### plugins moved to a directory


import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
from math import sqrt
import re
from optparse import OptionParser

from cpt_utilities import *
from plugins import *


###max x-axis for graphs: ootherwise setting different ranges is difficult
MAX_GRAPH_X = 1000


isRoot = True



try:
    import ROOT
except:
    print "ROOT cannot be loaded, running textual only"
    isRoot = False
    exit(1)



usage = """For simple CMSRUN jobs, the stdout file must have a name of the form WHATEVER_1.stdout, WHATHEVER_2.stdout, etc, 
and the same apply to the FJR xml files (WHATHEVER_1.xml).
For jobs submitted through CRAB, standard names will be used."""
parser = OptionParser(usage = usage)
#parser.add_option("--no-auto-bin",action="store_true", dest="noAutoBin", default=False,
#                  help="Automatic histo binning")
parser.add_option("--type",action="store", dest="TYPE",default="CRAB",
                  help="Type of the log/xml files, can be CRAB,CMSSW,CMSSWCRAB")
#parser.add_option("--stdout",action="store", dest="STDOUT",default="CMSSW",
#                  help="Name type of stdout file. If your files are named e.g. my_1.stdout, my_2.stdout, ... put 'my'")
#parser.add_option("--fjr",action="store", dest="FJR",default="crab_fjr",
#                  help="Name type of fjr xml file. If your files are named e.g. my_1.xml, my_2.xml, ... put 'my'")


(options, args) = parser.parse_args()


if len(argv)<2:
    print "USAGE: "+argv[0]+" crab_dir <outfile>"
    exit(1)

LOGDIR = args[0]
if len(args)>1:
    OUTFILE = args[1]
else:
    OUTFILE = ""


### Values are: StorageTiming, CrabTiming, Timing, EventTiming, ModuleTiming, ProducerTiming
acceptedSummaries = ['StorageTiming', "CrabTiming", "Timing","ProducerTiming"]
#acceptedSummaries = ['StorageTiming', "CrabTiming" ,"ProducerTiming"]


###discard the first event in histo filling
discardFirstEvent_Module = True
discardFirstEvent_Producer = True



### Init array of quantities
LABELS = [ ]


### from hh:mm:ss to secs
def translateTime(str):
    seconds = 0
    mult = 1
    time = str.split(':')
    i = 1
    while i <= len(time):
        seconds += float(time[-i])*mult
        mult *=60
        i +=1
    return seconds


def computeErrorStat(job_output, SUMMARY):
    #Computing err statistics
    if not job_output["Success"]:
        for err in job_output["Error"].keys():
            err = str(err)
            if err.find(".")!=-1:
                err = err[:err.find(".")] ### uhm, why?
            
            if not SUMMARY["Error"].has_key(err): SUMMARY["Error"][err] = 0
            SUMMARY["Error"][err] += 1
                #End comp error stat

def computeBinEdges(label,samplesBinEdges, value ):
    if not samplesBinEdges.has_key(label):
        samplesBinEdges[label] = {}    
        samplesBinEdges[label]['lowerBin'] = 9999999
        samplesBinEdges[label]['upperBin'] = 0
                    
    if value < samplesBinEdges[label]['lowerBin']: 
        samplesBinEdges[label]['lowerBin'] = value
    elif value > samplesBinEdges[label]['upperBin'] :
        samplesBinEdges[label]['upperBin'] = value



def setBinEdges(job_output, label):
    #if label == "tstoragefile-read-total-msecs":
    #    lowerBin = 0.0
    #    upperBin = 1000.*1000.
    #    bins = 200
    binEdges = {}
    if label.find("msecs") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 100*600000. ###60k secs 
        binEdges['bins'] = 6000 ##10 secs bin
    elif label.find("Percentage") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 100.
        binEdges['bins'] = 100 
    elif label.find("EventTime") != -1:
        binEdges['lowerBin'] = 0
        binEdges['upperBin'] = 1000
        binEdges['bins'] = 1000 
    elif label.find("Time") != -1 and label.find("TimeEvent")==-1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 60000. ### 60k secs
        binEdges['bins'] = 6000 ### 10 secs bin 
    elif label.find("num") != -1:
        binEdges['lowerBin'] = 0
        binEdges['upperBin'] = 1000000 
        binEdges['bins'] = 100000 
    elif label.find("Error") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 1. 
        binEdges['bins'] = 1   
    elif label.find("TimeEvent") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 1. 
        binEdges['bins'] = 1 
#    elif label.find("TimeModule") != -1:
#        binEdges['lowerBin'] = 0.0
#        binEdges['upperBin'] = 10. 
#        binEdges['bins'] = 1        
    else:
        binEdges['lowerBin'] = 0
        binEdges['upperBin'] = 10000
        binEdges['bins'] = 10000   

    #if not noAutoBin:
    #    binEdges['lowerBin'] = 0.9*binEdges2[label]['lowerBin']
    #    binEdges['upperBin'] = 1.1*binEdges2[label]['upperBin']
  
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
    MEAN_COMP = {} ### stores stat info

    firstDir = True
    tempI=0

    samplesBinEdges = {} #{'lowerBin':{},'upperBin':{}}

    
    #Begin dir analysis
    if os.path.isdir(LOGDIR)==False and os.path.islink(LOGDIR)==False:
        print LOGDIR
        print "[ERROR] Directory not Valid"
        exit(1)


    SUMMARY = {"Success":0, "Failures":0, "Error":{}}
    spDirName = splitDirName(LOGDIR)
    
    OUTFILE = LOGDIR.strip('/').split("/")[-1]+'.root' 
       
    print " "
    print "OutFile:",OUTFILE
    print "Analyzing "+LOGDIR

    #totalFiles = 0
    ###Parsing Files
    CRAB_LOGDIR = LOGDIR+"/res/"
    ### use stdout or xml for both?
    if options.TYPE == "CRAB": LOGS = os.popen("ls "+CRAB_LOGDIR+"*.stdout")
    elif  options.TYPE == "CMSSW": LOGS = os.popen("ls "+LOGDIR+"/*.xml")
    elif options.TYPE == "CMSSWCRAB": LOGS = os.popen("ls "+CRAB_LOGDIR+"CMSSW*.stdout")
    else: 
        print "[ERROR] No valid log/xml file given"
        exit(1)
    for x in LOGS:
        #Parse crabDir
        x = x.strip('\n')
        if options.TYPE == "CRAB": rValue = parseDir_Crab(LOGDIR, x, acceptedSummaries)
        elif  options.TYPE == "CMSSW": rValue = parseDir_CMSSW( x, acceptedSummaries)
        elif  options.TYPE == "CMSSWCRAB": rValue = parseDir_CMSSWCrab( LOGDIR, x, 'cmssw', acceptedSummaries)

        
        if rValue!=1: job_output = rValue
        else: continue
        #end Parse crabDir

        ###UserQuantities
        totalMB = 0
        totalActualMB = 0
        totalReadTime = 0
   
        if job_output.has_key('tstoragefile-read-total-megabytes'): totalMB += float(job_output['tstoragefile-read-total-megabytes'])
        if job_output.has_key('tstoragefile-readv-total-megabytes'): totalMB += float(job_output['tstoragefile-readv-total-megabytes'])
        
        if job_output.has_key('tstoragefile-read-actual-total-megabytes'): totalActualMB += float(job_output['tstoragefile-read-actual-total-megabytes'])
        if job_output.has_key('tstoragefile-readv-actual-total-megabytes'): totalActualMB += float(job_output['tstoragefile-readv-actual-total-megabytes'])

        

        if isinstance(spDirName, str)==False and spDirName.has_key("EventsJob"):
            events = spDirName['EventsJob']
            if spDirName['EventsJob'][-1]=='k': events =  spDirName['EventsJob'][:-1]+'000'
            job_output['User_ReadkBEvt'] = 1024*totalMB/float(events)
        job_output['Actual_Read+Readv_Total_MB'] = totalActualMB
        
        #totalFiles+=1
        computeErrorStat(job_output, SUMMARY)

        #begin label cycle
        for label in job_output.keys():
            if isinstance( job_output[label] , float):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                SINGLE_DIR_DATA[label].append( job_output[label] )
            elif  isinstance( job_output[label] , int):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                job_output[label] = float(job_output[label]) 
                SINGLE_DIR_DATA[label].append( float(job_output[label]) )
            elif  isinstance( job_output[label] , list):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                SINGLE_DIR_DATA[label].append( job_output[label])
            elif  isinstance( job_output[label] , dict):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = {}
                SINGLE_DIR_DATA[label] = job_output[label]
            else:
                continue
         
            if not label in LABELS:
                if not label in ['TimeEvent_record','TimeEvent_run','TimeEvent_event']:
                    LABELS.append(label)
        #end label cycle
        if job_output["Success"]==True: SUMMARY["Success"] +=1
        else: SUMMARY["Failures"] +=1
        
    SUMMARY["Total"] = SUMMARY["Failures"]+SUMMARY["Success"]
    #end log cycle

    LABELS.sort()

    #Creating plots and statistics (if ROOT LOADED)
    if isRoot:
        outFile = ROOT.TFile(OUTFILE,"RECREATE")

        single_H = {}
        sampleName=OUTFILE.replace(".root","")

        ### ERRORS HAVE A DIFFERENT TREATMENT
        single_H["Error"] = {}
        label="Error"
        single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName,sampleName,200,0,1)
        for err in SUMMARY[label].keys():
            single_H[label].Fill(err, float(SUMMARY[label][err])) #/float(SUMMARY["Total"]) )
            
        if float(SUMMARY["Success"])==0:
            print LOGDIR," has no successful job"
            outFile.Write()
            outFile.Close()
            exit(0)

        single_Graph = {}
        for label in LABELS:
            if label=="Error": continue
            #if label.find("TimeEvent")!=-1: continue ##these are plotted separately
            #if label.find("TimeModule")!=-1: continue ##these are plotted separately

            single_H[label] = {}
            binEdges = setBinEdges(job_output,label) 
            single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName, sampleName, binEdges['bins'], binEdges['lowerBin'], binEdges['upperBin'])
            single_H[label].StatOverflows(ROOT.kTRUE)
            
            if not SINGLE_DIR_DATA.has_key(label):
                print "[WARNING]: "+label+" quantity not available"
                continue

            if isinstance( SINGLE_DIR_DATA[label] , float):
                single_H[label].Fill( SINGLE_DIR_DATA[label] )
            elif isinstance( SINGLE_DIR_DATA[label] , str):
                single_H[label].Fill( float(entry) )
            elif isinstance( SINGLE_DIR_DATA[label] , list):
                isListOfList = False
                for entry in SINGLE_DIR_DATA[label]:
                    if isinstance( entry , float) or isinstance( entry , str):  
                        single_H[label].Fill( float(entry) )
                    elif isinstance( entry , list): 
                        isListOfList = True
                        break
                    else:
                        print "[WARNING]: I don't know how to process this info: "+label
                if isListOfList:
                    xlabel=""
                    if label.find("dstat")!=-1:       xlabel = "WN_dstat-Seconds"
                    elif label.find("vmstat")!=-1:    xlabel = "WN_vmstat-Seconds"
                    elif label.find("TimeEvent")!=-1: xlabel = "TimeEvent_record"
                    elif label.find("net")!=-1:       xlabel = 'WN_net-Seconds'
                    else:
                        print "[WARNING] please provide an x quantity for "+label+". Not plotting."
                        continue
                    
                    ### which plot you want also divided by single jobs (overlapped)?
                    saveSingleJobGraphs = False
                    rebin = 10
                    if label.find("Event")!=-1: rebin=1
                    if label.find("net")!=-1: saveSingleJobGraphs=True
                    fillGraph(label, sampleName, single_Graph, single_H, SINGLE_DIR_DATA, xlabel,rebin,saveSingleJobGraphs )
            else:
                print "[WARNING]: not a float, not an array, not a string: label="+label
    
            nBins = single_H[label].GetNbinsX()

        prod_H2 = {}
        ### Producers statistics
        if "ProducerTiming" in acceptedSummaries:
            for label in LABELS:
                if label.find("TimeModule")==-1 : continue ##these are plotted separately
                if label.find("event")!=-1 or label.find("record")!=-1: continue
                
                prod_H2[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName, sampleName, 100, 0, 1)
                prod_H2[label].StatOverflows(ROOT.kTRUE)
                
                if not SINGLE_DIR_DATA.has_key(label):
                    print "[WARNING]: "+label+" quantity not available"
                    continue
                i=0
                for entry in SINGLE_DIR_DATA[label]["TOTAL"]:
                    if i==0 and discardFirstEvent_Producer: 
                        i=1
                        continue
                    prod_H2[label].Fill(label[len("TimeModule-"):], entry)

        

        outFile.Write()
        outFile.Close()


if __name__ == '__main__':
    getJobStatistics(LOGDIR,OUTFILE)
