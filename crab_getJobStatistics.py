#!/usr/bin/python
#################################################################
# crab_getJobStatistics.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_getJobStatistics.py,v 1.8 2009/12/16 14:50:03 leo Exp $
#################################################################


#
# put options for xml/log file names
#
# where is exit code in CMSSW xmls???
# always the same record for TimeEvent



import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
from math import sqrt
import re
from crab_utilities import *
from optparse import OptionParser

isRoot = True

try:
    import ROOT
except:
    print "ROOT cannot be loaded, running textual only"
    isRoot = False
    exit(1)



usage = ""
parser = OptionParser(usage = usage)
parser.add_option("--type",action="store", dest="TYPE",default="CRAB",
                  help="Type of the log/xml files, can be CRAB or CMSSW")


(options, args) = parser.parse_args()


if len(argv)<2:
    print "USAGE: "+argv[0]+" crab_dir <outfile>"
    exit(1)

LOGDIR = args[0]
if len(args)>1:
    OUTFILE = args[1]
else:
    OUTFILE = ""


acceptedSummaries = ['StorageTiming', "CrabTiming", "Timing"]



### Init array of quantities
LABELS = [ ]


def parseXML_Crab(myXML, mapping):
#    mapping["Success"] = False
#    mapping["Error"] = {}

    XML_file = open(myXML.strip("\n").strip(" "))
    doc = xml.dom.minidom.parse(XML_file)

    for node in doc.getElementsByTagName("Metric"):
        if not node.parentNode.attributes["Metric"].value in acceptedSummaries: continue
        if node.attributes["Name"].value=="CpuTime":
            cpuTime =  node.attributes["Value"].value.replace('"','').split(" ")
            mapping["UserTime"] = float(cpuTime[0])
            mapping["SysTime"] = float(cpuTime[1])
            mapping["CpuPercentage"] = float(cpuTime[2].strip("%"))
        else:
            try:
                value = float(node.attributes["Value"].value)
            except:
                value = node.attributes["Value"].value 
            mapping[node.attributes["Name"].value] = value #float(node.attributes["Value"].value )
        
    for node in doc.getElementsByTagName("FrameworkError"):
        mapping[node.attributes["Type"].value] = node.attributes["ExitStatus"].value

    exitCode = float(mapping["ExeExitCode"])
#    if exitCode ==0:
#        mapping["Success"] = True
#    else:    
#        if not mapping["Error"].has_key( mapping["ExeExitCode"]  ):
#            mapping["Error"][ mapping["ExeExitCode"] ]=0
#        mapping["Error"][ mapping["ExeExitCode"] ]+=1
    
    return mapping


def parseXML_CMSSW(myXML, mapping):
    mapping["Success"] = False
    mapping["Error"] = {}

    XML_file = open(myXML.strip("\n"))
    
    doc = xml.dom.minidom.parse(XML_file)
    for node in doc.getElementsByTagName("Metric"):
        perfType = node.parentNode.attributes["Metric"].value
        mapping[perfType+"_"+node.attributes["Name"].value] =  node.attributes["Value"].value 
        
    for node in doc.getElementsByTagName("counter-value"):
        perfType = node.parentNode.localName
        if perfType == "storage-timing-summary":
            subsystem =  node.attributes["subsystem"].value
            type = node.attributes["counter-name"].value
            for attr in node.attributes.keys():
                if attr== "subsystem" or  attr== "counter-name": continue
                mapping[perfType+"_"+subsystem+"-"+type+"-"+ attr] = node.attributes[attr].value
        
    for x in mapping.keys():
        print x, mapping[x]
    return mapping




def getTimingStats(logfile, mapping):
    pipe = os.popen("grep -E 'TimeEvent|Begin processing the' "+logfile)
    pipe
    record = -1
    mapping["TimeEvent_record"] = []
    mapping["TimeEvent_event"] = []
    mapping["TimeEvent_secs"] = []
    mapping["TimeEvent_cpuSecs"] = []
    mapping["TimeEvent_cpuPercentage"] = []

    for x in pipe:
        find1 =  x.find("Begin processing the")
        find2 = x.find("TimeEvent> ")
        if find1 !=-1 :
            record = float( x[len("Begin processing the"): x.find("record")-3]) ##-3 is to cut away st,nd, rd,th
        elif find2 != -1: 
            mapping["TimeEvent_record"].append(record)
            data = x[len("TimeEvent> "):].split(" ")
            mapping["TimeEvent_event"].append(float(data[0]))
            
            mapping["TimeEvent_secs"].append(float( data[2]))
            mapping["TimeEvent_cpuSecs"].append(float(data[3]))
            mapping["TimeEvent_cpuPercentage"].append(100*float(data[3])/float(data[2]) )
            

    #print mapping        

    



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



def parseDir_Crab(logdir, subdir, totalFiles):
    job_output = {}
    lognum =  subdir[subdir.find("res/CMSSW"):].split("_")[1].split(".")[0]
    log_file =  logdir+"CMSSW_"+str(lognum)+".stdout"

    if float(os.stat( log_file).st_size)<1:
        print "[ERROR] "+log_file+" EMPTY!"
        return 1 #continue
    else:
        parseCrab_stdOut( log_file,job_output)
        totalFiles += 1

        if job_output["Success"]:
            getTimingStats(log_file, job_output)

            xml_file = logdir+"crab_fjr_"+str(lognum)+".xml"
            if not os.path.isfile( xml_file ):
                print "[ERROR] "+xml_file+" NOT FOUND!"
                return 1
            else:
                if float(os.stat( xml_file ).st_size)<1:
                    print "[ERROR] "+xml_file+" EMPTY!"
                    return 1
                else:
                    parseXML_Crab( xml_file,job_output)
                    totalFiles += 1
    
    return job_output


def parseDir_CMSSW(logname, totalFiles):
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
        parseXML_CMSSW( xmlFile,job_output)
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
    elif label.find("Time") != -1 and label.find("TimeEvent")==-1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 40000. ### 40k secs=11h
        binEdges['bins'] = 4000 ### 10 secs bin 
    elif label.find("num") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 1000000. 
        binEdges['bins'] = 100000 
    elif label.find("Error") != -1:
        binEdges['lowerBin'] = 0.0
        binEdges['upperBin'] = 1. 
        binEdges['bins'] = 1   
    elif label.find("TimeEvent") != -1:
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
    MEAN_COMP = {} ### stores stat info

    firstDir = True
    tempI=0

    
    #Begin dir analysis
    if os.path.isdir(LOGDIR)==False and os.path.islink(LOGDIR)==False:
        print LOGDIR
        print "[ERROR] Directory not Valid"
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
    if options.TYPE == "CRAB": LOGS = os.popen("ls "+logdir+"*.stdout")
    elif  options.TYPE == "CMSSW": LOGS = os.popen("ls "+LOGDIR+"/*.xml")
    else: 
        print "[ERROR No valit log/xml file given]"
        exit(1)
    for x in LOGS:
        #Parse crabDir
        x = x.strip('\n')
        if options.TYPE == "CRAB": rValue = parseDir_Crab(logdir, x, totalFiles)
        elif  options.TYPE == "CMSSW": rValue = parseDir_CMSSW( x, totalFiles)
        
        if rValue!=1: job_output = rValue
        else: continue
        #end Parse crabDir

        spName = splitDirName(LOGDIR)
        ###UserQuantities
        totalMB = 0
        totalReadTime = 0
        #for quant in job_output.keys():
        #    if len(quant.split('-'))==4 and quant.find('readv-total-megabytes')!=-1:
        #        print quant
        #        totalMB += float(job_output[quant])
        #    if len(quant.split('-'))==4 and quant.find('readv-total-msecs')!=-1:
        #        totalReadTime += float(job_output[quant])

        if job_output.has_key('tstoragefile-read-total-megabytes'): totalMB += float(job_output['tstoragefile-read-total-megabytes'])
        if job_output.has_key('tstoragefile-readv-total-megabytes'): totalMB += float(job_output['tstoragefile-readv-total-megabytes'])

        job_output['User_ReadkBEvt'] = 1024*totalMB/float(spName['EventsJob'])
        
        #if job_output.has_key('tstoragefile-read-total-msecs'):
        #    totalReadTime += float(job_output['tstoragefile-read-total-msecs'])
        #    job_output['User_Wall-Read_CpuPercentage'] = 100.*( float(job_output['ExeTime']) - totalReadTime/1000.)/float(job_output['ExeTime'])


        totalFiles+=1
        computeErrorStat(job_output, SUMMARY)

        #begin label cycle
        for label in job_output.keys():
            #print label
            ### checks for float values
            
            #if label.find("TimeEvent")==-1: 
            #    try: 
            #        float( job_output[label])
            #        if not label in LABELS: LABELS.append(label)
            #    except: 
            #        continue

            #SINGLE_DIR_DATA[label] = job_output[label]
            #if label =="CpuPercentage": print  SINGLE_DIR_DATA["CpuPercentage"]
            #begin job output if
                #if job_output.has_key(label):
                #if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                #SINGLE_DIR_DATA[label].append(float(job_output[label]))
                
            if isinstance( job_output[label] , float):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                SINGLE_DIR_DATA[label].append( job_output[label] )
            elif  isinstance( job_output[label] , int):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                SINGLE_DIR_DATA[label].append( float(job_output[label]) )
            elif  isinstance( job_output[label] , list):
                if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
                SINGLE_DIR_DATA[label].append( job_output[label])
            else:
                continue
   
            if not label in LABELS:
                #print label
                if not label in ['TimeEvent_record','TimeEvent_run','TimeEvent_event']:
                    LABELS.append(label)
            #try: 
            #    float( job_output[label])
            #    if not label in LABELS: LABELS.append(label)
            #except: 
            #    continue

            #if not MEAN_COMP.has_key(label): MEAN_COMP[label] = {"N":0,"X":0,"X2":0}
            #MEAN_COMP[label]["N"]+= 1
            #MEAN_COMP[label]["X"]+= float(job_output[label])
            #MEAN_COMP[label]["X2"]+= float(job_output[label])*float(job_output[label])

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
            if label.find("TimeEvent")!=-1: continue ##these are plotted separately
            single_H[label] = {}
            binEdges = setBinEdges(job_output,label) 
            single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName, sampleName, binEdges['bins'], binEdges['lowerBin'], binEdges['upperBin'])
            single_H[label].StatOverflows(ROOT.kTRUE)
            
            if not SINGLE_DIR_DATA.has_key(label):
                print "[WARNING]: "+label+" quantity not available"
                continue

            if isinstance( SINGLE_DIR_DATA[label] , float):
                single_H[label].Fill( SINGLE_DIR_DATA[label] )
            else:
                for entry in SINGLE_DIR_DATA[label]:
                    single_H[label].Fill( float(entry) )

            #if label == "tstoragefile-read-total-msecs":
            nBins = single_H[label].GetNbinsX()
            single_H[label].SetBinContent( nBins , single_H[label].GetBinContent( nBins )+
                                                        single_H[label].GetBinContent( nBins+1 )) 
        single_Graph = {}
        for label in ['TimeEvent_secs','TimeEvent_cpuSecs','TimeEvent_cpuPercentage']:
            #print label
            if label.find("TimeEvent")==-1: continue
            if label.find("record")!=-1 or label.find("event")!=-1 : continue
            #single_H[label] = {}
            #binEdges = setBinEdges(job_output,label) 
            #single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName, sampleName, binEdges['bins'], binEdges['lowerBin'], binEdges['upperBin'])
            #single_H[label].StatOverflows(ROOT.kTRUE)
            
            single_Graph[label] = ROOT.TGraph()
            
            if not SINGLE_DIR_DATA.has_key(label):
                print "[WARNING]: "+label+" quantity not available"
                continue
            nIter = len( SINGLE_DIR_DATA[label] )
            i=0
           
            while i<nIter: #for entry in SINGLE_DIR_DATA[label]:
                j = 0
                while j< len( SINGLE_DIR_DATA[label][i] ):
                    #print label, SINGLE_DIR_DATA["TimeEvent_record"][i][j], SINGLE_DIR_DATA[label][i][j]
                    #single_H[label].Fill( str(SINGLE_DIR_DATA["TimeEvent_record"][i][j]), SINGLE_DIR_DATA[label][i][j])
                    single_Graph[label].SetPoint(j, SINGLE_DIR_DATA["TimeEvent_record"][i][j], SINGLE_DIR_DATA[label][i][j])
                    j += 1
                i += 1
                
            outFile.WriteTObject( single_Graph[label] ,'QUANT'+label+'-SAMPLE'+sampleName);

        outFile.Write()
        outFile.Close()

        



if __name__ == '__main__':
    getJobStatistics(LOGDIR,OUTFILE)
