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
Palo Alto Networks lab-publish.py

This script runs the publishing Workflow for new VM in Lab in a Box.

Execute the script and it automatically builds (e.g., python3 lab-publish.py)

This software is provided without support, warranty, or guarantee.
Use at your own risk.
'''

import os
import re
import sys
from sys import platform
import time
import getpass
import fnmatch
import time
import platform
import logging
import argparse
from os.path import expanduser
from subprocess import call
from logging.handlers import RotatingFileHandler
try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    raise ValueError("requests support not available, please install module. \n Please install python requests library.")
import xml.etree.ElementTree as ET


logger = logging.getLogger(__name__)
logLevel = 'DEBUG'
maxSize = 10000000
numFiles = 10
handler = RotatingFileHandler(
    'licensing.log', maxBytes=maxSize, backupCount=numFiles
    )
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel("DEBUG")

# system variable represents device being queried. This can be in the form
# of an IP address or FQDN (e.g., 10.10.10.1 or system.example.com).
#
# Change to your system.
parser = argparse.ArgumentParser(description='VM-Series License script options.')
parser.add_argument("-o", "--ovaname",
                    help="Name of OVA to export. To use: ./lab-publish.py -o pan-panos.ova,
                    default="pan-panos.ova", required=True)
parser.add_argument("-j", "--jname",
                    help="Name of JSON descriptor / profile.
                    default="vm.json", required=True)
parser.add_argument("-s", "--savedir",
                    help="Sets directory to save files.
                    default="~/", required=True)

                
    