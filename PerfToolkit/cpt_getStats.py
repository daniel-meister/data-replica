#!/usr/bin/python
#################################################################
# cpt_getStats.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: cpt_getStats.py,v 1.2 2010/01/14 17:52:48 leo Exp $
#################################################################


### corrected bug in setting logscales for graphs



from sys import argv,exit
from os import popen, path
import re
from cpt_utilities import *
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
parser.add_option("--no-auto-bin",action="store_true", dest="noAutoBin", default=False,
                  help="Automatic histo binning")
parser.add_option("--binwidth-time",action="store", dest="BinWidthTime", default=30,
                  help="Bin width of time histos in seconds")


(options, args) = parser.parse_args()

if len(args)<1:
    print usage
    print """For more help, """+argv[0]+" --help"
    exit(1)


###if you want to add a label to canvas names
LABEL=""

###filter quantities to be plotted
filter = [
    ".*read.*[^(max|min)].*",
#    ".*(read-num-successful-operations).*",
#    ".*read-max-msec.*",
#    ".*read.*(total-msecs).*",
#    ".*seek.*(total-msecs|total-megabytes|num-successful-operations).*",
    "Time",
    "Percentage",
    "User",
    "Error"
]

plotFilter = [  
   "readv-total-msecs",
   "read-total-msecs",
   "TimeEvent",
   "Percentage",
   "UserTime",
   "WrapperTime"
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


summaryPlots =  (
"CpuPercentage",
"UserTime",
"ExeTime",
"tstoragefile-read-total-msecs"
)

legendComposition = ["Site","Cfg","Label"] 

doSummary = True


def doRebin(histo, wantedBinWidth):
    nBins = histo.GetNbinsX()
    ### msecs and time histos has 10 secs bin width (see crab_getJobstatistics.py)
    binWidth = histo.GetBinWidth(1) 
    histoName = histo.GetName()

    ### msecs to secs conversion
    if histoName.find('msecs') !=-1: binWidth /= 1000
    rebin = 1
    ratio=1.5

    if binWidth < wantedBinWidth:
        ratio = float(wantedBinWidth)/float(binWidth)
    ### if no bin width given or no valid ratio, stick to std minima
    if nBins % ratio == 0:
        rebin = int(ratio)
    else:
        nMaxBins = 100
        if histo.GetName().find('msecs')!=-1 or histo.GetName().find('Time')!=-1:
            nMaxBins = 1000
        if nBins>nMaxBins:
            if nBins%nMaxBins == 0:
                rebin = int(nBins/nMaxBins)
            
    if rebin > 1:  histo.Rebin( rebin )
        
            


fileList = []
for arg in args:
    if arg.find('*')!=-1 or arg.find('?')!=-1:
        try:
            pipe=os.popen("ls "+arg)
        except:
            print "[ERROR]: files "+ arg+" do not exist, throwing away from flies list"
            continue
        for p in pipe.readlines():
            fileList.append(p)
    else:
        if not path.isfile(arg):
            print "[ERROR]: file "+arg+" does not exist, throwing away from flies list"
            continue
        fileList.append(arg)
    




toBePlotAlone = []
toBePlotTogether = {}
sitePalette = {}
histos = {}
graphs = {}
sePalette = {"dcap":1,"gsidcap":2,"file":5,"local":4,'tfile':5,'rfio':6}
rootFile = {}
spName = {}
STATS = {}

xAxisRange = {}

cName = args[0][:args[0].find(".")]
for file in fileList:
    rootFile[file] =  ROOT.TFile(file)
    listOfHistoKeys = ROOT.gDirectory.GetListOfKeys();
    sitePalette =  getHistos(listOfHistoKeys, histos, graphs,  filter)
    sampleName = file.replace(".root","")
    spName[sampleName] =  splitDirName(sampleName)



keys =  histos.keys()
keys.sort()
findPlotTogetherHisto(plotFilter, plotTogether, keys,  toBePlotAlone, toBePlotTogether)


###Stats from histos
for quant in keys: 
    for sample in histos[quant].keys():
        myH = histos[quant][sample]
                
        if not STATS.has_key(sample): STATS[sample]={'Error':{}}
        if quant == "Error": 
            STATS[sample]["Failures"] = myH.Integral()
            if not histos.has_key("CpuPercentage"):
                STATS[sample]["Success"] = 0
                    
            elif not histos["CpuPercentage"].has_key(sample):
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
        wBinWidth = -1
        if myH.GetName().find('msecs') !=-1 or myH.GetName().find('Time') !=-1: wBinWidth =options.BinWidthTime 
        doRebin(myH, wBinWidth)
        ### get range infos
        if not options.noAutoBin:
            if not xAxisRange.has_key(quant): xAxisRange[quant] = [1000000000,0]
            getMaxHistoRange(myH, xAxisRange[quant])
        

canvas = {}
legend = {}

### legend entries for each sample
legLabel = {}
for sample in sorted(spName.keys()):
    if isinstance(spName[sample], str):
        legLabel[sample] = spName[sample]
    else:
        legLabel[sample] = ""
        for x in legendComposition:
            legLabel[sample] += spName[sample][x]+" "

printWikiStat(STATS, "", ".*(min|max).*", legLabel)

drawOpt = "histo"
for quant in toBePlotAlone:
    if quant in summaryPlots: continue
    h=1
    histoKeys =  histos[quant].keys()
    histoKeys.sort()
    maxY = 0.0
    firstLabel=''
    for histo in histoKeys:
        setHisto(histos[quant][histo], h, "","",quant, 1 )
        if not options.noAutoBin:
            histos[quant][histo].GetXaxis().SetRangeUser(xAxisRange[quant][0], xAxisRange[quant][1])
        
        firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo,  maxY, quant )
        h +=1

    if len(firstLabel)<2: continue
    canvas[quant] = createCanvas(LABEL+cName+"-"+quant)
    legend[quant] = createLegend()
    if quant != "Error":  histos[quant][firstLabel[1]].DrawNormalized(drawOpt)
    else:  histos[quant][firstLabel[1]].Draw(drawOpt)
    for histo in histoKeys:
        legend[quant].AddEntry(histos[quant][histo],legLabel[sample], "l" )

        if histo==firstLabel[1]: continue
        if quant != "Error": histos[quant][histo].DrawNormalized(drawOpt+" sames")
        else:  histos[quant][histo].Draw(drawOpt+" sames")
    legend[quant].Draw()
    if options.savePng:
        canvas[quant].Update()
        canvas[quant].SaveAs(LABEL+cName+"-"+quant+".png") 

for sel in toBePlotTogether.keys():
    if quant in summaryPlots: continue
    firstHisto = True
    goodHistos = {}
    maxY = 0
    firstLabel = ()
    for quant in toBePlotTogether[sel]:
        print quant
        seType = quant.split("-")[0]
        goodHistos[quant]=[]
        histoKeys = histos[quant].keys()
        histoKeys.sort()
        h=1
        for histo in histoKeys:
            setHisto(histos[quant][histo], h,sePalette[seType] ,"",sel, 1 )
            if not options.noAutoBin:
                histos[quant][histo].GetXaxis().SetRangeUser(xAxisRange[quant][0], xAxisRange[quant][1])
           
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo, maxY, quant, goodHistos[quant])
            h+=1
            
    if firstLabel == (): continue
    canvas[sel] = createCanvas(LABEL+cName+"-"+sel)
    legend[sel] = createLegend()
    histos[firstLabel[0]][firstLabel[1]].DrawNormalized(drawOpt)
    
    for quant in toBePlotTogether[sel]:
        for histo in goodHistos[quant]:
            legend[sel].AddEntry(histos[quant][histo],legLabel[sample]+" "+quant.split("-")[0] ,"l" )
            if quant==firstLabel[0] and histo==firstLabel[1]: continue
            histos[quant][histo].DrawNormalized(drawOpt+" same")
            
    legend[sel].Draw()
    if options.savePng:
        canvas[sel].Update()
        canvas[sel].SaveAs(LABEL+"-"+sel+".png") 



### plot graphs
graphCanvas = {}
mGraph = {}
for quant in graphs.keys():
    graphCanvas[quant] = createCanvas(LABEL+cName+"-"+quant) 
    legend[quant] = createLegend()
    mGraph[quant] = ROOT.TMultiGraph()
    graphCanvas[quant].SetLogx()
    graphCanvas[quant].SetLogy()
    i=0
    for sample in graphs[quant].keys():
        legend[quant].AddEntry(graphs[quant][sample],legLabel[sample] ,"p" )
        graphs[quant][sample].SetMarkerColor(i+1)
        graphs[quant][sample].SetLineColor(i+1)
        graphs[quant][sample].SetMarkerStyle(20+i)
        mGraph[quant].Add( graphs[quant][sample])
        i += 1

    mGraph[quant].Draw("ap")
    mGraph[quant].GetXaxis().SetTitle("record")
    mGraph[quant].GetYaxis().SetTitle(quant)
    mGraph[quant].GetXaxis().SetRangeUser(0.000001,500)
    if quant.find('ecs')!=-1:  mGraph[quant].GetYaxis().SetRangeUser(0.001,30)
    mGraph[quant].Draw("ap")
    legend[quant].Draw()
    if options.savePng:
        graphCanvas[quant].Update()
        graphCanvas[quant].SaveAs(LABEL+cName+"-"+quant+".png") 


#Print grand view
if not doSummary: popen("sleep 6000000000")

viewCanvas = {}
viewCanvas["Overview"] = summaryPlots

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
        legend[quant] = createLegend()

        if not histos.has_key(quant):
            print "[WARNING] Histo "+quant+" not available"
            continue
        for h in histos[quant].keys():
            setHisto(histos[quant][h], myH, "","",quant, 1 )
            
            if not options.noAutoBin:
                histos[quant][h].GetXaxis().SetRangeUser(xAxisRange[quant][0], xAxisRange[quant][1])
            
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][h], h,  maxY, quant )
            histos[quant][h].SetLineWidth(2)
            legend[quant].AddEntry(histos[quant][h],legLabel[h] ,"l" )
            
            myH+=1
        i+=1

        if firstLabel == (): continue
        histos[firstLabel[0]][firstLabel[1]].DrawNormalized(drawOpt)
    
        for h in histos[quant].keys():
            histolabel = h
            if h==firstLabel[1]: continue
            histos[quant][h].DrawNormalized(drawOpt+" same")
        legend[quant].Draw()

    viewTCanvas[c].Draw()
    if options.savePng:
        viewTCanvas[c].Update()
        viewTCanvas[c].SaveAs(LABEL+cName+"-"+c+".png") 


popen("sleep 60000")
