#!/usr/bin/python
#################################################################
# crab_cfrSamples.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_cfrSamples.py,v 1.4 2009/11/27 10:50:28 leo Exp $
#################################################################

from sys import argv,exit
from os import popen
import re
from crab_utilities import *

try:
    import ROOT
except:
    print "ROOT cannot be loaded"
    exit(1)

if len(argv)!=2:
    print """Usage: """+argv[0]+""" result_file.root"""
    exit(1)

rootFile = ROOT.TFile(argv[1])

rootFile_split = argv[1].replace(".root","").split("-")

print  argv[1].split(".")

print len(rootFile_split)

if len(rootFile_split)==5:
    TEST, DATASET, EVENTSJOB, CMSSWVERSION, DATE = rootFile_split
    LABEL=""
elif len(rootFile_split)==6:
    TEST, DATASET, EVENTSJOB, CMSSWVERSION, LABEL, DATE = rootFile_split

LABEL = TEST+"-"+CMSSWVERSION+"-"+DATE

posFilter = [
    ".*(read-total-msecs).*",
    ".*(open-total-msecs).*",
    ".*(read-num-successful-operations).*",
#    ".*(readv-total-msecs).*",
#    ".*read-max-msec.*",
##    ".*read.*(total-msecs).*",
##    ".*write.*(total-msecs|total-megabytes).*",
    "Crab.*",
#    "ExeTime",
    "Error"
]

negFilter = [
    ".*(min|max|actual).*",
    ".*(stageout).*"
]

plotTogether = [
    #"read-total-megabytes",
    "read-total-msecs",
    "open-total-msecs",
    "read-num-successful-operations"
    ]

doSummary = False



listOfHistoKeys = ROOT.gDirectory.GetListOfKeys();
sitePalette = {}
sePalette = {"dcap":1,"gsidcap":2,"file":5,"local":4}
histos, sitePalette =  getHistos(listOfHistoKeys, posFilter, negFilter)
keys =  histos.keys()
keys.sort()


toBePlotAlone, toBePlotTogether = findPlotTogetherHisto(plotTogether, keys)

canvas = {}
legend = {}
for quant in toBePlotAlone:
    histoKeys =  histos[quant].keys()
    histoKeys.sort()
    maxY = 0.0
    firstLabel=''
    for histo in histoKeys:
        histolabel = histo
        setHisto(histos[quant][histo], sitePalette[histo.split('-')[0]], "","",quant,10 )
        firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo,  maxY, quant )
    
    if len(firstLabel)<2: continue
 
    canvas[quant] = createCanvas(LABEL+"-"+quant)
    legend[quant] = createLegend()
    if quant != "Error":  histos[quant][firstLabel[1]].DrawNormalized("")
    else:  histos[quant][firstLabel[1]].Draw("")
    for histo in histoKeys:
        legend[quant].AddEntry(histos[quant][histo],histolabel.split('-')[0],"l" )
        if histo==firstLabel[1]: continue
        if quant != "Error": histos[quant][histo].DrawNormalized("sames")
        else:  histos[quant][histo].Draw("sames")

    legend[quant].Draw()
    canvas[quant].Update()
    canvas[quant].SaveAs(LABEL+"-"+quant+".png")   


for sel in toBePlotTogether.keys():
    firstHisto = True
    goodHistos = {}
    maxY = 0
    firstLabel = ()
    for quant in toBePlotTogether[sel]:
        seType = quant.split("-")[0]
        goodHistos[quant]=[]
        histoKeys = histos[quant].keys()
        histoKeys.sort()
        for histo in histoKeys:
            setHisto(histos[quant][histo], sitePalette[histo.split('-')[0]],sePalette[seType] ,"",sel,10 )
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo, maxY, quant, goodHistos[quant])

    if firstLabel == (): continue
    canvas[sel] = createCanvas(LABEL+"-"+sel)
    legend[sel] = createLegend()
    legend[sel].AddEntry(histos[firstLabel[0]][firstLabel[1]],firstLabel[1].split('-')[0]+" "+firstLabel[0].split("-")[0] ,"l" )
    histos[firstLabel[0]][firstLabel[1]].DrawNormalized("")
    
    for quant in toBePlotTogether[sel]:
        for histo in goodHistos[quant]:
            if quant==firstLabel[0] and histo==firstLabel[1]: continue
            histolabel = histo
            Site = histolabel.split('-')[0]
            legend[sel].AddEntry(histos[quant][histo],Site+" "+quant.split("-")[0] ,"l" )
            histos[quant][histo].DrawNormalized("same")
            
    legend[sel].Draw()
    canvas[sel].Update()
    canvas[sel].SaveAs(LABEL+"-"+sel+".png")   
 
#Print grand view
if not doSummary: popen("sleep 6000000000")

viewCanvas = {}
viewCanvas["Overview"] = ("CrabCpuPercentage",
"CrabSysCpuTime",
"CrabUserCpuTime",
"ExeTime"
)

viewCanvas["Read-Msecs"] = (
"tstoragefile-read-total-msecs",
#"tstoragefile-read-via-cache-total-msecs",
#"tstoragefile-read-prefetch-to-cache-total-msecs",
"local-cache-read-total-msecs",
"local-cache-readv-total-msecs",
"gsidcap-read-total-msecs",
"gsidcap-readv-total-msecs",
"dcap-read-total-msecs",
"dcap-readv-total-msecs",
"file-read-total-msecs",
"file-readv-total-msecs"
)

viewTCanvas = {}
for c in viewCanvas.keys():
    viewTCanvas[c] = ROOT.TCanvas(LABEL+SEL_SAMPLE+"-"+c,LABEL+SEL_SAMPLE+"-"+c)
    ROOT.gPad.SetFillColor(0)
    ROOT.gPad.SetBorderSize(0)

    divideCanvas( viewTCanvas[c], len(viewCanvas[c]) )
    i=1
    for quant in viewCanvas[c]:
        viewTCanvas[c].cd(i)
        myH=1
        
        #print histos.keys()
        if not histos.has_key(quant): continue
        for h in histos[quant].keys():
            same=""
            if myH!= 1:
                same = "sames"
            else:
                histos[quant][h].GetXaxis().SetTitle(quant)
            
            histos[quant][h].SetStats(0000000)
            histos[quant][h].DrawNormalized(same)
            
            myH+=1
        i+=1
        legend[quant].Draw()
    viewTCanvas[c].Draw()

popen("sleep 60000")
