#!/bin/bash
'true' '''\'
exec '$(dirname '$(readlink '$0')')'/venv/bin/python3 '$0' '$@'
'''

# https://github.com/Swind/pure-python-adb

import sys
from sys import platform
from ppadb.client import Client as AdbClient
import json
import sys
import getopt
import os
import glob


# Fields
devices = None
app_config = None
device_config = None
options = {}
needs_reboot = False
player_roles = {
    'audience': 0,
    'actor': 1,
    'technician': 2
}


def main(argv):
    os.system('clear')

    print('\n------------------------')
    print('🍍 VR Theater setup tool')
    print('------------------------\n')

    get_options(argv)

    # start server
    if platform == "darwin":
        os.system('platform-tools/darwin/adb devices')
    else:
        os.system('platform-tools/wind32/adb.exe devices')

    # start client
    client = AdbClient(host='127.0.0.1', port=5037)
    devices = client.devices()

    if len(devices) == 0:
        print('- no devices found\n')
        return

    # load config files
    with open('data/config.json', 'r') as file:
        data = file.read()
    app_config = json.loads(data)

    with open('data/device.json', 'r') as file:
        data = file.read()
    device_config = json.loads(data)

    # create temp app config file
    if 'role' in options:
        app_config['PlayerRole'] = player_roles[options['role'].lower()]
    with open('data/tmp/config.json', 'w') as outfile:
        json.dump(app_config, outfile, indent=4)

    # setup devices
    for i, device in enumerate(devices):
        print('Device ' + str(i+1) + ' / ' + str(len(devices)))

        # install app
        if 'install' in options:
            install(device)

        # push app config file
        print('\t - copy app config')
        device.push('data/tmp/config.json',
                    '/storage/emulated/0/Android/data/de.vollstock.VRTheater/files/config.json')

        # grant app permission
        print('\t - set app permissions')
        device.shell('pm grant de.vollstock.VRTheater android.permission.ACCESS_FINE_LOCATION')
        device.shell('pm grant de.vollstock.VRTheater android.permission.android.permission.WRITE_EXTERNAL_STORAGE')
        device.shell('pm grant de.vollstock.VRTheater android.permission.READ_EXTERNAL_STORAGE')
        device.shell('pm grant de.vollstock.VRTheater android.permission.RECORD_AUDIO')

        # device config
        print('\t - configure device')
        device.shell('setprop persist.psensor.screenoff.delay ' + str(device_config['ScreenoffDelay']))
        device.shell('setprop persist.psensor.sleep.delay ' + str(device_config['SleepDelay']))
        device.shell('setprop persist.pvr.openrecenter ' + str(device_config['CalibrateOnBoot']))
        device.shell('setprop persist.pvr.config.target_fps ' + str(device_config['FPSLimit']))
        device.shell('setprop persist.pvr.psensor.reset_pose ' + str(device_config['ResetPoseOnWake']))
        device.shell('setprop persist.pvrpermission.autogrant 1')

        # kiosk
        if 'kiosk' in options:
            set_kiosk_mode(device, options['kiosk'])

        # reboot
        if(needs_reboot):
            print('\t - reboot device')
            device.shell('reboot')

    os.remove("data/tmp/config.json")

    print('\ndone')


def get_options(argv):
    try:
        opts, args = getopt.getopt(
            argv, 'ik:r:', ['install', 'kiosk=', 'role='])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-i', '--install'):
            options['install'] = True
        elif opt in ('-k', '--kiosk'):
            options['kiosk'] = arg == '1'
        elif opt in ('-r', '--role'):
            options['role'] = arg
        else:
            print_usage()
            sys.exit()


def print_usage():
    print('Usage: python '+__file__+' [options]')
    print('  -i, --install           Install a new APK on the device')
    print('  -k, --kiosk <enable>    1 = enable, 0 = disable')
    print('  -r, --role <role>       "Audience" (default), "Actor" or "Technician"')
    print('\n')


def install(device):
    apks = glob.glob('data/builds/*.apk')
    
    if len(apks) == 0:
        print('\t - no APK found')
        return

    # uninstall
    if(device.is_installed('de.vollstock.VRTheater')):
        print('\t - uninstalling old APK')
        device.uninstall('de.vollstock.VRTheater')

    # install
    print('\t - installing ' + apks[0])
    device.install(apks[0])


def set_kiosk_mode(device, enable):
    global needs_reboot

    enable_string = 'enable' if enable else 'disable'
    print('\t - ' + enable_string + ' kiosk mode')
    if(enable):
        device.push('data/config.txt', '/storage/self/primary/config.txt')
        device.push('data/SystemKeyConfig.prop',
                    '/data/local/tmp/SystemKeyConfig.prop')
    else:
        device.shell('rm /storage/self/primary/config.txt')
        device.shell('rm /data/local/tmp/SystemKeyConfig.prop')

    needs_reboot = True


if __name__ == '__main__':
    main(sys.argv[1:])
