#!/bin/sh
# This is a simple installer script for
# postfix and dovcot.
#
# It is not intended for public use. This
# mail server is insecure and mean for
# LiaB use only.

# Installing postfix
echo "installing postfix..."
echo "installing dovecot (IMAP(s)/POP3(s)"
sudo dnf -y install postfix dovecot
echo "starting postfix..."
sudo systemctl start postfix
echo "enabling postfix..."
sudo systemctl enable postfix

echo "Adding host entry in /etc/hosts for mail.demoinabox.net"
sudo sed -i '$a192.168.35.134 mail.demoinabox.net' /etc/hosts
echo "Getting the server config files."
curl -k https://raw.githubusercontent.com/packetalien/pan_liab_Installer/beta/utility_scripts/mailserver.tar.gz -o mailserver.tar.gz
echo "Unpacking the server config files."
tar -zxvf mailserver.tar.gz
sudo rm -rf /etc/dovecot/
sudo rm -rf /etc/postfix/
sudo tar -zxvf /home/panse/mailserver/dovecot.tar.gz -C /etc/
sudo tar -zxvf /home/panse/mailserver/postfix.tar.gz -C /etc/

echo "Copying over postfix built in keys as a backup."
sudo cp /etc/pki/tls/private/diab_wildcard.key /etc/pki/tls/private/postfix.key
sudo cp /etc/pki/tls/certs/diab_wildcard.crt /etc/pki/tls/certs/postfix.pem
sudo cp /home/panse/certs/'Demo in a Box CA.crt' /etc/ssl/certs/DiaBCA.crt
sudo cp /home/panse/certs/'Demo in a Box CA.crt' /etc/pki/ca-trust/source/anchors/DiaBCA.crt
sudo update-ca-trust extract
echo "setting up dovecot keys and certs"
sudo rm -rf /etc/pki/dovecot/certs/dovecot.pem
sudo rm -rf /etc/pki/dovecot/private/dovecot.pem
echo "Copying keys to default, just in case. Properly configure with postconf"
echo "in a few seconds."
sudo cp /etc/pki/tls/private/diab_wildcard.key /etc/pki/dovecot/private/dovecot.pem
sudo cp /etc/pki/tls/certs/diab_wildcard.crt /etc/pki/dovecot/certs/dovecot.pem
echo "Adding dovecot to mail group"
sudo gpasswd -a dovecot mail
sudo chmod 0600 /var/mail/*

echo "*****************************************"
echo "Adding GoPhish and victim users..."
sudo adduser clickme
sudo echo "Paloalto1!" | passwd clickme --stdin
echo "Created clickme, password: Paloalto1!"
sudo adduser evilbit
sudo echo "Paloalto1!" | passwd evilbit --stdin
echo "Created evilbit, password: Paloalto1!"
echo "*****************************************"

echo "starting and enabling dovecot"
sudo systemctl start dovecot
sudo systemctl enable dovecot

echo "*****************************************"
echo "Tap* Tap* This thing on? Checking Dovecot..."
sudo sudo ss -lnpt | grep dovecot
echo "You should see a list of ports"
echo "If not contact #labinabox on slack"
echo "*****************************************"
echo "*****************************************"
echo "Tap* Tap* This thing on? Checking Ports on .134..."
sudo ss -lnpt | grep master | grep 192.168.35.134
echo "You should see a list of ports"
echo "If not contact #labinabox on slack"
echo "*****************************************"
sudo systemctl restart postfix
sudo systemctl enable postfix
echo "For questions please contact #labinabox"