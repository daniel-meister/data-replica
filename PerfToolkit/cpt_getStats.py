#!/usr/bin/python
#################################################################
# cpt_getStats.py 
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: cpt_getStats.py,v 1.7 2010/03/04 15:49:44 leo Exp $
#################################################################

# added plotting of bar histograms of summaryPlots
# fixes according to new dir naming scheme supported
# added sampleTitles variable
# added setCPTMode
# replotted errors

### TODO: make a nice check in plotting canvas based on plotFilter
###       use formatting for png filenames (SITE, etc...)
###       add to png filenames also LABEL
###       when usrtime/quantity too small, not plotted
###       better plotting functions!


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
parser.add_option("--save-root",
                  action="store_true", dest="saveRoot", default=False,
                  help="Saves created histos in a ROOT file. If enabled, these histos will be not drawn on screen")
parser.add_option("--no-auto-bin",action="store_true", dest="noAutoBin", default=False,
                  help="Automatic histo binning")
parser.add_option("--binwidth-time",action="store", dest="BinWidthTime", default=30,
                  help="Bin width of time histos in seconds")
parser.add_option("--no-plots",action="store_false", dest="drawPlots", default=True,
                  help="Do not draw plots")
parser.add_option("--label",action="store", dest="Label", default="",
                  help="Label to be used in naming plots, etc")
parser.add_option("--mode",action="store", dest="Mode", default="Default",
                  help="Preconfigured modes for analysis: SiteMon, Default")

(options, args) = parser.parse_args()

if len(args)<1:
    print usage
    print """For more help, """+argv[0]+" --help"
    exit(1)


### if you want to add a label to canvas names
### sampleTitles stores the name of this sample, eg a T2_CH_CSCS measure with a certaing cfg. It will be used
###     as histo title for sommaries and as header in the tables
PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary =  setCPTMode(options.Mode)
strippedText="" # this in case you want to remove some string from the set name

LABEL=options.Label
PNG_NAME_FORMAT.append(LABEL)
#LABEL="QCDvsBB"
###name prefix of png files
#PNG_NAME_FORMAT= ['Site',"Cfg",'Patch']
#legendComposition = ['Cfg',"SE",'Patch'] 
#PNG_NAME_FORMAT= ['Site',"Cfg",'Setting','Label']
#legendComposition = ["NJobs"] 
#PNG_NAME_FORMAT= ['Site',"Cfg"]
#legendComposition = ['Date']     
#sampleTitles = ["Site","Cfg"]
#PNG_NAME_FORMAT= ['Site','Patch',"Cfg"]
#legendComposition = ["Cfg","Patch","Set"] 


### global drawing options
drawOpt = "histo"

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
    

if len(fileList)==0:
    print "[ERROR] No good files has been given as input, exiting"
    exit(1)


toBePlotAlone = []
toBePlotTogether = {}
samplePalette = {}
histos = {}
graphs = {}
sePalette = {"dcap":1,"gsidcap":2,"file":5,"local":4,'tfile':5,'rfio':6}
### you need to keep all the TFiles open in order to keep the histos loaded
rootFile = {}
spName = {}
STATS = {}

xAxisRange = {}

cName = args[0][:args[0].find(".")]
for file in sorted(fileList):
    rootFile[file] =  ROOT.TFile(file)
    listOfHistoKeys = ROOT.gDirectory.GetListOfKeys();
    sampleName = getHistos(listOfHistoKeys, histos, graphs, samplePalette, filter, negFilter)
    spName[sampleName] =  splitDirName(sampleName, strippedText)

keys =  histos.keys()
keys.sort()
findPlotTogetherHisto(plotFilter, plotTogether, keys,  toBePlotAlone, toBePlotTogether)


###Stats from histos
#### a loop is instatiated over hist keys, a global STATS[sample][quant] dict 
#### is created to hold the statistics of samples
for quant in keys: 
    for sample in histos[quant].keys():
        myH = histos[quant][sample]
                
        if not STATS.has_key(sample): STATS[sample]={'Error':{}}
        mySTATS = STATS[sample]
        ### success/error stats: if no CpuPerc value found, no successes
        if quant == "Error": 
            mySTATS["Failures"] = myH.Integral()
            if not histos.has_key("CpuPercentage"):
                mySTATS["Success"] = 0
            elif not histos["CpuPercentage"].has_key(sample):
                mySTATS["Success"] = 0
            else:
                mySTATS["Success"]  =  histos["CpuPercentage"][sample].Integral() #- STATS[sample]["Failures"] 

            for i in range(myH.GetNbinsX()):
                errLabel = myH.GetXaxis().GetBinLabel(i+1)
                if errLabel!="": 
                    if not mySTATS["Error"].has_key(errLabel): 
                        mySTATS["Error"][errLabel] = 0
                    #print errLabel, myH.GetBinContent(i+1)
                    mySTATS["Error"][errLabel] = 100*round(myH.GetBinContent(i+1)/mySTATS["Failures"],1)

            #plotting the percentage of error over ALL jobs
            Total = mySTATS["Success"]+ mySTATS["Failures"]
            if Total!=0:
                myF = ROOT.TF1("myF",str(Total),0,2000)
                myH.Divide(myF)
                
        else: 
            ### Here X is the Producer/module label, Y the actual value. Only the first bin is filled
            if quant.find("TimeModule")!=-1:
                #bin = 1
                #while bin <= myH.GetNbinsX():
                mean = myH.GetBinContent(1)
                error = myH.GetBinError(1)
            ### all the others
            else:
                mean =  myH.GetMean(1)
                error = myH.GetRMS(1) 
            mySTATS[quant] = (mean, error)

        ### histos rebinning
        wBinWidth = -1
        if myH.GetName().find('msecs') !=-1 or myH.GetName().find('Time') !=-1: wBinWidth =options.BinWidthTime 
        if quant!="Error": doRebin(myH, wBinWidth)
        ### get range infos
        if not options.noAutoBin:
            if not xAxisRange.has_key(quant): xAxisRange[quant] = [1000000000,0]
            getMaxHistoRange(myH, xAxisRange[quant])
        

### recreating error histograms
ERROR_CODES = []
for sample in STATS.keys():
    for code in STATS[sample]['Error'].keys():
        if not code in  ERROR_CODES: ERROR_CODES.append(code)
ERROR_CODES = sorted(ERROR_CODES)
ERROR_HISTOS = {}
for sample in STATS.keys():
    histos['Error'][sample].Delete()
    histos['Error'][sample] = ROOT.TH1F('QUANTError-SAMPLE'+sample,sample,200,0,1)
    for code in ERROR_CODES:
        if len(STATS[sample]["Error"].keys())==0: continue
        if STATS[sample]["Error"].has_key(code):
            histos['Error'][sample].Fill(code, float(STATS[sample]['Error'][code]) )
        else:
            histos['Error'][sample].Fill(code, 0. )


### legend entries for each sample, needed also for Twiki stats
legLabel = {}
for sample in sorted(spName.keys()):
    legLabel[sample] = ""
    if isinstance(spName[sample], str):
        legLabel[sample] += spName[sample]
      
    else:
        for x in legendComposition:
            legLabel[sample] += spName[sample][x]+" "

### png filenames. takes info from spName only from the first sample
### also setting histoTitle
PNG_NAME=""
histoTitle = ""
sampleKey = spName.keys()[0]
if isinstance(  spName[sampleKey], str):
    PNG_NAME = sampleKey
else:
    for x in PNG_NAME_FORMAT:
        if spName[sampleKey].has_key(x) and not isinstance(spName[sampleKey], str): 
            PNG_NAME+=spName[sampleKey][x]+"-"
        else: PNG_NAME += x+"-"
    PNG_NAME = PNG_NAME[:-1]
    for x in sampleTitles:
        if spName[sampleKey].has_key(x): histoTitle += spName[sampleKey][x]+" "




### printing statistics
printWikiStat(STATS, "", ".*(min|max).*", legLabel, histoTitle)
if not options.drawPlots: exit(0)

if options.saveRoot: rootOutFile = ROOT.TFile.Open( PNG_NAME+".root","recreate")


legend = {}
canvas = {}
### plotting stand alone histos
for quant in toBePlotAlone:
    if quant in summaryPlots: continue
    histoKeys =  histos[quant].keys()
    histoKeys.sort()
    maxY = 0.0
    firstLabel=''
    for histo in histoKeys:
        myH = histos[quant][histo]
        setHisto( myH, samplePalette[histo], "","",quant, 1 )
        if not options.noAutoBin:
            myH.GetXaxis().SetRangeUser(xAxisRange[quant][0], xAxisRange[quant][1])
        ### finds the histo with the max height
        firstLabel, maxY = getMaxHeightHisto( firstLabel, myH, histo,  maxY, quant )

    ### if all histos are empty, do not plot
    if len(firstLabel)<2: continue
    canvas[quant] = createCanvas(PNG_NAME+"-"+quant)
    legend[quant] = createLegend()
    ### actual plotting
    if quant != "Error":  histos[quant][firstLabel[1]].DrawNormalized(drawOpt)
    else:  histos[quant][firstLabel[1]].Draw(drawOpt)
    for histo in histoKeys:
        myH = histos[quant][histo]
        legend[quant].AddEntry( myH, legLabel[sample], "l" )
        if histo==firstLabel[1]: continue
        if quant != "Error": myH.DrawNormalized(drawOpt+" sames")
        else:  myH.Draw(drawOpt+" sames")
    legend[quant].Draw()
    if options.savePng:
        canvas[quant].Update()
        canvas[quant].SaveAs(LABEL+cName+"-"+quant+".png") 


### plotting overlapping plots
for sel in toBePlotTogether.keys():
    ### not plotting plots already in summary canvas
    if sel in summaryPlots: continue
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
            color = 1
            if sePalette.has_key(seType): color = sePalette[seType]
            setHisto(histos[quant][histo], samplePalette[histo], color ,"",sel, 1 )
            if not options.noAutoBin:
                histos[quant][histo].GetXaxis().SetRangeUser(xAxisRange[quant][0], xAxisRange[quant][1])
           
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo, maxY, quant, goodHistos[quant])
                
    if firstLabel == (): continue
    canvas[sel] = createCanvas(PNG_NAME+"-"+sel)
    legend[sel] = createLegend()
    histos[firstLabel[0]][firstLabel[1]].DrawNormalized(drawOpt)
    
    for quant in toBePlotTogether[sel]:
        for histo in goodHistos[quant]:
            legend[sel].AddEntry(histos[quant][histo],legLabel[histo]+" "+quant.split("-")[0] ,"l" )
            if quant==firstLabel[0] and histo==firstLabel[1]: continue
            histos[quant][histo].DrawNormalized(drawOpt+" same")
            
    legend[sel].Draw()
    if options.savePng:
        canvas[sel].Update()
        canvas[sel].SaveAs(PNG_NAME+"-"+sel+".png") 






### plot graphs
toPlot = False
#if "TimeEvent" in plotFilter: toPlot = True
#if "dstat" in plotFilter: toPlot = True

graphCanvas = {}
mGraph = {}
for quant in graphs.keys():
#    if not toPlot: continue
    if quant.find("dstat")!=-1:
        printGraph(quant, graphs, graphCanvas, mGraph, legend, legLabel, samplePalette, PNG_NAME, "seconds")
        if options.savePng:
            graphCanvas[quant].Update()
            graphCanvas[quant].SaveAs(PNG_NAME+"-"+quant+".png") 




### plotting TimeModule producers timing stats
if "TimeModule" in plotFilter: toPlot = True

if toPlot:
    isFirst = True
    TimeModuleC = createCanvas(LABEL+cName+"-TimingModule")
    TimeModuleL = createLegend()
    TimeModule_H  = {}

for sample in STATS.keys():
    if not toPlot: continue

    TimeModule_H[sample]  = ROOT.TH1F(sample+"-TimeModule","",10,0,1)
    for quant in STATS[sample].keys():
        if quant.find("TimeModule")==-1: continue
        bin = TimeModule_H[sample].Fill(quant[len("TimeModule_"):], STATS[sample][quant][0])
        TimeModule_H[sample].SetBinError(bin,STATS[sample][quant][1] )
        TimeModule_H[sample].SetLineColor(  samplePalette[sample] )
#setHisto(TimeModule_H[sample] , samplePalette[sample], 1 ,"",sel, 1 )
        #firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][histo], histo, maxY, quant, goodHistos[quant])
    if isFirst:
        TimeModule_H[sample].DrawNormalized(drawOpt)
        isFirst = False
    else:
       TimeModule_H[sample].DrawNormalized(drawOpt+" sames")
   
if toPlot:
    if options.savePng:
        TimeModuleC.Update()
        TimeModuleC.SaveAs(PNG_NAME+"-TimingModule.png") 


#Print grand view
if not doSummary: popen("sleep 6000000000")

viewCanvas = {}
viewCanvas["Overview"] = summaryPlots

viewTCanvas = {}
for c in viewCanvas.keys():
    ROOT.gStyle.SetCanvasDefH(800);
    ROOT.gStyle.SetCanvasDefW(1200); 
    viewTCanvas[c] = createCanvas(PNG_NAME+"-"+c) 
    #ROOT.gPad.SetFillColor(0)
    #ROOT.gPad.SetBorderSize(0)

    divideCanvas( viewTCanvas[c], len(viewCanvas[c]) )
    i=1
    for quant in viewCanvas[c]:
        viewTCanvas[c].cd(i)
        maxY = 0.0
        firstLabel=()
        legend[quant] = createLegend()

        if not histos.has_key(quant):
            print "[WARNING] Histo "+quant+" not available"
            continue
        for h in sorted(histos[quant].keys()):
            setHisto(histos[quant][h], samplePalette[h], "","",quant, 1 )
            
            if not options.noAutoBin:
                histos[quant][h].GetXaxis().SetRangeUser(xAxisRange[quant][0], xAxisRange[quant][1])
            
            firstLabel, maxY = getMaxHeightHisto( firstLabel, histos[quant][h], h,  maxY, quant )
            histos[quant][h].SetLineWidth(2)
            legend[quant].AddEntry(histos[quant][h],legLabel[h] ,"l" )
        i+=1

        if firstLabel == (): continue
        if quant.find("Error")==-1:
            histos[firstLabel[0]][firstLabel[1]].DrawNormalized(drawOpt)
        else:
            histos[firstLabel[0]][firstLabel[1]].Draw(drawOpt)


        for h in histos[quant].keys():
            histolabel = h
            if h==firstLabel[1]: continue
            if quant.find("Error")==-1:
                histos[quant][h].DrawNormalized(drawOpt+" same")
            else:
                histos[quant][h].Draw(drawOpt+" same")

        legend[quant].Draw()

    viewTCanvas[c].Draw()
    if options.savePng:
        viewTCanvas[c].Update()
        viewTCanvas[c].SaveAs(PNG_NAME+cName+"-"+c+".png") 

histo_summary = {} 
plotHistoFromStats(histo_summary, STATS, summaryPlots, legendComposition, strippedText)
ROOT.gStyle.SetPadBottomMargin(0.2)
ROOT.gStyle.SetPadLeftMargin(0.15)
ROOT.gStyle.SetCanvasDefH(800);
ROOT.gStyle.SetCanvasDefW(1200);

canvas_summary =  createCanvas(PNG_NAME+"_summary")
#{}
divideCanvas( canvas_summary, len(histo_summary))
cN=1
for plot in histo_summary.keys():
    canvas_summary.cd(cN)
    ROOT.gStyle.SetPadLeftMargin(20)
    cN += 1
    histo_summary[plot].SetBarOffset(0.5)
    histo_summary[plot].SetStats(0000000)
    histo_summary[plot].GetYaxis().SetTitleOffset(1.7)
    histo_summary[plot].GetXaxis().SetLabelSize(0.05)
    histo_summary[plot].SetTitle(histoTitle)
    if options.saveRoot:  histo_summary[plot].Write()
    else:
        #canvas_summary[plot] = createCanvas(PNG_NAME+"-"+plot+"_summary")
        histo_summary[plot].Draw("h e")
if options.savePng:
    canvas_summary.Update()
    canvas_summary.SaveAs(PNG_NAME+cName+"-Summary.png") 
        
if options.saveRoot: rootOutFile.Close()

popen("sleep 60000")
