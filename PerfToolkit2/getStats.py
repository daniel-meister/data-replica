#!/usr/bin/python
#################################################################
# revampedstats.py
#
# Author: Marco - Andrea Buchmann <marco.andrea.buchmann@cern.ch> and Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: getStats.py,v 1.1 2011/09/14 12:21:16 leo Exp $
#################################################################


### TODO: make a nice check in plotting canvas based on plotFilter
###       use formatting for png filenames (SITE, etc...)
###       add to png filenames also LABEL
###       when usrtime/quantity too small, not plotted
###       better plotting functions!


from sys import argv,exit
from os import popen, path
import re
from utils import *
from optparse import OptionParser

try:
    import ROOT
except:
    print "ROOT cannot be loaded"
    exit(1)
savePng=False;
usage = """sys.argv[0] input.root <input2.root, ...> OR you can search for a variable sys.argv[0] --search WN_net_CPU input.root <input2.root, ...>"""
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
                  help="Preconfigured modes for analysis: SiteMon, SiteMonExt,SiteCfrExt, Default")

#### brand new options
parser.add_option("--search",
                  action="store", dest="dosearch", default=False,
                  help="Search for a given variable and return a list of possibilities.")
parser.add_option("--draw",
                  action="store", dest="drawvars", default=False,
                  help="Draw a given (set of) variable(s): %prog --draw var1,var2,var3,... ; If you're unsure about the name of the variable, use --search first.")
parser.add_option("--config",
                  action="store_true", dest="giveconfig", default=False,
                  help="Show the configuration (number of Jobs etc.) for all provided files")
parser.add_option("--DoSummary",
                  action="store_true", dest="DoSummary", default=False,
                  help="Show the summary table")
parser.add_option("--todo",
                  action="store_true", dest="showtodo", default=False,
                  help="Show the To Do List")
parser.add_option("--morecowbell",
                  action="store_true", dest="cowbell", default=False,
                  help="You want more cowbell?")

(options, args) = parser.parse_args()

### if you want to add a label to canvas names
### sampleTitles stores the name of this sample, eg a T2_CH_CSCS measure with a certaing cfg. It will be used
###     as histo title for sommaries and as header in the tables
PNG_NAME_FORMAT,legendComposition,sampleTitles,filter,negFilter,plotFilter,plotTogether,summaryPlots,doSummary =  setCPTMode(options.Mode)
strippedText=["RHAUTO_", "CMSSW_"] # this in case you want to remove some string from the set name

LABEL=options.Label
PNG_NAME_FORMAT.append(LABEL)

if options.cowbell == True:
  do_cowbell()
  exit(0)

fileList = []
for arg in args:
    if arg.find('*')!=-1 or arg.find('?')!=-1:
        try:
            pipe=os.popen("ls "+arg)
        except:
            print "[ERROR]: files "+ arg+" do not exist; have been thrown away from file list"
            continue
        for p in pipe.readlines():
            fileList.append(p)
    else:
        if not path.isfile(arg):
            print "[ERROR]: file "+arg+" does not exist, has been thrown away from file list"
            continue
        fileList.append(arg)
    

if len(fileList)==0 and options.dosearch!=False:
    print "You have to specify at least one file to search for a variable."
    exit(1)

if len(fileList)==0:
    print "[ERROR] No good files has been given as input, exiting"
    exit(1)

toBePlotAlone = []
toBePlotTogether = {}
samplePalette = {}
histos = {}
branches = {}
#graphs = {}
sePalette = {"dcap":1,"gsidcap":2,"file":5,"local":4,'tfile':5,'rfio':6}
### you need to keep all the TFiles open in order to keep the histos loaded
rootFile = {}
spName = {}
performancetree = {}
infotree = {}
branchlist = {}
STATS = {}
strippedText=["RHAUTO_", "CMSSW_"] # this in case you want to remove some string from the set name

if options.showtodo != False:
  print bcolors.WARNING+"This is my to do list:"+bcolors.ENDC
  print "The error and success rate are determined incorrectly."
  print "Error (the corresponding variables are called Error and ErrorWeight) : Work has been completed but needs testing!"
  print "test everything (including saving) with multiple files"
  
  print bcolors.OKGREEN+"This is what I've already completed:"+bcolors.ENDC
  print "Check file saving (there was a weird png error with TimeJob_CpuPercentage) with some more root files"
  print "open questions (no-auto-bin, label)"
  print "summary table : Working on it!"
  print "saving (png&root) quantities needs to be implemented. done: one root file is gerenated for saveroot, one png per canvas for savepng"
  print "WN implementation needs to be finished - legend problem (disappear). see below."
  print "actual drawing needs to be finished - DONE."
  print "Search function"
  print "config function"
  print "canvas/pad function"
  print "candidate finder function"
  print "legend generator"
  print "pad divider"
  print "wn detector, drawing for wn-type quantities"
  print "special error handling (error&error_weight) in abstract histo maker"
  print "dozens of other functions"
  print "there was a problem with makeabstracthisto - for some reason th2f seem to cause problems (nice ehem 'feature' of pyroot) - circumvented with TGraph. "
  print "there was a problem with create_legend - for some reason legends would never get drawn. scope problem in pyroot. awesome."
  exit(0)

xAxisRange = {}

cName = args[0][:args[0].find(".")]

if options.giveconfig	!=False :
  print_config(fileList)
  exit(0)
fileinformation={}
modevariables=[]
legend=ROOT.TLegend(0.7,0.7,0.85,0.85)
legend.SetFillColor(10)
legend.SetLineColor(10)
legend.SetLineWidth(10)

if(options.saveRoot) :
  outfile = ROOT.TFile("img/output.root","RECREATE");
else :
  outfile=""

for file in sorted(fileList):
    rootFile[file] =  ROOT.TFile(file)
    fileinformation[file]={}
    getinfoabout(file,fileinformation[file])
    performancetree[file] = rootFile[file].Get("Performance")
    infotree[file] = rootFile[file].Get("info_tree")

    branchlist = performancetree[file].GetListOfBranches()
    if options.dosearch== False :
      print "Opening file",file
      if options.drawvars == False:
	## it is pointless to fill all of these if we're dealing with user provided quantities.
	sampleName = fillLists(branchlist, modevariables, branches, histos, performancetree[file], samplePalette, file, filter, negFilter)
	spName[sampleName] =  splitDirName(sampleName, strippedText)

if options.dosearch!= False :
  searchfor(options.dosearch,fileList[0],False) # the last argument basically tells the search to spit out the results on the screen and not just return the result collection
  exit(0)

legends={}

if options.drawvars!=False or options.Mode !=False:
## in this case the user provides us with the variables that (s)he wants to have plotted.
  collection=[]
  canvases={}
  numvar=0
  all_variables=[]
  if options.drawvars!=False :
    processallvariables(options.drawvars.split(","),collection,fileList,performancetree,histos,canvases,fileinformation,legends,STATS,options,outfile)
  if options.Mode !=False :
    processallvariables(modevariables,              collection,fileList,performancetree,histos,canvases,fileinformation,legends,STATS,options,outfile)

if options.DoSummary==True:
  legLabel = {}
  for sample in sorted(spName.keys()):
    legLabel[sample] = ""
    if isinstance(spName[sample], str):
        legLabel[sample] += spName[sample]
      
    else:
        for x in legendComposition:
            if spName[sample].has_key(x):
                legLabel[sample] += spName[sample][x]+" "

  histoTitle = ""
  sampleKey = spName.keys()[0]
  if not isinstance(  spName[sampleKey], str):
    for x in sampleTitles:
        if spName[sampleKey].has_key(x): histoTitle += spName[sampleKey][x]+" "
  PrintSummary(STATS, "", ".*(min|max).*", legLabel, histoTitle)

abort_mission = raw_input("The variables you requested have been plotted and now appear onscreen. If you'd like to close the script, please hit enter")
exit(0)

  
  

