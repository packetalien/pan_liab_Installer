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

__author__ = "Richard Porter (rporter@paloaltonetworks.com)"
__copyright__ = "Copyright 2021, Palo Alto Networks"
__version__ = "1.6"
__license__ = "MIT"
__status__ = "Production"

import os
import sys
import time
import getpass
import hashlib
import fnmatch
import json
import logging
import webbrowser
import shutil
import json
import glob
import logging
from distutils import errors
from shutil import rmtree
from urllib import request
from time import strftime
from time import sleep
from platform import system
from subprocess import call
from subprocess import Popen
from logging.handlers import RotatingFileHandler
from os.path import expanduser
from os import path
from shutil import copy
from urllib.error import HTTPError

'''
Setting up a simple logger. Check 'installer.log' for
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

panos_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/master/vmx/pan-vm50.vmx"
setools_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/master/vmx/linux-utility.vmx"
msft_dc_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/master/vmx/msft-dc.vmx"
msft_rodc_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/master/vmx/msft-rodc.vmx"
vminfo_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/master/json/vminfo.json"
fusion_url = "https://raw.githubusercontent.com/packetalien/fusion-network-config/master/vmnet-configure.py"
win_install_url = "https://docs.google.com/document/d/1c1aGucFgBEEhtdHuiNxpUYyT9sMXEZ7FlnZ7KWSEB6U"
win_network_url = "https://docs.google.com/document/d/1K9lvADAzlJa4R4S4G6aohYcT2t0BqYEK_183Oq7LRIs"
macos_install_url = "https://docs.google.com/document/d/1c1aGucFgBEEhtdHuiNxpUYyT9sMXEZ7FlnZ7KWSEB6U"
workstation_url = "https://github.com/packetalien/diabresources/blob/master/db/defaultse?raw=true"
pan_license_url = "https://drive.google.com/open?id=1JcyZgitSsGY0JCTXoUJPAJRweZHyX2AQ"
liab_gdrive = "https://drive.google.com/drive/u/0/folders/1Yh6Ca4wThWRmwEWtVuShc2uqicV0ziW4"
config_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/master/json/config.json"
vm50auth = "https://drive.google.com/file/d/1PWEnzE6S4AsRPt1xeDMjENCAZD-tKpoS/view?usp=sharing"

# MacOS Network Configurator Variables
netCFG = "https://raw.githubusercontent.com/packetalien/fusion-network-config/master/netcfg.json"
netfile = "/Library/Preferences/VMware Fusion/networking"
netfileheader = "VERSION=1,0"

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
python_mac = "/usr/bin/python3"

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

continue_banner = r'''
.=====================================================.
||                                                   ||
||   _       _--""--_                                ||
||     " --""   |    |   .--.           |    ||      ||
||   " . _|     |    |  |    |          |    ||      ||
||   _    |  _--""--_|  |----| |.-  .-i |.-. ||      ||
||     " --""   |    |  |    | |   |  | |  |         ||
||   " . _|     |    |  |    | |    `-( |  | ()      ||
||   _    |  _--""--_|             |  |              ||
||     " --""                      `--'              ||
||                                                   ||
`=====================================================
A MAJOR Error occured.

The script can attempt to continue.

ARE YOU SURE YOU WISH TO PROCEED? 

Enter YES exactly to proceed!
Enter NO to exit!
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
If you have not configured Windows Network Settings.
You will need to import the defaultse file or the above
will be the case :).
Go to:
https://docs.google.com/document/d/1K9lvADAzlJa4R4S4G6aohYcT2t0BqYEK_183Oq7LRIs
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
    When SOCs Fight these Battles
    With a Keyboard and A Hammer
    On a Zoom in the Room
    They call this a
    Muddled, Huddle, Zweedle, Fuddle
    Keyboard, Puddle, Coffee, Paddle, Battle
'''

flex_banner = r'''
                       ---                                     
                    -        --                             
                --( /     \ )XXXXXXXXXXXXX                   
            --XXX(   O   O  )XXXXXXXXXXXXXXX-              
           /XXX(       U     )        XXXXXXX\               
         /XXXXX(              )--   XXXXXXXXXXX\             
        /XXXXX/ (      O     )   XXXXXX   \XXXXX\
        XXXXX/   /            XXXXXX   \   \XXXXX----        
        XXXXXX  /          XXXXXX         \  ----  -         
---     XXX  /          XXXXXX      \           ---        
  --  --  /      /\  XXXXXX            /     ---=         
    -        /    XXXXXX              '--- XXXXXX         
      --\/XXX\ XXXXXX                      /XXXXX         
        \XXXXXXXXX                        /XXXXX/
         \XXXXXX                         /XXXXX/         
           \XXXXX--  /                -- XXXX/       
            --XXXXXXX---------------  XXXXX--         
               \XXXXXXXXXXXXXXXXXXXXXXXX-            
                 --XXXXXXXXXXXXXXXXXX-

Who you gonna call?
FlexCredits!
https://docs.google.com/document/d/1x40oGCSPsS0efBxPyoeFyQf6eJIhwiMPGlbZyw-Zyrc/edit
'''

missing_banner = r'''
                       ---                                     
                    -        --                             
                --( /     \ )XXXXXXXXXXXXX                   
            --XXX(   O   O  )XXXXXXXXXXXXXXX-              
           /XXX(       U     )        XXXXXXX\               
         /XXXXX(              )--   XXXXXXXXXXX\             
        /XXXXX/ (      O     )   XXXXXX   \XXXXX\
        XXXXX/   /            XXXXXX   \   \XXXXX----        
        XXXXXX  /          XXXXXX         \  ----  -         
---     XXX  /          XXXXXX      \           ---        
  --  --  /      /\  XXXXXX            /     ---=         
    -        /    XXXXXX              '--- XXXXXX         
      --\/XXX\ XXXXXX                      /XXXXX         
        \XXXXXXXXX                        /XXXXX/
         \XXXXXX                         /XXXXX/         
           \XXXXX--  /                -- XXXX/       
            --XXXXXXX---------------  XXXXX--         
               \XXXXXXXXXXXXXXXXXXXXXXXX-            
                 --XXXXXXXXXXXXXXXXXX-

Something was missing???????


'''

major_error = r'''
Art by Shanaka Dias
            __:.__
           (_:..'"=
            ::/ o o\         AHAH!
           ;'-'   (_)     Spaceman Spiff      .
           '-._  ;-'        wins again !  _'._|\/:
           .:;  ;   .            .         '- '   /_
          :.. ; ;,   \            \       _/,    "_<
         :.|..| ;:    \            \__   '._____  _)
         :.|.'| ||   And I wanted             _/ /
         :.|..| :'     to install things!    `;--:
         '.|..|:':       _               _ _ :|_\:
      .. _:|__| '.\.''..' ) ___________ ( )_):|_|:
:....::''::/  | : :|''| "/ /_=_=_=_=_=/ :_[__'_\3_)
 ''      '-''-'-'.__)-'
'''

# Functions

def timestamp():
    '''
    Function returns a timestamp in %Y%m%d-%H%M%S format.
    '''
    stamp = strftime("%Y%m%d-%H%M%S")
    return stamp

def searchdir():
    try:
        if system() == "Darwin":
            searchdir = getuser() + os.sep + vmware_dir_macos
            logger.info("Built Search Directory: %s" % (getuser() + os.sep + vmware_dir_macos))
            return searchdir
        elif system() == "Windows":
            searchdir = getuser() + os.sep + vmware_dir_windows
            logger.info("Built Search Directory: %s" % (getuser() + os.sep + vmware_dir_windows))
            return searchdir
    except IOError as e:
        logger.debug("An IOError has occured as %s" % e)

def save(url, filename):
    '''
    Simple download function based on requests. Takes in
    a url and a filename. Saves to directory filemane indicates.
    '''
    try:
        print("Getting File.... %s" % (filename))
        sleep(2)
        request.urlretrieve(url,filename)
    except:
        print("Soemthing went wrong in save() and the program cannot continue safely.")
        print("\n\nExiting...")
        exit()

def getnet(netCFG):
    try:
        webURL = request.urlopen(netCFG)
        netdata = webURL.read()
        encoding = webURL.info().get_content_charset('utf-8')
        netjson = json.loads(netdata.decode(encoding))
        logger.info(netjson)
        return netjson
    except HTTPError as err:
        logger.debug(err)
        print(err)

def getvminfo(vminfo_url):
    '''
    Retrieves vminfo.json from a url and hash checks with master.
    '''
    try:
        webURL = request.urlopen(vminfo_url)
        netdata = webURL.read()
        encoding = webURL.info().get_content_charset('utf-8')
        vminfo = json.loads(netdata.decode(encoding))
        logger.debug(vminfo)
        return vminfo
    except HTTPError as err:
        logger.debug(err)
        print(err)

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

def get_vmx(url, filename, each, vminfo, tmp):
    '''
    This function retrieves vmx from resource github.
    Calls the move_vmx() function to replace vmx file.
    TODO: Format PEP8
    TODO: Unit Testing and Valdiation
    '''
    os.chdir(tmp)
    home = getuser()
    try:
        if system() == "Darwin":
            print("{:-^30s}".format("Automatically Configurating %s Network Settings." % (vminfo.get(each))))
            print("\n")
            print("Getting preconfigured %s Settings File." % (vminfo.get(each)))
            logger.debug(url)
            logger.debug(filename)
            save(url, tmp + os.sep + filename)
            logger.info("Success: got the file from URL: %s" % (url))
            print("Success: got the file from URL: %s" % (url))
            copy(findfile(filename, home + os.sep + vmware_dir_macos), findfile(filename, home + os.sep + vmware_dir_macos) + ".bak")
            logger.info("Copied %s to %s" % (findfile(filename, home + os.sep + vmware_dir_macos), findfile(filename, home + os.sep + vmware_dir_macos) + ".bak"))
            print("Copied %s to %s" % (findfile(filename, home + os.sep + vmware_dir_macos), findfile(filename, home + os.sep + vmware_dir_macos) + ".bak"))
            copy(tmp + os.sep + filename, home + os.sep + vmware_dir_macos + vminfo.get(each).get('macos'))
            logger.info("Copied %s to %s" % (tmp + os.sep + filename, home + os.sep + vmware_dir_macos + vminfo.get(each).get('macos')))
            print("Copied %s to %s" % (tmp + os.sep + filename, home + os.sep + vmware_dir_macos + vminfo.get(each).get('macos')))
            logger.debug("Success, replaced local vmx with master vmx.")
            logger.info("Cleaning up. Deleting %s" % (os.getcwd + os.sep + filename))
            os.remove(tmp + os.sep + filename)
        elif system() == "Windows":
            print("{:-^30s}".format("Automatically Configurating %s Network Settings." % (vminfo.get(each))))
            print("\n")
            print("Getting preconfigured %s Settings File." % (vminfo.get(each)))
            logger.debug(url)
            logger.debug(filename)
            save(url, tmp + os.sep + filename)
            logger.info("Success: got the file from URL: %s" % (url))
            print("Success: got the file from URL: %s" % (url))
            copy(findfile(filename, home + os.sep + vmware_dir_windows), findfile(filename, home + os.sep + vmware_dir_windows) + ".bak")
            logger.info("Copied %s to %s" % (findfile(filename, home + os.sep + vmware_dir_windows), findfile(filename, home + os.sep + vmware_dir_windows) + ".bak"))
            print("Copied %s to %s" % (findfile(filename, home + os.sep + vmware_dir_windows), findfile(filename, home + os.sep + vmware_dir_windows) + ".bak"))
            copy(tmp + os.sep + filename, home + os.sep + vmware_dir_windows + os.sep + vminfo.get(each).get('windows'))
            logger.info("Copied %s to %s" % (tmp + os.sep + filename, home + os.sep + vmware_dir_windows + os.sep + vminfo.get(each).get('windows')))
            print("Copied %s to %s" % (tmp + os.sep + filename, home + os.sep + vmware_dir_windows + os.sep + vminfo.get(each).get('windows')))
            logger.debug("Success, replaced local vmx with master vmx.")
            logger.info("Cleaning up. Deleting %s" % (home + os.sep + filename))
            os.remove(tmp + os.sep + filename)
        else:
            logger.info("Operating System not recognized.")
    except:
        logger.debug("An exception occured in get_vmx()")

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

def findova(filename):
    '''
    Function searches user directory for file.
    It returns location/file. 

    Uses os.walk for compatibility.
    '''
    try:
        if system() == "Darwin":
            if os.path.exists(os.sep + r"Volumes" + os.sep + r"GoogleDrive"):
                logger.info("Found Google Drive")
                home = os.sep + r"Volumes" + os.sep + r"GoogleDrive"
                for base, dirs, files, in os.walk(home):
                    if filename in files:
                        logger.debug("Found %s" % (os.path.join(base, filename)))
                        return os.path.join(base, filename)
            else:
                logger.info("Could not find Google Drive. Looking in ~/Downloads")
                home = getuser() + os.sep + "Downloads" 
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
                logger.info("Could not find Google Drive. Looking in $env:USERPROFILE Downloads")
                for base, dirs, files, in os.walk(home):
                    if filename in files:
                        logger.debug("Found %s" % (os.path.join(base, filename)))
                        return os.path.join(base, filename)            
    except OSError as err:
        print(err)
        logger.debug(err)
        print("Catastrophic Failure in findova()")
        logger.info("Catastrophic Error in findova() function.")

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
def netmove(netfile):
    try:
        print("{:-^40s}".format("Backing up Config"))
        netfilebak = netfile + filetimestamp()
        logger.info("Moving %s" % (netfilebak))
        call(
            ["sudo", "mv" ,"-f" , netfile,
            netfilebak]
            )
        print("Moved %s to %s" % (netfile, netfilebak))
        logger.info("Moved %s to %s" % (netfile, netfilebak))
    except OSError as err:
        print(err)
        logger.debug(err)

def netcreate(newfile, netfile):
    # Function Variables
    try:
        if os.path.exists(getuser() + os.sep + "networking"):
            print("{:-^40s}".format("Moving new Config"))
            call(
                ["sudo", "mv" ,"-f" , newfile, netfile]
                )
            print("Moved %s to %s" % (newfile, netfile))
            logger.info("Moved %s to %s" % (newfile, netfile))
        else:
            print("{:-^40s}".format("ERROR"))
            print("Could Not Find File")
            print("Script will Exit. It cannot continue")
            print("{:-^40s}".format("ERROR"))
            exit()
    except OSError as err:
        print(err)
        logger.debug(err)

def netcheck(home):
    # Check for old network files
    try:
        if os.path.exists(getuser() + os.sep + "networking"):
            print("{:-^40s}".format("WARNING"))
            print("Found a networking file in %s" % (getuser()))
            print("Removing for a clean build")
            logger.info("{:-^40s}".format("WARNING"))
            logger.info("Found a networking file in %s" % (getuser()))
            logger.info("Removing for a clean build")
            os.remove(home + os.sep + "networking")
            print("{:-^40s}".format("COMPLETE"))
    except OSError as err:
        print(err)
        logger.debug(err)

def enablep():
    #Enables promiscuious mode in VMWare Fusion
    try:
        print("{:-^40s}".format("Enabling Promiscuious Mode"))
        call(
            ["sudo", "touch", "/Library/Preferences/VMware Fusion/promiscAuthorized"]
            )
    except OSError as err:
        print(err)
        logger.debug(err)

def netbuilder(netinfo, netfileheader, home):
    # network file found in:
    # /Library/Preferences/VMWare\ Fusion/networking
    #baseline answers for VMWare Fusion network file.
    vnet_prefix = "VNET_"
    dhcp_suffix = "_DHCP"
    netmask_suffix = "_HOSTONLY_NETMASK"
    subnet_suffix = "_HOSTONLY_SUBNET"
    adapter_suffix = "_VIRTUAL_ADAPTER"
    nat_suffix = "_NAT"
    logger.debug("Ran netcheck()")
    os.chdir(home)
    try:
        networking = open("networking", "a+")
        print("{:-^40s}".format("Building Network from JSON config"))
        logger.info("{:-^40s}".format("Building Network from JSON config"))
        networking.write(netfileheader + "\n")
        print(netfileheader)
        try:
            for each in netinfo:
                networking.write("answer " + vnet_prefix + netinfo.get(each).get('VNET') + dhcp_suffix + " " + netinfo.get(each).get("DHCP") + "\n")
                print("answer " + vnet_prefix + netinfo.get(each).get('VNET') + dhcp_suffix + " " + netinfo.get(each).get("DHCP"))
                networking.write("answer " + vnet_prefix + netinfo.get(each).get('VNET') + netmask_suffix + " " + netinfo.get(each).get("NETMASK") + "\n")
                print("answer " + vnet_prefix + netinfo.get(each).get('VNET') + netmask_suffix + " " + netinfo.get(each).get("NETMASK"))
                networking.write("answer " + vnet_prefix + netinfo.get(each).get('VNET') + subnet_suffix + " " + netinfo.get(each).get("SUBNET") + "\n")
                print("answer " + vnet_prefix + netinfo.get(each).get('VNET') + subnet_suffix + " " + netinfo.get(each).get("SUBNET"))
                networking.write("answer " + vnet_prefix + netinfo.get(each).get('VNET') + adapter_suffix + " " + netinfo.get(each).get("VIRTUAL_ADAPTER") + "\n")
                print("answer " + vnet_prefix + netinfo.get(each).get('VNET') + adapter_suffix + " " + netinfo.get(each).get("VIRTUAL_ADAPTER"))
                if netinfo.get(each).get("NAT") == "yes":
                    networking.write("answer " + vnet_prefix + netinfo.get(each).get('VNET') + nat_suffix + " " + netinfo.get(each).get("NAT") + "\n")
                    print("answer " + vnet_prefix + netinfo.get(each).get('VNET') + nat_suffix + " " + netinfo.get(each).get("NAT"))
        except OSError as err:
            print(err)
            logger.debug(err)
        print("{:-^40s}".format("Build Complete"))
        networking.close()
    except OSError as err:
        print(err)
        logger.debug(err)

def netstop():
    # Stop VMWare Fusion Networking
    try:
        print("{:-^40s}".format("Stopping"))
        call(
            ["sudo", "/Applications/VMware Fusion.app/Contents/Library/vmnet-cli", "--stop"]
            )
        print("{:-^40s}".format("Stopped"))
    except OSError as err:
        print(err)
        logger.debug(err)

def netstart():
    # Stop VMWare Fusion Networking
    try:
        print("{:-^40s}".format("Starting"))
        call(
            ["sudo", "/Applications/VMware Fusion.app/Contents/Library/vmnet-cli", "--start"]
            )
        print("{:-^40s}".format("Started"))
    except OSError as err:
        print(err)
        logger.debug(err)

def netconfigure():
    # Configure VMWare Fusion Networking
    try:
        print("{:-^40s}".format("vnet-cli configurator"))
        call(
            ["sudo", "/Applications/VMware Fusion.app/Contents/Library/vmnet-cli", "--configure"]
            )
        print("{:-^40s}".format("configuration complete"))
    except OSError as err:
        print(err)
        logger.debug(err)

def network_loader():
    '''
    Loads network settings for SE Virtual Environment.
    TODO: Validate if Network is already configured.
    ''' 
    try:
        netinfo = getnet(netCFG)
        home = getuser()
        system_type = system()
    except OSError as err:
        print(err)
        logger.debug(err)
    try:
        if system_type == "Darwin":
            stop_fusion()
            enablep()
            netcheck(home)
            netmove(netfile)
            netbuilder(netinfo, netfileheader, home)
            netcreate(home + os.sep + "networking", netfile)
            start_fusion()
            netstop()
            netconfigure()
            netstart()
            shutil.rmtree(home + os.sep + "networking")
        elif system_type == "Windows":
            print("VMware Workstation import process is in the GUI.")
            print("This process should have already been completed.")
            print(network_configure)
        else:
            logger.debug("Not MacOS, found %s" % system())
            print("Not MacOS, found %s" % system())
    except OSError as err:
        logger.debug(err)
        print(err)

def verify_continue():
    answer = None 
    print(continue_banner)
    while answer not in ("yes", "no"): 
        answer = input("Enter yes or no: ") 
        if answer == "yes": 
             print(continue_banner)
        elif answer == "no": 
             print("Installer will Exit in 10 seconds.")
             print("Log into Slack #labinabox for help.")
             sleep(5)
             print(major_error)
             sleep(5)
             #exit() 
        else: 
        	print("Please enter yes or no.")        
def main():
    oscheck = system()
    try:
        os.mkdir(getuser() + os.sep + "tmp")
        print("Working Directory '%s' created" % (getuser() + os.sep + "tmp"))
        os.chdir(getuser() + os.sep + "tmp")
        tmp = getuser() + os.sep + "tmp"
        print("Changed to %s working directory." % (getuser() + os.sep + "tmp"))
        print("The script will attempt to remove %s upon completion." % (getuser() + os.sep + "tmp"))
    except OSError as error:
            print(error)
            print("Directory '%s' could not be created" % (getuser() + os.sep + "tmp"))
            print("This is a major error.")
            verify_continue()
            logger.debug("Directory '%s' could not be created" % (getuser() + os.sep + "tmp"))
    try:
        vminfo = getvminfo(vminfo_url)
        network_loader()
        for each in vminfo:
            if findova(vminfo.get(each).get('ova')):
                print("\n")
                print()
                print("{:-^30s}".format("Searching"))
                logger.debug("File located: %s" % (vminfo.get(each).get('ova')))
                print("SUCCESS: File %s Located." % (vminfo.get(each).get('ova')))
                print("{:-^30s}".format("Searching"))
                print("\n")
                print("{:-^30s}".format("Skipping SHA1 Check"))
                #local_sha = sha1sum(findova(vminfo.get(each).get('ova')))
                #print("Local SHA1 Summary: %s" % (local_sha))
                #print("{:-^30s}".format("Comparing HASH"))
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
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                        time.sleep(10)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
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
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                        time.sleep(10)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
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
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                        time.sleep(10)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
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
                                        get_vmx(panos_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                        time.sleep(10)
                                    elif vminfo.get(each).get('name') == "linux-utility":
                                        get_vmx(setools_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-dc":
                                        get_vmx(msft_dc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
                                    elif vminfo.get(each).get('name') == "msft-rodc":
                                        get_vmx(msft_rodc_vmx, vminfo.get(each).get('vmx'), each, vminfo, tmp)
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
                print("Install process, could not find %s" % (vminfo.get(each).get('ova')))
                logger.info("Install process, could not find %s" % (vminfo.get(each).get('ova')))
                print(missing_banner)
                print("\n\n Script will continue without: %s" % (vminfo.get(each).get('ova')))
                pass
        try:
            os.chdir(getuser())
            shutil.rmtree(getuser() + os.sep + "tmp")
            print("Directory '%s' has been removed successfully" % (getuser() + os.sep + "tmp"))
        except OSError as err:
            print(err)
            print("Directory '%s' can not be removed" % (getuser() + os.sep + "tmp"))
    
    except OSError as err:
        print ("\n")
        print("{:-^30s}".format("ERROR"))
        print(
            "A major error has occured and the install process has halted."
            )
        print(err)
        logger.debug(err)
        print("For support contact #labinabox on Slack.")
        print("{:-^30s}".format("ERROR"))
        print ("\n")
        exit()

if __name__ == "__main__":
    main()
    exit()
