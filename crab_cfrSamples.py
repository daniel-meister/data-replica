#!/usr/bin/python
#################################################################
# crab_cfrSamples.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_cfrSamples.py,v 1.2 2009/11/19 16:38:20 leo Exp $
#################################################################

from sys import argv,exit
from os import popen
import re

try:
    import ROOT
except:
    print "ROOT cannot be loaded"
    exit(1)

LABEL = "PAT1_"
#SAMPLE = "RH-AUTO_CH-AUTO_CACHE-20_15k" #"15k"
SAMPLE = "15k"


samples = [
"DESY-"+LABEL+SAMPLE,
"UCSD-"+LABEL+SAMPLE,
"Rome-"+LABEL+SAMPLE
    ]

cuts = [
    LABEL,
    "_100j_",
    "_QCDPt80_"
    ]

filter = [
    ".*read.*(total-msecs|total-megabytes).*",
#    ".*read.*(total-msecs).*",
#    ".*write.*(total-msecs|total-megabytes).*",
    "Crab.*",
    "ExeTime",
    "Error"
]



if len(argv)!=2:
    print """Usage: """+argv[0]+""" result_file.root"""

rootFile = ROOT.TFile(argv[1])


##########TO BE PUT IN EXT MODULE
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


nextkey = ROOT.gDirectory.GetListOfKeys();
#key = nextkey()
#while key = nex=key():

    #obj = key->ReadObj();

histos = {}
bins = {}
for key in nextkey:
    obj = key.ReadObj();
    if obj.IsA().InheritsFrom("TH1"):
        histoName = obj.GetName()
        if histoName.find("QUANT") == -1: continue
        
        QUANT = histoName[histoName.find("QUANT")+len("QUANT"):
                          histoName.find("-SAMPLE")]
        SAMPLE = histoName[histoName.find("SAMPLE")+len("SAMPLE"):]

        if not histos.has_key(QUANT):
            histos[QUANT] = {}
        for s in samples:
            myFilter = re.compile(s)
            if myFilter.search(SAMPLE) == None: continue
            histos[QUANT][SAMPLE] = obj
            


canvas = {}
legend = {}
keys =  histos.keys()
keys.sort()
for quant in keys:

    toPlot = False
    for f in filter:
        myFilter = re.compile(f)
        if not myFilter.search(quant) == None:
            toPlot = True
            break

    if not toPlot: continue

    print quant 

    nHisto =  len( histos[quant].keys() ) 
    canvas[quant] = ROOT.TCanvas(LABEL+quant,LABEL+quant)
    legend[quant] = ROOT.TLegend(0.15,0.8,0.9,0.9)
    legend[quant].SetTextFont(42)
    legend[quant].SetBorderSize(0)

    legend[quant].SetFillColor(0)

    h=1
    same = ""
    histoKeys =  histos[quant].keys()
    histoKeys.sort()
    for histo in histoKeys:
        ROOT.gPad.SetFillColor(0)
        ROOT.gPad.SetBorderSize(0)
        #canvas[sample].cd(h)
        histolabel = histo
        for cut in cuts:
            histolabel = histolabel.replace(cut,"")

        histos[quant][histo].SetLineColor(h)
        histos[quant][histo].SetTitle(histolabel)

        if h!= 1:
            same = "sames"
        else:
             histos[quant][histo].GetXaxis().SetTitle(quant)
        histos[quant][histo].Rebin(4)
        histos[quant][histo].SetLineWidth(2)
        #histos[quant][histo].SetStats(0000000)

        histos[quant][histo].SetTitle("")
        if quant.find("Error") == -1: 
            histos[quant][histo].DrawNormalized(same)
        else:
            histos[quant][histo].Draw(same)
                        
                        
        histolabel = histo
        for cut in cuts:
            histolabel = histolabel.replace(cut,"")
        
        legend[quant].AddEntry(histos[quant][histo],histolabel,"l" )
        h +=1
    legend[quant].Draw()
        

#Print grand view

viewCanvas = {}
viewCanvas["Overview"] = ("CrabCpuPercentage",
"CrabSysCpuTime",
"CrabUserCpuTime",
"ExeTime"
)

viewCanvas["Read-Msecs"] = ("tstoragefile-read-total-msecs",
"tstoragefile-read-via-cache-total-msecs",
"tstoragefile-read-prefetch-to-cache-total-msecs",
"local-cache-read-total-msecs",
"local-cache-readv-total-msecs",
"gsidcap-read-total-msecs",
"gsidcap-readv-total-msecs",
"file-read-total-msecs",
"file-readv-total-msecs"
)

viewTCanvas = {}
for c in viewCanvas.keys():
    viewTCanvas[c] = ROOT.TCanvas(LABEL+"-"+c,LABEL+"-"+c)
    divideCanvas( viewTCanvas[c], len(viewCanvas[c]) )
    i=1
    for quant in viewCanvas[c]:
        viewTCanvas[c].cd(i)
        myH=1
        if not histos.has_key(quant): continue
        for h in histos[quant].keys():
            same=""
            if myH!= 1:
                same = "sames"
            else:
                histos[quant][h].GetXaxis().SetTitle(quant)
            
            histos[quant][h].DrawNormalized(same)
            
            myH+=1
        i+=1
        legend[quant].Draw()
    viewTCanvas[c].Draw()

popen("sleep 60000")
