#!/bin/env python

from sys import exit, argv
from os import popen, getenv, path, environ
from optparse import OptionParser
import json

from DBSAPI.dbsApi import DbsApi
from DBSAPI.dbsException import *
from DBSAPI.dbsApiException import *
#from DBSAPI.dbsOptions import DbsOptionParser

from dbs_utils import *
#from dbs_transferRegister import getSeName, getDatasetBlockList


def deleteReplicaFromBlock(self, block, storage_element):
    try:
        #Calling the Implementation function
        from dbsApiDeleteReplicaFromBlock import dbsApiImplDeleteReplicaFromBlock
        return  dbsApiImplDeleteReplicaFromBlock(self, block, storage_element)
    except Exception, ex:
        if (isinstance(ex,DbsApiException) or isinstance(ex,SAXParseException)):
            raise ex
        else:
            raise DbsApiException(args="Unhandled Exception: "+str(ex), code="5991")


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    
    question is a string that is presented to the user.
    default is the presumed answer if the user just hits <Enter>.
    It must be yes (the default), no or None (meaning
    an answer is required of the user).
    
    The answer return value is one of yes or no.
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    
    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
            


usage = """Usage: """+argv[0]+""" [--dbs=ph01|ph02] [--all] [--site=TX_YY_SITE] dataset

If --all is used, the the dataset will be unregistered and deleted from ALL the sites. Otherwise,
it will only be deleted and invalidated from the site specified in --site.

The invalidation is actually done through the DBSInvalidateDataset.py provided by CRAB [*]. If you
just want to invalidate a dataet, but not to delete the data from the SE, try to use this tool instead.

[*]
https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideCrabForPublication?redirectedfrom=CMS.SWGuideCrabForPublication#Invalidate_a_dataset_in_DBS
""" 

myparser = OptionParser(usage = usage, version="")
myparser.add_option("--dbs",action="store", dest="DBS",default="ph02",
                  help="DBS instance, can be: ph01, ph02")
myparser.add_option("--all",action="store_true", dest="ALL",default=False,
                  help="Delete the sample from all the sites, and invalidate the dataset")
myparser.add_option("--site",action="store", dest="SITE",default="",
                  help="""Delete the sample from this site, both physically and from DBS (just the replica information. If the dataset is 
                  available at other sites, it is still VALID in DBS). """)
myparser.add_option("--yes",action="store_true", dest="YES",default=False,
                    help="""Answer YES to all the questions. USE IT WITH CARE! """)

myparser.add_option("--debug",action="store_true", dest="DEBUG",default=False,
                    help="Verboooose")


(options, args) = myparser.parse_args()


if len(args)==0:
    print usage
    print "\n[ERROR] Please give a dataset name"
    exit(1)
    
###Options sanity check
if options.SITE=="" and options.ALL==False:
    print "Select one site targeted for deletion and invalidation or --all to delete and invalidate from all sites. Exiting."
    exit(1)
elif options.SITE!="" and options.ALL!=False:
    print "Select one site targeted for deletion and invalidation or --all to delete and invalidation from all sites. Exiting."
    exit(1)


### Checking CMSSW env and version
testCMSSW = getenv("CMSSW_VERSION")
if testCMSSW is None:
    print "[ERROR] CMSSW env is not set, exiting..."
    exit(1)

IS_CMSSW4 = True
CMSSW_major = testCMSSW[ len("CMSSW_"): len("CMSSW_")+1]
if float(CMSSW_major) <4:
    IS_CMSSW4 = False
    #print "[ERROR] This release of "+argv[0]+" only works for CMSSW_4_X_Y"
    #exit(1)
    
### CRAB env (this is one of the vars I was able to find, eg CRABPATH is not "export"ed)
testCRAB = getenv("CRABLIBPYTHON")
if testCRAB is None:
    print "[ERROR] CRAB env is not set, exiting..."
    exit(1)

### checks existance of proxy
pipe = os.popen("voms-proxy-info")
if pipe.close()!=None:
    print "[ERROR] Grid Proxy not found. Please create a voms-proxy before using this program: voms-proxy-init -voms cms"
    exit(-1)
                            

DATASET=args[0]
DBS_SERVER = {"ph01":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_01_writer/servlet/DBSServlet",
              "ph02":"https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet"}



### defining DBS env
opts = dbsOpts()
opts.instance = 'cms_dbs_ph_analysis_02'
opts.url = DBS_SERVER[options.DBS]
api = DbsApi(opts.__dict__)



### Invalidate the daatset (--invalidate only)
#if options.INVALIDATE:
#    print "----- Invalidating dataset"
#    command = "DBSInvalidateDataset.py --DBSURL="+DBS_SERVER[options.DBS]+" --datasetPath="+DATASET+" --files"
#    out = popen(command).readlines()
#    if out!=[]: print out
#    exit(1)        

## finding sites
SITES = []
SiteToSe, SeToSite = getSeName()

out = popen("""dbs search --url="""+DBS_SERVER[options.DBS]+""" --query=\"find site where dataset="""+DATASET+"""\"""")
for line in out:
    line = line.strip('\n').strip()
    if line=="": continue
    if line.find('.')==-1 or line.find('Using')!=-1: continue
    mysite = line.strip('\n')
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
if not options.ALL:
    if not options.SITE in SITES:
        print "[ERROR]: selected site does not host any data, exiting..."
        exit(1)
    else:
        SiteDelList.append(options.SITE)
else:
    SiteDelList = SITES

Blocks = getDatasetBlockList(api, DATASET)

failedFiles = []


###recap and ask for confirmation
recap_text = "";
print "\n############# ACTIONS YOU HAVE SELECTED"
   
for site in SITES:
    ### continue if not the selected site
    if options.SITE!="" and site!=options.SITE: continue
    recap_text += "----- Removing files from "+site+" and relative DBS entry\n"

if options.ALL:
    recap_text += "----- ALL the copies will be deleted, and the dataset INVALIDATED in dbs"
print recap_text
print "#############\n "

if not options.YES:
    answer = query_yes_no("Are you sure to continue?","no")
    if answer != True:
        print "Exiting..."
        exit(1)


### the actual deletion cycle
for site in SITES:
    ### continue if not the selected site
    if options.SITE!="" and site!=options.SITE: continue
    
    ### get the pfn string
    lfnRoot = fileList[0][:fileList[0].rfind("/")]
    command = "wget --no-check-certificate -O- \"https://cmsweb.cern.ch/phedex/datasvc/xml/prod/lfn2pfn?node="+site+"&protocol=srmv2&lfn="+lfnRoot+"\" 2>/dev/null |sed -e \"s/.*pfn='\([^']*\).*/"""+r"\1\n"+"""/\" 2>/dev/null"""
    pfnRoot = popen(command).readlines()[0].strip('\n')
    ### looping over files
    failedDeletions = 0
    print "Deletion in progress..."
    for f in fileList:
        newF = f.replace(lfnRoot,pfnRoot)
        command = "lcg-del -b -D srmv2 -l "+newF
        if options.DEBUG: print command
        out = popen(command).readlines()
        if out!=[]:
            print "### Error "
            print out
            for o in out:
                ### simple error check
                if o.find("No such file")!=-1:
                    alreadyDeleted = True
                    break
            if not alreadyDeleted:
                failedDeletions +=1
                failedFiles.append(newF)

    if failedDeletions!=0:
        print "------ ERROR ------"
        print "Some file deletion failed (see above), DBS invalidation part will continue but you have to take care of these orphan files!"
        print "Failed files for "+ site +":\n"
        for x in failedFiles:
            print x
        print "\n"
        #continue

    ### Delete the subdir
    out = popen("srmrmdir "+pfnRoot).readlines()
    # if subdir is not empty, usually is like this
    #         ['Return code: SRM_NON_EMPTY_DIRECTORY\n', 'Explanation: non empty directory, no recursion flag specified \n', '\n']
    if out!=[]:
        if out[0].find("SRM_NON_EMPTY_DIRECTORY"):
            SE_ROOT = pfnRoot[ : pfnRoot.find("=")+1]
            print "\n[WARNING]: "+out[1].strip("\n")
            print "[WARNING] check the directory content wit the command:"
            print "[WARNING]      srmls "+pfnRoot
            print "[WARNING] you may want to maually clean up the directory, e.g. with a similar command:"
            print "[WARNING]    for i in `srmls "+pfnRoot+" | awk '{print $2}'`; do srmrm "+SE_ROOT+"$i ; done"
            print "[WARNING] and then delete the parent directory/ies with srmrmdir\n"
        else: print "\n[WARNING]: ", out

    print "\n---Removing the dataset from DBS for SE: " +site
    # List all storage elements
    print "\nDeleting block replica from "+site
    for block in Blocks:
        try:
            if not IS_CMSSW4:
                api.deleteReplicaFromBlock( block["Name"], str(SiteToSe[site]) )
            else:
                deleteReplicaFromBlock( api, block["Name"], str(SiteToSe[site]) )
            print "Block replica "+block["Name"]+" removed"
        
        except DbsApiException, ex:
            print "Caught API Exception %s: %s "  % (ex.getClassName(), ex.getErrorMessage() )
            if ex.getErrorCode() not in (None, ""):
                print "DBS Exception Error Code: ", ex.getErrorCode()
            

### invalidate dataset after deletion has been performed for all sites
if options.ALL:
    print "\n----- Invalidating dataset"
    command = "DBSInvalidateDataset.py --DBSURL="+DBS_SERVER[options.DBS]+" --datasetPath="+DATASET+" --files"
    out = popen(command).readlines()
    if out!=[]:
        for o in out:
            print o.strip("\n")
