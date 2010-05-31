#!/bin/env python

from sys import exit, argv
from os import popen, getenv, path
from optparse import OptionParser
import json

usage = """Usage: """+argv[0]+""" [--dbs=ph01|ph02] [--all] [--site=TX_YY_SITE] dataset

If --all is used, the the dataset will be unregistered and deleted from ALL the sites. Otherwise,
it will only be deleted from the site specified in --site
""" 

parser = OptionParser(usage = usage, version="%prog 0.1")
parser.add_option("--dbs",action="store", dest="DBS",default="ph02",
                  help="DBS instance, can be: ph01, ph02")
parser.add_option("--all",action="store_true", dest="DEL_ALL",default=False,
                  help="Delete the sample from all the sites, and unregister the dataset")
parser.add_option("--site",action="store", dest="SITE",default="",
                  help="Delete the sample from this sites. Warning: the dataset won't be unregistered")

(options, args) = parser.parse_args()
if len(args)==0:
    print "Please give a dataset name"
    exit(1)
elif options.SITE=="" and options.DEL_ALL==False:
    print "Select one site targeted for deletion or --all to delete and unregister from all sites. Exiting."
    exit(1)
elif options.SITE!="" and options.DEL_ALL!=False:
    print "Select one site targeted for deletion or --all to delete and unregister from all sites. Exiting."
    exit(1)

### Checking CMSSW env
testCMSSW = getenv("CMSSW_BASE")
if testCMSSW is None:
    print "CMSSW env is not set, exiting..."
    exit(1)

DATASET=args[0]

DBS_SERVER = {"ph01":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_01_writer/servlet/DBSServlet",
              "ph02":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet"}

## finding sites
SITES = []
print """dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find site where dataset="""+DATASET+"""\""""
#exit(1)
out = popen("""dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find site where dataset="""+DATASET+"""\"""")
for line in out:
    line = line.strip('\n').strip()
    if line=="": continue
    if line.find('.')==-1 or line.find('Using')!=-1: continue
    mysite = line.strip('\n')
    #if len(mysite)!=2: continue
    #mysite =  mysite[1].strip()[1:-1].strip('\'')
    ### get CMS site name from sitedb
    out2 = popen("wget -O- --no-check-certificate https://cmsweb.cern.ch/sitedb/json/index/SEtoCMSName?name="+mysite).readlines()[0]
    out2 = out2.replace("'","\"")
    mysiteCMS = json.loads(out2)['0']["name"]
    SITES.append(mysiteCMS)

## finding file list
fileList = []
out = popen("""dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find file where dataset="""+DATASET+"""\"""")
print """dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find file where dataset="""+DATASET+"""\""""
for line in out:
    if line.find("/store")==-1: continue
    fileList.append(line.strip('\n'))

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

for site in SITES:
    print "----- Removing files from "+site+" in 10 seconds, press CTRL-C for killing the process"
    popen("sleep 10")
    ### get the pfn string
    lfnRoot = fileList[0][:fileList[0].rfind("/")]
    command = "wget -O- \"http://cmsweb.cern.ch/phedex/datasvc/xml/prod/lfn2pfn?node="+site+"&protocol=srmv2&lfn="+lfnRoot+"\" 2>/dev/null |sed -e \"s/.*pfn='\([^']*\).*/"""+r"\1\n"+"""/\" """
    pfnRoot = popen(command).readlines()[0].strip('\n')
    ### looping over files
    for f in fileList:
        newF = f.replace(lfnRoot,pfnRoot)
        command = "srmrm "+newF
        print command
        out = popen(command).readlines()
        if out!=[]: print out

### Delete the subdir
out = popen("srmrmdir "+pfnRoot).readlines()
if out!=[]: print out

### invalidate dataset
if options.DEL_ALL:
    print "----- Invalidating dataset"
    command = "DBSInvalidateDataset.py --DBSURL="+DBS_SERVER[options.DBS]+" --datasetPath="+DATASET+" --files"
    out = popen(command).readlines()
    if out!=[]: print out
