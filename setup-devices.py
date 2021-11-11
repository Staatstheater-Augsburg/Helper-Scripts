#!/bin/bash
"true" '''\'
exec "$(dirname "$(readlink "$0")")"/venv/bin/python3 "$0" "$@"
'''

from tkinter import *
from tkinter import filedialog
import platform
from ppadb.client import Client as AdbClient
import json
import os


class SetupGui:
    headline_font = ('Helvetica', 12, 'bold')
    font = ('Helvetica', 12)

    def __init__(self, root):
        self.options = {
            'install': IntVar(value=0),
            'role': IntVar(value=0),
            'avatar': StringVar(),
            'set_kiosk_mode': IntVar(value=0),
            'kiosk_mode': IntVar(value=0),
        }

        self.create_widgets(root)
        return

    def create_widgets(self, root):
        settings_frame = Frame(root).pack(
            side=RIGHT,
            fill=BOTH,
            expand=False
        )

        log_frame = Frame(root, bg='grey')
        log_frame.pack(
            padx=0, pady=0,
            side=LEFT,
            fill=BOTH,
            expand=True
        )

        # Install

        Checkbutton(settings_frame,
                    text='Neues APK installieren',
                    font=self.headline_font,
                    variable=self.options['install']).pack(
                        anchor=W,
                        pady=(20, 0),
                        padx=(20, 20))

        # Rolle

        Label(settings_frame,
              text="Rolle",
              font=self.headline_font,
              justify=LEFT).pack(
            anchor=W,
            pady=(20, 5),
            padx=(20, 20))

        Radiobutton(settings_frame,
                    text='Gast',
                    font=self.font,
                    variable=self.options['role'],
                    value=0).pack(anchor=W, padx=40)

        Radiobutton(settings_frame,
                    text='Darsteller',
                    font=self.font,
                    variable=self.options['role'],
                    value=1).pack(padx=40, anchor=W)

        Radiobutton(settings_frame,
                    text='Techniker',
                    font=self.font,
                    variable=self.options['role'],
                    value=2).pack(padx=40, anchor=W)

        # Avatar

        Label(settings_frame,
              text="Avatar",
              font=self.headline_font,
              justify=LEFT).pack(
            anchor=W,
            pady=(20, 5),
            padx=(20, 20))

        Entry(settings_frame, width=20,
              textvariable=self.options['avatar']).pack(
            anchor=W, padx=40)

        # Kiosk mode

        Checkbutton(settings_frame,
                    text='Kiosk-Modus ändern',
                    font=self.headline_font,
                    variable=self.options['set_kiosk_mode']).pack(
                        anchor=W,
                        pady=(20, 5),
                        padx=(20, 20))

        Radiobutton(settings_frame,
                    text='An',
                    font=self.font,
                    variable=self.options['kiosk_mode'],
                    value=1).pack(padx=40, anchor=W)

        Radiobutton(settings_frame,
                    text='Aus',
                    font=self.font,
                    variable=self.options['kiosk_mode'],
                    value=0).pack(padx=40, anchor=W)

        # Go button

        button = Button(settings_frame,
                        text='Konfiguration starten',
                        command=start_setup,
                        relief=FLAT,
                        font=self.font)
        button.pack(
            anchor=SW,
            fill=X,
            expand=True,
            pady=(40, 20),
            padx=(20, 20))

        if platform.system() != 'Darwin':
            button.configure({
                'fg': "white", 'activeforeground': "white",
                'bg': "#e5017b", 'activebackground': "#fe1f96"})

        # Log

        self.log_text = Text(log_frame,
                             wrap=WORD,
                             height=1, width=1,
                             bg='grey',
                             padx=20, pady=20)
        scroll = Scrollbar(log_frame)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.configure(command=self.log_text.yview)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)

    def log(self, message, new_line=True):
        self.log_text.insert(END, message)
        if new_line:
            self.log_text.insert(END, '\n')
        root.update()

    def clear_log(self):
        self.log_text.delete("1.0", "end")
        root.update()


def start_setup():
    global root
    gui.clear_log()
    gui.log('🍍  \n')
    gui.log('Starte konfiguration...\n')

    needs_reboot = False

    # start server
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        os.system('platform-tools/darwin/adb devices')
    else:
        os.system('platform-tools\win32\\adb.exe devices')

    # start client
    client = AdbClient(host='127.0.0.1', port=5037)
    devices = client.devices()

    if len(devices) == 0:
        gui.log('Keine Brillen gefunden\n')
        return
    else:
        gui.log(str(len(devices)) + ' Brillen gefunden\n')

    # load config files
    with open('data/config.json', 'r') as file:
        data = file.read()
    app_config = json.loads(data)

    with open('data/device.json', 'r') as file:
        data = file.read()
    device_config = json.loads(data)

    # create temp app config file
    app_config['PlayerRole'] = gui.options['role'].get()
    if app_config['PlayerRole'] is not 0:
        app_config['VoiceChatEnabled'] = True
    
    app_config['Avatar'] = gui.options['avatar'].get()

    with open('data/tmp/config.json', 'w') as outfile:
        json.dump(app_config, outfile, indent=4)

    # get apk to install
    if gui.options['install'].get() == 1:
        apk = filedialog.askopenfilename(
            title='Welches APK soll installiert werden?',
            initialdir='data/builds',
            filetypes=[("Elektrotheater App", ".apk")]
        )
        if apk == '':
            gui.log('Kein APK ausgewählt, Installation abgebrochen')
            return

    # setup devices
    for i, device in enumerate(devices):
        gui.log('Brille ' + str(i+1) + ' / ' + str(len(devices)))

        # install app
        if gui.options['install'].get() == 1:
            # uninstall
            if(device.is_installed('de.vollstock.Elektrotheater')):
                gui.log('\t - deinstalliere altes APK')
                device.uninstall('de.vollstock.Elektrotheater')

            # install
            gui.log('\t - installiere ' + os.path.basename(apk))
            device.install(apk)

        # push app config file
        gui.log('\t - kopiere App Konfiguration')
        device.push('data/tmp/config.json',
                    '/storage/emulated/0/Android/data/de.vollstock.Elektrotheater/files/config.json')

        # grant app permission
        gui.log('\t - setze App Berechtigungen')
        device.shell(
            'pm grant de.vollstock.Elektrotheater android.permission.ACCESS_FINE_LOCATION')
        device.shell(
            'pm grant de.vollstock.Elektrotheater android.permission.android.permission.WRITE_EXTERNAL_STORAGE')
        device.shell(
            'pm grant de.vollstock.Elektrotheater android.permission.READ_EXTERNAL_STORAGE')
        device.shell(
            'pm grant de.vollstock.Elektrotheater android.permission.RECORD_AUDIO')

        # device config
        gui.log('\t - konfiguriere Brille')
        device.shell('setprop persist.psensor.screenoff.delay ' +
                     str(device_config['ScreenoffDelay']))
        device.shell('setprop persist.psensor.sleep.delay ' +
                     str(device_config['SleepDelay']))
        device.shell('setprop persist.pvr.openrecenter ' +
                     str(device_config['CalibrateOnBoot']))
        device.shell('setprop persist.pvr.config.target_fps ' +
                     str(device_config['FPSLimit']))
        device.shell('setprop persist.pvr.psensor.reset_pose ' +
                     str(device_config['ResetPoseOnWake']))
        device.shell('setprop persist.pvrpermission.autogrant 1')

        # kiosk
        if gui.options['set_kiosk_mode'].get() == 1:
            enable = gui.options['kiosk_mode'].get() == 1
            enable_string = 'aktiviere' if enable else 'deaktiviere'
            gui.log('\t - ' + enable_string + ' Kiosk-Mode')
            if(enable):
                device.push('data/config.txt',
                            '/storage/self/primary/config.txt')
                device.push('data/SystemKeyConfig.prop',
                            '/data/local/tmp/SystemKeyConfig.prop')
            else:
                device.shell('rm /storage/self/primary/config.txt')
                device.shell('rm /data/local/tmp/SystemKeyConfig.prop')

            needs_reboot = True

        # reboot
        if(needs_reboot):
            gui.log('\t - Brille wird neu gestartet')
            device.shell('reboot')

    os.remove('data/tmp/config.json')

    gui.log('\nfertig')


def main():
    global root
    root = Tk()
    root.title("Elektrotheater Brillen-Setup")
    root.minsize(640, 480)

    global gui
    gui = SetupGui(root)

    root.mainloop()


main()
