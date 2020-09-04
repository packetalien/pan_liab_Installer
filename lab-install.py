#!/usr/bin/env python3
# Copyright (c) 2018, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Author: Richard Porter rporter@paloaltonetworks.com

'''
Palo Alto Networks lab-install.py

This script retrieves and installs SE Lab in a Box

Execute the script and it auomtatically builds (e.g., python lab-install.py)

This software is provided without support, warranty, or guarantee.
Use at your own risk.
'''

__author__ = "Richard Porter (@packetalien)"
__copyright__ = "Copyright 2018, Palo Alto Networks"
__version__ = "1.4"
__license__ = "MIT"
__status__ = "Beta"

import os
import sys
import time
import getpass
import hashlib
import fnmatch
import requests
import logging
import webbrowser
import shutil
import json
import glob
from time import strftime
from platform import system
from subprocess import call
from subprocess import Popen
from logging.handlers import RotatingFileHandler
from os.path import expanduser
from os import path
from shutil import copy
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


'''
Setting up a simple logger. Check 'controller.log' for
logger details.
'''

logger = logging.getLogger(__name__)
logLevel = 'DEBUG'
maxSize = 10000000
numFiles = 10
handler = RotatingFileHandler(
    'installer.log', maxBytes=maxSize, backupCount=numFiles
    )
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel("DEBUG")


# These are ordered lists, they are not smart. If you mess with the order, the script breaks
# TODO: Upgrade to new vmcontrols library wrapper.
# TODO: add _ for PEP8
# TODO: Migrate variables below to new JSON format.
# TODO: Move to imported files for portability.
# TODO look at path normalization, Localized Variables
# TODO: Create builder class for installer
# TODO: Move local variables to a conf file in 3.0
# URLS

# Firewall IP for Licensing
fwip = "192.168.55.10"

panos_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/pan-vm50.vmx"
setools_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/linux-utility.vmx"
msft_dc_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/msft-dc.vmx"
msft_rodc_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/msft-rodc.vmx"
vminfo_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/json/vminfo.json"
fusion_url = "https://raw.githubusercontent.com/packetalien/fusion-network-config/master/vmnet-configure.py"
win_install_url = "https://docs.google.com/document/d/1c1aGucFgBEEhtdHuiNxpUYyT9sMXEZ7FlnZ7KWSEB6U"
win_network_url = "https://docs.google.com/document/d/1K9lvADAzlJa4R4S4G6aohYcT2t0BqYEK_183Oq7LRIs"
macos_install_url = "https://docs.google.com/document/d/1c1aGucFgBEEhtdHuiNxpUYyT9sMXEZ7FlnZ7KWSEB6U"
workstation_url = "https://github.com/packetalien/diabresources/blob/master/db/defaultse?raw=true"
pan_license_url = "https://drive.google.com/open?id=1JcyZgitSsGY0JCTXoUJPAJRweZHyX2AQ"
liab_gdrive = "https://drive.google.com/drive/u/0/folders/1Yh6Ca4wThWRmwEWtVuShc2uqicV0ziW4"
config_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/json/config.json"
vm50auth = "https://drive.google.com/file/d/1PWEnzE6S4AsRPt1xeDMjENCAZD-tKpoS/view?usp=sharing"

# TODO: Move all of this to a CONF file.
# Default Directories
vmware_dir_windows = "Documents\Virtual Machines"
vmware_dir_macos = "Virtual Machines.localized"
IT_SCCM_dir = "C:\ProgramData"
gstream = "g:/"

# Legacy Directory (deprecated)
legacy_dir = "IT-Managed-VMs"

# Default Application install paths for MacOS and Windows
# TODO: Move to python3 when IT supports it.
chrome_path = "open -a /Applications/Google\ Chrome.app %s"
chrome_path_win = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'
vnetlib_windows = r"c:\Program Files (x86)\VMware\VMware Workstation\vnetlib64.exe"
python_mac = "/usr/bin/python"

# Files TODO: Move to conf file.
# Files TODO: Normalize naming.
vmnetfile = "fusion-vmnet-config.txt"
fusion_loader = 'vmnet-configure.py'
workstationcfgfile = "defaultse"
vminfo_filename = "vminfo.json"
panos_vmx_filename = "pan-vm50.vmx"
setools_vmx_filename = "linux-utility.vmx"
msft_dc_filename = "msft-dc.vmx"
msft_rodc_filename = "msft-rodc.vmx"
IT_artifact_file = "liab-installed.txt"
pan_license_filename = "pan-license-vmseries.py"

# Hard Coded hashes, TODO: Move to conf file.
vminfo_sha = "fa2ee715c3fc4891124aa42131ad8186d8abbcaa"
panos_vmx_hash = "e37b2c76c84a3eee1b2564d957d443c5bac5d8f7"
se_tools_vmx_hash = "75c7e8a038b73c316dd55f69ac91aadd40251662"
msft_dc_hash = "da81e84a956fbee76132640fdd8b9d58a9be0cca"
msft_rodc_hash = "4f8a858be733b90751a5e155ed34591ad121371e"
pan_license_hash = "752bad5ff36e7a4c41a49fa7f3feb41f0f26aa21"

# API Keys for VM-Series
passkey8 = "LUFRPT10VGJKTEV6a0R4L1JXd0ZmbmNvdUEwa25wMlU9d0N5d292d2FXNXBBeEFBUW5pV2xoZz09"
passkey9 = "LUFRPT1tZVhOVFFMUERLZk5qd09Kd3FLT3FMcXRwOTg9Y2NOdGxCM01PZEhRcFhZem94MXhzeUp1eW54RWxZbTZvSCtsUFJvMTlTQU1qbUVGWGNtdjZ0aWFGZENGQUhVdA=="

# Start Up VM Variable
start_message = '''
___________((_____))
____________))___((
___________((_____))
____________))___((
___________((_____))____________$$$$$$
____________))___((____________$$____$$
_$$$$$$$$$$$$$$$$$$$$$$$$$$$$$______$$
__$$$$$$$$Start$$$$$$$$$$$$$$_______$$
___$$$$$$$$$$the$$$$$$$$$$$________$$
____$$$$$$VM-50$$$$$$$$$$$________$$
____$$$$$$$$NOW$$$$$$$$$$$______$$
_____$$$$$$$$$$$$$$$$$$$$_____$$
_____$$$$$$$$$$$$$$$$$$$$$$$$$
______$$$$$$$$$$$$$$$$$$
_______$$$$$$$$$$$$$$$$
_________$$$$$$$$$$$$
___________$$$$$$$$
_$$$$$$$$$$$$$$$$$$$$$$$$$$$$
___$$$$$$$$$$$$$$$$$$$$$$$$
_____$$$$$$$$$$$$$$$$$$$$__
We do not auto-start the VM-Series.
In order for licensing to work you
need to start the VM50. Do so NOW
as it takes 5-10 min to boot.
'''
start_message_again = '''
___________((_____))
____________))___((
___________((_____))
____________))___((
___________((_____))____________$$$$$$
____________))___((____________$$____$$
_$$$$$$$$$$$$$$$$$$$$$$$$$$$$$______$$
__$$$$$$$$Start$$$$$$$$$$$$$$_______$$
___$$$$$$$$$$the$$$$$$$$$$$________$$
____$$$$$$VM-50$$$$$$$$$$$________$$
____$$$$$$$$NOW$$$$$$$$$$$______$$
_____$$$$$$$$$$$$$$$$$$$$_____$$
_____$$$$$$$$$$$$$$$$$$$$$$$$$
______$$$$$$$$$$$$$$$$$$
_______$$$$$$$$$$$$$$$$
_________$$$$$$$$$$$$
___________$$$$$$$$
_$$$$$$$$$$$$$$$$$$$$$$$$$$$$
___$$$$$$$$$$$$$$$$$$$$$$$$
_____$$$$$$$$$$$$$$$$$$$$__
What the first message was not clear?
START THE VM-Series, that is why the API
is not accessible!
'''

network_configure = r'''
              _
             | |
             | |===( )   //////
             |_|   |||  | o o|
                    ||| ( c  )                  ____
                     ||| \= /                  ||   \_
                      ||||||                   ||     |
                      ||||||                ...||__/|-"
                      ||||||             __|________|__
                        |||             |______________|
                        |||             || ||      || ||
                        |||             || ||      || ||
------------------------|||-------------||-||------||-||-------
                        |__>            || ||      || ||
Please configure your Windows Network Settings.
You will need to import the defaultse file or the above
will be the case :).
'''

print_authcode_message = r'''
                               __________
                    __________/VVVVVVVVVV\
                   /VVVVVVVVVVVVVVVVVVVVVV|
                 /VVVVVVVVVVVVVVVVVVVVVVV/
               /VVVVVVVVVVVVVVVVVVVVVVVV/
              |VVVV^^^^^^^^^^^^         |
             |                    vvvvvv\\
             |     vvvvvvvVVVVVVVVVVVVVV/
             |/VVVVVVVVVVVVVVVVVVVVVVVVV|
             |VVVVVVV^^^^^^^^^^         |
              |V/                        \\
              |             vvvvvvvvvvvvv|
               \  /VVVVVVVVVVVVVVVVVVVVVV\
                \/VVVVVVVVVVVVVVVVVVVVVVVV\____
                 |VVVVVVVV^^^^^^^^^^___________)
             |\__|/ _____ //--------   \\xx/
             | xx\ /%%%%///   __     __  \\ \\
             \_xxx %%%%  /   /  \   /  \    |
             / \x%%%%       ((0) ) ((0) )   |
            / #/|%%%%        \__/   \__/     \__  ______-------
            \#/ |%%%%             @@            \/
              _/%%%%                             |_____
     ________/|%%%%                              |    -----___
-----         |%%%%     \___                  __/
           ___/\%%%%    /  --________________//
     __----     \%%%%                     ___/
    /             \%%%%                   _/
                     \%%%%              _/
                       \%%%%           /
                          \%%         |
                           |%%        |
    No Auth Code Found
    Not even a Sound
    No Auth Code Today
    It is Far Away
    Not in a Hat
    Not in the Code
    Not in the Commode
    Can you find the Link?
    It surely does not stink!

if you are seeing this message please enter an AuthCode:
'''

# Functions

def timestamp():
    '''
    Function returns a timestamp in %Y%m%d-%H%M%S format.
    '''
    stamp = strftime("%Y%m%d-%H%M%S")
    return stamp

def save(url, filename):
    '''
    Simple download function based on requests. Takes in
    a url and a filename. Saves to directory filemane indicates.
    '''
    with open(filename, "wb") as f:
        print("Downloading %s" % filename)
        logger.debug("Downloading %s" % filename) 
        response = requests.get(url, stream=True, verify=False)
        total_length = response.headers.get('content-length')
        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" %
                                 ('*' * done, ' ' * (50-done)) )    
                sys.stdout.flush()
    print("\n")

def sha1sum(filename):
    '''
    Takes in a filename and returns a sha1 summary hash.
    Uses hashlib.sha1(). Expects a string as the filename.
    Can take literal path.
    Will not map userdirectory from ~
    Uses read(128* filename.block_size) for speed.
    '''
    shasum = hashlib.sha1()
    logger.info("Started sha1 on file %s: " % filename)
    print("Started sha1 on file: %s " % filename)
    print("This could take some time....")
    logger.debug("Started at %s" % str(timestamp()))
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * shasum.block_size), b''):
            shasum.update(chunk)
    logger.debug("Finished sha1 at: %s" % str(timestamp()) )
    return shasum.hexdigest()

def check_sha1sum(master,local):
    '''
    This function compares master SHA1 with locally generated
    one.
    '''
    try:
        if master == local:
            logger.debug("SHA1 MATCH.")
            return True
        else:
            logger.debug("SHA1 MISSMATCH.")
            return False
    except:
        logger.debug("something went wrong in check_sha1sum()")

def stop_fusion():
    '''
    Function uses osascript to stop Fusion.
    '''
    try:
        call(['osascript', '-e', 'tell application "VMWare Fusion" to quit'])
    except:
        logger.debug("Exception occured in start_fusion()")

def stop_workstation():
    '''
    Function sends a taskkill command to Windows.
    TODO: use check_call and check_output
    
    WARNING: Function uses shell=True argument due
    to Windows commmand processing compatibility with
    VMWare Workstation.
    '''
    # "C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe"
    try:
        process = "vmware.exe"
        cmd = r"C:\Windows\System32\taskkill.exe"
        cmdtrue = (cmd + " " + "/f" + " " + "/im" + " " + process)
        logger.debug("Sent following command to shell: %s" % (cmdtrue))
        call(cmdtrue, shell=True)
    except:
        print("Something happened stopping Workstation.")
        logger.info("Something happened stopping Workstation.")    

def start_fusion():
    '''
    Function uses osascript to activate Fusion.
    '''
    try:
        call(['osascript', '-e', 'tell application "VMWare Fusion" to activate'])
    except:
        logger.debug("Exception occured in start_fusion()")

def start_workstation():
    '''
    Function sends start vmware.exe command to Windows
    via subprocess.call().
    TODO: use check_call and check_output
    
    WARNING: Function uses shell=True argument due
    to Windows commmand processing compatibility with
    VMWare Workstation.
    '''
    try:
        cmd = r"c:\Program Files (x86)\VMware\VMware Workstation\vmware.exe"
        logger.debug("Sending following command to shell: %s" % (cmd))
        Popen(cmd, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
        logger.info("VMWare Workstation Started %s" % (cmd))
    except:
        logger.debug("Exception occured in start_workstation()")
        logger.info("Problem starting VMWare Workstation. Is it installed?")

# TODO: Migrate vmware_dir_macos to conf file for portability. 
# target 3.0 releases.
# TODO: Make this smarter, error conditions, what if vmx does not exist, etc.
# Should be okay for now.
# TODO: Format me please!

def get_vmx(url, filename):
    '''
    This function retrieves vmx from resource github.
    Calls the move_vmx() function to replace vmx file.
    TODO: Format PEP8
    TODO: Unit Testing and Valdiation
    '''
    try:
        if system() == "Darwin":
            print("{:-^30s}".format("Automatically Configurating vmnets."))
            print("\n")
            print("Getting preconfigured vmx file.")
            logger.debug(url)
            logger.debug(filename)
            save(url, getuser() + os.sep + filename)
            logger.info("Success: got the file from URL: %s" % (url))
            print("Success: got the file from URL: %s" % (url))
            copy(findfile(filename, getuser() + os.sep + vmware_dir_macos), findfile(filename, getuser() + os.sep + vmware_dir_macos) + ".bak")
            logger.info("Copied %s to %s" % (findfile(filename, getuser() + os.sep + vmware_dir_macos), findfile(filename, getuser() + os.sep + vmware_dir_macos) + ".bak"))
            print("Copied %s to %s" % (findfile(filename, getuser() + os.sep + vmware_dir_macos), findfile(filename, getuser() + os.sep + vmware_dir_macos) + ".bak"))
            copy(getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_macos))
            logger.info("Copied %s to %s" % (getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_macos)))
            print("Copied %s to %s" % (getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_macos)))
            logger.debug("Success, replaced local vmx with master vmx.")
            logger.info("Cleaning up. Deleting %s" % (getuser() + os.sep + filename))
            os.remove(getuser() + os.sep + filename)
        elif system() == "Windows":
            print("{:-^30s}".format("Automatically Configurating vmnets."))
            print("\n")
            print("Getting preconfigured vmx file.")
            logger.debug(url)
            logger.debug(filename)
            save(url, getuser() + os.sep + filename)
            logger.info("Success: got the file from URL: %s" % (url))
            print("Success: got the file from URL: %s" % (url))
            copy(findfile(filename, getuser() + os.sep + vmware_dir_windows), findfile(filename, getuser() + os.sep + vmware_dir_windows) + ".bak")
            logger.info("Copied %s to %s" % (findfile(filename, getuser() + os.sep + vmware_dir_windows), findfile(filename, getuser() + os.sep + vmware_dir_windows) + ".bak"))
            print("Copied %s to %s" % (findfile(filename, getuser() + os.sep + vmware_dir_windows), findfile(filename, getuser() + os.sep + vmware_dir_windows) + ".bak"))
            copy(getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_windows))
            logger.info("Copied %s to %s" % (getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_windows)))
            print("Copied %s to %s" % (getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_windows)))
            logger.debug("Success, replaced local vmx with master vmx.")
            logger.info("Cleaning up. Deleting %s" % (getuser() + os.sep + filename))
            os.remove(getuser() + os.sep + filename)
        else:
            logger.info("Operating System not recognized.")
    except:
        logger.debug("An exception occured in get_vmx()")

def getvminfo(url, filename):
    '''
    Retrieves vminfo.json from a url and hash checks with master.
    '''
    try:
        if os.path.exists(filename):
            if check_sha1sum(vminfo_sha,sha1sum(filename)) == False:
                logger.info("Virtual Machine data out of date, getting new file now.")
                save(url, filename)
                logger.debug("Saved %s as %s" % (url, filename))
                vminfo = json.loads(open(findfile(filename, os.getcwd())).read())
                logger.debug("Loaded new file as %s \n" % (vminfo))
                return vminfo
            else:
                logger.debug("Found local file, hash matched remote.")
                vminfo = json.loads(open(findfile(filename, os.getcwd())).read())
                logger.debug("Loaded local file as %s \n" % (vminfo))
                return vminfo
        else:
            logger.debug("File not found, going to get it.")
            save(url, filename)
            logger.debug("Saved %s as %s" % (url, filename))
            vminfo = json.loads(open(filename).read())
            return vminfo
    except:
        logger.debug("Exception occured in getvminfo().")

def getuser():
    '''
    Function gets local userdir.
    '''
    home = expanduser("~")
    return home

# TODO: Update with pathlib.Path.rglob after moving to 3.X

def findfile(filename, searchdir):
    '''
    Function searches user directory for file.
    It returns location/file. 
    
    Uses os.walk for compatibility.
    '''
    for base, dirs, files, in os.walk(searchdir):
        if filename in files:
            return os.path.join(base, filename)

def find_license_file(filename, searchdir):
    '''
    Function searches user directory for
    pan-license-vmseries.py.
    It compares to the file HASH.
    
    It returns location/file. 
    
    Uses os.walk for compatibility.
    '''
    for base, dirs, files, in os.walk(searchdir):
        if filename in files:
            return os.path.join(base, filename)
        
# TODO: Update with pathlib.Path.rglob after moving to 3.X        

def findova(filename):
    '''
    Function searches user directory for file.
    It returns location/file. 

    Uses os.walk for compatibility.
    '''
    try:
        if system() == "Darwin":
            home = getuser()
            for base, dirs, files, in os.walk(home):
                if filename in files:
                    logger.debug("Found %s" % (os.path.join(base, filename)))
                    return os.path.join(base, filename)
        elif system() == "Windows":
            if os.path.exists(gstream):
                logger.debug("Located Google Drive.")
                for base, dirs, files, in os.walk(os.path.normpath(gstream)):
                    if filename in files:
                        logger.debug("Found %s" % (os.path.join(base, filename)))
                        return os.path.join(base, filename)
            else:
                home = getuser()
                for base, dirs, files, in os.walk(home):
                    if filename in files:
                        logger.debug("Found %s" % (os.path.join(base, filename)))
                        return os.path.join(base, filename)            
    except:
        print("Catastrophic Failure in findova()")
        logger.info("Catastrophic Error in findova() function.")

def findlic(filename):
    '''
    Function searches user directory for file.
    It returns location/file. 

    Uses os.walk for compatibility.
    '''
    try:
        if system() == "Darwin":
            home = getuser()
            for base, dirs, files, in os.walk(home):
                if filename in files:
                    logger.debug("Found %s" % (os.path.join(base, filename)))
                    return os.path.join(base, filename)
        elif system() == "Windows":
            if os.path.exists(gstream):
                logger.debug("Located Google Drive.")
                for base, dirs, files, in os.walk(os.path.normpath(gstream)):
                    if filename in files:
                        logger.debug("Found %s" % (os.path.join(base, filename)))
                        return os.path.join(base, filename)
            else:
                home = getuser()
                for base, dirs, files, in os.walk(home):
                    if filename in files:
                        logger.debug("Found %s" % (os.path.join(base, filename)))
                        return os.path.join(base, filename)            
    except:

def dir_check(directory):
    '''
    This function checks if a directory exists.
    '''
    try:
        if path.exists(directory):
            logger.info("Directory Located %s" % directory)
            return True
        else:
            return False
    except IOError as e:
        logger.debug("An IOError has occured as %s" % e)

def dir_build():
    '''
    This function buids the default VMWare Directory.
    '''
    try:
        if system() == "Darwin":
            os.mkdir(getuser() + os.sep + vmware_dir_macos)
            logger.info("Created Directory: %s" % (getuser() + os.sep + vmware_dir_macos))
        elif system() == "Windows":
            os.mkdir(getuser() + os.sep + vmware_dir_windows)
            logger.info("Created Directory: %s" % (getuser() + os.sep + vmware_dir_windows))
    except IOError as e:
        logger.debug("An IOError has occured as %s" % e)
        
def unpackova(filename, location):
    '''
    Unpacks OVA with OVFTool. Looks for OVFTool in
    the default installed directory of Windows and
    MacOS. 
    TODO: Remove HardCoding of App location.
    
    Expects full location of file and unpack directory.

    For Windows, uses "/" intead of os.sep for compatibility
    with ovftool.exe. This seems to be isolated to
    ovftool.exe and vmrun.exe.
    '''
    try:
        logger.debug("Started ova upack at %s"
                     % str(timestamp()))
        if system() == "Darwin":
            call(["/Applications/VMware Fusion.app/Contents/Library/VMware OVF Tool/ovftool",
                filename, location])
        elif system() == "Windows":
            builddir = os.path.normpath("\"" + getuser() + os.sep +  vmware_dir_windows + "\"")
            unpackbuilder = os.path.normpath("\"" + filename + "\"")
            cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe\"")
            cmdtrue = (cmd + " " + unpackbuilder + " " + builddir)
            logger.debug("Started ova upack at %s"
                        % str(timestamp()))
            logger.debug("Sent following command to shell: %s" % (cmdtrue))
            call(cmdtrue, shell=True)
            logger.debug("Completed ova unpack at %s"
                        % str(timestamp()))
        else:
            print("Unsupported OS Detected, exiting....")
            logger.info("Unsupported OS Detected, exiting....")
            exit()    
        logger.debug("Completed ova unpack at %s"
                     % str(timestamp()))
    except:
        logger.debug("Exception occured in unpackova().")

def startvm(vmx):
    '''
    Starts a virtual machine on Windows or MacOS.
    Expects a full path for vmx variable.
    
    Looks for vmrun in default install directories.
    
    TODO: Remove hardcoded path to vmrun.
    '''
    try:
        if system() == "Darwin":
            call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","start",
                vmx])
        elif system() == "Windows":
            cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe\"")
            cmdtrue = os.path.normpath(cmd +
                                    " " + "-T" + " " + "ws" +
                                    " " + "start" + " " + os.path.normpath("\"%s\"" % (vmx)))
            logger.debug("Sent the following to Windows Shell: %s" % (cmdtrue))
            call(cmdtrue, shell=True)
        else:
            print("Unsupported OS Detected, exiting....")
            logger.info("Unsupported OS Detected, exiting....")
            exit()
        logger.debug("Succesfully started %s" % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" % (e))

def deletevm(vmx):
    '''
    Deletes a virtual machine on Windows or MacOS.
    Expects a full path for vmx variable.
    
    Looks for vmrun in default install directories.
    
    TODO: Remove hardcoded path to vmrun.
    '''
    try:
        if system() == "Darwin":
            call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","deleteVM",
                vmx])
        elif system() == "Windows":
            cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe\"")
            cmdtrue = os.path.normpath(cmd +
                                    " " + "-T" + " " + "ws" +
                                    " " + "deleteVM" + " " + os.path.normpath("\"%s\"" % (vmx)))
            logger.debug("Sent the following to Windows Shell: %s" % (cmdtrue))
            call(cmdtrue, shell=True)
        else:
            print("Unsupported OS Detected, exiting....")
            logger.info("Unsupported OS Detected, exiting....")
            exit()
        logger.debug("Succesfully deleted %s" % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" % (e))

def suspendvm(vmx):
    '''
    Suspends a virtual machine on Windows or MacOS.
    Expects a full path for vmx variable.
    
    Looks for vmrun in default install directories.
    
    TODO: Remove hardcoded path to vmrun.
    '''
    try:
        if system() == "Darwin":
            call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","suspend",
                vmx])
        elif system() == "Windows":
            cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe\"")
            cmdtrue = os.path.normpath(cmd +
                                    " " + "-T" + " " + "ws" +
                                    " " + "suspend" + " " + os.path.normpath("\"%s\"" % (vmx)))
            logger.debug("Sent the following to Windows Shell: %s" % (cmdtrue))
            call(cmdtrue, shell=True)
        else:
            print("Unsupported OS Detected, exiting....")
            logger.info("Unsupported OS Detected, exiting....")
            exit()
        logger.debug("Succesfully deleted %s" % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" % (e))

def stopvm(vmx):
    '''
    Stops a virtual machine on Windows or MacOS.
    Expects a full path for vmx variable.
    
    Looks for vmrun in default install directories.
    
    TODO: Remove hardcoded path to vmrun.
    '''
    try:
        if system() == "Darwin":
            call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","stop",
                vmx])
        elif system() == "Windows":
            cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\\vmrun.exe\"")
            cmdtrue = os.path.normpath(cmd +
                                    " " + "-T" + " " + "ws" +
                                    " " + "stop" + " " + os.path.normpath("\"%s\"" % (vmx)))
            logger.debug("Sent the following to Windows Shell: %s" % (cmdtrue))
            call(cmdtrue, shell=True)
        else:
            print("Unsupported OS Detected, exiting....")
            logger.info("Unsupported OS Detected, exiting....")
            exit()
        logger.debug("Succesfully deleted %s" % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" % (e))

def network_loader():
    '''
    Loads network settings for SE Virtual Environment.
    TODO: Cleanup functions, remove installer files.
    TODO: Validate if Network is already configured.
    ''' 
    try:
        if system() == "Darwin":
            logger.info("Going to get network loader script. %s" % (fusion_url))
            save(fusion_url, getuser() + os.sep + fusion_loader)
            print("{:-^30s}".format("Automatically Configuring Network."))
            print("{:-^30s}".format("Please enter SSO password."))
            call(["sudo", python_mac, getuser() + os.sep + fusion_loader])
        elif system() == "Windows":
            print("VMware Workstation import process is in the GUI.")
            print("The installer will bring up the instructions")
            print("Please import it in Virtual Networks Editor.")
            print("\nOpening instructions in 5 seconds.")
            time.sleep(5)
            webbrowser.get(chrome_path_win).open(win_network_url)
            print(network_configure)
        else:
            print("Unsupported OS detected, program will exit.")
            logger.info("Unsupported OS. Now exiting.")
            exit()
    except:
        logger.debug("Exception occured in network_loader() os type: %s" % (system()))

def set_auth_code(passkey, fwip, authcode):
    try:
        ctype = "op"
        cmd = "<request><license><fetch><auth-code>%s</auth-code></fetch></license></request>" % (authcode)
        call = "https://%s/api/?type=%s&cmd=%s&key=%s" % (fwip, ctype, cmd, passkey)
        r = requests.get(call, verify=False)
        logger.debug("set_auth_code() returned %s" % r.text)
        print("Set Authcode Function returned: %s" % r.text)
        return r.text
    except requests.exceptions.ConnectionError as e:
        print("There was a problem with setting the authCode.")
        print("If this is helpful the error was captured as: " + e)
        logger.debug("Exception as %s" % e)

def fetchlic(passkey):
    try:
        ctype = "op"
        cmd = "<request><license><fetch/></license></request>"
        call = "https://%s/api/?type=%s&cmd=%s&key=%s" % (fwip, ctype, cmd, passkey)
        r = requests.get(call, verify=False)
        return r.text
    except requests.exceptions.ConnectionError as e:
        print("There was a problem with fetching licenses from the support server.")
        print("If this is helpful the error was captured as: " + e)

def api_access_check(fwip):
    try:
        # old admin password check
        result8 = syscheck(passkey8,fwip)
        # new lab passwordk check
        result9 = syscheck(passkey9,fwip)
        # TODO: Clean this up if possible.
        if (result8 == 200):
            logger.debug("Access successful with legacy api-key %s" % passkey8)
            passkey = passkey8
            print("Access with admin:paloalto, old version detected.")
            return passkey
        elif(result9 == 200):
            logger.debug("Access successful with new api-key %s " % passkey9)
            print("Access with admin:Paloalto1!, new version detected.")
            passkey = passkey9
            return passkey
        else:
            print("Access failed, do you have a custom admin password?")
            return passkey8
    except requests.exceptions.ConnectionError as e:
        print("Attempted to access API. System not available.")

def syscheck(passkey,fwip):
    try:
        ctype = "op"
        cmd = "<show><system><info></info></system></show>"
        call = "https://%s/api/?type=%s&cmd=%s&key=%s" % (fwip, ctype, cmd, passkey)
        r = requests.get(call, verify=False)
        return r.status_code
    except requests.exceptions.ConnectionError as e:
        print("Attempted to access API. System not available.")
        print(start_message)
        
def pan_license(fwip):
    '''
    Licenses VM-Series.
    TODO: Add Hash Checking for vm50auth.txt
    ''' 
    try:
        try:
            if findlic("vm50auth.txt"):
                authcode = open(findlic("vm50auth.txt"), "r").read().rstrip()
                logger.debug("Read file vm50auth.txt")
            else:
                print(print_authcode_message)
                authcode = input("ENTER AUTH CODE:")
        except IOError as e:
            logger.debug("IOError as %s" % (e))
            print("")
        logger.info("Starting licensing process.")
        passkey = api_access_check(fwip)
        if syscheck(passkey,fwip) == 200: 
            auth_results = set_auth_code(passkey, fwip, authcode)
            logger.debug("Sent authcode to VM-Series, returned %s"
                        % (auth_results))
            print("Sent authcode to VM-Series, it returned %s"
                % (auth_results))
            time.sleep(5)
        else:
            count = 1
            while syscheck(passkey, fwip) != 200:
                print("VM-Series API not accessible. Waiting 15 Seconds then retrying.")
                if count == 1:
                    print(start_message_again)
                    count = 0
                time.sleep(15)
                passkey = api_access_check(fwip)
                if syscheck(passkey,fwip) == 200:
                    logger.debug("Set Support Key temporarily for CSP 245")
                    auth_results = set_auth_code(passkey, fwip, authcode)
                    logger.debug("Attempted to send authcode to VM-Series, returned %s"
                                % (auth_results))
                    print("Sent Authcode to VM-Series, it returned %s"
                        % (auth_results))
    except:
        logger.debug("Exception occured in the license process")
        
def main():
    oscheck = system()
    try:
        vminfo = getvminfo(vminfo_url, vminfo_filename)
        network_loader()
        for each in vminfo:
            if findova(vminfo.get(each).get('ova')):
                print("\n")
                print("{:-^30s}".format("Searching"))
                logger.debug("File located: %s" % (vminfo.get(each).get('ova')))
                print("SUCCESS: File %s Located." % (vminfo.get(each).get('ova')))
                print("{:-^30s}".format("Searching"))
                print("\n")
                print("{:-^30s}".format("Performing SHA1 Check"))
                local_sha = sha1sum(findova(vminfo.get(each).get('ova')))
                print("Local SHA1 Summary: %s" % (local_sha))
                print("{:-^30s}".format("Comparing HASH"))
                if check_sha1sum(vminfo.get(each).get('sha1sum'), local_sha) == True:
                    print("Integrity Check Successful.")
                    print("{:-^30s}".format("SHA1 Check Complete"))
                    print("\n")
                    logger.info("Integrity Check Successful.")
                else:
                    print("SHA1 Check shows different HASH. OVA may not be current. Consider re-downloading.")
                    if oscheck == "Darwin":
                        webbrowser.get(chrome_path).open(vminfo.get(each).get('sourceurl'))
                        logger.debug("Opened Browser to SourceURL for %s" % (vminfo.get(each).get('name')))
                    elif oscheck == "Windows":
                        webbrowser.get(chrome_path_win).open(vminfo.get(each).get('sourceurl'))
                        logger.debug("Opened Browser to SourceURL for %s" % (vminfo.get(each).get('name')))
                    else:
                        logger.debug("Tried to open browser to SourceURL."
                                     + " Unsupported OS detected")
                    print("{:-^30s}".format("SHA1 Check Complete"))
                    print("\n")
                    logger.info("Integrity Check Fail. Re-download suggested.")
                print("{:-^30s}".format("Unpacking %s" % (vminfo.get(each).get('ova'))))
                logger.debug("{:-^30s}".format("Unpacking %s" % (vminfo.get(each).get('ova'))))
                print("This will take some time.")
                try:
                    if oscheck == "Darwin":
                        if dir_check(getuser() + os.sep + vmware_dir_macos):
                            if vminfo.get(each).get('status') == True:
                                unpackova(findova(vminfo.get(each).get('ova')),
                                        getuser() + os.sep + vmware_dir_macos)
                                logger.info("Unpack completed at %s" % str(timestamp()))
                                print("Unpack completed at %s" % str(timestamp()))
                                try:
                                    if vminfo.get(each).get('name') == "pan-vm50":
                                        stop_fusion()
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                        print(start_message)
                                        time.sleep(10)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'))
                                        start_fusion()
                                    else:
                                        pass
                                except:
                                    logger.info("Exception occured in vmx replacement.")
                        else:
                            dir_build()
                            if vminfo.get(each).get('status') == True:
                                unpackova(findova(vminfo.get(each).get('ova')),
                                        getuser() + os.sep + vmware_dir_macos)
                                logger.info("Unpack completed at %s" % str(timestamp()))
                                print("Unpack completed at %s" % str(timestamp()))
                                try:
                                    if vminfo.get(each).get('name') == "pan-vm50":
                                        stop_fusion()
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                        print(start_message)
                                        time.sleep(10)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'))
                                        start_fusion()
                                    else:
                                        pass
                                except:
                                    logger.info("Exception occured in vmx replacement.")
                        startvm(findfile(vminfo.get(each).get('vmx'), getuser()
                                         + os.sep + vmware_dir_macos))
                        logger.info("Successfully started %s" %
                                    (findfile(vminfo.get(each).get('vmx'), getuser()
                                              + os.sep + vmware_dir_macos)))
                        stopvm(findfile(vminfo.get(each).get('vmx'), getuser()
                                        + os.sep + vmware_dir_macos))
                        logger.info("Successfully stopped %s" %
                                    (findfile(vminfo.get(each).get('vmx'), getuser()
                                              + os.sep + vmware_dir_macos)))
                    elif oscheck == "Windows":
                        if dir_check(getuser() + os.sep + vmware_dir_windows):
                            if vminfo.get(each).get('status') == True:
                                unpackova(findova(vminfo.get(each).get('ova')),
                                        getuser() + os.sep + vmware_dir_windows)
                                logger.info("Unpack completed at %s" % str(timestamp()))
                                print("Unpack completed at %s" % str(timestamp()))
                                try:
                                    if vminfo.get(each).get('name') == "pan-vm50":
                                        stop_workstation()
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                        print(start_message)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'))
                                        start_workstation()
                                    else:
                                        pass
                                except:
                                    logger.info("Exception occured in vmx replacement.")
                            startvm(findfile(vminfo.get(each).get('vmx'), getuser()
                                            + os.sep + vmware_dir_windows))
                            logger.info("Successfully started %s" %
                                        (findfile(vminfo.get(each).get('vmx'), getuser()
                                                + os.sep + vmware_dir_windows)))
                            stopvm(findfile(vminfo.get(each).get('vmx'), getuser()
                                            + os.sep + vmware_dir_windows))
                            logger.info("Successfully stopped %s" %
                                        (findfile(vminfo.get(each).get('vmx'), getuser()
                                                + os.sep + vmware_dir_windows)))
                        else:
                            dir_build()
                            if vminfo.get(each).get('status') == True:
                                unpackova(findova(vminfo.get(each).get('ova')),
                                        getuser() + os.sep + vmware_dir_windows)
                                logger.info("Unpack completed at %s" % str(timestamp()))
                                print("Unpack completed at %s" % str(timestamp()))
                                try:
                                    if vminfo.get(each).get('name') == "pan-vm50":
                                        stop_workstation()
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                        print(start_message)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'))
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'))
                                        start_workstation()
                                    else:
                                        pass
                                except:
                                    logger.info("Exception occured in vmx replacement.")
                            startvm(findfile(vminfo.get(each).get('vmx'), "\"%s\"" % (getuser()
                                            + os.sep + vmware_dir_windows)))
                            logger.info("Successfully started %s" %
                                        (findfile(vminfo.get(each).get('vmx'), getuser()
                                                + os.sep + vmware_dir_windows)))
                            stopvm(findfile(vminfo.get(each).get('vmx'), "\"%s\"" % (getuser()
                                            + os.sep + vmware_dir_windows)))
                            logger.info("Successfully stopped %s" %
                                        (findfile(vminfo.get(each).get('vmx'), getuser()
                                                + os.sep + vmware_dir_windows)))
                    else:
                        logger.info("Unsupported OS Detected, install will halt.")
                        exit()
                except:
                    logger.debug("Error in the unpack process.")
                    print("Error in the unpack process.")
            else:
                print("\n")
                print("{:-^30s}".format("Download Check Failed"))
                print("{:-^30s}".format("Opening URL to Install Instructions"))
                print("{:-^30s}".format("Could not find: %s" % (vminfo.get(each).get('ova'))))
                logger.info("Download Check Failed. Opening install instructions and LiaB gDrive Folder.")
                print("{:-^30s}".format("Opening URL to Install Instructions"))
                if oscheck == "Darwin":
                    webbrowser.get(chrome_path).open(macos_install_url)
                    webbrowser.get(chrome_path).open(liab_gdrive)
                    logger.debug("Opened Browser to SourceURL for %s" % (macos_install_url))
                elif oscheck == "Windows":
                    webbrowser.get(chrome_path_win).open(win_install_url)
                    webbrowser.get(chrome_path_win).open(liab_gdrive)
                    logger.debug("Opened Browser to SourceURL for %s" % (win_install_url))
                else:
                    logger.debug("Tried to open browser to SourceURL."
                                    + " Unsupported OS detected")
                print("\n")
                print("Exiting install process, could not find %s" % (vminfo.get(each).get('ova')))
                logger.info("Exiting install process, could not find %s" % (vminfo.get(each).get('ova')))
                exit()
        pan_license(fwip)
    except:
        print ("\n")
        print("{:-^30s}".format("ERROR"))
        print(
            "A major error has occured and the install process has halted."
            )
        logger.debug("Error, install halted.")
        print("For support contact #labinabox on Slack.")
        print("{:-^30s}".format("ERROR"))
        print ("\n")
        exit()

if __name__ == "__main__":
    main()
    exit()
