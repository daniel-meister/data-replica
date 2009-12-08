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

LABEL = ""# "CIEMAT-"
#SEL_SAMPLE = "RH-AUTO_CH-AUTO_CACHE-20_15k" #"15k"
SEL_SAMPLE = "QCD_Pt80"


samples = [
SEL_SAMPLE
    ]

cuts = [
    LABEL,
    "-QCD_Pt80+Summer09.MC_31X_V3.v1+GEN.SIM.RECO-",
    "300000-",
    "15000",
    "10000",
    "CMSSW_3_1_4-",
    "CMSSW_3_3_2-"

    ]

filter = [
    ".*read.*(total-msecs|total-megabytes).*",
    ".*(read-num-successful-operations).*",
#    ".*read-max-msec.*",
##    ".*read.*(total-msecs).*",
##    ".*write.*(total-msecs|total-megabytes).*",
    "Crab.*",
    "ExeTime",
    "Error"
]

plotTogether = [
    #"cache-read-total-megabytes",
    "read-total-megabytes",
    "read-total-msecs",
    "open-total-msecs",
    "read-num-successful-operations"
    ]


doSummary = False

if len(argv)!=2:
    print """Usage: """+argv[0]+""" result_file.root"""

rootFile = ROOT.TFile(argv[1])
cName = argv[1][:argv[1].find(".")]

listOfHistoKeys = ROOT.gDirectory.GetListOfKeys();
sitePalette = {}
sePalette = {"dcap":1,"gsidcap":2,"file":5,"local":4,'tfile':5}
histos, sitePalette =  getHistos(listOfHistoKeys, filter)
keys =  histos.keys()
keys.sort()
toBePlotAlone, toBePlotTogether = findPlotTogetherHisto(plotTogether, keys)


canvas = {}
legend = {}
for quant in toBePlotAlone:
    h=1
    histoKeys =  histos[quant].keys()
    histoKeys.sort()
    maxY = 0.0
    firstLabel=''
    for histo in histoKeys:
        setHisto(histos[quant][histo], h, "","",quant,4 )
        firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo,  maxY, quant )
        h +=1

    if len(firstLabel)<2: continue
    canvas[quant] = createCanvas(LABEL+cName+"-"+quant)
    legend[quant] = createLegend()
    if quant != "Error":  histos[quant][firstLabel[1]].DrawNormalized("")
    else:  histos[quant][firstLabel[1]].Draw("")
    for histo in histoKeys:
        histolabel = histo
        for cut in cuts: histolabel = histolabel.replace(cut,"")
        legend[quant].AddEntry(histos[quant][histo],histolabel,"l" )
        if histo==firstLabel[1]: continue
        if quant != "Error": histos[quant][histo].DrawNormalized("sames")
        else:  histos[quant][histo].Draw("sames")
    legend[quant].Draw()
        

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
        h=1
        for histo in histoKeys:
            setHisto(histos[quant][histo], h,sePalette[seType] ,"",sel,10 )
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo, maxY, quant, goodHistos[quant])
            h+=1
            
    if firstLabel == (): continue
    canvas[sel] = createCanvas(LABEL+"-"+sel)
    legend[sel] = createLegend()
    histos[firstLabel[0]][firstLabel[1]].DrawNormalized("")
    
    for quant in toBePlotTogether[sel]:
        for histo in goodHistos[quant]:
            histolabel = histo
            for cut in cuts: histolabel = histolabel.replace(cut,"")
            legend[sel].AddEntry(histos[quant][histo],histolabel+" "+quant.split("-")[0] ,"l" )
            if quant==firstLabel[0] and histo==firstLabel[1]: continue
            histos[quant][histo].DrawNormalized("same")
            
    legend[sel].Draw()
#    canvas[sel].Update()
#    canvas[sel].SaveAs(LABEL+"-"+sel+".png") 


#Print grand view
print "END"
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
