#!/bin/bash

for i in `seq 1 10000000`; do 
    (date="`date +%s`" && cat /proc/net/dev | cut -d: -f2 | awk '{rx += $1}{ tx +=$9 }END{print "[NET]", "'"$date"'" ,"RX:",rx, "TX:",tx }') >> ${1} ; 
    sleep 10; 
done 
