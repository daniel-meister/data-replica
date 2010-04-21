#!/bin/bash

LOG="cmssw"

eval `scram ru -sh`

vmstat -nd 10 &> ${LOG}_vmstat.log  &
PIDSTAT=$!
./net.sh ${LOG}_net.log &
PIDWATCH=$!
sleep 60
( /usr/bin/time cmsRun -j ${LOG}.xml pset.py ) &> ${LOG}.stdout
kill -9 $PIDSTAT $PIDWATCH
