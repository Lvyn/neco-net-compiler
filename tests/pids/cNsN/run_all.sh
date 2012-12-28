#!/bin/sh

date > begin_run_all

./run.sh default
./run.sh dps -dps
./run.sh dps_no -dps -no

date > end_run_all

