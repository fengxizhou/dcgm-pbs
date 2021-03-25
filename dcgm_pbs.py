#!/usr/bin/python2
import sys
import argparse
import subprocess
import glob
import re
import os


gpuDeviceRE = re.compile(r'/dev/nvidia\d+')
whilespaceSepRE = re.compile(r'[,\s+]')
dcgmCreateGroupRE = re.compile(r'Successfully.+\s+(\d+)$')


def get_all_supported_gpus():
    devices = {}
    nvidia_devices = glob.glob("/dev/nvidia*")
    for dev in nvidia_devices:
        if gpuDeviceRE.match(dev):
            proc = subprocess.Popen(['ls', '-al', dev], stdout=subprocess.PIPE)
            proc.wait()
            output = proc.communicate()[0].decode().rstrip()
            fields = whilespaceSepRE.split(output)
            devices[fields[4]+':'+fields[6]] = int(fields[6])
    return devices

def get_attached_gpus(jobid, gpu_devices=None):
    if gpu_devices is None:
        gpu_devices = get_all_supported_gpus()
    attached_devices = []
    cgroup_devices = '/sys/fs/cgroup/devices/pbspro.service/jobid/{}/devices.list'.format(jobid)
    try:
        with open(cgroup_devices) as f:
            for line in f.readlines():
                fields = whilespaceSepRE.split(line)
                if len(fields) >= 3 and fields[1] in gpu_devices:
                    attached_devices.append(gpu_devices[fields[1]])
    except IOError:
        print("can not open {}".format(cgroup_devices))
        pass
    return attached_devices

def start_collection(jobid):
    attached_devices = get_attached_gpus(jobid)
    attached_devices_s = ','.join([str(d) for d in attached_devices])
    groupId = -1
    if len(attached_devices) >= 1:
        proc = subprocess.Popen(['dcgmi', 'group', '-c', jobid, '-a', attached_devices_s], stdout=subprocess.PIPE)
        proc.wait()
        output = proc.communicate()[0].decode().split('\n')
        if len(output) > 0:
            m = dcgmCreateGroupRE.match(output[0])
            if m:
                groupId = int(m.group(1))
                with open("/tmp/dcgm-group-{}".format(jobid), "w+") as f:
                    f.write(str(groupId))
                    
    if groupId != -1:
        subprocess.call(['dcgmi', 'stats', '-g', str(groupId), '-e'])
        subprocess.call(['dcgmi', 'stats', '-g', str(groupId), '-s', jobid])

def stop_collection(jobid):
    subprocess.call(['dcgmi', 'stats', '-x', jobid])
    subprocess.call(['dcgmi', 'stats', '-v', '-j', jobid]) 
    with open("/tmp/dcgm-group-{}".format(jobid), "r") as f: 
        groupId = f.readline()
        subprocess.call(['dcgmi', 'group', '-d', groupId])
    

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
