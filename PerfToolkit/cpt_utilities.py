#!/usr/bin/python
#################################################################
# crab_utilities.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: cpt_utilities.py,v 1.5 2010/03/04 15:50:54 leo Exp $
#################################################################

### dynamical precision writing in printWikiStats
### first migration to a plugin structure
### added sampleTitle header to printWikiStats
### divided Date and hour in  splitDirName
### added setCPTMode

### TODO:
#### place an external flag on getHistoMaximum (for chosing norm/notNormalized)
#### sensible sorting!!!!

from sys import argv,exit
from os import popen
import re
import ROOT
from math import sqrt


def divideCanvas(canvas, numberOfHisto):
    if numberOfHisto <=3:
        canvas.Divide(numberOfHisto)
    elif numberOfHisto == 4:
        canvas.Divide(2,2)
    elif numberOfHisto == 8:
        canvas.Divide(4,2)
    elif  numberOfHisto >4 and numberOfHisto < 7:
        canvas.Divide(3,2)
    elif  numberOfHisto >4 and numberOfHisto < 10:
        canvas.Divide(3,3)   
    elif  numberOfHisto >=10 and numberOfHisto < 13:
        canvas[label].Divide(3,4)

def createCanvas(title):
    canvas = ROOT.TCanvas(title,title)
    ROOT.gPad.SetFillColor(0)
    ROOT.gPad.SetBorderSize(0)
    return canvas

def createLegend():
    legend = ROOT.TLegend(0.,1,1.,0.75)
    legend.SetTextFont(42)
    legend.SetBorderSize(0)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    return legend


def setHisto(histo, color, lineStyle,title,Xtitle, rebin):
    histo.Sumw2()
    histo.Rebin(rebin)
    histo.SetLineWidth(3)
    histo.SetStats(0000000)
    histo.SetTitle("")
    histo.StatOverflows(ROOT.kTRUE)
    histo.SetLineColor(color)
    histo.SetTitle(title)
    histo.GetXaxis().SetTitle(Xtitle)
    if lineStyle !="": histo.SetLineStyle( lineStyle ) 
#    nBins = histo.GetNbinsX()
#    histo.SetBinContent(nBins, histo.GetBinContent(nBins+1) )




def getHistos(listOfKeys, histos, graphs, sitePalette, posFilter, negFilter=""):
    for key in listOfKeys:
        obj = key.ReadObj();
        if obj.IsA().InheritsFrom("TH1") or obj.IsA().InheritsFrom("TGraph") or obj.IsA().InheritsFrom("TH2") :
            histoName = obj.GetName()
            if histoName.find("QUANT") == -1: continue
        
            QUANT = histoName[histoName.find("QUANT")+len("QUANT"): histoName.find("-SAMPLE")]
            SAMPLE = histoName[histoName.find("SAMPLE")+len("SAMPLE"):]

            if not sitePalette.has_key(SAMPLE): 
                if len(sitePalette)>0: myColor = sorted(sitePalette.values())[-1] +1 
                else: myColor=1
                sitePalette[SAMPLE] = myColor

            toPlot = False
            for f in posFilter:
                myFilter = re.compile(f)
                if not myFilter.search(QUANT) == None:
                    toPlot = True
                    break

            if negFilter!='':
                for f in negFilter:
                    myFilter = re.compile(f)
                    if not myFilter.search(QUANT) == None:
                        toPlot = False
                        break

            if not toPlot: continue
                    
            if  obj.IsA().InheritsFrom("TGraph"):
                if not graphs.has_key(QUANT):
                    graphs[QUANT] = {}
                graphs[QUANT][SAMPLE] = obj

            else:
                if not histos.has_key(QUANT):
                    histos[QUANT] = {}
                histos[QUANT][SAMPLE] = obj
            
    return SAMPLE


def getMaxHeightHisto(firstLabel, histo, histoName, maxY, quant="", goodHistoList=""):
    ###if empty, exit
    if histo.Integral() == 0: return firstLabel, maxY
    
    maxBin =  histo.GetMaximumBin()
    if histo.GetName().find("Error")==-1:
        maxValue =  histo.GetBinContent( maxBin )/ histo.Integral()
    else:
        maxValue =  histo.GetBinContent( maxBin )

    ###separated case for Error histos (first bin is not 0 bin)
    if histo.GetName().find("Error")!=-1:
        if maxValue>maxY:
            firstLabel = quant,histoName
            maxY = maxValue

    ### check if the only bin is the first one, and if given fill goodHistoList with which are not
    if not (maxBin == 1 and maxValue==1) and not (maxValue==1 and histo.GetBinLowEdge(maxBin)==0 ):
        if goodHistoList!="": goodHistoList.append(histoName)
        if maxValue>maxY:
            firstLabel = quant,histoName
            maxY = maxValue


    return firstLabel, maxY




def findPlotTogetherHisto(plotFilter, plotTogether, keys, toBePlotAlone, toBePlotTogether):
    compiledFilters = []
    for f in plotFilter:
        compiledFilters.append( re.compile(f) )
    for quant in keys:
        selected = False        
        for f in compiledFilters:
            if not f.search(quant) == None:
                selected = True
                break
        if not selected: continue
        
        together=False
        for sel in plotTogether:
            if not toBePlotTogether.has_key(sel): toBePlotTogether[sel] = []
            if quant.find(sel)!=-1 and quant.find("tstorage")==-1:
                if quant not in toBePlotTogether[sel]: toBePlotTogether[sel].append(quant)
                together = True
                break
        if not together:
            if quant not in toBePlotAlone: toBePlotAlone.append(quant)


#retrieves data from dir name. Three cases provided:
# - the dir is in the format: KEY1.LABEL1-KEY2.LABEL2-etc
# - the dir is in the format: SITE-CFG-DATASET-NEVTS-LABEL-DATE (back compatibility)
# - none of the above: the dir name is returned as a string
def splitDirName(dirName, strippedText=""):
    output = {}
    if strippedText!="" and dirName.find(strippedText)!=-1:
        dirName = dirName.replace(strippedText,"")
    splittedDirName = dirName.split("-")
    isKeyLabel = True
    for comp in splittedDirName:
        comp = comp.split(".")
        if len( comp ) <2:
            isKeyLabel = False
            output = {}
            break
        else:
            label=""
            for i in range(1, len(comp)): label += comp[i]+"_"
            if comp[0]=="Date": 
                output[comp[0]] = label[:-5]
                output["Hour"] = label[-5:-1]
            else: output[comp[0]] = label[:-1]
    ###returns dirName if not in the right format
    if len(splittedDirName)<6 and not isKeyLabel: 
        return dirName
    elif not isKeyLabel:
        output['Site'] = splittedDirName[0]
        output['Cfg'] = splittedDirName[1]
        output['Dataset'] = splittedDirName[2]
        output['EventsJob'] = splittedDirName[3]
        if output['EventsJob'][-3:] == '000': output['EventsJob'] = output['EventsJob'][:-3]+"k"
        output['Label'] = splittedDirName[4]
        output['Date'] = splittedDirName[5][0:8]
        output['Hour'] = splittedDirName[5][8:]

    return output




def computeStat(X):
    N = len( X)
    #if MEAN_COMP["N"]==0:
    if N==0:
        mean = 0
        variance = 0
        return mean, variance

    sumX2=0
    sumX = 0
    for x in X:
        sumX += x
        sumX2 += x*x
    
    mean = sumX/N #MEAN_COMP["X"]/MEAN_COMP["N"]
    variance = (sumX2/N) - mean*mean #MEAN_COMP["X2"]/MEAN_COMP["N"] - mean*mean
    if variance >0:
        variance = sqrt(variance)
    else:
        variance = 0
    return mean, variance








def printWikiStat(DIR_SUMMARY, posFilter, negFilter, legLabels, histoTitle=""):
    perc=0
    LABELS = []

    ###Creating header
    header = ""
    if histoTitle!="":
        print "|* "+ histoTitle+" *|"
    tasks = DIR_SUMMARY.keys()
    tasks.sort()
    for dir in tasks:
        header += " *"+legLabels[dir]+"* |"
        sortedKeys =  sorted(DIR_SUMMARY[dir].keys())
        for l in sortedKeys:
            if not l in LABELS: LABELS.append(l)

    print "|  |",header

    ###Success rate
    line = "| *Success*|"
    for dir in tasks:
        total = DIR_SUMMARY[dir]["Success"] + DIR_SUMMARY[dir]["Failures"]
        if total==0:
            perc = 0
            line += "%.1f%% (%.0f / %.0f) |" %(perc,DIR_SUMMARY[dir]["Success"], total)
        else:
            perc = 100*DIR_SUMMARY[dir]["Success"]/total
            line += "%.1f%% (%.0f / %.0f) |" %(perc,DIR_SUMMARY[dir]["Success"], total)
    print line

    ###Error Rate
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


    #### Actual quantities
    orderedLabels = {}
    orderedProducers = []
    myPosFilter = re.compile(posFilter)
    myNegFilter = re.compile(negFilter)

    for label in LABELS:
        if myPosFilter.search(label) == None or not myNegFilter.search(label) == None : continue

        #orderedProducers = []
        lwork = label.split("-")
        if lwork[0]=="TimeModule":
            quant = lwork[-1]
            orderedProducers.append(quant)

        elif len(lwork)>2:
            tech = lwork[0]
            meas = lwork[1]
            quant = lwork[-1]
            quant2 = label[ label.find(meas):]
            
            char = ""
            for x in lwork[2:-1]:
                char = x+"-"
            char.strip("-")
            
            if not orderedLabels.has_key(meas):
                orderedLabels[meas] = {}
            if not orderedLabels[meas].has_key(quant): orderedLabels[meas][quant] = {}
            if not orderedLabels[meas][quant].has_key(quant2): orderedLabels[meas][quant][quant2] = []

            orderedLabels[meas][quant][quant2].append(label)
        else:
            if label != "ExeExitCode" and label!="Success" and label!="Failures" and label!="Error":
                line = ""
                line += "| *"+label+"*|"
                for dir in tasks:
                    if DIR_SUMMARY[dir].has_key(label):
                        if label.find("Module")!=-1:
                            line += " %.2e +- %.2e |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                        else:
                            line += " %.2f +- %.2f |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                    else:
                        line += " // |"
                print line

    #TimeModule printing
    
    if len(orderedProducers)>0:
        line = ""
        print "| *TimeProducers*||||||"
        for producer in sorted(orderedProducers):
            line = ""
            line += "| *"+producer+"*|"
            for dir in tasks:
                if DIR_SUMMARY[dir].has_key("TimeModule-"+producer):
                    line += " %.2e +- %.2e |" %(DIR_SUMMARY[dir]["TimeModule-"+producer][0], DIR_SUMMARY[dir]["TimeModule-"+producer][1])
                else:
                    line += " // |"
            print line

    # putting tstorage entries at the first place
    for meas in sorted(orderedLabels.keys()):
        for quant in  sorted(orderedLabels[meas].keys()):
            for quant2 in  sorted(orderedLabels[meas][quant].keys()):
                orderedLabels[meas][quant][quant2].sort()
                for label in orderedLabels[meas][quant][quant2]:
                    if label.find('tstoragefile')!=-1: 
                        orderedLabels[meas][quant][quant2].remove(label)
                        orderedLabels[meas][quant][quant2].insert(0, label)
                        break
    line =""
    for meas in sorted(orderedLabels.keys()):
        #if not meas in ["read","readv","seek","open"]: continue
        print "| *"+meas.upper()+"*|", header #|||||"
        for quant in  sorted(orderedLabels[meas].keys()):
            #for char in  orderedLabels[meas][quant].keys():
            for quant2 in  sorted(orderedLabels[meas][quant].keys()):
                for label in orderedLabels[meas][quant][quant2]:
                    if label != "ExeExitCode" and label!="Success" and label!="Failures":
                        line = ""
                        if label.find("tstorage")!=-1: line += "|*"+label+"* |"
                        else: line += "|  * _"+label+"_ *|"
                        for dir in tasks:
                            if DIR_SUMMARY[dir].has_key(label):
                                if DIR_SUMMARY[dir][label][0] <0.1:
                                    line += " %.2e +- %.2e |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])
                                else:
                                    line += " %.2f +- %.2f |" %(DIR_SUMMARY[dir][label][0], DIR_SUMMARY[dir][label][1])

                            else:
                                line += " // |"
                        print line




#histoRange is a 2-d sequence with low and upper limits
def getMaxHistoRange(myH, histoRange):
    firstNotEmptyBin=1
    lastNotEmptyBin=1
    firstFound = False

    nBins = myH.GetNbinsX()
    interval = 1
    if nBins>=1000: interval=1
    if nBins>=10000: interval=100
    if nBins>=100000: interval=1000
    
    bin=1
    while bin in range(1,nBins+2):
        binContent = myH.GetBinContent(bin)
        if binContent!=0:
            lastNotEmptyBin = bin
            if not firstFound:
                firstNotEmptyBin = bin
                firstFound = True
        bin+=interval

    lowRange = myH.GetBinCenter( firstNotEmptyBin) -  myH.GetBinWidth( firstNotEmptyBin)/2.
    upRange = myH.GetBinCenter( lastNotEmptyBin ) + myH.GetBinWidth( lastNotEmptyBin)/2.

    if lowRange < histoRange[0]: histoRange[0] = 0.7*lowRange#  - interval*myH.GetBinWidth( firstNotEmptyBin)/2.
    if upRange > histoRange[1]: histoRange[1] = 1.3*upRange

 

### plots th2f from stats for summaryPlots.
### legendComposition is used to mark the different bins
def plotHistoFromStats(histos2d, stats, summaryPlots, legendComposition, strippedText=""):
    statsKeys = stats.keys()
    statsKeys.sort()
    for plot in summaryPlots:
        ###plotting here errors makes no sense
        if plot.find("Error") != -1: continue
        histos2d[plot] = histos2d[plot] =  ROOT.TH1F(plot,"",1,0,0)
        
        i=1
        isFirst = True
        for task in statsKeys:
            taskLabel=""
            splittedTaskName = splitDirName(task, strippedText)
            if isinstance(splittedTaskName, str): taskLabel = splittedTaskName
            else:
                for leg in legendComposition: taskLabel += splittedTaskName[leg]+"-"
                taskLabel = taskLabel[:-1]
            if plot in stats[task]:
                histos2d[plot].Fill(taskLabel, stats[task][plot][0])
                histos2d[plot].SetBinError(i, stats[task][plot][1] )
                histos2d[plot].GetYaxis().SetTitle(plot)
                isFirst = False
                i+=1
    


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


### uhm... check how if fills
def fillGraph(label, sampleName, single_Graph,  single_H, SINGLE_DIR_DATA, xQuantity):
    print "Filling graph: "+ label
    single_Graph[label] = ROOT.TGraphAsymmErrors()
    if not SINGLE_DIR_DATA.has_key(label):
        print "[WARNING]: "+label+" quantity not available"
        exit
    nIter = len( SINGLE_DIR_DATA[label] )
    i=0
    X = {}
    while i<nIter: #for entry in SINGLE_DIR_DATA[label]:
        j = 0
        while j< len( SINGLE_DIR_DATA[label][i] ):
            record = str(SINGLE_DIR_DATA[xQuantity][i][j])
            if not X.has_key(record): X[record] = [] 
            X[record].append( float(SINGLE_DIR_DATA[label][i][j]) )
            
            single_H[label].Fill(float(SINGLE_DIR_DATA[label][i][j]))
            j += 1
        i += 1
            
    sortedKeys = X.keys()
    sortedKeys.sort(key=float)
    j=0
    for record in sortedKeys:
        #if float(record)>MAX_GRAPH_X: continue
        mean, sigma = computeStat(X[record])
        single_Graph[label].SetPoint(j, float(record), mean)
        single_Graph[label].SetPointError(j, 0, 0 , sigma, sigma )
        j+=1
    single_Graph[label].SetName( 'QUANT'+label+'-SAMPLE'+sampleName )
    single_Graph[label].Write( 'QUANT'+label+'-SAMPLE'+sampleName);


def printGraph(quant, graphs, graphCanvas, mGraph, legend, legLabel, samplePalette, PNG_NAME, xLabel=""):
    graphCanvas[quant] = createCanvas(PNG_NAME+"-"+quant) 
    legend[quant] = createLegend()
    mGraph[quant] = ROOT.TMultiGraph()
    #graphCanvas[quant].SetLogx()
    #graphCanvas[quant].SetLogy()
    i=0
    for sample in graphs[quant].keys():
        legend[quant].AddEntry(graphs[quant][sample],legLabel[sample] ,"l" )
        ### set graph style
        graphs[quant][sample].SetMarkerColor(samplePalette[sample])
        graphs[quant][sample].SetLineColor(samplePalette[sample])
        graphs[quant][sample].SetLineWidth(2)
        graphs[quant][sample].SetMarkerStyle(20+i)
        
        mGraph[quant].Add( graphs[quant][sample])
        i += 1

    mGraph[quant].Draw("al")
    mGraph[quant].GetXaxis().SetTitle(xLabel)
    mGraph[quant].GetYaxis().SetTitle(quant)
    #mGraph[quant].GetXaxis().SetRangeUser(0.000001,500)
    ### uncomment the following line if you want to put a specific range on TGraph's Y axix
    #if quant.find('ecs')!=-1:  mGraph[quant].GetYaxis().SetRangeUser(0.001,30)
    mGraph[quant].Draw("al")
    legend[quant].Draw()



### this sets plot options/filter for a CPT working mode
### possible modes are: SiteMon
def setCPTMode(mode):
    
    if mode=="SiteMon":
        PNG_NAME_FORMAT= ['Site',"Cfg"]
        legendComposition = ['Date']     
        sampleTitles = ["Site","Cfg"]
        strippedText="" # this in case you want to remove some string from the set name
        
        ###filter quantities to be considered
        filter = [
            ".*read.*sec.*",
            #".*read.*",
            #    ".*open.*",
            #   ".*seek.*",
            "Time",
            "Percentage",
            "Error"#,
            #"Actual",
            #"dstat"
            ]

        negFilter = [
            "TimeModule",
            "TimeEvent",
            "local",
            ".*read.*m(in|ax).*",
            ".*open.*m(in|ax).*"
            ]
        
###filter quantities to be plotted
        plotFilter = [  
            "Actual",
            #"readv-total-msecs",
            "tstorage-read-total-msecs",
            "Time_Delay",
            "Percentage",
            "UserTime",
            "Error",
            "dstat-CPU",
            "dstat-DISK",
            "dstat-NET",
            "dstat-MEM"
            #   "TimeModule"
            ]
### plot these quantities overlapped (excluded)
        plotTogether = [
            #"cache-read-total-megabytes",
            #"TimeModule",
            "readv-total-megabytes",
            "read-total-megabytes",
            "readv-total-msecs",
            "read-total-msecs"
            #"open-total-msecs",
            ]
        
### they can not be in plotFilter?
        summaryPlots =  (
            "CpuPercentage",
            "TimeJob_User",
            "TimeJob_Exe",
            "tstoragefile-read-total-msecs",
            "Time_Delay",
            "Error"
            )
        
        doSummary = True

    elif mode=="Default":
        PNG_NAME_FORMAT= ['Site',"Cfg","Sw"]
        legendComposition = ['Site','Cfg']     
        sampleTitles = [""]
        strippedText="" # this in case you want to remove some string from the set name
        
        ###filter quantities to be considered
        filter = [
            #    ".*read.*sec.*",
            ".*read.*",
            #    ".*open.*",
            #   ".*seek.*",
            "Time",
            "Percentage",
            "User",
            "Error",
            "Actual"#,
            #"dstat"
            ]

        negFilter = [
            "TimeModule",
            "TimeEvent",
            "local",
            ".*read.*m(in|ax).*",
            ".*open.*m(in|ax).*"
            ]
        
###filter quantities to be plotted
        plotFilter = [  
            "Actual",
            #"readv-total-msecs",
            "read-total-msecs",
            "Time_Delay",
            "Percentage",
            "UserTime",
            "Error",
            "dstat-CPU",
            "dstat-DISK",
            "dstat-NET",
            "dstat-MEM"
            #   "TimeModule"
            ]
### plot these quantities overlapped (excluded)
        plotTogether = [
            #"cache-read-total-megabytes",
            #"TimeModule",
            "readv-total-megabytes",
            "read-total-megabytes",
            "readv-total-msecs",
            "read-total-msecs"
            #"open-total-msecs",
            ]
        
### they can not be in plotFilter?
        summaryPlots =  (
            "CpuPercentage",
            "UserTime",
            "ExeTime",
            "tstoragefile-read-total-msecs",
            "Time_Delay",
            "Error"
            )
        
        doSummary = True

    else:
        print "Mode "+mode+" does not exist"

    return PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary
