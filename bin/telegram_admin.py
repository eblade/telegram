#!/usr/bin/env python

from __future__ import print_function
import argparse
import json
import os
from getpass import getpass
from telegram.auth.internal import hashpass
from telegram.auth.sign import generate_key_pair


parser = argparse.ArgumentParser('telegram-client')
parser.add_argument('--config-dir', '-c', default='~/.telegram', help='config file location (default ~/.telegram)')

subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

showuser_parser = subparsers.add_parser('showuser', help="Show user info")
showuser_parser.add_argument('username', help="The username of the user")

adduser_parser = subparsers.add_parser('adduser', help="Add a new user")
adduser_parser.add_argument('username', help="The username of the new user")
adduser_parser.add_argument('--fullname', '-f', help="The full name of the new user")
adduser_parser.add_argument('--email', '-e', help="The email of the new user")
adduser_parser.add_argument('--password', '-p', help="The password (specified by hidden input if omitted)")
adduser_parser.add_argument('--admin', '-a', action="store_true", help="Give the user admin rights")

args = parser.parse_args()

config_dir = os.path.expanduser(args.config_dir)
users_filename = os.path.join(config_dir, 'users.json')
passwd_filename = os.path.join(config_dir, 'passwd')

if not os.path.exists(config_dir):
    print('Creating config dir "%s"' % config_dir)
    os.mkdir(config_dir)


try:
    with open(users_filename, 'r') as f:
        users = json.load(f)
except IOError:
    print("No users.json found!")
    users = {}


def print_user(username):
    user = users[username]
    print(username + ':')
    print('  Full name: ' + user.get('fullname'))
    print('     E-mail: ' + user.get('email'))
    print('      Admin: ' + ('yes' if user.get('admin', False) else 'no'))

def store_users():
    with open(users_filename, 'w') as f:
        json.dump(users, f, indent=2)

if args.command == 'showuser':
    if args.username in users:
        print_user(args.username)
    else:
        print('No such user "%s"' % args.username)

elif args.command == 'adduser':
    if args.username in users:
        print('User already exists!')
        exit(-1)


    if args.password is None:
        password1 = getpass('Choose your password: ')
        password2 = getpass('Re-type the password: ')
        if password1 != password2:
            print("Passwords did not match!")
            exit(-1)
        password = password1
    else:
        password = args.password

    with open(passwd_filename, 'a') as f:
        f.write(args.username)
        f.write(':')
        f.write(hashpass(password))
        f.write('\n')

    private_key, public_key = generate_key_pair(args.username)

    user = {
        'fullname': args.fullname or args.username,
        'email': args.email,
        'admin': args.admin,
        'private_key': private_key,
        'public_key': public_key,
    }

    users[args.username] = user
    store_users()
    print_user(args.username)

