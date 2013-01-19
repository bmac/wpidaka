#!/bin/bash                                                                     

# load the secrets into the environmental variables
source ~/wpidakasecrets.txt

# run the script using the virtual env's python and log any errors

echo "Started running wpidaka.py at `date`"
~/virtualenv/wpidaka/bin/python ~/code/wpidaka/wpidaka.py -m $1 -v
echo "Completed wpidaka.py at `date`"

