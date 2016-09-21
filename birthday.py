import re
import smtplib
from datetime import datetime, date
from sys import argv, exit
from email.mime.text import MIMEText
from configparser import ConfigParser
from email.utils import formatdate

def mail(addr, person):
    config = ConfigParser()
    config.read('config')
    text = ""
    with open('birthdaytext', 'r') as f:
        text = f.read()
    s = smtplib.SMTP(config['mailserver']['address'], 587)
    s.starttls()
    s.login(config['mailserver']['user'], config['mailserver']['password'])
    for address in addr:
        text = text.replace('RECEPIENT', address[0])
        text = text.replace('BIRTHDAYKID', person)
        msg = MIMEText(text)
        msg['Subject'] = config['mail']['subject']
        msg['From'] = config['mail']['from']
        msg['Date'] = formatdate()
        msg['To'] = address[1]
        s.send_message(msg)
    s.quit()

def main():
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
                if delta.days == -1:
                    birthdays.append(parsed[0])

    if len(birthdays) > 0:
        for pers in birthdays:
            mail(addresses, pers)

if __name__ == "__main__":
    main()
