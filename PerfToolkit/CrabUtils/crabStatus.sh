#!/bin/bash

for i in `ls | grep $1`; do
    crab -status -continue $i | grep -E 'working|List' | sed "s:$PWD/::g" | sed "s:.*\(working directory\)\([^ ]*\):\2:g"   ;
    done

