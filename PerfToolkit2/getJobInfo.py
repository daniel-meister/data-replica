#!/usr/bin/python
#################################################################
# cpt_getJobInfo.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: new_cpt_getJobInfo.py,v 1.2 2011/07/01 13:24:14 buchmann Exp $
#################################################################

### plugins moved to a directory

import sys; sys.path.append('/usr/lib/root')
import xml.dom.minidom
from xml.dom.minidom import Node
from sys import argv,exit
import os
from math import sqrt
import re
from optparse import OptionParser

#from bleeding_cpt_utilities import *
import utils
from plugins import *
from array import array


###max x-axis for graphs: ootherwise setting different ranges is difficult
#MAX_GRAPH_X = 1000


isRoot = True



try:
    import ROOT
except:
    print "ROOT cannot be loaded, running textual only"
    isRoot = False
    exit(1)



usage = """For simple CMSRUN jobs, the stdout file must have a name of the form WHATEVER_1.stdout, WHATHEVER_2.stdout, etc, 
and the same apply to the FJR xml files (WHATHEVER_1.xml).
For jobs submitted through CRAB, standard names will be used."""
parser = OptionParser(usage = usage)
#parser.add_option("--no-auto-bin",action="store_true", dest="noAutoBin", default=False,
#                  help="Automatic histo binning")
parser.add_option("--type",action="store", dest="TYPE",default="CRAB",
                  help="Type of the log/xml files, can be CRAB,CMSSW,CMSSWCRAB")
#parser.add_option("--stdout",action="store", dest="STDOUT",default="CMSSW",
#                  help="Name type of stdout file. If your files are named e.g. my_1.stdout, my_2.stdout, ... put 'my'")
#parser.add_option("--fjr",action="store", dest="FJR",default="crab_fjr",
#                  help="Name type of fjr xml file. If your files are named e.g. my_1.xml, my_2.xml, ... put 'my'")

parser.add_option("--dataset",action="store", dest="DATASET",default="NONE",
                  help="Dataset used, default: NONE. This value will be stored in the info_tree TTree")
parser.add_option("--sw",action="store", dest="SW",default="NONE",
                  help="Software used, e.g. CMSSW_4_2_0, default: NONE. This value will be stored in the info_tree TTree")
parser.add_option("--site",action="store", dest="SITE",default="NONE",
                  help="Site tested, e.g. T2_CH_CSCS, default: NONE. This value will be stored in the info_tree TTree")
parser.add_option("--config",action="store", dest="CONFIG",default="NONE",
                  help="Configuration file used, default: NONE. This value will be stored in the info_tree TTree")
parser.add_option("--eventsJob",action="store", dest="EVENTSJOB",default="-1",
                  help="Number of events/job, default: -1. This value will be stored in the info_tree TTree")
parser.add_option("--timestamp",action="store", dest="TIMESTAMP",default="0",
                  help="Timestamp for the test done (UTC), default: 0. This value will be stored in the info_tree TTree")
parser.add_option("--comments",action="store", dest="COMMENTS",default="NONE",
                  help="Various comments, like the number of jobs, etc, default: NONE. This value will be stored in the info_tree TTree")
    
(options, args) = parser.parse_args()


if len(argv)<2:
    print "USAGE: "+argv[0]+" crab_dir <outfile>"
    exit(1)

LOGDIR = args[0]
if len(args)>1:
    OUTFILE = args[1]
else:
    OUTFILE = ""


### Values are: StorageTiming, CrabTiming, Timing, EventTiming, ModuleTiming, ProducerTiming
acceptedSummaries = ['StorageTiming', "CrabTiming", "Timing","ProducerTiming"]
#acceptedSummaries = ['StorageTiming', "CrabTiming" ,"ProducerTiming"]


###discard the first event in histo filling
discardFirstEvent_Module = True
discardFirstEvent_Producer = True

### Init array of quantities
LABELS = [ ]


from ROOT import gROOT


### from hh:mm:ss to secs

def computeErrorStat(job_output, SUMMARY):
    #Computing err statistics
    if not job_output["Success"]:
        for err in job_output["Error"].keys():
            err = str(err)
            if err.find(".")!=-1:
                err = err[:err.find(".")] ### uhm, why?
            
            if not SUMMARY["Error"].has_key(err): SUMMARY["Error"][err] = 0
            SUMMARY["Error"][err] += 1
                #End comp error stat


def makeCleanLabel(inputlabel,job_output):
    cleanlabel=inputlabel.replace("-","_")
    cleanlabel=cleanlabel.replace("+","__")
    return cleanlabel

def pushJobOutput( label, job_output, SINGLE_DIR_DATA):
  if isinstance( job_output[label] , float):
    if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
    SINGLE_DIR_DATA[label].append( job_output[label] )
  elif  isinstance( job_output[label] , int):
    if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
    job_output[label] = int(job_output[label]) 
    SINGLE_DIR_DATA[label].append( job_output[label] )
  elif  isinstance( job_output[label] , list):
    if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = []
    SINGLE_DIR_DATA[label].append( job_output[label])
  elif  isinstance( job_output[label] , dict):
    if not SINGLE_DIR_DATA.has_key(label): SINGLE_DIR_DATA[label] = {}
    SINGLE_DIR_DATA[label] = job_output[label]



def getJobStatistics(LOGDIR,OUTFILE):
    DIR_SUMMARY = {}
    SUMMARY = {} ###stores full stat
    SINGLE_DIR_DATA = {} ###stores single entries
    MEAN_COMP = {} ### stores stat info

    firstDir = True
    tempI=0

    samplesBinEdges = {} #{'lowerBin':{},'upperBin':{}}
    
    #Begin dir analysis
    if os.path.isdir(LOGDIR)==False and os.path.islink(LOGDIR)==False:
        print LOGDIR
        print "[ERROR] Directory not Valid"
        exit(1)


    SUMMARY = {"Success":0, "Failures":0, "Error":{}}
    spDirName = splitDirName(LOGDIR)
    
    OUTFILE = LOGDIR.strip('/').split("/")[-1]+'.root'
    #OUTFILE = 'BUGSQUASH.root' 
       
    print " "
    print "OutFile:",OUTFILE
    print "Analyzing "+LOGDIR

    #totalFiles = 0
    ###Parsing Files
    CRAB_LOGDIR = LOGDIR+"/res/"
    ### use stdout or xml for both?
    if options.TYPE == "CRAB": LOGS = os.popen("ls "+CRAB_LOGDIR+"*.stdout")
    elif  options.TYPE == "CMSSW": LOGS = os.popen("ls "+LOGDIR+"/*.xml")
    elif options.TYPE == "CMSSWCRAB": LOGS = os.popen("ls "+CRAB_LOGDIR+"CMSSW*.stdout")
    else: 
        print "[ERROR] No valid log/xml file given"
        exit(1)
    
    


    ### creating a TTree
    outFile = ROOT.TFile(OUTFILE,"RECREATE")
    perfTree = ROOT.TTree('Performance', 'Performance')
    ### loop over logfiles/jobs
    Total_jobs=0
    Total_successfulJobs=0
    #isFirstJob = True
    valueContainer = {}

    for x in LOGS:
        #Parse crabDir
        x = x.strip('\n')
        if options.TYPE == "CRAB": rValue = parseDir_Crab(LOGDIR, x, acceptedSummaries)
        elif  options.TYPE == "CMSSW": rValue = parseDir_CMSSW( x, acceptedSummaries)
        elif  options.TYPE == "CMSSWCRAB": rValue = parseDir_CMSSWCrab( LOGDIR, x, 'cmssw', acceptedSummaries)

        
        if rValue!=1: job_output = rValue
        else: continue
        #end Parse crabDir
	Total_jobs+=1
	if job_output["Success"]:
	  Total_successfulJobs+=1

        ###UserQuantities
        totalMB = 0
        totalActualMB = 0
        totalReadTime = 0
   
        if job_output.has_key('tstoragefile-read-total-megabytes'): totalMB += float(job_output['tstoragefile-read-total-megabytes'])
        if job_output.has_key('tstoragefile-readv-total-megabytes'): totalMB += float(job_output['tstoragefile-readv-total-megabytes'])
        
        if job_output.has_key('tstoragefile-read-actual-total-megabytes'): totalActualMB += float(job_output['tstoragefile-read-actual-total-megabytes'])
        if job_output.has_key('tstoragefile-readv-actual-total-megabytes'): totalActualMB += float(job_output['tstoragefile-readv-actual-total-megabytes'])


#	print job_output["Job_Number"]

	### TODO: some estimate of read_kB/event
	### TODO: find a good error handling
	computeErrorStat(job_output, SUMMARY)

	### here, we are creating the tree structure, depending on the log content  
	for label in job_output.keys():
	  if not valueContainer.has_key(label):
	    if isinstance( job_output[label] , float) or isinstance( job_output[label] , list) :
	      valueContainer[label]=ROOT.std.vector( float )()
	      perfTree.Branch(str(makeCleanLabel(label,job_output)),valueContainer[str(label)])
	    if label=="Error":
	      valueContainer[label]=ROOT.std.vector( float )()
	      perfTree.Branch(str(makeCleanLabel(label,job_output)),valueContainer[str(label)])
#	      valueContainer[label+"_weight"]=ROOT.std.vector( float )()
#	      perfTree.Branch(str(makeCleanLabel(label,job_output))+"_weight",valueContainer[str(label)])
	  pushJobOutput( label, job_output, SINGLE_DIR_DATA)

	isFirstJob=False
    ###end log cycle
    ###
    
    ###the previous loop gathers the info and creates the tree structure
    ###this one actually fills the tree
    ###TODO: better if conditions
    for job in range(0,Total_successfulJobs):
      for label in SINGLE_DIR_DATA.keys():
	if label=="Error": 	continue
	if isinstance( SINGLE_DIR_DATA[label][job] , float):
	  valueContainer[label].clear()
	  valueContainer[label].push_back(SINGLE_DIR_DATA[label][job])
	elif isinstance( SINGLE_DIR_DATA[label][job] , list):
	  valueContainer[label].clear()
	  for entry in SINGLE_DIR_DATA[label][job]:
	    valueContainer[label].push_back(entry)
      ###tree filling
      perfTree.Fill()
    
#    Still need to record errors:
    label="Error"
    for err in SUMMARY[label].keys():
      print str(err)+" : "+str(SUMMARY[label][err])
      for job in range(0,int(SUMMARY[label][err])):
	valueContainer[label].clear()
	valueContainer[label].push_back(float(err))
	perfTree.Fill()

#############################################3 something entirely new here -- the job info!
    gROOT.ProcessLine(
	  "struct MyStruct {\
	  Char_t site[100];\
          Char_t dataset[200];\
          Char_t sw[100];\
          Char_t config[100];\
	  Char_t script[100];\
	  Char_t eventsJob[100];\
	  Char_t timestamp[100];\
	  Char_t comments[200];\
          Char_t njobs[100];\
	  };" );
    
    from ROOT import MyStruct, AddressOf;
    mystruct = MyStruct();
    info_tree = ROOT.TTree("info_tree","info_tree");
    info_tree.Branch("site",AddressOf(mystruct,'site'),'site/C');
    info_tree.Branch("dataset",AddressOf(mystruct,'dataset'),'dataset/C');
    info_tree.Branch("sw",AddressOf(mystruct,'sw'),'sw/C');
    info_tree.Branch("config",AddressOf(mystruct,'config'),'config/C');
    info_tree.Branch("comments",AddressOf(mystruct,'comments'),'comments/C');
    info_tree.Branch("eventsJob",AddressOf(mystruct,'eventsJob'),'eventsJob/C');
    info_tree.Branch("timestamp",AddressOf(mystruct,'timestamp'),'timestamp/C');
    info_tree.Branch("njobs",AddressOf(mystruct,'njobs'),'njobs/C');
    

#    fullstring=LOGDIR.strip('/').split("/")[-1].replace(".root","")
#    print "starting out with fullstring ",fullstring
#    bla_site = fullstring[0:fullstring.find("-")]
#    bla_rest = fullstring[fullstring.find("-")+1:len(fullstring)]
#    bla_script=bla_rest[0:bla_rest.find("-")]
#    bla_rest = bla_rest[bla_rest.find("-")+1:len(bla_rest)]
#    bla_nevents=int(bla_rest[0:bla_rest.find("-")])
#    bla_rest = bla_rest[bla_rest.find("-")+1:len(bla_rest)]
#    bla_config=bla_rest[0:bla_rest.find("-")]
#    bla_rest = bla_rest[bla_rest.find("-")+1:len(bla_rest)]
#    bla_timestamp=bla_rest[0:bla_rest.find("__")]

    #mystruct.site="%s" % bla_site
    #mystruct.config="%s" % bla_config
    #mystruct.script="%s" % bla_script
    #mystruct.timestamp="%s" % bla_timestamp
    #mystruct.nevents="ne%s" % bla_nevents
    #mystruct.njobs="nj%s" % str(Total_jobs)
    
    mystruct.site="%s" % options.SITE
    mystruct.config="%s" % options.CONFIG
    mystruct.sw="%s" % options.SW
    mystruct.timestamp="%s" % options.TIMESTAMP
    mystruct.eventsJob="ne%s" % options.EVENTSJOB
    mystruct.njobs="nj%s" % str(Total_jobs)
    mystruct.comments="ne%s" % options.COMMENTS

    
    info_tree.Fill()
    
    
###############################################################info tree two
#    information_tree = ROOT.TTree("information_tree","information_tree");
#    label="site";
#    configContainer = {}
#    configContainer[label]=ROOT.std.vector( str )()
#    information_tree.Branch(str(label),configContainer[str(label)])
#    configContainer[label].push_back("blubbie");
#    information_tree.Fill();

######

    
    information_tree = ROOT.TTree("information_tree","information_tree");
    
    configContainer = {}
    
    configunit="site"
    configContainer[configunit]=ROOT.std.vector( str )()
    information_tree.Branch(str(configunit),configContainer[configunit])
    configContainer[configunit].push_back( mystruct.site);
    
    configunit="config"
    configContainer[configunit]=ROOT.std.vector( str )()
    information_tree.Branch(str(configunit),configContainer[configunit])
    configContainer[configunit].push_back(mystruct.config);
    
    configunit="sw"
    configContainer[configunit]=ROOT.std.vector( str )()
    information_tree.Branch(str(configunit),configContainer[configunit])
    configContainer[configunit].push_back( mystruct.sw );
    
    configunit="eventsJob"
    configContainer[configunit]=ROOT.std.vector( str )()
    information_tree.Branch(str(configunit),configContainer[configunit])
    configContainer[configunit].push_back(str(mystruct.eventsJob));
    
    configunit="timestamp"
    configContainer[configunit]=ROOT.std.vector( str )()
    information_tree.Branch(str(configunit),configContainer[configunit])
    configContainer[configunit].push_back(mystruct.timestamp);
    
    
    information_tree.Fill();


#############################################3 /something entirely new here -- the job info!


    outFile.Write()
    outFile.Close()


if __name__ == '__main__':
    getJobStatistics(LOGDIR,OUTFILE)
    from time import gmtime, strftime
    os.environ['TZ'] = 'US/Eastern'
    time.tzset()
#    time.tzname('EST', 'EDT')
    print strftime("%a, %d %b %Y %H:%M:%S and add 2h", gmtime())
    
