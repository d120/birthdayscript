import re
import smtplib
from datetime import datetime, date
from sys import argv, exit
from email.mime.text import MIMEText
from configparser import ConfigParser
from email.utils import formatdate

from ldap3 import Server, Connection, ALL_ATTRIBUTES, SEARCH_SCOPE_WHOLE_SUBTREE

LDAP_URL = "ldap://10.162.32.201"
LDAP_USER_SCOPE = 'ou=People,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de'

def init_ldap(config):
    # Connect to LDAP
    curUser = config['mailserver']['user'];
    passwd = config['mailserver']['password'];
    s = Server(LDAP_URL, use_ssl=True, get_info=ALL_ATTRIBUTES)
    c = Connection(s, user="cn=" + curUser + ",ou=Services,dc=fachschaft,dc=informatik,dc=tu-darmstadt,dc=de", password=passwd)
    if not c.bind():
        print('Error in bind: ', c.result['description'])
        exit()
    return c

def mail(addr, person, config):
    text = ""
    with open('birthdaytext', 'r') as f:
        text = f.read()
    s = smtplib.SMTP(config['mailserver']['address'], 587)
    s.starttls()
    s.login(config['mailserver']['user'], config['mailserver']['password'])
    text = text.replace('BIRTHDAYKID', person)
    for address in addr:
        tmp = text.replace('RECIPIENT', address[0])
        msg = MIMEText(tmp)
        msg['Subject'] = config['mail']['subject']
        msg['From'] = config['mail']['from']
        msg['Date'] = formatdate()
        msg['To'] = address[1]
        s.send_message(msg)
    s.quit()

def main():
    config = ConfigParser()
    config.read('config')
    c = init_ldap(config);
    today = date.today()
    c.search(search_base=LDAP_USER_SCOPE, search_filter='(objectClass=d120Person)', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['givenName', 'sn', 'mail', 'birthday', 'birthmonth'])
    addresses = []
    birthdays = []
    for l in c.response:
        attr = l['attributes']
        if not 'birthday' in attr or not 'birthmonth' in attr:
            continue
        addresses.append([attr['givenName'][0],attr['mail'][0]])
        birthday = date(today.year, int(attr['birthmonth'][0]), int(attr['birthday'][0]))
        delta = today - birthday
        if delta.days == -1:
            birthdays.append(attr['givenName'][0] + ' ' + attr['sn'][0])

    if len(birthdays) > 0:
        for pers in birthdays:
            mail(addresses, pers, config)

if __name__ == "__main__":
    main()
