# This script adapted from Jason Fosen's SANS 505 Course Startup Script
# With Permission!
#
#
# Thank you Jason for the fantastic Class!



[CmdletBinding()] 
Param ([Switch] $SkipNetworkInterfaceCheck, [Switch] $SkipActiveDirectoryCheck)


###############################################################################
#

" --------------------------------------------------------"
" --------------Getting Script Parameters-----------------"
" --------------------------------------------------------"
" --------------------------------------------------------"
" !!!!!!!!!!!!!!!!!!!!!!!WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!"
" NO ERROR CHECKING in Read-Prompt YET. You've been WARNED"
" !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
" --------------------------------------------------------"
 
#
# This sets the stage for the script.
#
###############################################################################
" --------------------------------------------------------"
$server_name = Read-Host -Prompt "Enter Server Name: "
" --------------------------------------------------------"
Rename-Computer -NewName $server_name -Force
$server_ipv4 = Read-Host -Prompt "Enter Server IPv4 IP (no error correction, get it right): "
" --------------------------------------------------------"
$server_gateway = Read-Host -Prompt "Enter Server IPv4 Gateway (no error correction, get it right): "
" --------------------------------------------------------"
$server_dns = Read-Host -Prompt "Enter Server IPv4 DNS (no error correction, get it right): "
" --------------------------------------------------------"
$server_netbios = Read-Host -Prompt "Enter Server NetBIOS name: "
" --------------------------------------------------------"
" Server Domain must be just <domain>.<suffix> right now -"
" The user/group creation uses $var.Split() and only     -"
" takes one period at the moment.                         "
" --------------------------------------------------------" 
$server_domain = Read-Host -Prompt "Enter Domain FQDN (e.g., example.com): "
" --------------------------------------------------------"

$PWD = Read-Host "Please enter your password!"
" --------------------------------------------------------"
$server_directory = Read-Host -Prompt "Enter server resource directory (recommend c:\Resources): "
 
" --------------------------------------------------------"
" --------------------------------------------------------"
" --- Creating Resource Directory at C:\Resources      ---"
New-Item -Path $server_directory -ItemType Directory
" --------------------------------------------------------"
" --------------Getting Script Resources------------------"
" --------------------------------------------------------"
" --------------------------------------------------------"
Invoke-WebRequest -Uri "https://lumberjack.labinabox.net/liab_demos/Resources.7z" -OutFile "$server_directory\Resources.zip"
Invoke-WebRequest -Uri "https://lumberjack.labinabox.net/liab_demos/diab_domain.csv" -OutFile "$server_directory\diab_domain.csv"

###############################################################################
#
" Checking for Administrator identity..."
#
# Remember, culture is temporarily set to en-US.
#
###############################################################################

if ($env:USERNAME -notlike "*Administrator*") { 
    "`n`nErrors will occur during the Active Directory installation"
    "if you are not logged on with the built-in Administrator account."
    "Please log on with the built-in Administrator account and run"
    "this script again.  Using a new account which has been added"
    "to the local Administrators group will NOT prevent the errors.`n"

    $try = Read-Host -Prompt "Hit any key to quit (or enter 'try' to continue anyway)"
    if ($try -ne "try") { exit }  
}





###############################################################################
#
" Disabling Windows Defender..."
#
###############################################################################

$wd = $null 
$wd = Get-Command -Name 'Set-MpPreference' -ErrorAction SilentlyContinue

if ($wd) { 
    Set-MpPreference -DisableRealtimeMonitoring $True -Force
    Set-MpPreference -DisableBehaviorMonitoring $True -Force
    Set-MpPreference -ExclusionPath @('C:\resources', 'C:\Temp', 'D:\') -Force 
    Set-MpPreference -ScanScheduleDay Never -Force
    Set-MpPreference -RemediationScheduleDay Never -Force
} 


###############################################################################
#
" Turning off Internet Explorer Enhanced Security..."
#
# Do this before the first reboot or else the change doesn't "stick."
# 
###############################################################################

$curpref = $ErrorActionPreference
if (-not $Verbose) { $ErrorActionPreference = "SilentlyContinue" } 
$iekey = get-item 'HKLM:\SOFTWARE\Microsoft\Active Setup\Installed Components' 
$subkey = $iekey.opensubkey("{A509B1A7-37EF-4b3f-8CFC-4F3A74704073}", $true)  #For Admins
$subkey.SetValue("IsInstalled", 0)
$subkey = $iekey.opensubkey("{A509B1A8-37EF-4b3f-8CFC-4F3A74704073}", $true)  #For Non-Admins
$subkey.SetValue("IsInstalled", 0)
$ErrorActionPreference = $curpref


###############################################################################
#
" Checking for at least one connected network adapter..."
#
###############################################################################

if ( @(Get-NetAdapter | Where { $_.Status -eq "Up" }).Count -eq 0 -And -not $SkipNetworkInterfaceCheck) {
    if (-not $Verbose) { cls }  

    "`n`nYour VM appears to not have any connected network adapters."
    "Enable the network adapter inside your VM and set it to use "
    "'Host-Only' or 'Internal' (or similar).  Your VM does not need"
    "network access outside of your host computer.  Run this script"
    "again afterwards please.`n"

    exit
}




###############################################################################
#
" Checking status as a domain controller..."
#
# Confirm that NTDS service exists and is running.
#
###############################################################################

$IsDomainController = $false

if ( @(get-service | select -expand Name) -contains "NTDS" -and 
    $(get-service -name "NTDS").Status -eq "Running" ) { $IsDomainController = $true }

if ($Verbose) {
    " Skip Active Directory Check = " + $SkipActiveDirectoryCheck
    " Is Domain Controller = " + $IsDomainController
}




###############################################################################
#
" Checking for Administrators group membership..."
#
# Only check if the VM is not a domain controller.
#
###############################################################################

if (-not $IsDomainController) {
    $CurrentWindowsID = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $CurrentPrincipal = new-object System.Security.Principal.WindowsPrincipal($CurrentWindowsID)
    
    if (-not $CurrentPrincipal.IsInRole(([System.Security.Principal.SecurityIdentifier]("S-1-5-32-544")).Translate([System.Security.Principal.NTAccount]).Value)) {
        "`nYou must be a member of the local Administrators group.`n"
        "Add your user account to the Administrators group, log off,"
        "log back in, and run this script again. `n" 
        exit
    }
}




###############################################################################
#
" Checking the network interface..."
#
#  Get any IPv4 interfaces which are using DHCP, try to set a static IP instead.
#  Use -SkipNetworkInterfaceCheck to bypass this section.
#
###############################################################################

$ipinterface = @( Get-NetIPInterface | Where { $_.AddressFamily -eq "IPv4" -and $_.Dhcp -eq "Enabled" } )

if ($SkipNetworkInterfaceCheck) { $ipinterface = @() } 

" Count of interfaces using DHCP = " + $ipinterface.Count | Write-Verbose

if ($ipinterface.Count -eq 0) {
    #Do nothing, assume good to go or that we will $SkipNetworkInterfaceCheck.
}
elseif ($ipinterface.Count -ge 2) {
    #Don't try to manage multiple NICs, ask attendee to do it manually.

    "`nSomething went wrong in the IP configuration step.`n" 
    exit
}
elseif ($ipinterface.Count -eq 1) {
    #Get the NIC currently using DHCP.
    $nic = Get-NetAdapter -InterfaceIndex $($ipinterface[0].InterfaceIndex) 
    
    #Disable DHCP on that NIC.
    $nic | Set-NetIPInterface -Dhcp Disabled

    #Assign static IPv4 address and set DNS to loopback.
    " Assigning an IP address of {0} ..." -f $server_ipv4
    $nic | New-NetIPAddress -AddressFamily IPv4 -IPAddress $server_ipv4 -PrefixLength 24 -DefaultGateway $server_gateway -Type Unicast | out-null
    " Setting primary DNS server to {0} ..." -f $server_dns
    $nic | Set-DnsClientServerAddress -ServerAddresses $server_dns
    

    #Test to confirm.
    Start-Sleep -Seconds 5
    if (-not $( Test-Connection -ComputerName $server_name -Count 1 -Quiet -ErrorAction SilentlyContinue) ) { 
        "`nSomething went wrong with the test connection step.`n"
        exit
    }
}

Get-NetIPAddress | Format-Table IpAddress, InterfaceAlias -AutoSize | Write-Verbose


###############################################################################
#
" Installing AD if necessary..."
#
# Use -SkipActiveDirectoryCheck to bypass this section.
# Must assign static IP and DNS before installing AD. 
#
###############################################################################

if ( $SkipActiveDirectoryCheck -or $IsDomainController ) {
    if ($Verbose) {
        " Skip Active Directory Check = " + $SkipActiveDirectoryCheck
        " Is Domain Controller = " + $IsDomainController
    }
}
elseif ( $(Get-WindowsFeature -Name AD-Domain-Services).Installed -eq $false ) {
    if (-not $Verbose) { cls } 

    "`n`n`n`n`n`n`n`n`n`n`n`nInstalling Active Directory..." #ISE progress bar covers this up, need many newlines.

    "`n`nAfter Active Directory has been installed and you have logged back on as" 
    "the domain administrator, please run this script again."  

    "`n`nYour new password will be $PWD (without the quotes)." 

    "`n`nNow, please wait a few minutes for the reboot..."

    "`n`nAnd don't forget to run this script again after you log back on!`n"

    if (-not $Verbose) { $WarningPreference = "SilentlyContinue" } #This is not $VerbosePreference dude. 
    Install-WindowsFeature -Name AD-Domain-Services -IncludeAllSubFeature -IncludeManagementTools | Out-Null
    
    Do { Start-Sleep -Seconds 5 ; " Waiting for AD to install...`n" } 
    while ( $(Get-WindowsFeature -Name ad-domain-services).installstate -ne "Installed") 

    $WarningPreference = "Continue" # The default warning preference.
}




###############################################################################
#
" Configuring the AD forest if necessary..."
#
# Use -SkipActiveDirectoryCheck to bypass this section.
# A reboot will occur after this section configures AD.
#
###############################################################################
if ( $SkipActiveDirectoryCheck -or $IsDomainController ) {
    if ($Verbose) {
        " Skip Active Directory Check = " + $SkipActiveDirectoryCheck
        " Is Domain Controller = " + $IsDomainController
    }
}
elseif ( $(Get-WindowsFeature -Name AD-Domain-Services).Installed -and $(get-service ntds).status -eq "Stopped" ) {
    "`n Configuring the AD forest now...`n"
    if (-not $Verbose) { $WarningPreference = "SilentlyContinue" } #This is not $VerbosePreference dude. 
    Install-ADDSForest -DomainName $server_domain -SafeModeAdministratorPassword $(convertto-securestring -string $PWD -asplaintext -force) -DomainNetbiosName $server_netbios -NoDnsOnNetwork -InstallDns -Force | Out-Null 

    if ($?) { 
        # The enabled/disabled state of NICs survives reboots, but disabling NICs here does
        # not decrease the reboot time while waiting for "Applying computer settings"...
        #   Get-NetAdapter | Disable-NetAdapter -Confirm:$False  

        "`n`n Rebooting...`n`n"
    }
    else {
        #Likely problem is having a live external network adapter.  What else to do here?
    } 

    $WarningPreference = "Continue"
    exit
}




###############################################################################
#
" Creating OUs and other AD objects..."
#
# The rest of the script is only executed if the VM is a controller.
#
###############################################################################

if (-not $IsDomainController -and -not $SkipActiveDirectoryCheck) { 
    if (-not $Verbose) { cls } 

    "`n`nYour VM is not a domain controller.  Please install and configure"
    "Active Directory using this script or by following the instructions"
    "in Appendix A at the end of the SEC505.1 manual.  Please ask the"
    "instructor if you would like help or if you have questions."
    "Please run this script again after installing Active Directory.`n`n`n"

    exit
}





$ErrorActionPreference = $curpref

# Firewall Rules for msft-dc

New-NetFirewallRule -DisplayName "User-ID Allow Port 5007" -Direction Inbound -LocalPort 5007 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Allow Web 443 CertSrv" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow
$mypwd = ConvertTo-SecureString -String "Paloalto1!" -Force -AsPlainText

# Exit if ADCS is already installed:
if ( $(Get-WindowsFeature -Name ADCS-Cert-Authority).installed ) { "PKI already installed!" ; exit } 

# Install Certificate Services, the IIS web enrollment pages, and OCSP responder IIS app:
Install-WindowsFeature -Name ADCS-Cert-Authority, ADCS-Web-Enrollment, ADCS-Online-Cert -IncludeManagementTools

# Configure as an Enterprise Root CA with a 4096-bit RSA public key:
Install-AdcsCertificationAuthority -CAType EnterpriseRootCA -KeyLength 4096 -ValidityPeriod Years -ValidityPeriodUnits 10 -CACommonName pedantictheory-CA -Force

# Install the IIS web enrollment app (http://yourca/certsrv/):
Install-AdcsWebEnrollment -Force

# Install the OCSP responder app in IIS:
Install-AdcsOnlineResponder -Force

# Enable the audit policy for Certification Services:
auditpol.exe /set /subcategory:"Certification Services" /success:enable /failure:enable

"Unnecessarily importing the Active Directory module...`n" | Write-Verbose
Iimport-Module -Name ActiveDirectory -ErrorAction SilentlyContinue | Out-Null 
Start-Sleep -Seconds 2  #Shouldn't be necessary, but seems to help avoid errors.


$curpref = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"

"Switching to the AD:\ drive...`n" | Write-Verbose

cd AD:\
$thisdomain = Get-ADDomain -Current LocalComputer

New-ADOrganizationalUnit -ProtectedFromAccidentalDeletion $false -Name "HVT" -Description "High-Value Targets"
New-ADOrganizationalUnit -ProtectedFromAccidentalDeletion $false -Name "RegularUsers" -Description "Normal Users"

$pw = ConvertTo-SecureString "Paloalto1!" -AsPlainText -Force



###############################################################################
#
" Creating OUs and other AD objects..."
#
# The rest of the script is only executed if the VM is a controller.
# Reference: https://adamtheautomator.com/new-aduser/
#
###############################################################################

$import_users = Import-Csv -Path "C:\Resources\diab_domain.csv"

$import_users | ForEach-Object {
    New-ADUser `
        -Name $($_.FirstName + " " + $_.LastName) `
        -GivenName $_.FirstName `
        -Surname $_.LastName `
        -Department $_.Department `
        -DisplayName $($_.FirstName + " " + $_.LastName) `
        -UserPrincipalName $_.SamAccountName + "@" + $server_domain `
        -SamAccountName $_.SamAccountName `
        -PasswordNeverExpires $True `
        -AccountPassword $(ConvertTo-SecureString $_.Password -AsPlainText -Force) `
        -Enabled $True `
}


## GROUPS 
New-ADGroup -Name "Engineering" -SamAccountName Engineering -DisplayName "Engineering" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -SamAccountName Sales -Name Sales -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Marketing" -SamAccountName Marketing -DisplayName "Marketing" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup  -SamAccountName Research -Name Research -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Communications" -SamAccountName Communications -DisplayName "Communications" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Stark_Industries" -SamAccountName Stark -DisplayName "Stark_Industries" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Information Technology" -SamAccountName IT -DisplayName "Information Technology" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Security" -SamAccountName Security -DisplayName "Security" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Leadership" -SamAccountName Leadership -DisplayName "Leadership" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Medical" -SamAccountName Medical -DisplayName "Medical" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Executive" -SamAccountName Executive -DisplayName "Executive" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Contractors" -SamAccountName Contractors -DisplayName "Contractors" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Transportation" -SamAccountName Transportation -DisplayName "Transportation" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Hackers" -SamAccountName Hackers -DisplayName "Hackers" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Entertainment" -SamAccountName Entertainment -DisplayName "Entertainment" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Scoundrels" -SamAccountName Scoundrels -DisplayName "Scoundrels" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Degobah" -SamAccountName Degobah -DisplayName "Degobah" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "nerfherders" -SamAccountName nerfherders -DisplayName "Scruffy Nerfherders" -GroupScope Universal -GroupCateMrtory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Gracebrothers" -SamAccountName Gracebrothers -DisplayName "Grace Brothers" -GroupScope Universal -GroupCatetory Security -Path "CN=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "Ballers" -SamAccountName Ballers -DisplayName "FutBall" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"
New-ADGroup -Name "ServiceAccounts"  -SamAccountName ServiceAccounts -DisplayName "Service Accounts" -GroupScope Universal -GroupCatetory Security -Path "OU=Users,DC=$server_domain.Split(".")[0],DC=$server_domain.Split(".")[1]"

# Major TODO: Update this to read from CSV and input variables correctly.

Add-ADGroupMember -Identity "Allowed RODC Password Replication Group" -Members "Sales", "Research", "Marketing", "Communications", "Medical", "Security", "Leadership", "Hackers", "Contractors", "Transportation"
Add-ADGroupMember -Identity "Engineering" -Members "chewie", "scott", "howard", "reggie"
Add-ADGroupMember -Identity "Entertainment" -Members "billspreston", "ted"
Add-ADGroupMember -Identity "Executive" -Members "leia", "vader", "kirk", "picard", "holdo", "jon", "director", "thanos", "loki", "Thor", "Odin"
Add-ADGroupMember -Identity "Hackers" -Members "r2d2", "bb8", "codebreaker"
Add-ADGroupMember -Identity "Information Technology" -Members "finn", "rose", "zola"
Add-ADGroupMember -Identity "Leadership" -Members "riker", "red", "maz", "hux", "rescue", "Thor", "Odin", "Sif", "Agent13"
Add-ADGroupMember -Identity "Marketing" -Members "hulk", "lando", "kitty", "hyde", "midge", "jackie", "kelso", "kylo"
Add-ADGroupMember -Identity "Medical" -Members "mccoy", "troy"
Add-ADGroupMember -Identity "Research" -Members "spock", "leonard", "sheldon", "amy", "bernadette", "rajesh"
Add-ADGroupMember -Identity "Sales" -Members "luke", "eric", "bob", "penny", "Laufey", "Fandral", "Hogun", "frigga", "redskull", "peacock", "granger", "humphries", "grace", "slocombe", "brahms", "lucas"
Add-ADGroupMember -Identity "Scoundrels" -Members "han"
Add-ADGroupMember -Identity "nerfherders" -Members "han"
Add-ADGroupMember -Identity "Communications" -Members "Heimdal"
Add-ADGroupMember -Identity "Stark_Instrusties" -Members "ironman"
Add-ADGroupMember -Identity "Security" -Members "rey", "phasma", "warmachine", "bucky", "dumdum", "maria"
Add-ADGroupMember -Identity "Contractors" -Members "deadpool", "spiderman", "gamora", "drax", "groot", "rocket", "star-lord"
Add-ADGroupMember -Identity "Transportation" -Members "poe", "happy"
Add-ADGroupMember -Identity "Degobah" -Members "yoda"
Add-ADGroupMember -Identity "Gracebrothers" -Members "peacock", "granger", "humphries", "grace", "slocombe", "brahms", "lucas"


"************* FINISHED *************"

# FIN-ACK
