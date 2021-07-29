# VR Theater Helper Scripts


# Development

## Create a Python environment
```bash
python3 -m venv venv
. venv/bin/activate
```

## Install dependencies

    pip install --upgrade pip
    pip install pysftp requests
    pip install -U pure-python-adb


## Get Android SDK platform tools

Download the native platform tools files from here from here:
https://developer.android.com/studio/releases/platform-tools#downloads

Now put the files in the folder for each platform, your are running the script on

    ── platform-tools
        ├─ darwin
        └─ win32


# Tools

## Automated Server deployment

    ./venv/bin/python deploy-server.py


## Device configuration tool

The setup tool will configure all Pico devices attached to the computer. This
way bulk installation of multiple devices is automated and becomes less painful.

### Running

    ./venv/bin/python setup-devices.py

| Parameter              | Description                                                                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `-i, --install`          | **Install a new APK on the device** The script is looking for `.apk` files in the `data/build` folder and will simply use the first one it can find. |
| `-k, --kiosk <enable>` | 1 = enable, 0 = disable'                                                                                                                             |
| `-r, --role <role>`      | "Audience" (default), "Actor" or"Technician"'                                                                                                        |


### Config files

The `data` folder contains several config files that are copied to the device.
Make changes in thos files for customization.