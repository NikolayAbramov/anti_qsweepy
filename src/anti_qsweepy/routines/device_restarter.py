"""
Device restarting utility

Usage:
    restart_device [part of device name]
Example:
    restart_device COM5

All devices whose name contains the [part of device name] string will be restarted using pnputil.
Run as administrator in order to avoid permission denied error.
"""
import win32com.client
import subprocess
import sys

def device_restarter_main():
    """restart_device script entry point"""
    if len(sys.argv)>1:
        print('Device restarting utility\n\n'
              'To get help enter command without arguments.\n'
              'If you get "permission denied" problem - run it as administrator.\n')
        name_contains = sys.argv[1]

        # Connect to WMI
        wmi = win32com.client.GetObject("winmgmts:")

        # Query for instances of Win32_PnPEntity (Plug and Play devices)
        for device in wmi.InstancesOf("Win32_PnPEntity"):
            if hasattr(device, 'DeviceID') and hasattr(device, 'Name'):
                if (device.Name is not None) and ( name_contains in device.Name):
                    print(f"Device Name: {device.Name}")
                    print(f"Device Instance ID: {device.DeviceID}\n")
                    cmd = 'pnputil /restart-device ' + f'"{device.DeviceID}"'
                    print(cmd)
                    subprocess.run(cmd)
    else:
        print("Device restarting utility\n\n"
              "Usage:\n"
              "restart_device [part of device name]\n\n"
              "Example:\n"
              "restart_device COM5\n\n"
              "All devices whose name contains the "
              "[part of device name] string will be restarted using pnputil.\n"
              "Run as administrator in order to avoid permission denied error.")

if __name__ == '__main__':
    device_restarter_main()
