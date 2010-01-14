#!/bin/bash

for i in `ls | grep $1`; do
    crab -kill all -continue $i
    done

