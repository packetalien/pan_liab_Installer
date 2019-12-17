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

ovalist = [
    "oss-tmsclient-linux.ova",
    "pan-soc.ova"
]
vmxlist = [
    "oss-tmsclient-linux.vmx",
    "pan-soc.vmx"
    ]
ovafiledir = [
    "/oss-tmsclient-linux.vmwarevm/",
    "/pan-soc.vmwarevm/"
    ]
ovafiledirwin = [
    "oss-tmsclient-linux/",
    "pan-soc/"
    ]
ovagdrive = [
    "https://drive.google.com/open?id=1MjAb3ouk4PsQUAMK1baDigSJfFirHAnO",
    "https://drive.google.com/open?id=16oFYYnb6Qb2u0NBEUZAavwGmpYvmjFBd"
    ]

chrome_path = "open -a /Applications/Google\ Chrome.app %s"
chrome_path_win = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s'

# Functions

def getuser():
    home = expanduser("~")
    return home

def filecheck(filename):
    home = getuser()
    basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
    searchdir = home + basedir
    for base, dirs, files, in os.walk(searchdir):
        if filename in files:
            return True

def filecheckwin(filename):
    home = getuser()
    basedir = os.path.normpath("/Documents/Virtual Machines/IT-Managed-VMs")
    searchdir = os.path.normpath(home + basedir)
    for base, dirs, files, in os.walk(searchdir):
        if filename in files:
            return True

def dircheckwin():
    try:
        print ("\n")
        print("{:-^30s}".format("IT-Managed-VMs Directory Check"))
        home = getuser()
        basedir = os.path.normpath("/Documents/Virtual Machines/IT-Managed-VMs")
        vmdir = os.path.normpath(home + basedir)
        if os.path.isdir(os.path.normpath(vmdir)):
            print("SUCCESS: Directory Located.")
            print("{:-^30s}".format("IT-Managed-VMs Directory Check"))
            logger.debug("Directory located.")
        else:
            print("Directory not found. Creating it now.")
            print("{:-^30s}".format("IT-Managed-VMs Directory Check"))
            cmd = "mkdir -p"
            cmdtrue = cmd + " " + os.path.normpath("\"" + vmdir + "\"")
            logger.debug("Directory not found, sending cmd: %s" % cmdtrue)
            call(cmdtrue, shell=True)
        print ("\n")
    except:
        print ("\n")
        print("{:-^30s}".format("ERROR"))
        print(
            "An error has occured while checking for VM Directory."
            )
        logger.info("An error occured during direcotry validation.")
        print("For support please joing #labinabox on Slack.")
        print("{:-^30s}".format("ERROR"))
        print ("\n")

def dircheckmacos():
    try:
        home = getuser()
        basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
        vmdir = home + basedir
        if os.path.isdir(vmdir):
            print("SUCCESS: Directory Located.")
            print("{:-^30s}".format("IT-Managed-VMs Directory Check"))
            logger.debug("Directory located.")
        else:
            print("Directory not found. Creating it now.")
            print("{:-^30s}".format("IT-Managed-VMs Directory Check"))
            logger.debug("Directory not found, creating: %s" % vmdir)
            call(["mkdir","-p",vmdir])
    except:
        print ("\n")
        print("{:-^30s}".format("ERROR"))
        print(
            "An error has occured while checking for VM Directory."
            )
        logger.info("An error occured during direcotry validation.")
        print("For support please joing #labinabox on Slack.")
        print("{:-^30s}".format("ERROR"))
        print ("\n")

def unpackova(filename):
    home = getuser()
    basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
    builddir = home + basedir
    unpackbuilder = home + basedir + "/" + filename
    call(["/Applications/VMware Fusion.app/Contents/Library/VMware OVF Tool/ovftool",unpackbuilder,builddir])

def unpackovawin(filename):
    home = getuser()
    basedir = "/Documents/Virtual Machines/IT-Managed-VMs"
    builddir = os.path.normpath("\"" + home + basedir + "\"")
    unpackbuilder = os.path.normpath("\"" + home + basedir + "/" + filename + "\"")
    cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe\"")
    cmdtrue = (cmd + " " + unpackbuilder + " " + builddir)
    call(cmdtrue, shell=True)

def startvm(vmvmx,vmvm):
    #pdb.set_trace()
    home = getuser()
    basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
    startvm = home + basedir + vmvm + vmvmx
    call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","start",startvm])

def deletevm(vmvm,vmvmx):
    home = getuser()
    basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
    deletevirtual = home + basedir + vmvm + vmvmx
    call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","deleteVM",deletevirtual])

def suspendvm(vmvmx,vmvm):
    home = getuser()
    basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
    suspendvm = home + basedir + vmvm + vmvmx
    call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","suspend",suspendvm])

def stopvm(vmvmx,vmvm):
    #pdb.set_trace()
    home = getuser()
    basedir = "/Documents/Virtual Machines.localized/IT-Managed-VMs"
    stopvm = home + basedir + vmvm + vmvmx
    call(["/Applications/VMware Fusion.app/Contents/Library/vmrun","stop",stopvm])

def startvmwin(vmvmx,vmvm):
    home = getuser()
    basedir = os.path.normpath("/Documents/Virtual Machines/IT-Managed-VMs")
    registervm = os.path.normpath("\"" + home + basedir + vmvm + "/" + vmvmx + "\"")
    cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
    cmdtrue = os.path.normpath(cmd + " " + "-T" + " " + "ws" + " " + "start" + " " + registervm)
    call(cmdtrue, shell=True)

def deletevmwin(vmvmx,vmvm):
    home = getuser()
    basedir = os.path.normpath("/Documents/Virtual Machines/IT-Managed-VMs")
    registervm = os.path.normpath("\"" + home + basedir + vmvm + "/" + vmvmx + "\"")
    cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
    cmdtrue = os.path.normpath(cmd + " " + "-T" + " " + "ws" + " " + "deleteVM" + " " + registervm)
    call(cmdtrue, shell=True)

def suspendvmwin(vmvmx,vmvm):
    home = getuser()
    basedir = os.path.normpath("/Documents/Virtual Machines/IT-Managed-VMs")
    registervm = os.path.normpath("\"" + home + basedir + vmvm + "/" + vmvmx + "\"")
    cmd = os.path.normpath("\"c:\Program Files (x86)\VMware\VMware VIX\\vmrun.exe\"")
    cmdtrue = os.path.normpath(cmd + " " + "-T" + " " + "ws" + " " + "suspend" + " " + registervm)
    call(cmdtrue, shell=True)


def main():
    count = 0
    countvm = 0
    countstart = 0
    countsuspend = 0
    oscheck = system()
    if oscheck == "Darwin":
        try:
            if filecheck(ovalist[1]):
                print("\n")
                print("{:-^30s}".format("File Check"))
                logger.debug("File located: %s" % ovalist[1])
                print("SUCCESS: File %s Located." % (ovalist[1]))
                print("{:-^30s}".format("File Check"))
                print("\n")
            else:
                print("\n")
                print("{:-^30s}".format("File Check"))
                print("File %s has not been downloaded." % (ovalist[1]))
                print("Opening a Chrome Browser window now.")
                logger.debug("File not found, opened browser to %s" % ovagdrive[1])
                webbrowser.get(chrome_path).open(ovagdrive[1])
                print("For support joing #labinabox on Slack.")
                print("{:-^30s}".format("File Check"))
                print("\n")
            if filecheck(vmxlist[0]):
                print("\n")
                print("{:-^30s}".format("Locating and deleteing deprecated VM"))
                logger.debug("File located: %s" % vmxlist[0])
                deletevm(ovafiledir[0],vmxlist[0])
                print("SUCCESS: VM DELETED.")
            if filecheck(vmxlist[1]):
                print("\n")
                print("\n")
                print("{:-^30s}".format("Importing OVA %s" % ovalist[1]))
                print("%s already unpacked" % vmxlist[1])
                logger.debug("%s already unpacked." % vmxlist[1])
                print("{:-^30s}".format("Importing OVA %s" % ovalist[1]))
                print("\n")
            else:
                print("\n")
                print("{:-^30s}".format("Importing OVA %s" % ovalist[1]))
                print("We are unpacking %s, this could take some time. \n " % (ovalist[1]))
                unpackova(ovalist[1])
                print("For support joing #labinabox on Slack.")
                print("{:-^30s}".format("Importing OVA %s" % ovalist[1]))
                print("\n")
            for eachstart in vmxlist:
                startvm(vmxlist[1],ovafiledir[1])
                stopvm(vmxlist[1],ovafiledir[1])
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
    elif oscheck == "Windows":
        try:
            for each in ovalist:
                if filecheckwin(each):
                    print("\n")
                    print("{:-^30s}".format("File Check"))
                    logger.debug("File located: %s" % each)
                    print("SUCCESS: File %s Located." % (each))
                    print("{:-^30s}".format("File Check"))
                    print("\n")
                else:
                    print("\n")
                    print("{:-^30s}".format("File Check"))
                    print("File %s has not been downloaded." % (each))
                    print("Opening a Chrome Browser window now.")
                    logger.debug("File not found, opened browser to %s" % ovagdrive[count])
                    webbrowser.get(chrome_path_win).open(ovagdrive[count])
                    print("For support joing #labinabox on Slack.")
                    print("{:-^30s}".format("File Check"))
                    print("\n")
                count = count + 1
            for eachvm in vmxlist:
                if filecheckwin(eachvm):
                    print("\n")
                    print("{:-^30s}".format("Importing OVA %s" % eachvm))
                    print("%s already unpacked" % eachvm)
                    logger.debug("%s already unpacked." % eachvm)
                    print("{:-^30s}".format("Importing OVA %s" % eachvm))
                    print("\n")
                else:
                    print("\n")
                    print("{:-^30s}".format("Importing OVA %s" % eachvm))
                    print("We are unpacking %s, this could take some time. \n " % (eachvm))
                    unpackovawin(ovalist[countvm])
                    print("For support joing #labinabox on Slack.")
                    print("{:-^30s}".format("Importing OVA %s" % eachvm))
                    print("\n")
                countvm = countvm + 1
            for eachstart in vmxlist:
                startvmwin(eachstart,ovafiledirwin[countstart])
                countstart = countstart + 1
                suspendvmwin(eachstart,ovafiledirwin[countsuspend])
                countsuspend = countsuspend + 1
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
    else:
        print ("\n")
        print("{:-^30s}".format("ERROR"))
        print(
            "A major error has occured and the install process has halted."
            )
        logger.debug("Error, install halted. Unsupported OS.")
        print("For support contact #labinabox on Slack.")
        print("{:-^30s}".format("ERROR"))
        print ("\n")

if __name__ == "__main__":
    main()