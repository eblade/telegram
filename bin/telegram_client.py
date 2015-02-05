from __future__ import print_function
import argparse
import time
import yaml
import json
import os
import requests


parser = argparse.ArgumentParser('telegram-client')
parser.add_argument('--config-file', '-f', default='~/.telegram/client.yaml', help='config file location (default ~/.telegram/client.yaml)')
parser.add_argument('to', help='whom to send to')
parser.add_argument('message', help='message to send')
parser.add_argument('--iterate', '-i', default=-1, type=int, help='send the message X times, and append the order number')
args = parser.parse_args()


config = yaml.load(open(os.path.expanduser(args.config_file), 'r'))
domain = config.get('domain')
username = config.get('username')
password = config.get('password')
target = args.to
session = requests.Session()

def auth(password):
    response = session.post('http://%s:8080/auth' % domain,
                            data=json.dumps({'username': username, 'password': password}),
                            headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        print('Authentication failure')
        exit(-1)

def send(message):
    response = session.post('http://%s:8080/send' % domain,
                            data=message,
                            headers={
                                'X-Telegram-From': '%s@%s' % (username, domain),
                                'X-Telegram-To': args.to,
                                'X-Telegram-Sign': 'abcd'
                            })
    print("Status code: %i" %response.status_code)
    print(response.headers)
    print(response.text)

auth(password or raw_input("Password for %s@%s:" % (username, domain)))

if args.iterate == -1:
    send(args.message)
else:
    for x in range(args.iterate):
        send('%s (%i)' % (args.message, x+1))
