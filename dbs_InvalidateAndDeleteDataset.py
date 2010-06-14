#!/bin/env python

from sys import exit, argv
from os import popen, getenv, path
from optparse import OptionParser
import json

from DBSAPI.dbsApi import DbsApi
from DBSAPI.dbsException import *
from DBSAPI.dbsApiException import *
#from DBSAPI.dbsOptions import DbsOptionParser

from dbs_utils import *
#from dbs_transferRegister import getSeName, getDatasetBlockList

usage = """Usage: """+argv[0]+""" [--dbs=ph01|ph02] [--all] [--site=TX_YY_SITE] dataset

If --all is used, the the dataset will be unregistered and deleted from ALL the sites. Otherwise,
it will only be deleted and invalidated from the site specified in --site
""" 

myparser = OptionParser(usage = usage, version="")
myparser.add_option("--dbs",action="store", dest="DBS",default="ph02",
                  help="DBS instance, can be: ph01, ph02")
myparser.add_option("--all",action="store_true", dest="DEL_ALL",default=False,
                  help="Delete the sample from all the sites, and invalidate the dataset")
myparser.add_option("--site",action="store", dest="SITE",default="",
                  help="Delete and invalidate the sample from this sites. ")
myparser.add_option("--invalidate",action="store_true", dest="INVALIDATE",default=False,
                  help="Only invalidate the dataset, it does not delete anything")


(options, args) = myparser.parse_args()
if len(args)==0:
    print "Please give a dataset name"
    exit(1)
if options.INVALIDATE:
    if options.SITE!="" or options.DEL_ALL!=False:
        print "--invalidate does not want any other option (--all or --site), please remove them. Exiting."
        exit(1)
elif options.SITE=="" and options.DEL_ALL==False:
    print "Select one site targeted for deletion and invalidation or --all to delete and invalidate from all sites. Exiting."
    exit(1)
elif options.SITE!="" and options.DEL_ALL!=False:
    print "Select one site targeted for deletion and invalidation or --all to delete and invalidation from all sites. Exiting."
    exit(1)


### Checking CMSSW env
testCMSSW = getenv("CMSSW_BASE")
if testCMSSW is None:
    print "CMSSW env is not set, exiting..."
    exit(1)

DATASET=args[0]

DBS_SERVER = {"ph01":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_01_writer/servlet/DBSServlet",
              "ph02":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet"}



### defining DBS env
opts = dbsOpts()
opts.instance = 'cms_dbs_ph_analysis_02'
opts.url = DBS_SERVER[options.DBS]
api = DbsApi(opts.__dict__)
        

### Invalidate the daatset (--invalidate only)
if options.INVALIDATE:
    print "----- Invalidating dataset"
    command = "DBSInvalidateDataset.py --DBSURL="+DBS_SERVER[options.DBS]+" --datasetPath="+DATASET+" --files"
    out = popen(command).readlines()
    if out!=[]: print out
    exit(1)        

## finding sites
SITES = []
SiteToSe, SeToSite = getSeName()

out = popen("""dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find site where dataset="""+DATASET+"""\"""")
for line in out:
    line = line.strip('\n').strip()
    if line=="": continue
    if line.find('.')==-1 or line.find('Using')!=-1: continue
    mysite = line.strip('\n')

    ### get CMS site name from sitedb
    #out2 = popen("wget -O- --no-check-certificate https://cmsweb.cern.ch/sitedb/json/index/SEtoCMSName?name="+mysite+" 2>/dev/null").readlines()[0]
    #out2 = out2.replace("'","\"")
    #if out2.find('Exception')!=-1:
    #    print "ERROR in contacting SiteDB"
    #    exit(1)
    #out2 = out2.replace("'","\"")
    #mysiteCMS = json.loads(out2)['0']["name"]
    SITES.append( SeToSite[mysite] )

## finding file list
fileList = []
out = popen("""dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find file where dataset="""+DATASET+"""\"""")

for line in out:
    if line.find("/store")==-1: continue
    fileList.append(line.strip('\n'))

if len(fileList)==0:
    print "No files in Dataset, exiting."
    exit(1)
    
print "\n"
print "The Dataset is available in " +str(SITES)

SiteDelList = []
if not options.DEL_ALL:
    if not options.SITE in SITES:
        print "[ERROR]: selected site does not host any data, exiting..."
        exit(1)
    else:
        SiteDelList.append(options.SITE)
else:
    SiteDelList = SITES

Blocks = getDatasetBlockList(api, DATASET)


for site in SITES:
    if options.SITE!="" and site!=options.SITE: continue
    
    print "----- Removing files from "+site+" in 10 seconds, press CTRL-C for killing the process"
    popen("sleep 10")
    ### get the pfn string
    lfnRoot = fileList[0][:fileList[0].rfind("/")]
    command = "wget -O- \"http://cmsweb.cern.ch/phedex/datasvc/xml/prod/lfn2pfn?node="+site+"&protocol=srmv2&lfn="+lfnRoot+"\" 2>/dev/null |sed -e \"s/.*pfn='\([^']*\).*/"""+r"\1\n"+"""/\" 2>/dev/null"""
    pfnRoot = popen(command).readlines()[0].strip('\n')
    ### looping over files
    for f in fileList:
        newF = f.replace(lfnRoot,pfnRoot)
        command = "srmrm "+newF
        print command
        out = popen(command).readlines()
        if out!=[]: print out
    print "Removing the dataset from DBS for SE: " +site
    try:
        # List all storage elements
        print ""
        print "deleting block replica from "+site
        for block in Blocks:
            try:
                api.deleteReplicaFromBlock( block["Name"], str(SiteToSe[site]) )
                print "Block replica "+block["Name"]+" removed"
        
    except DbsApiException, ex:
        print "Caught API Exception %s: %s "  % (ex.getClassName(), ex.getErrorMessage() )
        if ex.getErrorCode() not in (None, ""):
            print "DBS Exception Error Code: ", ex.getErrorCode()
            

### Delete the subdir
out = popen("srmrmdir "+pfnRoot).readlines()
if out!=[]: print out

### invalidate dataset
if options.DEL_ALL:
    print "----- Invalidating dataset"
    command = "DBSInvalidateDataset.py --DBSURL="+DBS_SERVER[options.DBS]+" --datasetPath="+DATASET+" --files"
    out = popen(command).readlines()
    if out!=[]: print out
