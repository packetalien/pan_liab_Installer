﻿# ========================================================================
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# ========================================================================

# This script creates the IT-Managed-VMs Directory and opens two instruction
# pages. First page is a pre-flight guide (installing and downloading needed
# scripts and tools). The second page is the instruction guide.

# When the script completes it will write out a simple text file named
# "liab-installer-step1.txt" 

# Author: Richard Porte
# Contact: rporter@paloaltonetworks.com

# Modules used by this script
Import-Module BitsTransfer

# Variables used by this script

$instructionsurl = "https://docs.google.com/document/d/1b3ZJ4Nv8iFp3DuOyNrn9WmTWQ2uYspU9cVKYYtFvM0M"
$pythoninstaller = "https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/lab-update.py"
$getpython = "https://www.python.org/ftp/python/3.7.7/python-3.7.7.exe"
$pythonout = ".\python-3.7.7.exe"
$pythonexe = "C:\Program Files (x86)\Python37-32\python.exe"
$pythoninstallername = "lab-update.py"


# Self-elevate the script if required
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {  if ([int](Get-CimInstance -Class Win32_OperatingSystem | Select-Object -ExpandProperty BuildNumber) -ge 6000) {
  $CommandLine = "-File `"" + $MyInvocation.MyCommand.Path + "`" " + $MyInvocation.UnboundArguments
  Start-Process -FilePath PowerShell.exe -Verb Runas -ArgumentList $CommandLine
  Exit
 }
}


$itdir = "$env:USERPROFILE\Documents\Virtual Machines\"

#Running test for IT Directory
if(!(Test-Path -Path $itdir )){

    New-Item -ItemType Directory -Force -Path $itdir
    "Created Directory: $itdir"
}

# Setting the script execution space to our IT-Managed-VMs directory

set-location $itdir

# MSI Name is hard coded (for some reason powershell did not like the VAR?
# Test Case for Install only if not present.
# TODO: Add case for update and an else for wrong version re-install

if(!(Test-Path -Path "c:\Program Files (x86)\Python37-32\python.exe"))
{

Start-BitsTransfer -Source $getpython -Destination $pythonout
& cmd /c "python-3.7.7.exe" "/quiet" "InstallAllUsers=1" "PrependPath=1"

}


if(Test-Path -Path "c:\Program Files (x86)\Python37-32\python.exe")
{
  Start-BitsTransfer -Source $pythoninstaller -Destination $pythoninstallername 
  & cmd /c $pythonexe "$pythoninstallername"
}
else {
  "Script could not find python. An install was attempted. Please contact #labinabox on Slack for support."
}
# Calling Chrome for Instructions Page

Start-Process "chrome.exe" $instructionsurl
# SIG # Begin signature block
# MIIPMQYJKoZIhvcNAQcCoIIPIjCCDx4CAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUyNLYTBefYfg+nog+Dn7lbibC
# Dnmgggx/MIIFtzCCA5+gAwIBAgITWgAAAAKvEDrpExwlZwAAAAAAAjANBgkqhkiG
# 9w0BAQsFADBXMQswCQYDVQQGEwJVUzEfMB0GA1UEChMWUGFsbyBBbHRvIE5ldHdv
# cmtzIEluYzEnMCUGA1UEAxMeUGFsbyBBbHRvIE5ldHdvcmtzIEluYyBSb290IENB
# MB4XDTE1MTAwNzIyMDYxOFoXDTI1MTAwNzIyMTYxOFowZDEVMBMGCgmSJomT8ixk
# ARkWBWxvY2FsMSAwHgYKCZImiZPyLGQBGRYQcGFsb2FsdG9uZXR3b3JrczEpMCcG
# A1UEAxMgUGFsbyBBbHRvIE5ldHdvcmtzIEluYyBEb21haW4gQ0EwggEiMA0GCSqG
# SIb3DQEBAQUAA4IBDwAwggEKAoIBAQC9XOQs3v81nNbFUdxYm4/0K5tsebFingkk
# OQwX/nUMGglggdK97rg7NUTqOLH/rru+Sq9Rpym3sPgE+yWu2yB+Dlpioe1SheB7
# s8yQvIEMZ37QUZFP20z/5iCfp5/yH7CI8wFtz3NdnPgXWliVRMB46MQ0Dnzdfz9D
# kVVqZiC3LN4cm/lW6T/LDK3BGh/q1cBbF7Hh5cfuU73FPEXoSjkxZpcfQnWVVXyd
# pxawJY2ATV/SxQgHuIkSORkm6X/5UKA1cgXTvek/L3PVK+i0TZ89JXOCVXqF477O
# tpsvaH3uQNpba8KPKLJUDZc9QqBCz+txZWfbV/6BW1Frs5K9yhAHAgMBAAGjggFt
# MIIBaTAQBgkrBgEEAYI3FQEEAwIBADAdBgNVHQ4EFgQUdJqiXVwjL2HiczegFjXc
# QniLFe8wGQYJKwYBBAGCNxQCBAweCgBTAHUAYgBDAEEwCwYDVR0PBAQDAgGGMA8G
# A1UdEwEB/wQFMAMBAf8wHwYDVR0jBBgwFoAUbR1jB6PdirzvY84GsmDKadyyxlow
# YQYDVR0fBFowWDBWoFSgUoZQaHR0cDovL2NybC5wYWxvYWx0b25ldHdvcmtzLmNv
# bS9jcmwvUGFsbyUyMEFsdG8lMjBOZXR3b3JrcyUyMEluYyUyMFJvb3QlMjBDQS5j
# cmwweQYIKwYBBQUHAQEEbTBrMGkGCCsGAQUFBzAChl1odHRwOi8vY3JsLnBhbG9h
# bHRvbmV0d29ya3MuY29tL2NybC9zamNjcmNhcHcwMXBfUGFsbyUyMEFsdG8lMjBO
# ZXR3b3JrcyUyMEluYyUyMFJvb3QlMjBDQS5jcnQwDQYJKoZIhvcNAQELBQADggIB
# AJiqqB6tPW/cWViNnqOMXzLO2ys9Kk/OKHCkK815Q3oE8Cyc/8obZgeBk/b4V5AV
# yAz0TYYwYkaEqWLqI46yJKIKBpFHczfyqMgJSdCWv92WMcDUGK8k9AEKg9S8WWfI
# W4pOYTvSvuQKbi7YcFbRdgM6Ju0u3RHwydW5F0QK5yhQEdG9qO/6YDQeN86kB5NA
# pPxta+yM0i4yh0HASomphXQN77C84OeA7mt6LpsUBBDU/8TUxM9J6J6B4YUxxkX1
# IToLtyXfZAA+kAh8s4kAz3zsg6dpPTrDKzj7nnezLZLFzN++VFxD9Z5RwAGU2lVE
# inXi8Vv/2ChuQnUN46/a3PDEcp1udPYSre10WeUfGBCnBuu4RUREewnOTMBKfFnK
# 8HN6AEfV9h2fnqYENYEYnhMYgBS7+DOfw8siPOrCHVA33lkYXf2690ENHTZPL5Cl
# 3R/a2PzYFd6JhalLFr6D0VUuMynmy+AzwEwHIo+n4Q5o3EjwFznWajDtBJhkSbqt
# Gq6W54GcbEmEmBfsulkCsJui+exRuhUt12rbaJXUDu64SAL0G6w+4dq0/yQjDVAF
# nFZpZR3MJ6XaKfmzKcojsRnImFtqQ3u/IR+Iq90WF6vuuSkmnF56Y9uWcn1+GxHP
# QTUvPF0X8/EThuVMHwmSNiE8TSma6GIKOXg7c7g/C92eMIIGwDCCBaigAwIBAgIT
# ZAAOCd5C5xeYyxU1lwAAAA4J3jANBgkqhkiG9w0BAQsFADBkMRUwEwYKCZImiZPy
# LGQBGRYFbG9jYWwxIDAeBgoJkiaJk/IsZAEZFhBwYWxvYWx0b25ldHdvcmtzMSkw
# JwYDVQQDEyBQYWxvIEFsdG8gTmV0d29ya3MgSW5jIERvbWFpbiBDQTAeFw0xOTEy
# MTgxNTM2MDJaFw0yMDEyMTcxNTM2MDJaMIGDMRUwEwYKCZImiZPyLGQBGRYFbG9j
# YWwxIDAeBgoJkiaJk/IsZAEZFhBwYWxvYWx0b25ldHdvcmtzMQwwCgYDVQQLEwNQ
# QU4xDjAMBgNVBAsTBVVzZXJzMREwDwYDVQQLEwhBbWVyaWNhczEXMBUGA1UEAxMO
# UmljaGFyZCBQb3J0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDB
# OcHfuEw4XaFVw2tWGupKxXuye+aJ/GzOykZ13UgGU2okCTqGMctdEnQ92W6yS504
# 63DHmr5ngX8LuYiUFBniOBGch/T9FUTcC7y31HDSySFcm2Lu7Y4W+pDbPIkQGin5
# 1aWY2E71YG+UwLK4aoImwsEL4op1pg8dAcBSmYB1pH3p4nDEmUMkG88cKQZw9bM1
# GpYW6KKr95HZVFNqKJTefuVjaMZSCG8mvdeqppqYRaqTlP1JOLNpO8EqUJwj47yx
# DLfmqxLGc2NhEgS2N413bNJnoSF+OXkG3S+VHVkqwoiEd3TBuKBlpUPvjiqgmKBf
# BfLVRYHzE25SozTs98HxAgMBAAGjggNJMIIDRTA9BgkrBgEEAYI3FQcEMDAuBiYr
# BgEEAYI3FQiCqMEsgfq9BILpnzuE4esegcH7emeD36whgcWUUAIBZAIBCDATBgNV
# HSUEDDAKBggrBgEFBQcDAzALBgNVHQ8EBAMCB4AwGwYJKwYBBAGCNxUKBA4wDDAK
# BggrBgEFBQcDAzAdBgNVHQ4EFgQUQMHH106k7EuXkA3hogWPmu/PlPcwHwYDVR0j
# BBgwFoAUdJqiXVwjL2HiczegFjXcQniLFe8wggEOBgNVHR8EggEFMIIBATCB/qCB
# +6CB+IZSaHR0cDovL2NybC5wYWxvYWx0b25ldHdvcmtzLmNvbS9jcmwvUGFsbyUy
# MEFsdG8lMjBOZXR3b3JrcyUyMEluYyUyMERvbWFpbiUyMENBLmNybIaBoWxkYXA6
# Ly8vQ049UGFsbyUyMEFsdG8lMjBOZXR3b3JrcyUyMEluYyUyMERvbWFpbiUyMENB
# LENOPXNqY2NlY2F2dzAxcCxDTj1DRFAsQ049UHVibGljJTIwS2V5JTIwU2Vydmlj
# ZXMsQ049U2VydmljZXMsQ049Q29uZmlndXJhdGlvbixEQz1wYWxvYWx0b25ldHdv
# cmtzLERDPWxvY2FsMIIBOAYIKwYBBQUHAQEEggEqMIIBJjCBggYIKwYBBQUHMAKG
# dmh0dHA6Ly9jcmwucGFsb2FsdG9uZXR3b3Jrcy5jb20vY3JsL3NqY2NlY2F2dzAx
# cC5wYWxvYWx0b25ldHdvcmtzLmxvY2FsX1BhbG8lMjBBbHRvJTIwTmV0d29ya3Ml
# MjBJbmMlMjBEb21haW4lMjBDQS5jcnQwgZ4GCCsGAQUFBzAChoGRbGRhcDovLy9D
# Tj1QYWxvJTIwQWx0byUyME5ldHdvcmtzJTIwSW5jJTIwRG9tYWluJTIwQ0EsQ049
# QUlBLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2VzLENOPVNlcnZpY2VzLENOPUNv
# bmZpZ3VyYXRpb24sREM9cGFsb2FsdG9uZXR3b3JrcyxEQz1sb2NhbDA3BgNVHREE
# MDAuoCwGCisGAQQBgjcUAgOgHgwccnBvcnRlckBwYWxvYWx0b25ldHdvcmtzLmNv
# bTANBgkqhkiG9w0BAQsFAAOCAQEAkjFzffrcyR3GArHwrtdEtpFVmNulkOtoxBil
# zmp2hscCVoWTvM4oMe/zd12IMl2k2AZIY9z92j32d/YI7M/P5f9g5nX2YIAFv0rm
# ZEJfwl88N3tEXeHzrigQbDENLp5mZZ0XKN8XaHjW+TNdFihrwLLzEWTkGuF9MgT4
# jdrNMST3FN48j4SP6bXZHIxPmBpeYPXH86/iz8UdllLGHJIvr0GnQ1sfSx9TztZE
# DruUo66Jxr+SlHEOvGgwgX0pOx74OMHfDj8rSM12kKARZd6e9KmXPIbkhW01/4Kx
# xIYE73LQN2fXLkEd/k/0dV7M7z7IxA0HlEXyZ21TBiyuz5Vi4TGCAhwwggIYAgEB
# MHswZDEVMBMGCgmSJomT8ixkARkWBWxvY2FsMSAwHgYKCZImiZPyLGQBGRYQcGFs
# b2FsdG9uZXR3b3JrczEpMCcGA1UEAxMgUGFsbyBBbHRvIE5ldHdvcmtzIEluYyBE
# b21haW4gQ0ECE2QADgneQucXmMsVNZcAAAAOCd4wCQYFKw4DAhoFAKB4MBgGCisG
# AQQBgjcCAQwxCjAIoAKAAKECgAAwGQYJKoZIhvcNAQkDMQwGCisGAQQBgjcCAQQw
# HAYKKwYBBAGCNwIBCzEOMAwGCisGAQQBgjcCARUwIwYJKoZIhvcNAQkEMRYEFMvF
# Wy3/FkL7L/9qmXBByJN/S7AIMA0GCSqGSIb3DQEBAQUABIIBAJ6FRgvCYohLsa7z
# Y5w1rPB4txDBE5y6yB7HfQQoozpeaYxJzn0ZbvNVMNHCcZBY665smG6qvLbXCyhf
# qhGcB8SUP3x8CHUmC/bnHi0Bz26Re2Q88sT8oc7YeNZnyovX/ZTUKC8FGVUkFFls
# c1pVd8NeO7JxeO2E5wQ1v2wd9SEAZBYWoYf1JPssvOQDgLPcXA2QBKCcVnqnprte
# hHlsSZrqb+Q2tJBq1tUjSeaH0EvgveFnfmQ/+X7fhYyMsWb/RrgSwEdIycxJPFkH
# oKJ4qcFeXFq2qwPcomaAlSJTXboKJa/6HYT4d9QfepHDa2hUobnKz2EMTQe19KdL
# uvvaWlc=
# SIG # End signature block
