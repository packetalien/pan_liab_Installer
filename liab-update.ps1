# ========================================================================
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
# ========================================================================

# Modules for Script

# LANDesk Elevated Privileges Code
# Self-elevate the script if required
if (-Not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {  if ([int](Get-CimInstance -Class Win32_OperatingSystem | Select-Object -ExpandProperty BuildNumber) -ge 6000) {
  $CommandLine = "-File `"" + $MyInvocation.MyCommand.Path + "`" " + $MyInvocation.UnboundArguments
  Start-Process -FilePath PowerShell.exe -Verb Runas -ArgumentList $CommandLine
  Exit
 }
}
"The script will now setup your envronment. This could take a while."

# OVA Array Variables

#Array's and Variables DO NOT TOUCH

$ovalist = @("oss-tmsclient-linux.ova","pan-soc.ova")
$vmxlist = @("oss-tmsclient-linux.vmx","pan-soc.vmx")
$ovadirlist = @("oss-tmsclient-linux\","pan-soc\")

#$userbase = "$env:USERPROFILE\Documents\Virtual Machines\IT-Managed-VMs\"
#$ovatoolcmd = "c:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe"
#$vmruncmd = "c:\Program Files (x86)\VMware\VMware VIX\vmrun.exe -T ws start"


#Setting up variables IT VM directory test
#This is a hard coded directory on all corproate laptops

$itdir = "$env:USERPROFILE\Documents\Virtual Machines\IT-Managed-VMs\"

$url = "https://drive.google.com/drive/folders/1Yh6Ca4wThWRmwEWtVuShc2uqicV0ziW4"

#Running test for IT Directory
if(!(Test-Path -Path $itdir )){
    New-Item -ItemType Directory -Force -Path $itdir
    "Created Directory: $itdir"
}
Set-Location $itdir

$ovadown = $ovalist[1]
$ovavmx = $vmxlist[1]
& cmd /c "c:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe" "--overwrite" "--acceptAllEulas" "--allowExtraConfig" "$ovadown" "."

# DOCUMENT ME
$ovadir = $ovadirlist[0]
$ovavmx = $vmxlist[0]
Set-Location "$env:USERPROFILE\Documents\Virtual Machines\IT-Managed-VMs\$ovadir"
Get-Location
Get-ChildItem -Path "." -Recurse -Include $ovavmx
& cmd /c "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" "-T" "ws" "deleteVM" "$ovavmx"
Start-Sleep 10
$ovadir = $ovadirlist[1]
$ovavmx = $vmxlist[1]
Set-Location "$env:USERPROFILE\Documents\Virtual Machines\IT-Managed-VMs\$ovadir"
Get-Location
Get-ChildItem -Path "." -Recurse -Include $ovavmx
& cmd /c "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" "-T" "ws" "start" "$ovavmx"
Start-Sleep 10
& cmd /c "C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe" "-T" "ws" "suspend" "$ovavmx"

# This section the script attempts to license the VM-Series


# THis is an artifact file left behind for SCCM

New-Item -Path C:\PANW\AppLogs -Name "liab-updates.txt" -ItemType "file" -Value "Update ran."


# SIG # Begin signature block
# MIIPLwYJKoZIhvcNAQcCoIIPIDCCDxwCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUCuQVi+7AKbbEhCWuFRMAYkNU
# 6u+gggx9MIIFtzCCA5+gAwIBAgITWgAAAAKvEDrpExwlZwAAAAAAAjANBgkqhkiG
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
# QTUvPF0X8/EThuVMHwmSNiE8TSma6GIKOXg7c7g/C92eMIIGvjCCBaagAwIBAgIT
# ZAALMobdei0jMuFwGAAAAAsyhjANBgkqhkiG9w0BAQsFADBkMRUwEwYKCZImiZPy
# LGQBGRYFbG9jYWwxIDAeBgoJkiaJk/IsZAEZFhBwYWxvYWx0b25ldHdvcmtzMSkw
# JwYDVQQDEyBQYWxvIEFsdG8gTmV0d29ya3MgSW5jIERvbWFpbiBDQTAeFw0xODEw
# MTQxODMzMzNaFw0xOTEwMTQxODMzMzNaMIGBMRUwEwYKCZImiZPyLGQBGRYFbG9j
# YWwxIDAeBgoJkiaJk/IsZAEZFhBwYWxvYWx0b25ldHdvcmtzMQwwCgYDVQQLEwNQ
# QU4xDjAMBgNVBAsTBVVzZXJzMQ8wDQYDVQQLEwZSZW1vdGUxFzAVBgNVBAMTDlJp
# Y2hhcmQgUG9ydGVyMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvWRa
# PqLKHY7zPMfuoiM1rzx0u+cxxuU6W4Z3lqmz84dSGWWR4DeGbyslrTI+1OWvD0up
# dbV4nFU687pzp728FTldecZrofzJLof8Jo28Xt3/NKyTVuq02mZrfKN4QBqAT3ro
# 79kY2Sl+shL4Uh7xWxxLhgFE94bWvr7E20H6/+y5QQ2A80sctrRP9H1lwZ+dKI6O
# g13LwJ2Cdg8RRPTPVH+dslsPkdQluUiQ6KzP0+R8yNMg93KdD4ZrRUj7CRrSXAry
# hKxg3ZKnVrKCDFFAVNTq+3K/1ZjUFNwCTFR7ZCyDUghcf/HplXr+DfqAtAynEiv0
# y6itGQ1buMQK5Mm5SQIDAQABo4IDSTCCA0UwPQYJKwYBBAGCNxUHBDAwLgYmKwYB
# BAGCNxUIgqjBLIH6vQSC6Z87hOHrHoHB+3png9+sIYHFlFACAWQCAQgwEwYDVR0l
# BAwwCgYIKwYBBQUHAwMwCwYDVR0PBAQDAgeAMBsGCSsGAQQBgjcVCgQOMAwwCgYI
# KwYBBQUHAwMwHQYDVR0OBBYEFM6Bg3Ebk/xTPlHJ+ryzxFv7oZqYMB8GA1UdIwQY
# MBaAFHSaol1cIy9h4nM3oBY13EJ4ixXvMIIBDgYDVR0fBIIBBTCCAQEwgf6ggfug
# gfiGUmh0dHA6Ly9jcmwucGFsb2FsdG9uZXR3b3Jrcy5jb20vY3JsL1BhbG8lMjBB
# bHRvJTIwTmV0d29ya3MlMjBJbmMlMjBEb21haW4lMjBDQS5jcmyGgaFsZGFwOi8v
# L0NOPVBhbG8lMjBBbHRvJTIwTmV0d29ya3MlMjBJbmMlMjBEb21haW4lMjBDQSxD
# Tj1zamNjZWNhdncwMXAsQ049Q0RQLENOPVB1YmxpYyUyMEtleSUyMFNlcnZpY2Vz
# LENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9cGFsb2FsdG9uZXR3b3Jr
# cyxEQz1sb2NhbDCCATgGCCsGAQUFBwEBBIIBKjCCASYwgYIGCCsGAQUFBzAChnZo
# dHRwOi8vY3JsLnBhbG9hbHRvbmV0d29ya3MuY29tL2NybC9zamNjZWNhdncwMXAu
# cGFsb2FsdG9uZXR3b3Jrcy5sb2NhbF9QYWxvJTIwQWx0byUyME5ldHdvcmtzJTIw
# SW5jJTIwRG9tYWluJTIwQ0EuY3J0MIGeBggrBgEFBQcwAoaBkWxkYXA6Ly8vQ049
# UGFsbyUyMEFsdG8lMjBOZXR3b3JrcyUyMEluYyUyMERvbWFpbiUyMENBLENOPUFJ
# QSxDTj1QdWJsaWMlMjBLZXklMjBTZXJ2aWNlcyxDTj1TZXJ2aWNlcyxDTj1Db25m
# aWd1cmF0aW9uLERDPXBhbG9hbHRvbmV0d29ya3MsREM9bG9jYWwwNwYDVR0RBDAw
# LqAsBgorBgEEAYI3FAIDoB4MHHJwb3J0ZXJAcGFsb2FsdG9uZXR3b3Jrcy5jb20w
# DQYJKoZIhvcNAQELBQADggEBAIuVGgJVPjTymZsCtkujJvMgHoYUPwdq77ohOlHx
# j+zFrMEVJLjJ/FfGlXVDxGU+mQJG598Gqoi9Nt7IH3I9Uu/7hJQj6kjiUXOXViks
# k1CeUGHlpZbSDqKGL1kVIqQv9bGEfFzEpEcZ1e+PaIfBOC5SWuAc64c3mCB2yQSL
# ZjBkDSCh0mJ3ySPudjP8XtnBWgzdrb6IaOJXae+10/aMICaA0dGAmu8jWg2/Hgzb
# BtQgjn9c0/rI3bxpGzqCfCwwMCE2SyOOsEgEQ7jra4Xgy7kywhJ8F4KUtRAImmee
# qK5SoQkXuIQ6lUX+MuJscehNTimFMMQj1VdtdwmgA1whNY0xggIcMIICGAIBATB7
# MGQxFTATBgoJkiaJk/IsZAEZFgVsb2NhbDEgMB4GCgmSJomT8ixkARkWEHBhbG9h
# bHRvbmV0d29ya3MxKTAnBgNVBAMTIFBhbG8gQWx0byBOZXR3b3JrcyBJbmMgRG9t
# YWluIENBAhNkAAsyht16LSMy4XAYAAAACzKGMAkGBSsOAwIaBQCgeDAYBgorBgEE
# AYI3AgEMMQowCKACgAChAoAAMBkGCSqGSIb3DQEJAzEMBgorBgEEAYI3AgEEMBwG
# CisGAQQBgjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEWBBS0iKpr
# FSchyz8x7aeAdQqyd5RHNjANBgkqhkiG9w0BAQEFAASCAQAipvY6Ncxb4ucEqqjl
# P3ZWRtQB1cdCO+OUOv6LrrEMQpzwPzo4g9WAUQqo6w15F6CRa9g1cRsoXaxcGl9n
# fe3HmLHC1mZlHafN5QkVB4VGRN+RG2Y9evmlOowWTfPfHMZqiHrX9m5IiWUxDNeI
# OlTyzf0TlBQ6nwJLr1v7nsm+CUXQfnaGT8IRU4p2yLw9yzi62RL80x6XB+4Uuqy0
# 0zpUkE+zrR8pAN5AO5YOAeGqbMbVELX6WS8rwVLmyA1azt6F7U3fxLlzEiScZN6b
# vs6iv4YJH0MLq5MiRzUAFbX9VMhHxMl2CLuAL8P2ymtHIAXwNx7xmk1jrwscL1yf
# 31ys
# SIG # End signature block
