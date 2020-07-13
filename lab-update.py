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
(e.g., python lab-install.py)

This software is provided without support, warranty, or guarantee.
Use at your own risk.
'''

__author__ = "Richard Porter (@packetalien)"
__copyright__ = "Copyright 2018, Palo Alto Networks"
__version__ = "1.1"
__license__ = "MIT"
__status__ = "Production"

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
import time
from time import strftime
from platform import system
from subprocess import call
from logging.handlers import RotatingFileHandler
from os.path import expanduser
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
vmware_dir_windows = "Documents\Virtual Machines"
vmware_dir_macos = "Virtual Machines.localized"

ovalist = [
    "pan-soc.ova"
]
vmxlist = [
    "pan-soc.vmx"
    ]
ovafiledir = [
    "/pan-soc.vmwarevm/"
    ]
ovafiledirwin = [
    "pan-soc/"
    ]
ovagdrive = [
    "https://drive.google.com/file/d/1c7VWEKHkvLewOrsjamn7q3p_Cw6p1o-O/view?usp=sharing"
    ]

chrome_path = "open -a /Applications/Google\ Chrome.app %s"
chrome_path_win = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

# Functions

def getuser():
    home = expanduser("~")
    return home

def timestamp():
    '''
    Function returns a timestamp in %Y%m%d-%H%M%S format.
    '''
    stamp = strftime("%Y%m%d-%H%M%S")
    return stamp

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
        print ("\n")

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

def main():
    '''
    Deletes old pan-soc and installs new.
    '''
    try:
        new_pan_soc = findova("pan-soc.ova")
        logger.debug("Found ova at: %s" % (new_pan_soc))
        old_pan_soc = findfile("pan-soc.vmx", getuser())
        logger.debug("Found vmx at: %s" % (old_pan_soc))
        logger.info("Deleteing old pan-soc")
        deletevm(old_pan_soc)
        if os.system() == "Darwin":
            logger.debug("MacOS Detected starting unpack to %s" % (getuser() + os.sep + vmware_dir_macos))
            unpackova(new_pan_soc, getuser() + os.sep + vmware_dir_macos)
        elif os.system() == "Windows":
            logger.debug("MacOS Detected starting unpack to %s" % (getuser() + os.sep + vmware_dir_macos))
            unpackova(new_pan_soc, getuser() + os.sep + vmware_dir_windows)
    except:
         logger.info("An exception occured in the main function, exiting...")
         exit()
     
if __name__ == "__main__":
    main()
