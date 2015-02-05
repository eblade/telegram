#!/usr/bin/env python

from __future__ import print_function
import argparse
import os
from gevent import monkey; monkey.patch_all()
from telegram.post.office import PostOffice
from telegram.auth.session import SessionHandler
from telegram.auth.internal import InternalAuth
from bottle import debug, request, response, Bottle, HTTPError, HTTPResponse, static_file, abort, redirect
from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler
import json

parser = argparse.ArgumentParser('telegram-client')
parser.add_argument('--config-dir', '-c', default='~/.telegram', help='config file location (default ~/.telegram)')
args = parser.parse_args()

config_dir = os.path.expanduser(args.config_dir)

telegram = Bottle()

internal_auth = InternalAuth(config_dir)
sessions = SessionHandler()
post_office = PostOffice(config_dir)

MEDIA_ROOT='/home/johan/git/telegram/media'
EMOTICON_ROOT = os.path.join(MEDIA_ROOT, 'emoticon')
GRAPHIC_ROOT = os.path.join(MEDIA_ROOT, 'graphic')

# auth
# expects body
#
# {
#   "auth-module": "pam" | "internal",
#   "username": "USERNAME",
#   "password": "PASSWORD"
# }
@telegram.post('/auth')
@telegram.post('/telegram/auth')
def auth():
    auth_data = request.json
    if auth_data is None:
        return HTTPError(403, u'Authentication failed: No auth data.')

    auth_module = auth_data.get('auth-module', 'internal')
    username = auth_data.get('username')
    password = auth_data.get('password')

    token = _auth(auth_module, username, password)

    if request.headers.get('Accepts', '').startswith('application/json'):
        response.set_cookie('token', token)
        print({ "result": "ok", "token": token })
        return { "result": "ok", "token": token }
    else:
        return HTTPResponse(status=200, headers={'Set-Cookie': sessions.get_cookie_header(token)})

def _auth(auth_module, username, password):
    if auth_module == 'internal':
        ok = internal_auth.authenticate(username, password)
    else:
        abort(403, u'Authentication failed: Unkown auth-module "%s".' % auth_module)

    if ok:
        token = sessions.create(username)
        return token
    else:
        abort(401, u'Authentication failed: Wrong username or password.')


@telegram.get('/new')
@telegram.get('/telegram/new')
def new():
    username = sessions.validate(request.cookies.get('auth-token'))
    if username is None:
        return HTTPError(401, "Invalid token")

    next_message = post_office.fetch(username)

    if next_message is None:
        return HTTPResponse(status=204)
    else:
        headers, body = next_message
        return HTTPResponse(body, status=200, headers=headers)


@telegram.route('/socket')
@telegram.route('/telegram/socket')
def socket():
    username = sessions.validate(request.cookies.get('auth-token'))
    print('User: %s' % username)
    if username is None:
        abort(401, "Invalid token")

    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, "Websocket request expected")

    def callback(headers, body):
        wsock.send(json.dumps({
            'status': 200,
            'request': 'new',
            'headers': headers,
            'body': body
        }))

    post_office.listen(username, callback)

    while True:
        try:
            message = wsock.receive()
            if message is not None:
                print("Message: " + message)
                message = json.loads(message)
                address = message.get('request')
                if address == 'new':
                    while True:
                        next_message = post_office.fetch(username)
                        if next_message is None:
                            wsock.send('{"status": 204}')
                            break
                        else:
                            headers, body = next_message
                            wsock.send(json.dumps({
                                'status': 200,
                                'request': 'new',
                                'headers': headers,
                                'body': body
                            }))

                elif address == 'proxy':
                    headers = message.get('headers', {})
                    body = message.get('body', '')
                    headers['X-Telegram-From'] = username
                    #try:
                    post_office.post(headers, body, foreign=False)
                    wsock.send(json.dumps({'status': 201,}))
                    #except:
                    #    wsock.send(json.dumps({'status': 404,}))

                elif address == 'close':
                    wsock.close()
                    break

                else:
                    wsock.send('{"status": 404}')
        except WebSocketError:
            print("WebSocketError")
            break


@telegram.post('/proxy')
@telegram.post('/telegram/proxy')
def proxy():
    username = sessions.validate(request.cookies.get('auth-token'))
    if username is None:
        abort(401, "Invalid token")
    headers = dict(request.headers)
    headers['X-Telegram-From'] = username
    post_office.post(headers, request.body, foreign=False)
    return HTTPResponse(status=201)


@telegram.post('/send')
@telegram.post('/telegram/send')
def send():
    post_office.post(request.headers, request.body)
    return HTTPResponse(status=201)


@telegram.get('/key')
def key():
    """
    Returns the private key for the logged in user.
    """
    username = sessions.validate(request.cookies.get('auth-token'))
    if username is None:
        abort(401, "Invalid token")
    
    key = post_office.get_private_key(username)
    
    if key is None:
        abort(404, "User has no key")
    else:
        return HTTPResponse(status=200, body=key)


@telegram.get('/key/<username>')
def key_for_user(username):
    """
    Returns the public key for any given user.

    :param unicode user: The username
    """
    key = post_office.get_public_key(username)
    
    if key is None:
        abort(404, "User has no key")
    else:
        return HTTPResponse(status=200, body=key)


@telegram.get('/')
@telegram.get('/web')
def web():
    username = sessions.validate(request.cookies.get('auth-token'))
    if username is None:
        redirect('/login')

    return static_file('telegram.html', './html')


@telegram.get('/login')
def login():
    username = sessions.validate(request.cookies.get('auth-token'))
    if username is not None:
        redirect('/web')

    return static_file('login.html', './html')


@telegram.post('/login')
def login():
    token = _auth('internal', request.forms.get('username'), request.forms.get('password'))
    return HTTPResponse(status=302, headers={
        'Set-Cookie': sessions.get_cookie_header(token),
        'Location': '/web',
    })

@telegram.get('/logout')
@telegram.get('/telegram/logout')
def logout():
    sessions.kill(request.cookies.get('auth-token'))
    redirect('/login')

@telegram.get('/js/<path:path>')
def js(path):
    return static_file(path, './html/js')


@telegram.get('/css/<path:path>')
def css(path):
    return static_file(path, './html/css')


# TODO Fix this up
#@telegram.post('/web_upload')
#def web_upload():
#    username = sessions.validate(request.cookies.get('auth-token'))
#    if username is not None:
#        abort(401, "Invalid token")
#
#    #category   = request.forms.get('category')
#    upload     = request.files.get('upload')
#    name, ext = os.path.splitext(upload.filename)
#    if ext not in ('.png','.jpg','.jpeg'):
#        return 'File extension not allowed.'
#
#    save_path = '/tmp' #get_save_path_for_category(category)
#    upload.save(save_path) # appends upload.filename automatically


@telegram.get('/image/emoticon/<icon:path>')
def image_emoticon(icon):
    return static_file(icon + '.png', EMOTICON_ROOT)


@telegram.get('/image/graphic/<icon:path>')
def image_graphic(icon):
    return static_file(icon + '.png', GRAPHIC_ROOT)


debug(True)
server = WSGIServer(('', 8080), telegram, handler_class=WebSocketHandler)
print("Starting web server.")
server.serve_forever()
