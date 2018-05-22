#   Copyright 2016 Fachschaft Informatik, TU-Darmstadt
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import re
import smtplib
from datetime import datetime, date, timedelta
from sys import argv, exit
from email.message import EmailMessage
from configparser import ConfigParser
from email.utils import formatdate
from email.headerregistry import Address
import getopt
import json

from ldap3 import Server, Connection, ALL_ATTRIBUTES, SEARCH_SCOPE_WHOLE_SUBTREE

config = ConfigParser()
config.read('config')

LDAP_URL = config['ldap']['url']
LDAP_USER_SCOPE = config['ldap']['user_scope']

def init_ldap(config):
    # Connect to LDAP
    curUser = config['ldap']['bind_dn'];
    passwd = config['ldap']['password'];
    s = Server(LDAP_URL, use_ssl=True, get_info=ALL_ATTRIBUTES)
    c = Connection(s, user=curUser, password=passwd)
    if not c.bind():
        print('Error in bind: ', c.result['description'])
        exit()
    return c

def mail(addr, person, config, dry_run):
    text = ""
    with open(config['mail']['template_file'], 'r') as f:
        text = f.read()
    s = smtplib.SMTP(config['mailserver']['address'], 587)
    s.starttls()
    s.login(config['mailserver']['user'], config['mailserver']['password'])
    text = text.replace('BIRTHDAYKID', person)
    tomorrow = date.today() + timedelta(days=1)
    bdate = '%02d. %02d.' % (tomorrow.day, tomorrow.month)
    text = text.replace('BIRTHDAY', bdate)
    for address in addr:
        tmp = text.replace('RECIPIENT', address[0])
        msg = EmailMessage()
        msg['Subject'] = config['mail']['subject']
        msg['From'] = config['mail']['from']
        msg['Date'] = formatdate(localtime=True)
        msg['To'] = Address(address[0] + " " + address[1] , addr_spec=address[2])
        msg.set_content(tmp)
        if dry_run:
            print(msg)
        else:
            s.send_message(msg)
    s.quit()

def get_all_birthdays():
    c = init_ldap(config);
    today = date.today()
    c.search(search_base=LDAP_USER_SCOPE, search_filter='(objectClass=d120Person)', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['givenName', 'sn', 'mail', 'birthday', 'birthmonth', 'birthyear'])
    birthdays = []
    for l in c.response:
        attr = l['attributes']
        if not 'birthday' in attr or not 'birthmonth' in attr:
            continue
        dob = None
        if 'birthyear' in attr:
            dob = date(int(attr['birthyear'][0]), int(attr['birthmonth'][0]), int(attr['birthday'][0]))
        birthday = date(today.year, int(attr['birthmonth'][0]), int(attr['birthday'][0]))
        delta = birthday - today
        if delta.days < 0:
            birthday = date(today.year+1, int(attr['birthmonth'][0]), int(attr['birthday'][0]))
            delta = birthday - today
        if not 'mail' in attr: attr['mail'] = ['']
        birthdays.append({ 'name': attr['givenName'][0], 'sn': attr['sn'][0], 'mail': attr['mail'][0],
            'birthday': birthday, 'delta': delta.days, 'dob': dob })
    birthdays.sort(key=lambda info: info['delta'])
    return birthdays

def get_birthdays():
    c = init_ldap(config);
    today = date.today()
    c.search(search_base=LDAP_USER_SCOPE, search_filter='(objectClass=d120Person)', search_scope=SEARCH_SCOPE_WHOLE_SUBTREE, attributes=['givenName', 'sn', 'mail', 'birthday', 'birthmonth'])
    addresses = []
    birthdays = []
    for l in c.response:
        attr = l['attributes']
        if not 'birthday' in attr or not 'birthmonth' in attr:
            continue
        if 'mail' in attr:
            addresses.append([attr['givenName'][0],attr['sn'][0],attr['mail'][0]])
        birthday = date(today.year, int(attr['birthmonth'][0]), int(attr['birthday'][0]))
        delta = today - birthday
        if delta.days == -1:
            birthdays.append(attr['givenName'][0] + ' ' + attr['sn'][0])
    return addresses, birthdays

def send_mails(addresses, birthdays, dry_run=True):
    if len(birthdays) > 0:
        for pers in birthdays:
            mail(addresses, pers, config, dry_run)

def usage():
    print("supported commands:")
    print("  -n    dry-run (list mails to be sent)")
    print("  -s    really send the mails listed by dry-run")
    print("  -l    list all birthdays in upcoming order")
    print("        options:")
    print("          -S json|ascii|html")
    print("")

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(argv[1:], "nslS:", [])
    except getopt.GetoptError as err:
        print(err)
        usage()
        exit(2)
    style = 'ascii'
    for o, a in opts:
        if o == '-S': style = a
    for o, a in opts:
        if o == '-s':
            addresses, birthdays = get_birthdays()
            send_mails(addresses, birthdays, False)
        elif o == '-n':
            addresses, birthdays = get_birthdays()
            send_mails(addresses, birthdays, True)
        elif o == '-l':
            lst = get_all_birthdays()
            if style == 'json':
                print(json.dumps(lst))
            elif style == 'ascii':
                for b in lst:
                    print('%02d.%02d. %20s %-30s %-42s' % (b['birthday'].day, b['birthday'].month, b['name'], b['sn'], b['mail']))
            elif style == 'html':
                print('<table>')
                for b in lst:
                    age = (date.today()-b['dob']).days/365.0 if b['dob']!=None else 0
                    print('<tr><td>%02d.%02d.</td><td>%20s %-30s</td><td>in %d days</td><td>%0.02f</td></tr>' % (b['birthday'].day, b['birthday'].month, b['name'], b['sn'], b['delta'], age))
                print('</table>')
