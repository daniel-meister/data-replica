#!/usr/bin/env python
#
# Revision: 1.3 $"
# Id: DBSXMLParser.java,v 1.3 2006/10/26 18:26:04 afaq Exp $"
#
# API Unit tests for the DBS JavaServer.
import sys,os
try:
    from DBSAPI.dbsApi import DbsApi
except:
    print "DBSAPI cannot be loaded... have you set up CMSSW environment?"
    sys.exit(1)
from DBSAPI.dbsException import *
from DBSAPI.dbsApiException import *
#from DBSAPI.dbsOptions import DbsOptionParser
from DBSAPI.dbsPrimaryDataset import DbsPrimaryDataset
from DBSAPI.dbsFileBlock import DbsFileBlock
from DBSAPI.dbsProcessedDataset import DbsProcessedDataset

from dbs_utils import *

import xml.dom.minidom
from xml.dom.minidom import Node

import data_replica 



PREFERRED_SITES = []
DENIED_SITES = ["T0","MSS"]


### TODO:
# block transfer/registration? --block option

usage = """Usage: """+sys.argv[0]+""" [--dbs=ph01|ph02] --to-site=TX_YY_SITE dataset

""" 

myparser = OptionParser(usage = usage, version="")
myparser.add_option("--dbs",action="store", dest="DBS",default="ph02",
                  help="DBS instance, can be: ph01, ph02 (default)")
myparser.add_option("--to-site",action="store", dest="TO_SITE",default="",
                  help="Destination site. ")
myparser.add_option("--whitelist",
                    action="store", dest="WHITELIST", default="",
                    help="Sets up a comma-separated White-list (preferred sites). Transfers will start from these sites. Sites not included in the whitelist will be not excluded.")
myparser.add_option("--blacklist",
                    action="store", dest="BLACKLIST", default="",
                    help="Sets up a comma-separated Black-list (excluded sites).")
        
#myparser.add_option("--block",action="store_true", dest="INVALIDATE",default=False,
#                  help="The argument is a block, not a dataset")

(options, args) = myparser.parse_args()

### Checking CMSSW env
testCMSSW = os.getenv("CMSSW_BASE")
print "CMSSW env is set to "+ testCMSSW
if testCMSSW is None:
    print "CMSSW env is not set, exiting..."
    exit(1)

if len(args)!=1:
    print "Please give a dataset name"
    exit(1)
if options.TO_SITE=="":
    print "Please give a destination"
    exit(1)   

DBS_SERVER = {"ph01":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_01_writer/servlet/DBSServlet",
              "ph02":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet"}
DATASET = args[0]
TO_SITE = options.TO_SITE

###SiteToSE and SEtoSite translation dicts, I want these global
SiteToSe, SeToSite = getSeName()


#Example
# $1 --to-site=T3_CH_PSI --from-site=T2_CH_CSCS dataset [or --block block]
#optManager  = DbsOptionParser()
#(opts,args) = optManager.getOpt()
opts = dbsOpts()
opts.instance = 'cms_dbs_ph_analysis_02'
opts.url = 'https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet'
api = DbsApi(opts.__dict__)


#def getBlockListFile(DATASET,BLOCK):
    #optManager  = DbsOptionParser()
    #(opts,args) = optManager.getOpt()
    #opts.instance = 'cms_dbs_ph_analysis_02'
    #opts.url = 'https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet'
    #api = DbsApi(opts.__dict__)

#    fileList = []
#    for afile in api.listFiles(path=DATASET, blockName=BLOCK):
#        fileList.append( afile['LogicalFileName'] )
#    return fileList



def createFileTxt(fileList):
    fileName = 'fileList_'+str(os.getpid())+".txt"
    myF = open(fileName, 'w')
    for f in fileList:
        myF.write(f+"\n")
    myF.close()
    print fileName
    return fileName

class drOptions:
    usePDS = False
    Replicate = True
    WHITELIST = ""
    BLACKLIST = ""
    RECREATE_SUBDIRS = False
    CASTORSTAGE = False
    DEBUG = False
    TOOL='lcg-cp'
    DRYRUN = False
    pass

def addBlockReplica(api,BLOCK, SE):
    try:
        print "Adding block "+BLOCK+" to SE "+SE
        block = DbsFileBlock (
            Name=BLOCK
            )
        
        api.addReplicaToBlock( BLOCK, str(SE))
    except DbsApiException, ex:
        print "Caught API Exception %s: %s "  % (ex.getClassName(), ex.getErrorMessage() )
        if ex.getErrorCode() not in (None, ""):
            print "DBS Exception Error Code: ", ex.getErrorCode()


### arrange sources, putting preferred ones before
def arrange_sources(sitelist,PREFERRED_SITES, DENIED_SITES ):
    new_sitelist = []
    notPref_sitelist = []
    for entry in sitelist:
        SiteName = SeToSite[entry["Name"]]
        allowed = True
        for dSite in DENIED_SITES:
            if dSite in SiteName:
                allowed = False
                break
        if not allowed:
            continue

        preferred=False
        for pSite in PREFERRED_SITES:
            if SiteName.find(pSite)!=-1:
                new_sitelist.append(entry)
                preferred = True
        if preferred: continue    
        notPref_sitelist.append(entry)

    for entry in notPref_sitelist:
        new_sitelist.append(entry)
    return new_sitelist

    

def dbs_transferRegister(DATASET, TO_SITE):
    #SiteToSe, SeToSite = getSeName()
    myBlocks = getDatasetBlockList(api, DATASET)

    if myBlocks!=1:
        totalDatasetSize = 0
        for block in myBlocks:
            totalDatasetSize += block['BlockSize']

        print "Dataset Size: "+ str(totalDatasetSize/(1024*1024*1024)) +" GB"

        for block in myBlocks:
            print "\n------- Copying block: "+ block['Name']
            print "Block Size: "+str( float(block['BlockSize'])/(1024*1024*1024))+" GB"
            logfile = "data_replica_"+str(os.getpid())+".log"
            fileList = getBlockListFile(api,DATASET,block['Name'])
            fileName = createFileTxt( fileList)
            myOptions = drOptions()
            myOptions.TO_SITE = TO_SITE
            myOptions.logfile = logfile
            
            sourceSEs = block['StorageElementList']
            data_replica.setBlackWhiteSiteList(options,PREFERRED_SITES, DENIED_SITES  )
            filteredSourceSEs = arrange_sources(sourceSEs ,PREFERRED_SITES, DENIED_SITES )
                        
            if filteredSourceSEs == []:
                print "[ERROR] No sites found for block:\n ",block['Name'],"\nplease review your blacklist. Exiting..."
                exit(1)
            for se in filteredSourceSEs:
                print "SE: " +se['Name']
                myOptions.FROM_SITE = SeToSite[ se['Name'] ]
                print "Copying from "+myOptions.FROM_SITE
                drExit = data_replica.data_replica([fileName], myOptions)
                if drExit!=0:
                    print "Some errors in copying, block not added to replica"
                    ### print error files?
                else:
                    print "\nCopy succeded for block "+ block["Name"]+", registering in DBS..."
                    addBlockReplica(api, block['Name'], SiteToSe[TO_SITE])
                    print os.getcwd()+"/"+fileName
                    os.unlink( os.getcwd()+"/"+fileName)
                    break
                
if __name__=="__main__":
    
    dbs_transferRegister(DATASET, TO_SITE)
    
