#!/usr/bin/python


import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
from math import sqrt

isRoot = True

try:
    import ROOT
except:
    print "ROOT cannot be loaded, running textual only"
    isRoot = False

if len(argv)<2:
    print "USAGE: "+argv[0]+" dir_of_crab_dirs <outfile.root>"
    exit(1)

if len(argv)==3:
    OUTFILE = argv[2]
else:
    OUTFILE = "results.root"

####### USE MAX RANGE FOR HISTOS

LABELS = ['ExeTime',
          'CrabUserCpuTime',
          'CrabSysCpuTime',
          'CrabCpuPercentage',
          'CrabWrapperTime',
          'CrabStageoutTime']
#          'tstoragefile-read-max-msecs',
#          'tstoragefile-read-actual-total-msecs',
#          'tstoragefile-read-total-megabytes',
#          'tstoragefile-write-max-msecs',
#          'tstoragefile-write-actual-total-msecs',
#          'tstoragefile-write-total-megabytes']

#LABELS = []

def parseXML(myXML, mapping):
    XML_file = open(myXML.strip("\n"))
    
    doc = xml.dom.minidom.parse(XML_file)
 
    for node in doc.getElementsByTagName("Metric"):
        mapping[node.attributes["Name"].value] = node.attributes["Value"].value 
        
    return mapping


def parseStdOut(log_file,crab_stdout):
    out =  os.popen("grep ExeExitCode "+log_file)
    crab_stdout["Success"] = False
    for x in out:
        metric= x.strip("\n").split("=")[1].strip("%")
        metric = float(metric)
        if metric == 0:
            crab_stdout["Success"] = True
            
    if not crab_stdout["Success"]:
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


def printStat(DIR_SUMMARY):
    perc=0
    for dir in DIR_SUMMARY.keys():
        print "\n----- TASK ",dir        
        print DIR_SUMMARY[dir]["Success"] , DIR_SUMMARY[dir]["Failures"]
        total = DIR_SUMMARY[dir]["Success"] + DIR_SUMMARY[dir]["Failures"]
        if total==0:
            perc = 0
        else:
            perc = 100*DIR_SUMMARY[dir]["Success"]/total
        print "Success rate: %.0f over %.0f (%.1f %%)" %(DIR_SUMMARY[dir]["Success"], total, perc)
        for label in LABELS:
            if label != "ExeExitCode" and label !='Success' and label!="Failures":
                if DIR_SUMMARY[dir].has_key(label):
                    print label+": %.2f +- %.2f" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                
#    TOTAL = computeTotalStat(DIR_SUMMARY)
#    print "\n----- TOTAL "
#    total = TOTAL["Success"] + TOTAL["Failures"]
#    if total==0:
#        perc = 0
#    else:
#        perc = 100*TOTAL["Success"]/total
#    print "Success rate: %.0f over %.0f (%.1f %%)" %(TOTAL["Success"], total, perc)
#    for label in LABELS:
#        if label != "ExeExitCode":
#            print label+": %.2f +- %.2f" %(TOTAL[label][0], TOTAL[label][1])


def printWikiStat(DIR_SUMMARY):
    perc=0
    header = "| |"
    tasks = DIR_SUMMARY.keys()
    tasks.sort()
    for dir in tasks:
        header += " *"+dir+"* |"

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

    line =""
    for label in LABELS:
#        if not DIR_SUMMARY[dir].has_key(label):
#            continue
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
#    elif numberOfHisto > 4 and numberOfHisto < 7:
#        canvas.Divide(3, 3)
    elif numberOfHisto == 8:
        canvas.Divide(4,2)
    elif  numberOfHisto >4 and numberOfHisto < 10:
        canvas.Divide(3,3)
    elif  numberOfHisto >9 and numberOfHisto < 13:
        canvas.Divide(3,4)







DIR_SUMMARY = {}
SUMMARY = {}

SINGLE_DIR_DATA = {}

DIRS = os.listdir(argv[1])


#for x in LABELS:
#    SINGLE_DIR_DATA[x] = {}
#    for dir in DIRS:
#        SINGLE_DIR_DATA[x][dir] = []


binEdges = {'low':{},'high':{}}
for dir in DIRS:

    SUMMARY = {"Success":0, "Failures":0}
    MEAN_COMP = {}

    if os.path.isdir(argv[1]+"/"+dir) == True:

        print "Analyzing "+dir
        #Parsing Files
        logdir = argv[1]+"/"+dir+"/res/"
        LOGS = os.popen("ls "+logdir+"*.stdout")
        for x in LOGS:
            job_output = {}
            lognum =  x[x.find("res/CMSSW"):].split("_")[1].split(".")[0]
            if float(os.stat( logdir+"CMSSW_"+str(lognum)+".stdout").st_size)<1:
                print "[ERROR] "+logdir+"CMSSW_"+str(lognum)+".stdout EMPTY!"
                continue
            else:
                parseStdOut( logdir+"CMSSW_"+str(lognum)+".stdout",job_output)

            if not job_output["Success"]:
                continue

            xml_file = logdir+"crab_fjr_"+str(lognum)+".xml"
            if not os.path.isfile( xml_file ):
                print "[ERROR] "+xml_file+" NOT FOUND!"
                #continue
            else:
                #print lognum
                if float(os.stat( xml_file ).st_size)<1:
                    print "[ERROR] "+xml_file+" EMPTY!"
                    #continue
                else:
                    parseXML( xml_file,job_output)

            #Computing statistics
            for label in job_output.keys():
                try:
                    float( job_output[label])
                    if not label in LABELS: 
                        LABELS.append(label)
                except:
                    continue

                if not SUMMARY.has_key(label): SUMMARY[label] = 0
                if not MEAN_COMP.has_key(label): MEAN_COMP[label] = {"N":0,"X":0,"X2":0}

                if not binEdges['low'].has_key(label):
                    binEdges['low'][label] = 9999999
                    binEdges['high'][label] = 0
                    
                if job_output.has_key(label):
                    value =  float(job_output[label])
                    if value <  binEdges['low'][label]:
                         binEdges['low'][label] = value
                    if value >  binEdges['high'][label]:
                         binEdges['high'][label] = value
                    
                    if not SINGLE_DIR_DATA.has_key(label):
                        SINGLE_DIR_DATA[label] = {}
                    if not SINGLE_DIR_DATA[label].has_key(dir):
                        SINGLE_DIR_DATA[label][dir] = []

                         
                    SINGLE_DIR_DATA[label][dir].append(float(job_output[label]))
                    MEAN_COMP[label]["N"]+= 1
                    MEAN_COMP[label]["X"]+= float(job_output[label])
                    MEAN_COMP[label]["X2"]+= float(job_output[label])*float(job_output[label])

            #print logdir+"CMSSW_"+str(lognum)+".stdout"
            if job_output["Success"]==True:
                SUMMARY["Success"] +=1
            else:
                SUMMARY["Failures"] +=1

        for label in LABELS:
            if label== "Success" or label == "Failures": continue
            if not MEAN_COMP.has_key(label): continue
            SUMMARY[label] = computeStat(MEAN_COMP[label])
        else:
            SUMMARY[label] = -1,-1
        DIR_SUMMARY[dir] = SUMMARY

LABELS.sort()
printStat(DIR_SUMMARY)
printWikiStat(DIR_SUMMARY)



#Creating plots
if isRoot:
    outFile = ROOT.TFile(OUTFILE,"RECREATE")

    DIR_SUMMARY_keys = DIR_SUMMARY.keys()
    DIR_SUMMARY_keys.sort()

    DIRS = os.listdir(argv[1])
    myCanvas = {}
    myH = {}
    for label in LABELS:
        if label== "Success" or label == "Failures": continue
#        myCanvas[label] = ROOT.TCanvas(label,label,200,10,700,500)
        myH[label] = ROOT.TH1F(label,label,len(DIR_SUMMARY_keys ),0,1)
        bin=1
        for dir in DIR_SUMMARY_keys:
            if not DIR_SUMMARY[dir].has_key(label): continue
            myH[label].Fill(dir,DIR_SUMMARY[dir][label][0])
            myH[label].SetBinError(bin,DIR_SUMMARY[dir][label][1])
            bin+=1
            
#        myH[label].Draw()
        #myCanvas[label].Update()
#        myCanvas[label].Write()
        #myCanvas[label].SaveAs(label+".png")
        

    single_Canvas = {}
    single_H = {}
    for label in LABELS:
#        single_Canvas[label] = ROOT.TCanvas("single_"+label,"single_"+label,200,10,700,500)

#        numberOfHisto = len(DIR_SUMMARY_keys)
#        print numberOfHisto
#        divideCanvas(single_Canvas[label], numberOfHisto)

#        single_Canvas[label].Divide(4,2)

        single_H[label] = {}
#        histoN = 1
        for dir in DIR_SUMMARY_keys:
#            print label, dir, binEdges['low'][label], binEdges['high'][label]
            if not SINGLE_DIR_DATA[label].has_key(dir): continue
            single_H[label][dir] = ROOT.TH1F('QUANT'+label+'-SAMPLE'+dir,dir,200,0.9*binEdges['low'][label],1.1*binEdges['high'][label])

            #single_H[label][dir].SetBit(ROOT.TH1F.kCanRebin)
            for entry in SINGLE_DIR_DATA[label][dir]:
                single_H[label][dir].Fill(entry)


#    for label in LABELS:
#        if label== "Success" or label == "Failures": continue

#        histoN=1
#        for dir in DIR_SUMMARY_keys:
#            single_Canvas[label].cd(histoN)
#            single_H[label][dir].Draw()
#            histoN += 1
#            single_Canvas[label].Update()

#        single_Canvas[label].Draw()
#        single_Canvas[label].Write()

        #single_Canvas[label].SaveAs("single_"+label+".png")

#    os.popen("sleep 100000")

    outFile.Write()
    outFile.Close()
#    os.popen("sleep 100000")


