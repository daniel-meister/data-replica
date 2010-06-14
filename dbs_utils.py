#!/bin/env python
import sys,os
from DBSAPI.dbsApi import DbsApi
from DBSAPI.dbsException import *
from DBSAPI.dbsApiException import *
from DBSAPI.dbsOptions import DbsOptionParser
from DBSAPI.dbsPrimaryDataset import DbsPrimaryDataset
from DBSAPI.dbsFileBlock import DbsFileBlock
from DBSAPI.dbsProcessedDataset import DbsProcessedDataset
from optparse import OptionParser

import xml.dom.minidom
from xml.dom.minidom import Node

class dbsOpts():
    pass

#a method for translating SiteName in SE
def getSeName():
    SiteToSe = {}
    SeToSite = {}
    if os.path.isfile('nodes'): os.unlink('nodes')
    os.popen('wget --no-check-certificate https://cmsweb.cern.ch/phedex/datasvc/xml/prod/nodes -O nodes 2>/dev/null')
    XML_file = open("nodes")
    try:
        doc = xml.dom.minidom.parse(XML_file)
    except:
        print "No valid xml file, exiting"
        exit(1)
        
    for node in doc.getElementsByTagName("node"):
        SiteToSe[node.getAttribute("name")] = node.getAttribute("se")
        SeToSite[node.getAttribute("se")] = node.getAttribute("name")
        
    return SiteToSe, SeToSite
        

def getDatasetBlockList(api, DATASET):
    print "Getting list"
    try:
        #optManager  = DbsOptionParser()
        #(opts2,args2) = optManager.getOpt()
        #class defOpts():
        #    pass

        #opts = defOpts()
        #opts.instance = 'cms_dbs_ph_analysis_02'
        #opts.url = 'https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet'
        #api = DbsApi(opts.__dict__)
        return api.listBlocks(DATASET)
    
    except DbsApiException, ex:
        print "Caught API Exception %s: %s "  % (ex.getClassName(), ex.getErrorMessage() )
        if ex.getErrorCode() not in (None, ""):
            print "DBS Exception Error Code: ", ex.getErrorCode()
        return 1

        
def getBlockListFile(api,DATASET,BLOCK):
    #optManager  = DbsOptionParser()
    #(opts,args) = optManager.getOpt()
    #opts.instance = 'cms_dbs_ph_analysis_02'
    #opts.url = 'https://cmsdbsprod.cern.ch:8443/cms_dbs_ph_analysis_02_writer/servlet/DBSServlet'
    #api = DbsApi(opts.__dict__)

    fileList = []
    for afile in api.listFiles(path=DATASET, blockName=BLOCK):
        fileList.append( afile['LogicalFileName'] )
    return fileList
