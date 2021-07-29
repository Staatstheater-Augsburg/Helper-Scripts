#!/bin/bash
"true" '''\'
exec "$(dirname "$(readlink "$0")")"/venv/bin/python3 "$0" "$@"
'''

import os
import pysftp
import requests
import sys
import math
import glob

myHostname = "5.35.243.170"
# myHostname = "10.0.2.10"
myUsername = "vollstock"
myPassword = "_Ywb92kvJ7-KIxeL"
myPort = 33322
remote_path = "/opt/game-server/"
script_path = os.getcwd()


def deploy():
    os.system('clear')
    print('\n---------------------------------------')
    print("🍍 Deploying the VR Theater Game Server")
    print('---------------------------------------\n')
    print("Connection...                  ", end=" ", flush=True)

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=myHostname, username=myUsername, password=myPassword, port=myPort, cnopts=cnopts) as sftp:
        sftp.cwd(remote_path)
        print("established")

        print("Stopping server...             ", end=" ", flush=True)
        r = requests.get("http://" + myHostname + ":5000/stop")
        print(r.text.strip())

        zips = glob.glob('data/builds/*.zip')

        print("Deleting old files...          ", end=" ", flush=True)
        sftp.execute("rm -fr "+remote_path+".*")
        sftp.execute("rm -fr "+remote_path+"*")
        print("done")

        if len(zips) == 0:
            print(' - no server ZIP found')
            return

        print("Uploading new files...")
        sftp.put(zips[0], callback=lambda x, y: progressbar(x, y))
        print("")

        print("Unpacking remote files...      ", end=" ", flush=True)
        sftp.execute("unzip "+remote_path+"build.zip -d "+remote_path)
        sftp.execute("rm "+remote_path+"build.zip")
        sftp.chmod("game-server.x86_64", 775)
        print("done")

        print("Starting server...             ", end=" ", flush=True)
        r = requests.get("http://" + myHostname + ":5000/start")
        print(r.text)


def progressbar(x, y):
    ''' progressbar for pysftp
    '''
    bar_len = 29
    filled_len = math.ceil(bar_len * x / float(y))
    percents = math.ceil(100.0 * x / float(y))
    bar = '■' * filled_len + ' ' * (bar_len - filled_len)
    # filesize = f'{math.ceil(y/1024):,} KB' if y > 1024 else f'{y} byte'
    filesize = format_bytes(y)
    sys.stdout.write(f'[{bar}] {percents} % ({filesize})\r')
    sys.stdout.flush()


def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return '{0:.2f}'.format(size) + ' ' + power_labels[n] + 'B'


deploy()
