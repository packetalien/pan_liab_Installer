#!/usr/bin/env python
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
Palo Alto Networks lab-update.py

This script updates Lab in a Box (LiaB).

Execute the script and it auomtatically updates LiaB 
(e.g., python lab-update.py)

This software is provided without support, warranty, or guarantee.
Use at your own risk.
'''

__author__ = "Richard Porter"
__copyright__ = "Copyright 2022, Palo Alto Networks"
__version__ = "3.0.64"
__license__ = "MIT"
__status__ = "Production"

from distutils import errors
import os
import sys
import time
import getpass
import hashlib
import fnmatch
import json
import pip
import importlib
import logging
import webbrowser
import shutil
import json
import glob
import logging
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

'''
Setting up a simple logger. Check 'controller.log' for
logger details.
'''

logger = logging.getLogger(__name__)
logLevel = 'DEBUG'
maxSize = 10000000
numFiles = 10
handler = RotatingFileHandler(
    'updates.log', maxBytes=maxSize, backupCount=numFiles
    )
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel("DEBUG")


# These are ordered lists, they are not smart. If you mess with the order, the script breaks
# TODO: Upgrade to new vmcontrols library wrapper.
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
config_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/json/config.json"
vm50auth = "https://drive.google.com/file/d/1PWEnzE6S4AsRPt1xeDMjENCAZD-tKpoS/view?usp=sharing"

# TODO: Move all of this to a CONF file.
# Default Directories
vmware_dir_windows = "Documents\Virtual Machines"
vmware_dir_macos = "Virtual Machines.localized"
IT_SCCM_dir = "C:\ProgramData"
gstream = "D:\Middleware\_Virtual_Machine_Images\_PaloAltoNetworks\DIAB_3.0.64"

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

vminfo_filename = "vminfo.json"
panos_vmx_filename = "pan-vm50.vmx"
setools_vmx_filename = "linux-utility.vmx"
msft_dc_filename = "msft-dc.vmx"
msft_rodc_filename = "msft-rodc.vmx"
IT_artifact_file = "liab-installed.txt"
vminfo_sha = "fa2ee715c3fc4891124aa42131ad8186d8abbcaa"

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

update_banner = r'''
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
You are about to update Lab in a BOX. This is permenant
and will DELETE Virtual Machines

ARE YOU SURE YOU WISH TO PROCEED? 

Enter yes exactly to proceed!
Enter no to exit!
'''

delete_banner = r'''
================================================.
     .-.   .-.     .--.                         |
    | OO| | OO|   / _.-' .-.   .-.  .-.   .''.  |
    |   | |   |   \  '-. '-'   '-'  '-'   '..'  |
    '^^^' '^^^'    '--'                         |
===============.  .-.  .================.  .-.  |
               | |   | |                |  '-'  |
               | |   | |                |       |
               | ':-:' |                |  .-.  |
               |  '-'  |                |  '-'  |
==============='       '================'       |
Getting some needed info, then:
CHOMP CHOMP CHOMP...
'''

no_banner = r'''
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
         :.|..| :'     to delete things!     `;--:
         '.|..|:':       _               _ _ :|_\:
      .. _:|__| '.\.''..' ) ___________ ( )_):|_|:
:....::''::/  | : :|''| "/ /_=_=_=_=_=/ :_[__'_\3_)
 ''      '-''-'-'.__)-'
'''

# Functions

def getuser():
    home = expanduser("~")
    return home

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
    try:
        print("Getting File.... %s" % (filename))
        sleep(2)
        request.urlretrieve(url,filename)
    except:
        print("Soemthing went wrong in save() and the program cannot continue safely.")
        print("\n\nExiting...")
        exit()
    

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

# NOT PEP8 cause PEP8 kept breaking my code
# Or I'm a part time idiot.
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

def findova(filename):
    '''
    Function searches user directory for file.
    It returns location/file. 

    Uses os.walk for compatibility.
    '''
    try:
        if system() == "Darwin":
            home = os.sep + r"Volumes" + os.sep + r"GoogleDrive"
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
    
    expects a full file location to a vmx file.
    
    startvm(vmx)
    
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
    
    expects a full file location to a vmx file.
    
    deletevm(vmx)
    
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

def findfile(filename, searchdir):
    '''
    Function searches user directory for file.
    It returns location/file. 
    
    Uses os.walk for compatibility.
    '''
    for base, dirs, files, in os.walk(searchdir):
        if filename in files:
            return os.path.join(base, filename)

def remove_vm_folder(each,vminfo):
    '''
    Checks for an existing folder under Virtual Machines directory.
    
    Looks for directory artifacts for .
    '''
    try:
        if system() == "Darwin":
            print("Looking for artifacts of %s" % (each))
            try:
                if getuser() + os.sep + vmware_dir_macos + vminfo.get(each).get('macos'):
                    print("Found artifacts of %s" % (each))
                    print("Attemping to remove %s" % (getuser() + os.sep + vmware_dir_macos + vminfo.get(each).get('macos')))
                    shutil.rmtree(getuser() + os.sep + vmware_dir_macos + vminfo.get(each).get('macos'))
                else:
                    print("Looks like vmrun deleted all of %s" % (each))
            except OSError as err:
                print(err)
                logger.debug(err)
        elif system() == "Windows":
            print("Looking for artifacts of %s" % (each))
            try:
                if getuser() + os.sep + vmware_dir_windows + os.sep + vminfo.get(each).get('windows'):
                    print("Found artifacts of %s" % (each))
                    print("Attemping to remove %s" % (getuser() + os.sep + vmware_dir_windows + os.sep + vminfo.get(each).get('windows')))
                    shutil.rmtree(getuser() + os.sep + vmware_dir_windows + os.sep + vminfo.get(each).get('windows'))
                else:
                    print("Looks like vmrun deleted all of %s" % (each))
            except OSError as err:
                print(err)
                logger.debug(err)
        else:
            print("Unsupported OS")
    except:
        print("An exception occured in the directory removal process.")
        logger.debug("Exception in remove_vm_folder().")

def verify_delete():
    answer = None 
    print(update_banner)
    while answer not in ("yes", "no"): 
        answer = input("Enter yes or no: ") 
        if answer == "yes": 
             print(delete_banner)
        elif answer == "no": 
             print("Installer will Exit in 10 seconds.")
             print("Log into Slack #labinabox for help.")
             sleep(5)
             print(no_banner)
             sleep(5)
             exit() 
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
            print("Script will attempt to proceed anyways.")
            logger.debug("Directory '%s' could not be created" % (getuser() + os.sep + "tmp"))
    verify_delete()
    try:
        vminfo = getvminfo(vminfo_url, vminfo_filename)
        for each in vminfo:
            if findova(vminfo.get(each).get('ova')):
                try:
                    vmx_file = findfile(vminfo.get(each).get('vmx'), getuser())
                    if vmx_file:
                        deletevm(vmx_file)
                    remove_vm_folder(each,vminfo)
                except:
                    print("Could not delete anything, script will attempt to continue")
                    logger.debug("Could not delete anything, script will attempt to continue")
                    pass
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