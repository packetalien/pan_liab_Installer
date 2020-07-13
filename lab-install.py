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

panos_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/pan-vm50.vmx"
setools_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/linux-utility.vmx"
msft_dc_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/msft-dc.vmx"
msft_rodc_vmx = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/vmx/msft-rodc.vmx"
vminfo_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/json/vminfo.json"
fusion_url = "https://raw.githubusercontent.com/packetalien/fusion-network-config/master/vmnet-configure.py"
win_install_url = "https://loop.paloaltonetworks.com/docs/DOC-36656"
win_network_url = "https://loop.paloaltonetworks.com/docs/DOC-36685"
macos_install_url = "https://loop.paloaltonetworks.com/docs/DOC-36686"
workstation_url = "https://github.com/packetalien/diabresources/blob/master/db/defaultse?raw=true"
pan_license_url = "https://drive.google.com/open?id=1JcyZgitSsGY0JCTXoUJPAJRweZHyX2AQ"
liab_gdrive = "https://drive.google.com/drive/u/0/folders/1Yh6Ca4wThWRmwEWtVuShc2uqicV0ziW4"
config_url = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/json/config.json"

# TODO: Move all of this to a CONF file.
# Default Directories
vmware_dir_windows = "Documents\Virtual Machines"
vmware_dir_macos = "Virtual Machines.localized"
IT_SCCM_dir = "C:\ProgramData"

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

def import_network_settings(config_file, location):
    '''
    Function sends start vnetlib.exe command to Windows
    via subprocess.call(). It "Attempts" to import
    network settings. The word attempt is used as
    results have been mixed, even with shell=True.
    
    WARNING: Function uses shell=True argument due
    to Windows commmand processing compatibility with
    VMWare Workstation.
    '''
    try:
        cmd = r"c:\Program Files (x86)\VMware\VMware Workstation\vnetlib.exe -- import "
        logger.debug("Sending following command to shell: %s" % (cmd))
        netcfg = getuser() + os.sep + config_file
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
    home = getuser()
    for base, dirs, files, in os.walk(home):
        if filename in files:
            return os.path.join(base, filename)

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

#TODO: Build OVF detector.

def integrity_checker():
    '''
    TODO: Create function that recovers from integrity fails.
    Function just passes right now.
    '''
    pass

def IT_artifact_creator():
    '''
    Function creates are appends to installer log file
    for IT to read
    '''
    if system() == "Darwin":
        if os.path.exists():
            pass
        else:
            pass
    elif system() == "Windows":
        if os.path.exists(IT_SCCM_dir + os.sep + IT_artifact_file):
            try:
                time_stamp = timestamp()
                f = open(IT_SCCM_dir + os.sep + IT_artifact_file, "a+")
                f.write(time_stamp + " - LiaB Install Complete.")
                f.close()
            except:
                logger.debug("Exception occured in Windows IT_Artifact_creator() a+")
                exit()
        else:
            try:
                time_stamp = timestamp()
                f = open(IT_SCCM_dir + os.sep + IT_artifact_file, "w+")
                f.write(time_stamp + " - LiaB Install Complete.")
                f.close()
            except:
                logger.debug("Exception occured in Windows IT_Artifact_creator() w+")
                exit()
    else:
        logger.info("Unsupported OS detected, process will exit.")
        exit()

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
            print("Getting defaultse config file now.")
            print("Please import it in Virtual Networks Editor.")
            print("Saving %s to: %s " % (workstation_url, getuser() + os.sep + vmware_dir_windows))
            logger.info("Windows vnetlib.exe uses an odd -- switch.")
            logger.info("Getting the config file, you will need to manually import.")
            logger.info("Saving %s to: %s " % (workstation_url, getuser() + os.sep + vmware_dir_windows))
            save(workstation_url, getuser() + os.sep + vmware_dir_windows + os.sep + workstationcfgfile)
            print("\nOpening instructions in 5 seconds.")
            time.sleep(5)
            webbrowser.get(chrome_path_win).open(win_network_url)
        else:
            print("Unsupported OS detected, program will exit.")
            logger.info("Unsupported OS. Now exiting.")
            exit()
    except:
        logger.debug("Exception occured in network_loader() os type: %s" % (system()))

def pan_license(vminfo):
    '''
    Licenses VM-Series.
    TODO: Cleanup functions, remove installer files.
    ''' 
    try:
        if system() == "Darwin":
            logger.info("Starting licensing process.")
            print("{:-^30s}".format("Starting Licensing Process."))
            print("{:-^30s}".format("It can take VM-Series 7 MIN to boot."))
            print("{:-^30s}".format("Please be patient."))
            startvm(findfile(vminfo.get("panvm50").get('vmx'), getuser() + os.sep + vmware_dir_macos))
            call([python_mac, findfile(pan_license_filename, getuser())])
        elif system() == "Windows":
            logger.info("Starting licensing process.")
            cmd = os.path.normpath("\"c:\Program Files (x86)\Python37-32\python.exe\"")
            print("{:-^30s}".format("Starting Licensing Process."))
            print("{:-^30s}".format("It can take VM-Series 7 MIN to boot."))
            print("{:-^30s}".format("Please be patient."))
            startvm(findfile(vminfo.get("panvm50").get('vmx'), getuser() + os.sep + vmware_dir_windows))
            license_file = findfile(pan_license_filename, getuser())
            cmdtrue = os.path.normpath(cmd + " " + os.path.normpath("\"%s\"" % (license_file)))
            logger.debug("Sent the following to Windows Shell: %s" % (cmdtrue))
            call(cmdtrue, shell=True)
        else:
            print("Unsupported OS detected, program will exit.")
            logger.info("Unsupported OS. Now exiting.")
            exit()
    except:
        logger.debug("Exception occured in network_loader() os type: %s" % (system()))

def file_checker():
    '''
    File audit check for Lab in a Box Install.
    This function will search for nessesary files
    and if they are not present, will exit the install
    with instructions to remediate.
    '''
    pass

def main():
    oscheck = system()
    try:
        vminfo = getvminfo(vminfo_url, vminfo_filename)
        network_loader()
        if find_license_file(pan_license_filename, getuser()):
            logger.info("Located current license installer.")
            print("Located current pan-license-vmseries.py.")
            pass
        else:
            logger.info("License installer not located. Exiting.")
            print("{:-^40s}".format("pan-license-vmseries.py ERROR"))
            print("Current license installer file not located, intaller will exit.")
            print("Opening location to installer file. Please download and restart install.")
            print("{:-^40s}".format("pan-license-vmseries.py ERROR"))
            if system() == "Darwin":
                webbrowser.get(chrome_path).open(pan_license)
            elif system() == "Windows":
                webbrowser.get(chrome_path_win).open(pan_license)
            exit()
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
        pan_license(vminfo)
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
