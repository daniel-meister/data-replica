#!/usr/bin/python
#################################################################
# cpt_getJobInfo.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: cpt_getJobInfo.py, v 1.9 2010/01/05 15:54:57 leo Exp $
#################################################################


# deleted overflow bin addition to last bin: it spoils stats





import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
from math import sqrt
import re
from cpt_utilities import *
from optparse import OptionParser

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
                  help="Type of the log/xml files, can be CRAB or CMSSW")
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
    return mapping


def parseXML_CMSSW(myXML, mapping):
    mapping["Success"] = True ###WorkAround
    mapping["Error"] = {}

    XML_file = open(myXML.strip("\n"))
    
    doc = xml.dom.minidom.parse(XML_file)
    for node in doc.getElementsByTagName("FrameworkError"):
        metric = node.attributes["ExitStatus"].value
        
        if not mapping["Error"].has_key(metric):
            mapping["Error"][metric]=0
        mapping["Error"][metric]+=1
        mapping["Success"] = False

    for node in doc.getElementsByTagName("Metric"):
        if not node.parentNode.attributes["Metric"].value in acceptedSummaries: continue
        perfType = node.parentNode.attributes["Metric"].value
        try:
            value = float(node.attributes["Value"].value)
        except:
            value = node.attributes["Value"].value
        mapping[node.attributes["Name"].value] = value
        
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
        
    return mapping




def getTimingStats(logfile, mapping):
    pipe = os.popen("grep -E 'TimeEvent|Begin processing the|TimeModule' "+logfile)
    record = -1
    mapping["TimeEvent_record"] = []
    mapping["TimeEvent_event"] = []
    mapping["TimeEvent_secs"] = []
    mapping["TimeEvent_cpuSecs"] = []
    mapping["TimeEvent_cpuPercentage"] = []
    mapping["TimeEvent_eleIsoDepositTk-CandIsoDepositProducer_secs"] = []

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
            
            mapping["TimeEvent_secs"].append(float( data[2]))
            mapping["TimeEvent_cpuSecs"].append(float(data[3]))
            mapping["TimeEvent_cpuPercentage"].append(100*float(data[3])/float(data[2]) )
        elif find3 !=-1:
            if x.find("eleIsoDepositTk CandIsoDepositProducer")!=-1:
                value = x.split(" ")[-1]
                mapping["TimeEvent_eleIsoDepositTk-CandIsoDepositProducer_secs"].append(float(value))
                
    pipe.close()

    #print mapping        


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
            job_output['UserTime'] = float(translateTime(timing[0]))
            job_output['SysTime'] = float(translateTime(timing[1]))
            job_output['ExeTime'] = float(translateTime(timing[2]))
            job_output['CpuPercentage'] = float(timing[3])

    return job_output


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



def parseDir_Crab(logdir, subdir):
    job_output = {}
    lognum =  subdir[subdir.find("res/CMSSW"):].split("_")[1].split(".")[0]
    log_file =  logdir+"CMSSW_"+str(lognum)+".stdout"

    if float(os.stat( log_file).st_size)<1:
        print "[ERROR] "+log_file+" EMPTY!"
        return 1 #continue
    else:
        parseCrab_stdOut( log_file,job_output)
        #totalFiles += 1

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
                    #totalFiles += 1 ???? double?
    
    return job_output


def parseDir_CMSSW(logname):
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
        if job_output["Success"]:
            parseCMSSW_stdOut(logFile, job_output)
            getTimingStats(logFile, job_output)
        #totalFiles += 1
    
    #print job_output
    return job_output

    
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
        
    print "OutFile:",OUTFILE
    print "Analyzing "+LOGDIR

    #totalFiles = 0
    ###Parsing Files
    logdir = LOGDIR+"/res/"
    ### use stdout or xml for both?
    if options.TYPE == "CRAB": LOGS = os.popen("ls "+logdir+"*.stdout")
    elif  options.TYPE == "CMSSW": LOGS = os.popen("ls "+LOGDIR+"/*.xml")
    else: 
        print "[ERROR No valit log/xml file given]"
        exit(1)
    for x in LOGS:
        #Parse crabDir
        x = x.strip('\n')
        if options.TYPE == "CRAB": rValue = parseDir_Crab(logdir, x)
        elif  options.TYPE == "CMSSW": rValue = parseDir_CMSSW( x)
        
        if rValue!=1: job_output = rValue
        else: continue
        #end Parse crabDir

        ###UserQuantities
        totalMB = 0
        totalReadTime = 0
   
        if job_output.has_key('tstoragefile-read-total-megabytes'): totalMB += float(job_output['tstoragefile-read-total-megabytes'])
        if job_output.has_key('tstoragefile-readv-total-megabytes'): totalMB += float(job_output['tstoragefile-readv-total-megabytes'])

        if isinstance(spDirName, str)==False:
            events = spDirName['EventsJob']
            if spDirName['EventsJob'][-1]=='k': events =  spDirName['EventsJob'][:-1]+'000'
            job_output['User_ReadkBEvt'] = 1024*totalMB/float(events)
        
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
            else:
                continue
   
            #if not options.noAutoBin and isinstance( job_output[label] , float):
            #    computeBinEdges(label,samplesBinEdges,  job_output[label] )
      
            if not label in LABELS:
                if not label in ['TimeEvent_record','TimeEvent_run','TimeEvent_event']:
                    LABELS.append(label)
        #end label cycle
        
        if job_output["Success"]==True: SUMMARY["Success"] +=1
        else: SUMMARY["Failures"] +=1
        
        
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
 
            nBins = single_H[label].GetNbinsX()
#            single_H[label].SetBinContent( nBins-1 , single_H[label].GetBinContent( nBins )+0)
#                                                        single_H[label].GetBinContent( nBins-1 )) 
        single_Graph = {}
        for label in ['TimeEvent_secs','TimeEvent_cpuSecs','TimeEvent_cpuPercentage','TimeEvent_eleIsoDepositTk-CandIsoDepositProducer_secs']:
            #print label
            if label.find("TimeEvent")==-1: continue
            if label.find("record")!=-1 or label.find("event")!=-1 : continue
            #single_H[label] = {}
            #binEdges = setBinEdges(job_output,label) 
            #single_H[label] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+sampleName, sampleName, binEdges['bins'], binEdges['lowerBin'], binEdges['upperBin'])
            #single_H[label].StatOverflows(ROOT.kTRUE)
            
            single_Graph[label] = ROOT.TGraphAsymmErrors()
            
            if not SINGLE_DIR_DATA.has_key(label):
                print "[WARNING]: "+label+" quantity not available"
                continue
            nIter = len( SINGLE_DIR_DATA[label] )
            i=0
           
            X = {}
            while i<nIter: #for entry in SINGLE_DIR_DATA[label]:
                j = 0
                
                while j< len( SINGLE_DIR_DATA[label][i] ):
                    record = str(SINGLE_DIR_DATA["TimeEvent_record"][i][j])
                    if not X.has_key(record): X[record] = [] 
                    X[record].append( float(SINGLE_DIR_DATA[label][i][j]) )
                    j += 1
                i += 1
            
            sortedKeys = X.keys()
            sortedKeys.sort()
            j=0
            for record in sortedKeys:
                if float(record)>MAX_GRAPH_X: continue
                mean, sigma = computeStat(X[record])
                single_Graph[label].SetPoint(j, float(record), mean)
                single_Graph[label].SetPointError(j, 0, 0 , sigma, sigma )
                j+=1

            single_Graph[label].SetName( 'QUANT'+label+'-SAMPLE'+sampleName )
            single_Graph[label].Write( 'QUANT'+label+'-SAMPLE'+sampleName);
           
        outFile.Write()
        outFile.Close()

        



if __name__ == '__main__':
    getJobStatistics(LOGDIR,OUTFILE)
