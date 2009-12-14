#!/bin/env python
#################################################################
# data_replica.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: data_replica.py,v 1.6 2009/12/14 16:57:07 leo Exp $
#################################################################


import os
from os import popen, path
from sys import argv,exit
from optparse import OptionParser
from time import time


PREFERRED_SITES = [""]
DENIED_SITES = ["HU"]
PROTOCOL = "srmv2"

SRM_OPTIONS = "-streams_num=1 "
#SRM_OPTIONS += "-cksm_type=negotiate "
#SRM_OPTIONS += "-overwrite_mode=ALWAYS "
SRM_OPTIONS += "-retry_num=1 "
SRM_OPTIONS += "-request_lifetime=6000 "

usage = """usage: %prog [options] list_file_to_be_transferred [dest_dir]

    This program will replicate a list of files from a site to another one using SRM

    list_file_to_be_transferred is a list of LFN you want to replicate to a site

    dest_dir must be a complete PFN, eg file:///home/user/, if none it will be retrieved from the lfn
    information and the destination site

    you must at least declare [dest_dir] or the --to_site option

    Sites must have a standard name, e.g. T2_CH_CSCS

    
[USE CASES]

  * Replicate a file list using DBS. In this case, a source nodes list is retrieved from PhEDEx data service: 

      data_replica --dbs filelist.list --to_site YOUR_SITE

  * Replicate a file list using DBS and giving a destination folder:

      data_replica --dbs filelist.list --to_site YOUR_SITE /store/user/leo

  * Replicate a file list NOT registered in DBS. In this case, you should specify --from_site.

      data_replica filelist.list --from_site FROM_SITE --to_site YOUR_SITE

  * Replicate a file list NOT registered in DBS, giving a destination folder.Also in this case, you should specify --from_site.

      data_replica filelist.list --from_site FROM_SITE --to_site YOUR_SITE /store/user/leo

  * Copying data locally: in this case you don't have to give the --to_site option but you need to give
  a dest_dir in PFN format. Warning: if you intend to use the --recreate_subdirs option, you need to create yourself the local directory structure:

      data_replica filelist.list --from_site FROM_SITE  file:///`pwd`/

  * Copying data from a local area: the list of files should contain only full paths:

  data_replica.py --from_site=LOCAL --to_site T3_CH_PSI local.list /store/user/leo/test1

"""

parser = OptionParser(usage = usage, version="%prog 0.1")
parser.add_option("--logfile",action="store", dest="logfile",default="data_replica.log",
                  help="file for the phedex-like log, default is data_replica.log")
parser.add_option("--dbs",
                  action="store_true", dest="useDBS", default=False,
                  help="Retrieve data distribution from DBS")
parser.add_option("--from_site",
                  action="store", dest="FROM_SITE", default="",
                  help="Source site, eg: T2_CH_CSCS. If LOCAL is indicated, the file list must be a list of global paths")
parser.add_option("--to_site",
                  action="store", dest="TO_SITE", default="",
                  help="Destination file, eg: T2_CH_CSCS")
parser.add_option("--recreate_subdirs",
                  action="store_true", dest="RECREATE_SUBDIRS", default=False,
                  help="Recreate the full subdir tree")

parser.add_option("--dryrun",
                  action="store_true", dest="DRYRUN", default=False,
                  help="Don not actually copy anything")

parser.add_option("--debug",
                  action="store_true", dest="DEBUG", default=False,
                  help="Verbose mode")

(options, args) = parser.parse_args()

if len(args)<1:
    print usage
    exit(1)
    
list = open(args[0])
if len(args) == 2:
    DESTINATION = args[1]
else:
    DESTINATION = ""

if len(args)<1:
    print "USAGE: "+argv[0]+" [options] list_file_to_be_transferred <dest_dir>"
    print "dest_dir must be a complete PFN, eg file:///home/user/"
    exit(1)

if options.useDBS and options.FROM_SITE!="":
    print "You can either query DBS for sites or choose one yourself, not both"
    exit(1)

if not options.useDBS and options.FROM_SITE=="":
    print "You can either query DBS for sites or choose one yourself, but at least one..."
    exit(1)

if options.TO_SITE == "":
    print "WARNING: no dest site given, assuming PFN destination"

if options.TO_SITE != "" and DESTINATION=="":
    print "No DESTINATION given, replicating data using lfn2pfn information"
    
if options.TO_SITE == "" and DESTINATION=="":
    print "You need to specify at least --to_site or dest_dir"    

if options.RECREATE_SUBDIRS and DESTINATION=="" and  options.useDBS:
    print "If you want to create a exact replica, you do not need --recreate_subdirs. Otherwise, you need to specify a dest_dir"
    exit(1)


FAILED_LOGFILE = "failedList_"+options.logfile
SUCCESS_LOGFILE = "successList_"+options.logfile
NOREPLICA_LOGFILE = "noReplica_"+options.logfile

MY_SITE = options.TO_SITE



############CHECK ON MISSING LFN,PROB WHEN NOT IN DBS!!!
###########
############ from local to SE?
##########
############ final statistics
##########
############ if no PFN?

def writeLog(logname,message):
    success_f = open(logname,"a")
    success_f.write(message)
    success_f.close()
                          
    

def printDebug(string):
    if options.DEBUG:
        print "[DEBUG]: "+string


###given a lfn and an array, retrieves and stores in the array a dictionary like {"node", node_name}
def retrieve_siteList(lfn,entry):
    if len(lfn)<2:
        print "[ERROR] NO VALID LFN!!!"
        return 1
    command = """wget -O- \"http://cmsweb.cern.ch/phedex/datasvc/xml/prod/FileReplicas?lfn="""+lfn+"""\"  2>/dev/null"""
    #print command
    out = popen(command)
    init = 0
    for x in out:
        old_x = x
        init = x[init:].find(" node='")
        while init!=-1:
            init += len(" node='")
            site = x[init:][:x[init:].find("'")]
            if site.find("CAF")==-1 and site.find("MSS")==-1 and site.find(MY_SITE)==-1:
                entry.append({"node":site} )
            x = x[init:]
            init = x.find(" node='")

        search_string = " bytes='"
        x = old_x[old_x.find("<file "):]
        init = x.find(search_string)
        while init!=-1:
            init += len(search_string)
            value = x[init:][:x[init:].find("'")]
            size = value
            x = x[init:]
            init = x.find(search_string)

        for y in entry:
            y["size"] = size

        
            

###given a lfn, a site and an array, retrieves and stores in the array a dictionary like {"pfn", value_of_pfn}            
def retrieve_pfn(lfn,site):
    pfn = ""
    #site = entry["node"]
    if len(lfn)<2:
        print "[ERROR] NO VALID LFN!!!"
        return 1

    if site=='LOCAL':
        pfn = "file:///"+lfn
    else:
        command = "wget -O- \"http://cmsweb.cern.ch/phedex/datasvc/xml/prod/lfn2pfn?node="+site+"&protocol="+PROTOCOL+"&lfn="+lfn+"""\" 2>/dev/null |sed -e \"s/.*pfn='\([^']*\).*/"""+r"\1\n"+"""/\" """
        out = popen(command)
        for x in out:
            pfn = x.strip("\n")

    printDebug(pfn)
    return pfn


### given a lfn and an empty dict, fills the dictionary as:
### {lfn_value:[{"node":node_value,"pfn":pfn_name}, {"node":node_value,"pfn":pfn_name}, ...], {..} }
def retrieve_siteAndPfn(lfn,filelist):
    entry = []
    retrieve_siteList(lfn,entry)
    for x in entry:
        x["pfn"] =  retrieve_pfn(lfn,x["node"])
    filelist[lfn]  =entry
                            

### arrange sources, putting preferred ones before
def arrange_sources(sitelist,PREFERRED_SITES ):
    new_sitelist = []
    for entry in sitelist:
        allowed = True
        for dSite in DENIED_SITES:
            if dSite in entry["node"]:
                allowed = False
                break
        if not allowed:
            continue
        for pSite in PREFERRED_SITES:
            if entry["node"] == pSite:
                new_sitelist.append(entry)

        if not entry["node"] in  PREFERRED_SITES:
            new_sitelist.append(entry)

    sitelist= new_sitelist
    return new_sitelist


###
def createSubdir(lfn, DESTINATION):
    pfn_DESTINATION = ""
    
    filename = lfn.split("/")[-1]
    print filename
    
    subdir = ""
    for dir in lfn.split("/")[:-1]:
        subdir += dir+"/"
        
    dir = ""
    for i in DESTINATION.split("/")[:-1]:
        print i
        dir += i+"/"
                    
    pfn_DESTINATION = dir+subdir
    pfn_DESTINATION += filename

    return pfn_DESTINATION

###
def copyFile(source, dest, srm_prot, myLog, logfile):

    myLog["from"] = source["node"]
    myLog["to"] = options.TO_SITE
    myLog["from-pfn"] = source["pfn"]
    myLog["to-pfn"] = dest
    myLog["t-assign"] = time()
    myLog["t-export"] = time()
    myLog["t-inxfer"] = time()
    myLog["t-xfer"] = time()
    myLog["size"] = source["size"]

    SUCCESS = -1
    error_log = ""
    command = "unset SRM_PATH && srmcp "+srm_prot+" "+SRM_OPTIONS+" "+source["pfn"]+" "+dest+ " 2>&1"
    printDebug( command )

    if not options.DRYRUN:
        pipe = popen(command)
        out = pipe.readlines()
        for l in out:
            error_log += l
        exit_status = pipe.close()

        if exit_status == None and len(error_log.strip(" ").strip("\n"))<1: #and (error_log.find("error")==-1 and error_log.find("FAILURE")==-1):
            SUCCESS = 0
        else:
            if exit_status == None:
                exit_status = 1
            exit_status = os.WEXITSTATUS(exit_status)
        
        myLog["t-done"] = time()
        myLog["report-code"] = SUCCESS
        myLog["detail"] = error_log

        writePhedexLog(myLog,logfile)

    else:
        myLog["t-done"] = time()

    if SUCCESS == 0:
        speed = float(myLog["size"])/((1024*1024)*float(float(myLog["t-done"]) - float(myLog["t-xfer"]) ) )
        writeLog(SUCCESS_LOGFILE,myLog["lfn"]+'\n')
    else:
        speed = 0
        #failed_f = open(FAILED_LOGFILE,"a")
        #failed_f.write(myLog["lfn"]+'\n')
        #failed_f.close()

    print "\t\t Elapsed Time: "+str( myLog["t-done"]-myLog["t-assign"] )+ " s"    
    print "\t\t Speed: "+str(speed)+" MB/s"
    print "\t\t Success: "+str(SUCCESS)
    print "\t\t Error: ",parseErrorLog(error_log)
    printDebug("\t\t Full Error: "+error_log)
    printDebug("sleeping")
    os.popen("sleep 10")
    return SUCCESS,error_log    




def parseErrorLog(error_log):
    new_error_log = ""
    init = error_log.find("failed with error:[")
    if init!=-1:
        end = error_log[init:].find("]")
        short_error_log = error_log[init:init+end]
        if short_error_log != "":
            new_error_log = "("+short_error_log+")"
        else:
            init = error_log.find("srm client error:")
            end = error_log[init:]
            short_error_log = error_log[init:]
        if short_error_log != "":
            new_error_log = "("+short_error_log.replace("\n","")+")"
        else:
            new_error_log = "()"

    init = error_log.find("SRM_FAILURE")
    if init != -1:
        new_error_log = "("+error_log[init:error_log.find("explanation")], error_log[error_log.find("state"):error_log.find("srm://")]+")"
    else:
        new_error_log = "("+error_log.replace("\n"," ")+")" 
        
    return new_error_log

###
def writePhedexLog(myLog,logfile):
    f_logfile = open(logfile,"a")

    order = ("task",
             "file",
             "from",
             "to",
             "priority",
             "report-code",
             "xfer-code",
             "size",
             "t-expire",
             "t-assign",
             "t-export",
             "t-inxfer",
             "t-xfer",
             "t-done",
             "lfn",
             "from-pfn",
             "to-pfn",
             "detail",
             "validate",
             "job-log")

    myLog["detail"] = parseErrorLog(myLog["detail"])

    if myLog["to"] == "":
        myLog["to"] = "local"
        
    date_pipe = popen("date -d @"+str(time())+" +\"%F %T\"")
    date = date_pipe.readlines()[0].strip("\n")

    log = date+": FileDownload[24130]: xstats: "
    for x in order:
        log += x+"="+str(myLog[x])+" "

    f_logfile.write(log+"\n")
    f_logfile.close()



###
def logTransferHeader(entry, pfn_DESTINATION):
    print "\n\t Trial from: "+entry["node"]+"--------------"
    print "\t\t From-PFN: "+entry["pfn"]
    print "\t\t To-PFN: "+pfn_DESTINATION
    print "\t\t Size: "+entry["size"] + " bytes ("+str(float(entry['size'])/(1024*1024))+" MB)"




################### BEGIN of MAIN

print """\n##########################################
Welcome to the DataReplica service
from PSI/ETHZ with love
##########################################\n"""

print "Preferred Sites: ",PREFERRED_SITES
print "Denied Sites: ", DENIED_SITES

os.popen("sleep 5")
printDebug("phedex-like logfile: "+ options.logfile)

filelist = {}
pipe = popen("cat "+args[0]+" | wc -l")
total_files = str(pipe.readlines()[0]).strip("\n")
pipe.close()

counter = 0
for lfn in list:
    lfn = lfn.strip("\n").strip(" ").strip("\t")

    if lfn!= "":
        SUCCESS = 1
        counter +=1
        print "\n### Copy process of file "+str(counter)+"/"+str(total_files)+": "+ lfn
        print "\t Use DBS: "+str(options.useDBS)
        print "\t From site: "+str(options.FROM_SITE)
        print "\t To site: "+str(options.TO_SITE)


        myLog = {"task":"1","file":"1","from":"","to":"",
                 "priority":"3", "report-code":"","xfer-code":"", "size":0,
                 "t-expire":9999999999, "t-assign":"","t-export":"","t-inxfer":"",
                 "t-xfer":"","t-done":"","lfn":"","from-pfn":"","to-pfn":"",
                 "detail":"","validate":"()","job-log":"none"}

        myLog["lfn"] = lfn

        if options.useDBS:
            retrieve_siteAndPfn(lfn,filelist)

        if DESTINATION != "":
             if DESTINATION[-1] != "/": DESTINATION+="/"
        else:
            print "Recreating the whole tree to "+options.TO_SITE

        filename = lfn.split("/")[-1]
        if options.TO_SITE!="":
            new_DESTINATION = ""
            if options.RECREATE_SUBDIRS:
                lfn_dir = ""
                for subdir in lfn.split("/")[:-1]:
                    lfn_dir += subdir+"/"
                new_DESTINATION = DESTINATION+lfn_dir
                #new_DESTINATION += filename
            else:
                new_DESTINATION = DESTINATION
            
            if new_DESTINATION != "":
                pfn_DESTINATION = retrieve_pfn(new_DESTINATION,options.TO_SITE)
                if pfn_DESTINATION[-1] != "/": pfn_DESTINATION+="/"
                pfn_DESTINATION += filename
            else:
                pfn_DESTINATION = retrieve_pfn(lfn,options.TO_SITE)

        else:
            if options.RECREATE_SUBDIRS:
                pfn_DESTINATION = createSubdir(lfn, DESTINATION)
            else:
                pfn_DESTINATION = DESTINATION+filename 
            
        srm_prot = ""
        if PROTOCOL == "srmv2":
            srm_prot = "-2"

        if options.useDBS:
            sources_list = arrange_sources(filelist[lfn],PREFERRED_SITES )
            if sources_list == []:
                print "ERROR: no replicas found"
                writeLog(NOREPLICA_LOGFILE,lfn+"\n")
                continue

            for entry in sources_list:
                logTransferHeader(entry, pfn_DESTINATION)
                SUCCESS, error_log = copyFile(entry, pfn_DESTINATION, srm_prot, myLog,options.logfile)
                if SUCCESS == 0:
                    break
                

        else:
            pfn = retrieve_pfn(lfn,options.FROM_SITE)
            source = {"pfn":pfn,"node":options.FROM_SITE}

            if options.FROM_SITE!='LOCAL':
                out_pipe = popen("lcg-ls -l "+pfn+" | awk '{print $5}'")
                out = out_pipe.readlines()
                out_pipe.close()

                if len(out) == 0:
                    print "[ERROR] file does not exist on source"
                    writeLog(NOREPLICA_LOGFILE,myLog["lfn"]+'\n')
                    continue
                source["size"] = out[0].strip("\n")
            else:
                ###Using lfn, as in this case is the full path
                if not os.path.isfile(lfn):
                    print "[ERROR] file does not exist on source"
                    writeLog(NOREPLICA_LOGFILE,myLog["lfn"]+'\n')
                    continue
                source["size"] = str(os.path.getsize(lfn))
                
            filename = lfn.split("/")[-1]

            if options.TO_SITE!="":
                if options.RECREATE_SUBDIRS:
                    subdir = ""
                    for dir in lfn.split("/")[:-1]:
                        subdir += dir+"/"

                    dir = ""
                    for i in DESTINATION.split("/")[:-1]:
                        print i
                        dir += i+"/"
                    
                    pfn_DESTINATION = dir+subdir
                    pfn_DESTINATION += filename
                    pfn_DESTINATION = retrieve_pfn(pfn_DESTINATION,options.TO_SITE)
                else:
                    if DESTINATION == "":
                        pfn_DESTINATION = retrieve_pfn(lfn,options.TO_SITE)
                    else:
                        pfn_DESTINATION = retrieve_pfn(DESTINATION+filename,options.TO_SITE)

            else:
                if options.RECREATE_SUBDIRS:
                    pfn_DESTINATION = createSubdir(lfn, DESTINATION)
                else:
                    pfn_DESTINATION = DESTINATION+filename

                    
            logTransferHeader(source,pfn_DESTINATION)
            SUCCESS, error_log = copyFile(source, pfn_DESTINATION, srm_prot, myLog, options.logfile)

        if SUCCESS != 0:
            writeLog(FAILED_LOGFILE,lfn+"\n")
                          

#logfile.close()






