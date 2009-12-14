#!/usr/bin/python
#################################################################
# crab_utilities.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_utilities.py,v 1.1 2009/12/08 14:32:28 leo Exp $
#################################################################

from sys import argv,exit
from os import popen
import re
import ROOT


def divideCanvas(canvas, numberOfHisto):
    if numberOfHisto <=3:
        canvas.Divide(numberOfHisto)
    elif numberOfHisto == 4:
        canvas.Divide(2,2)
    elif numberOfHisto == 8:
        canvas.Divide(4,2)
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
    legend = ROOT.TLegend(0.2,1,0.9,0.75)
    legend.SetTextFont(42)
    legend.SetBorderSize(0)
    legend.SetFillColor(0)
    legend.SetFillStyle(0)
    return legend


def setHisto(histo, color, lineStyle,title,Xtitle, rebin):
    histo.Rebin(rebin)
    histo.SetLineWidth(3)
    histo.SetStats(0000000)
    histo.SetTitle("")
    histo.StatOverflows(ROOT.kTRUE)
    histo.SetLineColor(color)
    histo.SetTitle(title)
    histo.GetXaxis().SetTitle(Xtitle)
    if lineStyle !="": histo.SetLineStyle( lineStyle ) 


def getHistos(listOfKeys, histos, posFilter, negFilter=""):
    myColor = 1
    sitePalette = {}
#    histos = {}
    #bins = {}
    for key in listOfKeys:
        obj = key.ReadObj();
        if obj.IsA().InheritsFrom("TH1"):
            histoName = obj.GetName()
            if histoName.find("QUANT") == -1: continue
        
            QUANT = histoName[histoName.find("QUANT")+len("QUANT"):
                                  histoName.find("-SAMPLE")]
            SAMPLE = histoName[histoName.find("SAMPLE")+len("SAMPLE"):]

            SITE =  SAMPLE.split("-")[0]
            if not sitePalette.has_key(SITE): 
                sitePalette[SITE] = myColor
                myColor +=1

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
        
            if not histos.has_key(QUANT):
                histos[QUANT] = {}
            histos[QUANT][SAMPLE] = obj
            
    return sitePalette


def getMaxHeightHisto(firstLabel, histo, histoName, maxY, quant="", goodHistoList=""):
    if histo.Integral() == 0:
        return firstLabel, maxY
    
    maxBin =  histo.GetMaximumBin()
    maxValue =  histo.GetBinContent( maxBin )/ histo.Integral()

    #zeroBin = histo.GetBinWithContent(0,(-100000,1000000))
    #zeroValue = histo.GetBinContent( zeroBin )/ histo.Integral()

    if not (maxBin == 1 and maxValue==1) and not (maxValue==1 and histo.GetBinLowEdge(maxBin)==0 ):
        if goodHistoList!="": goodHistoList.append(histoName)
        if maxValue>maxY:
            firstLabel = quant,histoName
            maxY = maxValue

    return firstLabel, maxY



def findPlotTogetherHisto(plotTogether, keys, toBePlotAlone, toBePlotTogether):
#    toBePlotAlone = []
#    toBePlotTogether = {}
    for quant in keys:
        together=False
        for sel in plotTogether:
            if not toBePlotTogether.has_key(sel): toBePlotTogether[sel] = []
            if quant.find(sel)!=-1 and quant.find("tstorage")==-1:
                if quant not in toBePlotTogether[sel]: toBePlotTogether[sel].append(quant)
                together = True
                break
        if not together:
            if quant not in toBePlotAlone: toBePlotAlone.append(quant)

#    return toBePlotAlone, toBePlotTogether


def splitDirName(dirName):
    output = {}
    ###The split("/")[-1] get rid of mother directories, eg mydir/crab_dir
    
    splittedDirName = dirName.strip('/').split("/")[-1].split("-")
    output['Site'] = splittedDirName[0]
    output['Cfg'] = splittedDirName[1]
    output['Dataset'] = splittedDirName[2]
    output['EventsJob'] = splittedDirName[3]
    output['Sw'] = splittedDirName[4]
    output['Date'] = splittedDirName[5][0:8]
    output['Hour'] = splittedDirName[5][8:]

    return output



def printWikiStat(DIR_SUMMARY, posFilter, negFilter):
    perc=0
    LABELS = []

    ###Creating header
    header = "| |"
    tasks = DIR_SUMMARY.keys()
    tasks.sort()
    for dir in tasks:
        print dir.split('-')
        header += " *"+dir.split("-")[0]+"-"+dir.split("-")[1]+" "+dir.split("-")[4]+" "+dir.split("-")[-1][:8]+"* |"
        for l in DIR_SUMMARY[dir].keys():
            if not l in LABELS: LABELS.append(l)

    print header

    ###Success rate
    line = "| *Success*|"
    for dir in tasks:
        total = DIR_SUMMARY[dir]["Success"] + DIR_SUMMARY[dir]["Failures"]
        if total==0:
            perc = 0
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
            if label != "ExeExitCode" and label!="Success" and label!="Failures" and label!="Error":
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


