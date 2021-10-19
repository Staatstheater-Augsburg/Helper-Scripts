#!/bin/bash
'true' '''\'
exec '$(dirname '$(readlink '$0')')'/venv/bin/python3 '$0' '$@'
'''

import os
import pysftp
import requests
import sys
import getopt
import math
import glob
from dotenv import dotenv_values

import pprint
# script_path = os.getcwd()


def print_usage():
    print('usage: python deploy-server.py -e <environment>')
    

def deploy(argv):

    # get command line parameters
    environment = None

    try:
        opts, args = getopt.getopt(argv, 'e:', ['environment='])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ('-e', '--environment'):
            environment = arg

    if (not environment):
        print_usage()
        sys.exit(2)


    os.system('clear')
    print('\n---------------------------------------')
    print('🍍 Deploying the VR Theater Game Server')
    print('---------------------------------------\n')

    # get environment variables
    config = dotenv_values('.env.' + environment)
    if(not config):
        print('Environment file not found: .env.' + environment)
        sys.exit(2)
    print('Environment...                 ', environment)

    print('Connection...                  ', end=' ', flush=True)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host=config['SERVER_IP'],
                           username=config['USER'],
                           password=config['PASSWORD'],
                           port=int(config['PORT']),
                           cnopts=cnopts) as sftp:
        sftp.cwd(config['REMOTE_PATH'])
        print('established')

        # Stop
        print('Stopping server...             ', end=' ', flush=True)
        r = requests.get('http://' + config['SERVER_IP'] + ':5000/stop')
        print(r.text.strip())

        zips = glob.glob('data/builds/*.zip')   

        # Delete
        print('Deleting old files...          ', end=' ', flush=True)
        sftp.execute('rm -fr '+config['REMOTE_PATH']+'.*')
        sftp.execute('rm -fr '+config['REMOTE_PATH']+'*')
        print('done')

        if len(zips) == 0:
            print(' - no server ZIP found')
            sys.exit(2)

        # Upload
        print('Uploading new files...')
        sftp.put(zips[0], callback=lambda x, y: progressbar(x, y))
        print('')

        # Unpack
        print('Unpacking remote files...      ', end=' ', flush=True)
        sftp.execute('unzip '+config['REMOTE_PATH'] +
                     os.path.basename(zips[0]) + ' -d ' + config['REMOTE_PATH'])
        sftp.execute('rm '+config['REMOTE_PATH'] + os.path.basename(zips[0]))
        sftp.chmod('game-server.x86_64', 775)
        print('done')

        # Start
        print('Starting server...             ', end=' ', flush=True)
        r = requests.get('http://' + config['SERVER_IP'] + ':5000/start')
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


if __name__ == '__main__':
    deploy(sys.argv[1:])
