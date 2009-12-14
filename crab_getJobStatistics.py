#!/usr/bin/python
#################################################################
# crab_getJobStatistics.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_getJobStatistics.py,v 1.4 2009/11/27 10:50:28 leo Exp $
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

#myFilter=""
#if len(argv)>2:
#myFilter = argv[1]

####### USE MAX RANGE FOR HISTOS

LABELS = [#'ExeTime',
          'CrabUserCpuTime',
          'CrabSysCpuTime',
          'CrabCpuPercentage',
          'CrabWrapperTime'
#          'User_Wall-Read_OverWall',
#          'User_ReadMBJob'
          #'CrabStageoutTime'
          ]


def parseXML(myXML, mapping):
    XML_file = open(myXML.strip("\n"))
    
    doc = xml.dom.minidom.parse(XML_file)
 
    for node in doc.getElementsByTagName("Metric"):
        mapping[node.attributes["Name"].value] = node.attributes["Value"].value 
        
    return mapping


def parseStdOut(log_file,crab_stdout):
    out =  os.popen("grep ExitCode "+log_file)
    crab_stdout["Success"] = False
    crab_stdout["Error"] = {}
 
    for x in out:
        metric= x.strip("\n").split("=")[1].strip("%")
        metric = float(metric)
        if metric == 0 or metric==60302:
            crab_stdout["Success"] = True
            break
        else:
            if not crab_stdout["Error"].has_key(metric):
                crab_stdout["Error"][metric]=0
            crab_stdout["Error"][metric]+=1
            
    if not  crab_stdout["Success"]:
        return crab_stdout

    for label in LABELS:
        out = os.popen("grep "+label+" "+log_file)
        for x in out:
            x_split = x.split("=")
            if len(x_split)<2: continue
            metric= x_split[1].strip("\n").strip("%")
            if metric == "NULL":
                metric=0
            else:
                metric = float(metric)
                  
            crab_stdout[label] = metric

    return crab_stdout



def parseCrabDir(logdir, subdir, totalFiles):
    job_output = {}
    lognum =  subdir[subdir.find("res/CMSSW"):].split("_")[1].split(".")[0]
    log_file =  logdir+"CMSSW_"+str(lognum)+".stdout"
    if float(os.stat( log_file).st_size)<1:
        print "[ERROR] "+log_file+" EMPTY!"
        return 1 #continue
    else:
        parseStdOut( log_file,job_output)
        totalFiles += 1

    if job_output["Success"]:
        xml_file = logdir+"crab_fjr_"+str(lognum)+".xml"
        if not os.path.isfile( xml_file ):
            print "[ERROR] "+xml_file+" NOT FOUND!"
        else:
            if float(os.stat( xml_file ).st_size)<1:
                print "[ERROR] "+xml_file+" EMPTY!"
            else:
                parseXML( xml_file,job_output)
    return job_output



def computeStat(MEAN_COMP):
    if MEAN_COMP["N"]==0:
        mean = 0
        variance = 0
        return mean, variance
        
    mean = MEAN_COMP["X"]/MEAN_COMP["N"]
    variance = MEAN_COMP["X2"]/MEAN_COMP["N"] - mean*mean
    if variance >0:
        variance = sqrt(variance)
    else:
        variance = 0
    return mean, variance



def printWikiStat(DIR_SUMMARY, posFilter, negFilter):
    perc=0
    header = "| |"
    tasks = DIR_SUMMARY.keys()
    tasks.sort()
    for dir in tasks:
        header += " *"+dir.split("-")[0]+"-"+dir.split("-")[1]+" "+dir.split("-")[-1][:8]+"* |"

    print header
    line = "| *Success*|"

    for dir in tasks:
        total = DIR_SUMMARY[dir]["Success"] + DIR_SUMMARY[dir]["Failures"]
        if total==0:
            perc = 0
        else:
            perc = 100*DIR_SUMMARY[dir]["Success"]/total
            line += "%.1f%% (%.0f / %.0f) |" %(perc,DIR_SUMMARY[dir]["Success"], total)
    print line

    ### [dir][label] not useful here...
    pError = {}
    line=""
    for dir in tasks:
        for err in DIR_SUMMARY[dir]["Error"].keys():
            if not pError.has_key(err):
                pError[err] = {}
            pError[err][dir] = DIR_SUMMARY[dir]["Error"][err]


    for err in pError.keys():
        line = "| *Error "+err+"* |"
        for dir in tasks:
            if not pError[err].has_key(dir): line += " // | "
            else:
                line += "%s%%  |" %( pError[err][dir])
        print line

    orderedLabels = {}
    myPosFilter = re.compile(posFilter)
    myNegFilter = re.compile(negFilter)

    for label in LABELS:
        if myPosFilter.search(label) == None or not myNegFilter.search(label) == None : continue

        lwork = label.split("-")
        if len(lwork)>2:
            tech = lwork[0]
            meas = lwork[1]
            quant = lwork[-1]
            char = ""
            for x in lwork[2:-1]:
                char = x+"-"
            char.strip("-")
            
            if not orderedLabels.has_key(meas):
                orderedLabels[meas] = {}
            if not orderedLabels[meas].has_key(quant):
                orderedLabels[meas][quant] = {}
            if not orderedLabels[meas][quant].has_key(char):
                orderedLabels[meas][quant][char] = []

            orderedLabels[meas][quant][char].append(label)
        else:
            if label != "ExeExitCode" and label!="Success" and label!="Failures":
                line = ""
                line += "| *"+label+"*|"
                for dir in tasks:
                    if DIR_SUMMARY[dir].has_key(label):
                        line += " %.2f +- %.2f |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                    else:
                        line += " // |"
            print line

    line =""
    orderedLabels2 = orderedLabels.keys()
    orderedLabels2.sort()
    for meas in orderedLabels2:
        if not meas in ["read","readv","seek","open"]: continue
        print "| *"+meas.upper()+"*||||||"
        for quant in  orderedLabels[meas].keys():
            for char in  orderedLabels[meas][quant].keys():
                for label in  orderedLabels[meas][quant][char]:
                    if label != "ExeExitCode" and label!="Success" and label!="Failures":
                        line = ""
                        line += "| *"+label+"*|"
                        for dir in tasks:
                            if DIR_SUMMARY[dir].has_key(label):
                                line += " %.2f +- %.2f |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                            else:
                                line += " // |"
                        print line



    

def computeTotalStat(DIR_SUMMARY):
    TOTAL_STAT = {}
    for label in LABELS:
        if label != "ExeExitCode":
            TOTAL_STAT[label] = [0,0]

    for label in TOTAL_STAT.keys():
        for dir in DIR_SUMMARY.keys():
            sigma2 = DIR_SUMMARY[dir][label][1]*DIR_SUMMARY[dir][label][1]
            if sigma2 != 0:
                TOTAL_STAT[label][0] += DIR_SUMMARY[dir][label][0]/sigma2
                TOTAL_STAT[label][1] += 1/sigma2

        if TOTAL_STAT[label][1]!=0:
            TOTAL_STAT[label][0] /= TOTAL_STAT[label][1]
            TOTAL_STAT[label][1] = sqrt(1/TOTAL_STAT[label][1])

    TOTAL_STAT["Success"]  = 0
    TOTAL_STAT["Failures"] = 0
    for dir in DIR_SUMMARY.keys():
        TOTAL_STAT["Success"] += DIR_SUMMARY[dir]["Success"]
        TOTAL_STAT["Failures"] += DIR_SUMMARY[dir]["Failures"]
        
    return TOTAL_STAT





def divideCanvas(canvas, numberOfHisto):
    if numberOfHisto <=3:
        canvas.Divide(numberOfHisto)
    elif numberOfHisto == 4:
        canvas.Divide(2,2)
    elif numberOfHisto == 8:
        canvas.Divide(4,2)
    elif  numberOfHisto >4 and numberOfHisto < 10:
        canvas.Divide(3,3)
    elif  numberOfHisto >9 and numberOfHisto < 13:
        canvas.Divide(3,4)



#def splitDirName(dirName):
#    output = {}
#    ###The split("/")[-1] get rid of mother directories, eg mydir/crab_dir
#    splittedDirName = dirName.split("/")[-1].split("-")
#    output['Site'] = splittedDirName[0]
#    output['Cfg'] = splittedDirName[1]
#    output['Dataset'] = splittedDirName[2]
#    output['EventsJob'] = splittedDirName[3]
#    output['Sw'] = splittedDirName[4]
#    output['Date'] = splittedDirName[5]
    
#    return output

    
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
    #DIRS = os.listdir(argv[1])

#    binEdges = {'low':{},'high':{}}
    firstDir = True
    tempI=0
 #   while tempI!=1:
 #       tempI=1
    
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
            job_output['User_Wall-Read_CpuPercentage'] = 100.*( float(job_output['CrabWrapperTime']) - totalReadTime/1000.)/float(job_output['CrabWrapperTime'])


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
#    for err in SUMMARY["Error"].keys():
#        SUMMARY["Error"][err] = #round(100*float(SUMMARY["Error"][err])/float(totalFiles), 1)

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


        #single_H = {}
        #sampleName=OUTFILE.strip(".root")
        
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

#    for dir in DIR_SUMMARY:
#        print dir

#    printWikiStat(DIR_SUMMARY, "", ".*(min|max).*")




if __name__ == '__main__':
    getJobStatistics(LOGDIR,OUTFILE)
