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
Palo Alto Networks lab-install.py

This script retrieves and installs SE Lab in a Box

Execute the script and it auomtatically builds (e.g., python lab-install.py)

This software is provided without support, warranty, or guarantee.
Use at your own risk.
'''

__author__ = "Richard Porter (@packetalien)"
__copyright__ = "Copyright 2018, Palo Alto Networks"
__version__ = "1.3"
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
import json
import glob
from time import strftime
from platform import system
from subprocess import call
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
'''
Left for legacy reasons, TODO: Delete during next update.
vm_list = [
    "panpanosvm50",
    "osssetoolslinux",
    "msftesm-dc",
    "msftvictimw7",
    "pansoc",
    "msfttmsclientw10",
    "msftrodc",
    "panpanorama",
    "panexpedition"
]
ovalist = [
    "pan-panos-vm50.ova",
    "oss-setools-linux.ova",
    "msft-esm-dc.ova",
    "msft-victim-w7.ova",
    "pan-soc.ova",
    "msft-tmsclient-w10.ova",
    "msft-rodc.ova",
    "pan-panorama.ova",
    "pan-expedition.ova"
]
vmxlist = [
    "pan-panos-vm50.vmx",
    "oss-setools-linux.vmx",
    "msft-dc.vmx",
    "msft-victim-w7.vmx",
    "pan-soc.vmx",
    "msft-w10.vmx",
    "msft-rodc.vmx",
    "pan-panorama.vmx",
    "pan-expedition.vmx"
    ]
ovafiledir = [
    "/pan-panos.vmwarevm/",
    "/oss-setools-linux.vmwarevm/",
    "/msft-esm-dc.vmwarevm/",
    "/msft-victim-w7.vmwarevm/",
    "/pan-soc.vmwarevm/",
    "/msft-tmsclient-w10.vmwarevm/",
    "/msft-rodc.vmwarevm/",
    "/pan-panorama.vmwarevm/",
    "/pan-expedition.vmwarevm/"
    ]
ovafiledirwin = [
    "pan-panos/",
    "oss-setools-linux/",
    "msft-esm-dc/",
    "msft-victim-w7/",
    "oss-tmsclient-linux/",
    "msft-tmsclient-w10/",
    "msft-rodc/",
    "pan-panorama/",
    "pan-expedition/"
    ]
'''
# TODO: Move to imported files for portability.
# TODO look at path normalization, Localized Variables
# TODO: Create builder class for installer
# TODO: Move local variables to a conf file in 3.0
# URLS

panos_vmx = "https://raw.githubusercontent.com/packetalien/diabresources/master/vmx/pan-panos-vm50.vmx"
setools_vmx = "https://raw.githubusercontent.com/packetalien/diabresources/master/vmx/oss-setools-linux.vmx"
vminfo_url = "https://raw.githubusercontent.com/packetalien/diabresources/master/db/vminfo.json"
fusion_url = 'https://raw.githubusercontent.com/packetalien/fusion-network-config/master/fusion-vmnet-config.txt'

# Default VMware Directories
vmware_dir_windows = "\"Documents\\Virtual Machines\\\"" 
vmware_dir_macos = "Virtual Machines.localized"

# Legacy Directory (deprecated)
legacy_dir = "IT-Managed-VMs"

# Default Chrome install paths for MacOS and Windows
chrome_path = "open -a /Applications/Google\ Chrome.app %s"
chrome_path_win = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

# Files TODO: Move to conf file.
vmnetfile = "fusion-vmnet-config.txt"
funsioncfgfile = 'networking'
vminfo_filename = "vminfo.json"
panos_vmx_filename = "pan-panos-vm50.vmx"
setools_vmx_filename = "pan-panos-vm50.vmx"

# Hard Coded hashes, TODO: Move to conf file.
vminfo_sha = "c3a090f12794cd35579ba9d8f0187761dfd4452e"
panos_vmx_hash = "559fbc57ef121eb88076e821454371e100e59061"
se_tools_vmx_hash = "28b694dfa0fd6ca75b466c14574e3b16cb8af8b6"

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
    try:
        call(['osascript', '-e', 'tell application "VMWare FUsion" to quit'])
    except:
        logger.debug("Exception occured in start_fusion()")

def stop_workstation():
    pass

def start_fusion():
    try:
        call(['osascript', '-e', 'tell application "VMWare FUsion" to activate'])
    except:
        logger.debug("Exception occured in start_fusion()")

def start_workstation():
    pass


# TODO: Migrate vmware_dir_macos to conf file for portability. 
# target 3.0 releases.
# TODO: Make this smarter, error conditions, what if vmx does not exist, etc.
# Should be okay for now.
# TODO: Format me please!

def get_vmx(url, filename):
    '''
    This function retrieves vmx from resource github.
    Calls the move_vmx() function to replace vmx file.
    '''
    try:
        if system() == "Darwin":
            save(url, getuser() + os.sep + filename)
            logger.info("Success: got the file from URL.")
            copy(findfile(filename, getuser() + os.sep + vmware_dir_macos), findfile(filename, getuser() + os.sep + vmware_dir_macos) + ".bak")
            logger.info("Copied %s to %s" % (findfile(filename, getuser() + os.sep + vmware_dir_macos), findfile(filename, getuser() + os.sep + vmware_dir_macos) + ".bak"))
            copy(getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_macos))
            logger.info("Copied %s to %s" % (getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_macos)))
            logger.debug("Success, replaced local vmx with master vmx.")
            logger.info("Cleaning up. Deleting %s" % (getuser() + os.sep + filename))
            os.remove(getuser() + os.sep + filename)
        elif system == "Windows":
            save(url, getuser() + os.sep + filename)
            logger.info("Success: got the file from URL.")
            copy(findfile(filename, getuser() + os.sep + vmware_dir_windows), findfile(filename, getuser() + os.sep + vmware_dir_windows) + ".bak")
            logger.info("Copied %s to %s" % (findfile(filename, getuser() + os.sep + vmware_dir_windows), findfile(filename, getuser() + os.sep + vmware_dir_windows) + ".bak"))
            copy(getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_windows))
            logger.info("Copied %s to %s" % (getuser() + os.sep + filename, findfile(filename, getuser() + os.sep + vmware_dir_windows)))
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
    try:
        logger.debug("Started ova upack at %s"
                     % str(timestamp()))
        call(["/Applications/VMware Fusion.app/Contents/Library/VMware OVF Tool/ovftool",
              filename, location])
        logger.debug("Completed ova unpack at %s"
                     % str(timestamp()))
    except:
        logger.debug("Exception occured in unpackova().")
        
def unpackovawin(filename):
    home = getuser()
    basedir = "/Documents/Virtual Machines/IT-Managed-VMs"
    builddir = os.path.normpath("\"" + home + basedir + "\"")
    unpackbuilder = os.path.normpath("\"" + home + basedir + "/" + filename + "\"")
    cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe\"")
    cmdtrue = (cmd + " " + unpackbuilder + " " + builddir)
    call(cmdtrue, shell=True)

def startvm(vmx):
    '''
    Starts a virtual machine in VMWare Fusion.
    Expects a full path for vmx variable.
    '''
    try:
        call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","start",
              vmx])
        logger.debug("Succesfully started %s" % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" % (e))
        
def deletevm(vmx):
    '''
    Deletes a virtual machine in VMWare Fusion.
    Expects a full path for vmx variable.
    '''
    try:
        call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","deleteVM",
              vmx])
    except:
        logger.debug("Exception occured in deletevm().")

def suspendvm(vmx):
    '''
    Suspends a virtual machine in VMWare Fusion.
    Expects a full path for vmx variable.
    '''
    try:
        call(["/Applications/VMware Fusion.app/Contents/Library/vmrun",
              "suspend", vmx])
        logger.debug("Successfully suspended %s" % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" (e))

def stopvm(vmx):
    '''
    Stops a virtual machine in VMWare Fusion.
    Expects a full path for vmx variable.
    '''
    try:
        call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","stop",vmx])
        logger.debug("Successfully stopped %s " % (vmx))
    except IOError as e:
        logger.debug("IOError as %s" % (e))

def startvmwin(vmx):
    try:
        cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
        cmdtrue = os.path.normpath(cmd +
                                   " " + "-T" + " " + "ws" +
                                   " " + "start" + " " + vmx)
        call(cmdtrue, shell=True)
    except:
        logger.debug("An exception occured in startvmwin()")

def deletevmwin(vmx):
    try:
        cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
        cmdtrue = os.path.normpath(cmd +
                                   " " + "-T" + " " + "ws"
                                   + " " + "deleteVM" + " " + vmx)
        call(cmdtrue, shell=True)
    except:
        logger.debug("An exception occured in deletevmwin()")

def suspendvmwin(vmx):
    try:
        cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
        cmdtrue = os.path.normpath(cmd +
                                   " " + "-T" + " " + "ws"
                                   + " " + "suspend" + " " + vmx)
        call(cmdtrue, shell=True)
    except:
        logger.debug("An exception occured in suspendvmwin()")

def stopvmwin(vmx):
    try:
        cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
        cmdtrue = os.path.normpath(cmd +
                                   " " + "-T" + " " + "ws"
                                   + " " + "stop" + " " + vmx)
        call(cmdtrue, shell=True)
    except:
        logger.debug("An exception occured in stopvmwin()")

#TODO: Remove system dependencies. Cross Platform.

#TODO: Build OVF detector.

def integrity_checker():
    '''
    TODO: Create function that recovers from integrity fails.
    Function just passes right now.
    '''
    pass

def main():
    oscheck = system()
    vminfo = getvminfo(vminfo_url, vminfo_filename)
    try:
        for each in vminfo:
            if findova(vminfo.get(each).get('ova')):
                print("\n")
                print("{:-^30s}".format("Searching...."))
                logger.debug("File located: %s" % (vminfo.get(each).get('ova')))
                print("SUCCESS: File %s Located." % (vminfo.get(each).get('ova')))
                local_sha = sha1sum(findova(vminfo.get(each).get('ova')))
                print("SHA: %s" % (local_sha))
                print("{:-^30s}".format("Checking Integrity...."))
                if check_sha1sum(vminfo.get(each).get('sha1sum'), local_sha) == True:
                    print("Integrity Check Successful.")
                    print("{:-^30s}".format("Check Complete...."))
                    logger.info("Integrity Check Successful.")
                else:
                    print("Integrity Check Fail. Consider re-downloading.")
                    if oscheck == "Darwin":
                        webbrowser.get(chrome_path).open(vminfo.get(each).get('sourceurl'))
                        logger.debug("Opened Browser to SourceURL for %s" % (vminfo.get(each).get('name')))
                    elif oscheck == "Windows":
                        webbrowser.get(chrome_path_win).open(vminfo.get(each).get('sourceurl'))
                        logger.debug("Opened Browser to SourceURL for %s" % (vminfo.get(each).get('name')))
                    else:
                        logger.debug("Tried to open browser to SourceURL."
                                     + " Unsupported OS detected")
                    print("{:-^30s}".format("Check Complete...."))
                    logger.info("Integrity Check Fail. Re-download suggested.")
                print("{:-^30s}".format("Unpacking....%s" % (vminfo.get(each).get('ova'))))
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
                                stop_fusion()
                                if vminfo.get(each).get('name') == "pan-panos-vm50":
                                    get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                elif vminfo.get(each).get('name') == "oss-setools-linux":
                                    get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                else:
                                    pass
                                start_fusion()
                        else:
                            dir_build()
                            if vminfo.get(each).get('status') == True:
                                unpackova(findova(vminfo.get(each).get('ova')),
                                        getuser() + os.sep + vmware_dir_macos)
                                logger.info("Unpack completed at %s" % str(timestamp()))
                                print("Unpack completed at %s" % str(timestamp()))
                                stop_fusion()
                                if vminfo.get(each).get('name') == "pan-panos-vm50":
                                    get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                elif vminfo.get(each).get('name') == "oss-setools-linux":
                                    get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                else:
                                    pass
                                start_fusion()
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
                                stop_fusion()
                                if vminfo.get(each).get('name') == "pan-panos-vm50":
                                    get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                elif vminfo.get(each).get('name') == "oss-setools-linux":
                                    get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                else:
                                    pass
                                start_fusion()
                        else:
                            dir_build()
                            if vminfo.get(each).get('status') == True:
                                unpackova(findova(vminfo.get(each).get('ova')),
                                        getuser() + os.sep + vmware_dir_windows)
                                logger.info("Unpack completed at %s" % str(timestamp()))
                                print("Unpack completed at %s" % str(timestamp()))
                                stop_fusion()
                                if vminfo.get(each).get('name') == "pan-panos-vm50":
                                    get_vmx(panos_vmx, vminfo.get(each).get('vmx'))
                                elif vminfo.get(each).get('name') == "oss-setools-linux":
                                    get_vmx(setools_vmx, vminfo.get(each).get('vmx'))
                                else:
                                    pass
                                start_fusion()
                    else:
                        logger.info("Unsupported OS Detected, install will halt.")
                        exit()
                except:
                    logger.debug("Error in the unpack process.")
                    print("Error in the unpack process.")
            else:
                print("\n")
                print("{:-^30s}".format("File Check"))
                print("File %s has not been downloaded." % (each))
                print("Opening a Chrome Browser window now.")
                logger.debug("File not found, opened browser to %s" % 
                            vminfo.get(each).get('sourceurl'))
                webbrowser.get(chrome_path).open(vminfo.get(each).get('sourceurl'))
                print("For support joing #labinabox on Slack.")
                print("{:-^30s}".format("File Check"))
                print("\n")
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