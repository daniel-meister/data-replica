#!/usr/bin/python
#################################################################
# crab_cfrSamples.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: crab_cfrSamples.py,v 1.6 2009/12/14 15:52:09 leo Exp $
#################################################################

from sys import argv,exit
from os import popen
import re
from crab_utilities import *
from optparse import OptionParser

try:
    import ROOT
except:
    print "ROOT cannot be loaded"
    exit(1)

usage = """%prog input.root <input2.root, ...> """
parser = OptionParser(usage = usage, version="%prog 0.1")
#parser.add_option("--logfile",action="store", dest="logfile",default="data_replica.log",
#                  help="file for the phedex-like log, default is data_replica.log")
parser.add_option("--save-png",
                  action="store_true", dest="savePng", default=False,
                  help="Saves created histos in png format")

(options, args) = parser.parse_args()

if len(args)<1:
    print usage
    print """For more help, """+argv[0]+" --help"
    exit(1)


###if you want to add a label to canvas names
LABEL=""

###filter quantities to be plotted
filter = [
    ".*read.*(total-msecs|total-megabytes).*",
#    ".*(read-num-successful-operations).*",
#    ".*read-max-msec.*",
#    ".*read.*(total-msecs).*",
    ".*seek.*(total-msecs|total-megabytes|num-successful-operations).*",
    "Time",
    "Percentage",
    "User",
    "Error"
]

### plot these quantities overlapped (excluded)
plotTogether = [
    #"cache-read-total-megabytes",
    "readv-total-megabytes",
    "read-total-megabytes",
    "readv-total-msecs",
    "read-total-msecs"
    #"open-total-msecs",
    #"read-num-successful-operations"
    ]


doSummary = True


def getRebin(quant):
    if quant.find("Percentage")!=-1: rebin=1
    elif quant.find("Error")!=-1: rebin=1
    else: rebin=1
    return rebin


fileList = []
for arg in args:
    if arg.find('*')!=-1 or arg.find('?')!=-1:
        pipe=os.popen("ls "+arg)
        for p in pipe.readlines():
            fileList.append(p)
    else:
        fileList.append(arg)
    




toBePlotAlone = []
toBePlotTogether = {}
sitePalette = {}
histos = {}
sePalette = {"dcap":1,"gsidcap":2,"file":5,"local":4,'tfile':5,'rfio':6}
rootFile = {}
spName = {}
STATS = {}

cName = args[0][:args[0].find(".")]
for file in fileList:
    rootFile[file] =  ROOT.TFile(file)

    listOfHistoKeys = ROOT.gDirectory.GetListOfKeys();
    sitePalette =  getHistos(listOfHistoKeys, histos,  filter)
    
    keys =  histos.keys()
    keys.sort()
    findPlotTogetherHisto(plotTogether, keys,  toBePlotAlone, toBePlotTogether)
    spName[file.strip(".root")] =  splitDirName(file.strip(".root"))

    ###Stats from histos
    for quant in keys: 
        for sample in histos[quant].keys():
            myH = histos[quant][sample]
            if not STATS.has_key(sample): STATS[sample]={'Error':{}}
            if quant == "Error": 
                STATS[sample]["Failures"] = myH.Integral()
                print  myH.Integral()
                if not  histos["CpuPercentage"].has_key(sample):
                    STATS[sample]["Success"] = 0
                else:
                    STATS[sample]["Success"]  =  histos["CpuPercentage"][sample].Integral() #- STATS[sample]["Failures"] 
                for i in range(myH.GetNbinsX()):
                    errLabel = myH.GetXaxis().GetBinLabel(i+1)
                    if errLabel!="": 
                        if not STATS[sample]["Error"].has_key(errLabel): 
                            STATS[sample]["Error"][errLabel] = 0
                        STATS[sample]["Error"][errLabel] = 100*round(myH.GetBinContent(i+1)/STATS[sample]["Failures"],1)
            
            # or quant == "Error": continue
            else: STATS[sample][quant] = ( histos[quant][sample].GetMean(1), histos[quant][sample].GetRMS(1) )
    

printWikiStat(STATS, "", ".*(min|max).*")

canvas = {}
legend = {}
for quant in toBePlotAlone:
    h=1
    histoKeys =  histos[quant].keys()
    histoKeys.sort()
    maxY = 0.0
    firstLabel=''
    for histo in histoKeys:
        rebin = getRebin(quant)
        setHisto(histos[quant][histo], h, "","",quant,rebin )
        firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo,  maxY, quant )
        h +=1

    if len(firstLabel)<2: continue
    canvas[quant] = createCanvas(LABEL+cName+"-"+quant)
    legend[quant] = createLegend()
    if quant != "Error":  histos[quant][firstLabel[1]].DrawNormalized("")
    else:  histos[quant][firstLabel[1]].Draw("")
    for histo in histoKeys:
        legLabel = spName[histo]["Site"]+" "+spName[histo]["Cfg"]+" "+spName[histo]["Sw"] 
        legend[quant].AddEntry(histos[quant][histo],legLabel,"l" )

        if histo==firstLabel[1]: continue
        if quant != "Error": histos[quant][histo].DrawNormalized("sames")
        else:  histos[quant][histo].Draw("sames")
    legend[quant].Draw()
    if options.savePng:
        canvas[sel].Update()
        canvas[sel].SaveAs(LABEL+"-"+sel+".png") 

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
            rebin = getRebin(quant)
            setHisto(histos[quant][histo], h,sePalette[seType] ,"",sel, rebin )
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo, maxY, quant, goodHistos[quant])
            h+=1
            
    if firstLabel == (): continue
    canvas[sel] = createCanvas(LABEL+cName+"-"+sel)
    legend[sel] = createLegend()
    histos[firstLabel[0]][firstLabel[1]].DrawNormalized("")
    
    for quant in toBePlotTogether[sel]:
        for histo in goodHistos[quant]:
            legLabel = spName[histo]["Site"]+" "+spName[histo]["Cfg"]+" "+spName[histo]["Sw"]
            legend[sel].AddEntry(histos[quant][histo],legLabel+" "+quant.split("-")[0] ,"l" )
            if quant==firstLabel[0] and histo==firstLabel[1]: continue
            histos[quant][histo].DrawNormalized("same")
            
    legend[sel].Draw()
    if options.savePng:
        canvas[sel].Update()
        canvas[sel].SaveAs(LABEL+"-"+sel+".png") 


#Print grand view
print "END"
if not doSummary: popen("sleep 6000000000")

viewCanvas = {}
viewCanvas["Overview"] = (
"CpuPercentage",
"UserTime",
"WrapperTime",
"tstoragefile-read-total-msecs"

)


viewTCanvas = {}
for c in viewCanvas.keys():
    
    viewTCanvas[c] = createCanvas(LABEL+cName+"-"+c) 
    ROOT.gPad.SetFillColor(0)
    ROOT.gPad.SetBorderSize(0)

    divideCanvas( viewTCanvas[c], len(viewCanvas[c]) )
    i=1
    for quant in viewCanvas[c]:
        viewTCanvas[c].cd(i)
        myH=1
        
        maxY = 0.0
        firstLabel=()

        if not histos.has_key(quant): continue
        for h in histos[quant].keys():
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][h], h,  maxY, quant )
            histos[quant][h].SetLineWidth(2)
            histos[quant][h].SetStats(0000000)
            
            myH+=1
        i+=1

        if firstLabel == (): continue
        histos[firstLabel[0]][firstLabel[1]].DrawNormalized("")
    
        for h in histos[quant].keys():
            histolabel = h
            if h==firstLabel[1]: continue
            histos[quant][h].DrawNormalized("same")
        legend[quant].Draw()

    viewTCanvas[c].Draw()

popen("sleep 60000")
