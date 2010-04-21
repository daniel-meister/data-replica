#!/bin/bash

CFG=$1
SW=CMSSW_3_6_0_pre5
LOG="cmssw"

DIR=Site.T3_CH_PSI-Cfg.${CFG}-Dataset.RelValProdTTbarJobRobotMC_3XY_V24_JobRobotv1-EventsJob.10000-Sw.${SW}-Date.`date +%Y%m%d%H%M`-Label.SingleJob
mkdir $DIR

#eval `scram ru -sh`

vmstat -nd 10 &> ${DIR}/${LOG}_vmstat_1.log  &
PIDSTAT=$!
./net.sh ${DIR}/${LOG}_net_1.log &
PIDWATCH=$!
sleep 60
( /usr/bin/time cmsRun -j ${DIR}/${LOG}_1.xml ${CFG}.py ) &> ${DIR}/${LOG}_1.stdout
kill -9 $PIDSTAT $PIDWATCH
