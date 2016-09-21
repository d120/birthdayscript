import re
import smtplib
from datetime import datetime, date
from sys import argv, exit
from email.mime.text import MIMEText
from configparser import ConfigParser

def mail(addr, person):
    config = ConfigParser()
    config.read('config')
    text = config['mail']['text']
    text = text.replace('RECEPIENT', addr[0])
    text = text.replace('BIRTHDAYKID', person)
    msg = MIMEText(config['mail']['text'])
    msg['Subject'] = config['mail']['subject']
    msg['From'] = config['mail']['from']
    msg['To'] = addr[1]
    s = smtplib.SMTP('mail.d120.de', 587)
    s.starttls()
    s.login(config['mailserver']['user'], config['mailserver']['password'])
    s.send_message(msg)
    s.quit()


today = date.today()
matcher = re.compile(r'\t')
if len(argv) != 2:
    exit(1)
path = argv[1]
addresses = []
birthdays = []
with open(path, "r") as f:
    for l in f:
        if l[0] == '#':
            continue
        parsed = matcher.split(l)
        if len(parsed) == 3:
            addresses.append([parsed[0], parsed[2]])
            birthday = datetime.strptime(parsed[1], '%d.%m.').replace(year=today.year).date()
            delta = today - birthday
            print(delta)
            if delta.days == -1:
                print("Happy Birthday %s" % parsed[0])
                birthdays.append(parsed[0])

if len(birthdays) > 0:
    for pers in birthdays:
        for address in addresses:
            mail(address, pers)

