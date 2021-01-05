#!/bin/sh
# This is a simple installer script for
# postfix and dovcot.
#
# It is not intended for public use. This
# mail server is insecure and mean for
# LiaB use only.

# Installing postfix
echo "installing postfix..."
sudo dnf -y install postfix
echo "starting postfix..."
sudo systemctl start postfix
echo "enabling postfix..."
sudo systemctl enable postfix

echo "Configuring /etc/postfix/main.cf for Demo in a Box..."

sudo sed -i 's/#myhostname = host.domain.tld/myhostname = mail.demoinabox.net/g' /etc/postfix/main.cf

sudo sed -i 's/#myorigin = $myhostname/myorigin = $myhostname/g' /etc/postfix/main.cf

sudo sed -i 's/inet_interfaces = localhost/#inet_interfaces = localhost/g' /etc/postfix/main.cf

sudo sed -i 's/#inet_interfaces = $myhostname/inet_interfaces = $myhostname/g' /etc/postfix/main.cf

sudo sed -i -e '$a192.168.35.134 mail.demoinabox.net' /etc/hosts

echo "installing dovecot (IMAP(s)/POP3(s)"
sudo dnf -y install dovecot

echo "configuring dovecot..."
sudo sed -i -e '30alisten = 192.168.35.134, ::' /etc/dovecot/dovecot.conf

sudo sed -i 's/ssl_cert = </etc/pki/dovecot/certs/dovecot.pem/ssl_cert = </etc/pki/tls/certs/diab_wildcard.crt/g' /etc/dovecot/conf.d/10-ssl.conf
sudo sed -i 's/ssl_key = </etc/pki/dovecot/private/dovecot.pem/ssl_cert = </etc/pki/tls/private/diab_wildcard.key/g' /etc/dovecot/conf.d/10-ssl.conf

echo "starting and enabling dovecot"
sudo systemctl start dovecot
sudo systemctl enable dovecot