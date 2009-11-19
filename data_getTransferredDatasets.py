#!/bin/env python
#################################################################
# data_getTransferredDatasets.py
#
# Author: Leonardo Sala <leonardo.sala@cern.ch>
#
# $Id: data_getTransferredDatasets.py,v 1.1 2009/11/19 16:33:36 leo Exp $
#################################################################


from os import popen
from sys import argv, exit
from time import time

usage = """This script queries the PhEDEx dataservice and finds all the datasets
completely transferred at a site, given a temporal interval. 

USAGE: """+argv[0]+""" site start_time [end_time] (format:YYYY-MM-DD)"""

if len(argv)<3:
    print usage
    exit(1)

site=argv[1]
date = argv[2]
if len(argv)==4:
    end_date = argv[3]
else:
    end_date = ""
#command = "dbsql 'find dataset, dataset.moddate where site="+site+"'| grep '/' | awk '{print $1,$2}'"





def parseDSVOutput(out):
    block_time = {}
    init = 0
    for x in out:
        init = x[init:].find("name='")
        while init != -1:
            sub_x = x[init:]
            
            end = sub_x[len("name='"):].find("'")
            
            block = sub_x[len("name='"):end+len("name='")].strip("\t").strip(" ")
            dataset = block.split("#")[0]

            if not block_time.has_key(dataset):
                block_time[dataset] = {}

            block_time[dataset][block] = {}
            
            x = sub_x[end:]
            init = x.find("name='")
            
            date_init = x.find("time_update='")
            time_update = x[date_init+len("time_update='"): x[date_init+len("time_update='"):].find("'")+date_init+len("time_update='")]
            
            block_time[dataset][block]["time_update"] = float(time_update)

            label = "complete='"
            date_init = x.find(label)
            time_update = x[date_init+len(label): x[date_init+len(label):].find("'")+date_init+len(label)]
            
            block_time[dataset][block][ label[:-2] ] = time_update

    return block_time




#command = "dbsql 'find block where site="+site+"'"
#out = popen(command)

#datasets_block = {}

#for x in out:
#    if x[0]!="/":
#        continue

#    if x.strip("").strip("\n")=="" :
#        continue

#    x = x.strip("\n")
#    dataset = x.split("#")[0]
#    #blo = x.split("#")[0]

#    if not datasets_block.has_key(dataset):
#        datasets_block[dataset] = []

#    datasets_block[dataset].append(x.strip("\t"))


command = """wget -O- \"http://cmsweb.cern.ch/phedex/datasvc/xml/prod/blockreplicas?node="""+site+"""\"  2>/dev/null"""
out = popen(command)
block_time = parseDSVOutput(out)



#command = """wget -O- \"http://cmsweb.cern.ch/phedex/datasvc/xml/prod/blockreplicas?node="""+site+"""&complete=n\"  2>/dev/null"""
#out = popen(command)
#block_time_uncompleted =  parseDSVOutput(out)

#print block_time_uncompleted

wanted_time_out = popen("date -d '"+date+"' +%s")
for y in wanted_time_out:
    wanted_time = float(y.strip("\n"))

end_date_h = ""
if end_date == "":
    end_date = time()
    for y in popen("date -d @"+str(end_date)):
        end_date_h = y.strip("\n")
else:
    end_date_h = end_date
    end_date_out = popen("date -d '"+end_date_h+"' +%s")
    for y in end_date_out:
            end_date = float(y.strip("\n"))

print """------ Datasets transferred from """+date+""" till """+end_date_h+"""\n"""
print ""

dataset_transferred = []


for dataset in block_time.keys():
    
    last_mod_time = 0
    for block in block_time[dataset].keys():
        if block_time[dataset][block]["complete"]=="n":
            last_mod_time = 0
            break
        
        mod_time = block_time[dataset][block]["time_update"]
        if mod_time>last_mod_time:
            last_mod_time = mod_time

    if last_mod_time > wanted_time and last_mod_time<end_date:
        dataset_transferred.append(dataset)


dataset_transferred.sort()
for d in dataset_transferred:
    print d


print ""

