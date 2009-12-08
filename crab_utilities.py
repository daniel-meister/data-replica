#!/usr/bin/python
#################################################################
# crab_utilities.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_cfrSamples.py,v 1.4 2009/11/27 10:50:28 leo Exp $
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


def getHistos(listOfKeys, posFilter, negFilter=""):
    myColor = 1
    sitePalette = {}
    histos = {}
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
            
    return histos, sitePalette


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



def findPlotTogetherHisto(plotTogether, keys):
    toBePlotAlone = []
    toBePlotTogether = {}
    for quant in keys:
        together=False
        for sel in plotTogether:
            if not toBePlotTogether.has_key(sel): toBePlotTogether[sel] = []
            if quant.find(sel)!=-1 and quant.find("tstorage")==-1:
                toBePlotTogether[sel].append(quant)
                together = True
                break
        if not together:
            toBePlotAlone.append(quant)

    return toBePlotAlone, toBePlotTogether
