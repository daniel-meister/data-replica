#!/usr/bin/python
#################################################################
# crab_cfrSamples.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id$
#################################################################

from sys import argv,exit
from os import popen
import re

try:
    import ROOT
except:
    print "ROOT cannot be loaded"
    exit(1)

LABEL = "T3Test_JRA1_"

samples = [
    "JRA_100j_15000evts_InclMu5_pt50_AOD_CMSSW332",
    "JRA_100j_15000evts_InclMu5_pt50_AOD_CMSSW332Patched",
#    "JRA_100j_15000evts_InclMu5_pt50_AOD_noTAdaptor_CACHE-20_CMSSW332",
#    "JRA_100j_15000evts_InclMu5_pt50_AOD_noTAdaptor_CACHE-50_CMSSW332",
    "JRA_100j_15000evts_InclMu5_pt50_AOD_RH-APP_CH-AUTO_CACHE-20_CMSSW332", 
    "JRA_100j_15000evts_InclMu5_pt50_AOD_RH-APP_CH-AUTO_CACHE-20_CMSSW332Patched",
    "JRA_100j_15000evts_InclMu5_pt50_AOD_RH-AUTO_CH-AUTO_CACHE-20_CMSSW332",
    "JRA_100j_15000evts_InclMu5_pt50_AOD_RH-AUTO_CH-AUTO_CACHE-20_CMSSW332Patched",
#    "PAT_100j_15000evts_InclMu5_pt50_AOD_CMSSW332",
#    "PAT_100j_15000evts_InclMu5_pt50_AOD_CMSSW332Patched",
#    "PAT_100j_15000evts_InclMu5_pt50_AOD_RH-AUTO_CH-AUTO_CACHE-20_CMSSW332",
#    "PAT_100j_15000evts_InclMu5_pt50_AOD_RH-AUTO_CH-AUTO_CACHE-20_CMSSW332Patched"


    ]

cuts = [
#    "PAT",
    "JRA",
    "_100j_",
    "_InclMu5_pt50_"
    ]

filter = [
    ".*read.*(total-msecs|total-megabytes).*",
#    ".*read.*(total-msecs).*",
#    ".*write.*(total-msecs|total-megabytes).*",
    "Crab.*",
    "ExeTime"
]

#quantities = [
#    "CrabCpuPercentage",
#    "CrabStageoutTime",
#    "CrabSysCpuTime",
#    "CrabUserCpuTime",
#    "CrabWrapperTime",
#    "ExeTime",
#    "dcap-position-num-successful-operations",
#    "dcap-position-total-msecs",
#    "dcap-read-num-successful-operations",
 #   "dcap-read-total-megabytes",
#    "dcap-readv-total-megabytes",
#    "dcap-readv-num-successful-operations",
#    "dcap-read-total-msecs",
#    "dcap-readv-total-msecs",
#    "tstoragefile-read-actual-num-successful-operations",
#    "tstoragefile-read-actual-total-megabytes",
#    "tstoragefile-read-actual-total-msecs",
#    "tstoragefile-read-num-successful-operations",
#    "tstoragefile-read-total-megabytes",
#    "tstoragefile-read-via-cache-total-megabytes",
#    "tstoragefile-read-via-cache-total-msecs",
#    "tstoragefile-read-total-msecs",
#    "tstoragefile-read-via-cache-num-successful-operations",
#    "tstoragefile-seek-num-successful-operations",
#    "tstoragefile-seek-total-msecs",
#    "tstoragefile-write-total-megabytes",
#    "tstoragefile-write-actual-total-megabytes"
#    ]


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
            if s == SAMPLE:
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
        histos[quant][histo].DrawNormalized(same)
        
        histolabel = histo
        for cut in cuts:
            histolabel = histolabel.replace(cut,"")
        
        legend[quant].AddEntry(histos[quant][histo],histolabel,"l" )
        h +=1
    legend[quant].Draw()
        

    
popen("sleep 60000")
