#!/bin/bash

for i in `ls | grep $1`; do
    crab -getoutput -continue $i
    done

