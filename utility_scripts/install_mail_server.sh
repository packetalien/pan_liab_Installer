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

echo "Configuring /etc/postfix/main.cf for Demo in a Box..."

sudo sed -i 's/#myhostname = host.domain.tld/myhostname = mail.demoinabox.net/g' /etc/postfix/main.cf
sudo sed -i 's/#inet_interfaces = $myhostname/inet_interfaces = $myhostname/g' /etc/postfix/main.cf
sudo sed -i 's/#mydomain = domain.tld/mydomain = mail.demoinabox.net/g' /etc/postfix/main.cf

sudo sed -i 's/#myorigin = $myhostname/myorigin = $myhostname/g' /etc/postfix/main.cf
sudo sed -i 's/inet_interfaces = all/#inet_interfaces = all/g' /etc/postfix/main.cf
sudo sed -i 's/inet_interfaces = $myhostname/#inet_interfaces = $myhostname/g' /etc/postfix/main.cf
sudo sed -i 's/inet_interfaces = localhost/#inet_interfaces = localhost/g' /etc/postfix/main.cf
sudo sed -i 's/#inet_interfaces = $myhostname/inet_interfaces = $myhostname, localhost/g' /etc/postfix/main.cf
sudo sed -i '286amynetworks = 192.168.55.0/24,192.168.35.0/24,192.168.45.0/24,192.168.25.0/24' /etc/postfix/main.cf
sudo sed -i 's/#home_mailbox = Maildir/home_mailbox = Maildir/g' /etc/postfix/main.cf
inet_interfaces = $myhostname, localhost

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

echo "configuring dovecot.conf"
echo "Added protocols imap and pop3"
echo "adding listiner at 192.168.35.134"
protocols = imap pop3 lmtp submission
sudo sed -i 's/protocols = imap pop3 lmtp submission/#protocols = imap pop3 lmtp submission/g' /etc/dovecot/dovecot.conf
sudo sed -i 's/#protocols = imap pop3/protocols = imap pop3/g' /etc/dovecot/dovecot.conf
sudo sed -i '24aprotocols = imap pop3' /etc/dovecot/dovecot.conf
sudo sed -i '31alisten = 192.168.35.134, ::' /etc/dovecot/dovecot.conf
echo "Configuring 10-mail.conf"
sudo sed -i '30amail_location = mail_location = maildir:~/Maildir' /etc/dovecot/conf.d/10-mail.conf
sudo sed -i '116amail_privileged_group = mail' /etc/dovecot/conf.d/10-mail.conf
echo "Configuring 10-auth.conf for dovecot"
sudo sed -i 's/auth_mechanisms = plain/auth_mechanisms = plain login/g' /etc/dovecot/conf.d/10-auth.conf
sudo sed -i 's/#disable_plaintext_auth = yes/disable_plaintext_auth = yes/g' /etc/dovecot/conf.d/10-auth.conf

#sudo sed -i 's/#disable_plaintext_auth = yes/disable_plaintext_auth = no/g' /etc/dovecot/conf.d/10-auth.conf
sudo gpasswd -a dovecot mail
echo "Configuring 10-ssl.conf for dovecot"
# Only uncomment if you generate a new dh.pem
# Generate one or dovecot breaks
#sudo sed -i '55assl_dh = </etc/dovecot/dh.pem' /etc/dovecot/conf.d/10-ssl.conf
#sudo sed -i 's/#ssl_min_protocol = TLSv1/ssl_min_protocol = TLSv1/g' /etc/dovecot/conf.d/10-ssl.conf
#sudo sed -i 's/#ssl_prefer_server_ciphers = no/ssl_prefer_server_ciphers = no/g' /etc/dovecot/conf.d/10-ssl.conf
#sudo sed -i '26assl_ca = /etc/ssl/certs/DiaBCA.crt' /etc/dovecot/conf.d/10-ssl.conf
echo "Configuring 10-master.conf for dovecot"
sudo sed -i 's/unix_listener auth-userdb {/#unix_listener auth-userdb {/g' /etc/dovecot/conf.d/10-master.conf
sudo sed -i '100a unix_listener /var/spool/postfix/private/auth {' /etc/dovecot/conf.d/10-master.conf
sudo sed -i '101amode = 0600' /etc/dovecot/conf.d/10-master.conf
sudo sed -i '102auser = postfix' /etc/dovecot/conf.d/10-master.conf
sudo sed -i '103agroup = postfix' /etc/dovecot/conf.d/10-master.conf


sudo chmod 0600 /var/mail/*

# Appended with static lines for consistency with sed.
# Yes, there may be a better way :) 
echo "configuring postfix/master.cf"
sudo sed -i '17asubmission     inet     n    -    y    -    -    smtpd' /etc/postfix/master.cf
sudo sed -i '18a\ \-o syslog_name=postfix/submission' /etc/postfix/master.cf
sudo sed -i '19a\ \ -o smtpd_tls_security_level=encrypt' /etc/postfix/master.cf
sudo sed -i '20a\ \ -o smtpd_tls_wrappermode=no' /etc/postfix/master.cf
sudo sed -i '20a\ \ -o smtpd_sasl_auth_enable=yes' /etc/postfix/master.cf
sudo sed -i '22a\ \ -o smtpd_relay_restrictions=permit_sasl_authenticated,reject' /etc/postfix/master.cf
sudo sed -i '23a\ \ -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination' /etc/postfix/master.cf
sudo sed -i '24a\ \ -o smtpd_sasl_type=dovecot' /etc/postfix/master.cf
sudo sed -i '25a\ \ -o smtpd_sasl_path=private/auth' /etc/postfix/master.cf

sudo sed -i '38asmtps     inet  n       -       y       -       -       smtpd' /etc/postfix/master.cf
sudo sed -i '39a\ \  -o syslog_name=postfix/smtps' /etc/postfix/master.cf
sudo sed -i '40a\ \  -o smtpd_tls_wrappermode=yes' /etc/postfix/master.cf
sudo sed -i '41a\ \  -o smtpd_sasl_auth_enable=yes' /etc/postfix/master.cf
sudo sed -i '42a\ \  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject' /etc/postfix/master.cf
sudo sed -i '43a\ \  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject' /etc/postfix/master.cf
sudo sed -i '44a\ \  -o smtpd_sasl_type=dovecot' /etc/postfix/master.cf
sudo sed -i '45a\ \  -o smtpd_sasl_path=private/auth' /etc/postfix/master.cf

sudo postconf "smtpd_tls_key_file = /etc/pki/tls/private/diab_wildcard.key"
sudo postconf "smtpd_tls_cert_file = /etc/pki/tls/certs/diab_wildcard.crt"
sudo postconf "smtpd_tls_loglevel = 1"
sudo postconf "smtp_tls_loglevel = 1"
sudo postconf "smtpd_sasl_type = dovecot"
sudo systemctl restart postfix

echo "*****************************************"
echo "Tap Tap, this thing on? Checking Ports..."
sudo ss -lnpt | grep master | grep 192.168.35.134
echo "*****************************************"



echo "*****************************************"
echo "Adding GoPhish and victim users..."
sudo adduser clickme
sudo echo "Paloalto1!" | passwd clickme --stdin
echo "Created clickme, password: Paloalto1!"
sudo adduser evilbit
sudo echo "Paloalto1!" | passwd evilbit --stdin
echo "Created evilbit, password: Paloalto1!"
echo "*****************************************"

#echo "*****************************************"
#echo "*****************************************"
#echo "*****************************************"
#echo "*****************************************"
#echo "Configuring and generating certs."
#echo "This could take as long as 10 min"
#echo "so be patient."
#echo "*****************************************"
#echo "*****************************************"
#echo "*****************************************"
#echo "*****************************************"
#sudo openssl dhparam -out /etc/dovecot/dh.pem 4096
#echo "*****************************************"

echo "starting and enabling dovecot"
sudo systemctl start dovecot
sudo systemctl enable dovecot

echo "*****************************************"
echo "Tap Tap, this thing on? Checking Dovecot..."
sudo sudo ss -lnpt | grep dovecot
echo "*****************************************"
sudo systemctl restart postfix
sudo systemctl enable postfix