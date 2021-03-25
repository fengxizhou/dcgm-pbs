#!/usr/bin/python2
import sys
import argparse
import subprocess
import glob
import re
import os

from dcgm_pbs import get_attached_gpus, start_collection, stop_collection

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="script to collect a job's gpu statistics")
    parser.add_argument("jobid")
    parser.add_argument("user")
    parser.add_argument("group")
    args = parser.parse_args()

    #start_collection(args.jobid, args.user, args.group)
    attached_gpus = get_attached_gpus(args.jobid)
    print(attached_gpus)

    start_collection(args.jobid)

    import time
    time.sleep(10)

    stop_collection(args.jobid)
