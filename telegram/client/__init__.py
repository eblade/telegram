
import json
import requests
import time
import threading

from telegram.post import Message


class TelegramClient(object):
    def __init__(self):
        # Session and State
        self._session = requests.Session()
        self._token = ''
        self._authenticated = False
        self._no_mail_today = 0

        # Connection Details
        self.domain = None
        self.username = None
        self.protocol = 'http'
        self.port = 8080
        self.polling = True

        # Callbacks
        self.on_token_change_callback = None
        self.on_message_callback = None
        

    @property
    def fullname(self):
        return '@'.join([self.username, self.domain])

    @property
    def token(self):
        self._update_token(False)
        return self._token

    @token.setter
    def token(self, token):
        if not token: return
        cookie_jar = self._session.cookies
        cookie_jar.set('auth-token', token, domain=self.domain)

    @property
    def authenticated(self):
        return self._authenticated

    @property
    def recommended_wait(self):
        if self._no_mail_today <= 10:
            return 1
        else:
            return min(180, (self._no_mail_today - 10) * 5)

    def _update_token(self, event=True):
        cookie_jar = self._session.cookies
        token = cookie_jar.get_dict(self.domain).get('auth-token')
        if self._token != token:
            print("Client: Update token %s" % token)
            self._token = token
            if event and callable(self.on_token_change_callback):
                self.on_token_change_callback(token)

    def auth(self, password=None):
        if password is None:
            if self.token:
                self.check()
                return
            else:
                raise PasswordRequired('Got no token')

        print("Client: Connection to %s://%s:%i as %s" % (
            self.protocol, self.domain, self.port, self.username
        ))

        response = self._session.post(
            '%s://%s:%i/auth' % (self.protocol, self.domain, self.port),
            data=json.dumps({'username': self.username, 'password': password}),
            headers={'Content-Type': 'application/json'})

        if response.status_code != 200:
            raise LoginFailed('Unable to login')

        self._authenticated = True
        self._update_token()

    def check(self):
        response = self._session.get(
            '%s://%s:%i/auth/check' % (self.protocol, self.domain, self.port),
        )
        if response.status_code != 200:
            print("Client: Token Expired [%i]" % response.status_code)
            self._authenticated = False
            raise PasswordRequired('Token expired')
        self._authenticated = True
        
    def send(self, to, message):
        headers={
            'X-Telegram-From': self.username,
            'X-Telegram-To': to,
        }
        response = self._session.post(
            '%s://%s:%i/send' % (self.protocol, self.domain, self.port),
            data=message,
            headers=headers
        )

        if response.status_code == 401:
            print("Client: Token Expired [%i]" % response.status_code)
            self._authenticated = False

        self._update_token()
        
        if callable(self.on_message_callback):
            self.on_message_callback(Message(headers, message, response.status_code))
    
    def receive(self, *args, **kwargs):
        if not self.authenticated:
            print("Client: No auth")
            return

        response = self._session.get(
            '%s://%s:%i/new' % (self.protocol, self.domain, self.port),
        )

        if response.status_code == 401:
            print("Client: Token Expired [%i]" % response.status_code)
            self._authenticated = False

        self._update_token()
        
        if response.status_code == 200 and callable(self.on_message_callback):
            self._no_mail_today = 0
            self.on_message_callback(
                Message(
                    response.headers, 
                    response.content.decode('utf-8'),
                    response.status_code
                )
            )
        else:
            self._no_mail_today += 1

    def close(self):
        pass
        

class TelegramSocket(TelegramClient):
    # override
    def __init__(self, *args, **kwargs):
        super(TelegramSocket, self).__init__(*args, **kwargs)
        self.protocol = 'ws'
        self.keep_open = False
        self.polling = False
        
    def connect(self):
        import websocket
        protocol = 'ws' if self.protocol == 'http' else 'wss'
        self.ws = websocket.WebSocketApp(
            '%s://%s:%i/socket' % (protocol, self.domain, self.port),
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            header=['Cookie: auth-token=' + self.token],
        )
        self.ws.on_open = self.on_open
        t = threading.Thread(target=self.ws.run_forever)
        t.run()

    def on_open(self, ws):
        print("Client: WS: Opening")
        self.keep_open = True
        def run():
            ws.send(json.dumps({'request': 'new'}))
            while(self.keep_open):
                time.sleep(.1)
            time.sleep(.1)
            ws.close()
        t = threading.Thread(target=run)
        t.run()

    def on_message(self, ws, message):
        print(message)
        if callable(self.on_message_callback):
            data = json.loads(message)
            if data.get('request') == 'new' and data.get('status') == 200:
                self.on_message_callback(Message(
                    data.get('headers'),
                    data.get('body'),
                    data.get('status')
                ))

    def on_error(self, ws, error):
        print("Client: WS: Error: " + error)

    def on_close(self, ws):
        print("Client: WS: Closing")

    # override
    def send(self, to, message):
        try:
            data = {
                'request': 'proxy',
                'headers': {
                    'X-Telegram-To': to
                },
                'body': message
            }
            self.ws.send(json.dumps(data))
        except Exception as e:
            raise SendError(str(e))

    # override
    def recieve(self, *args, **kwargs):
        pass

    # override
    def close(self):
        self.keep_open = False


class PasswordRequired(Exception):
    pass

class LoginFailed(Exception):
    pass

class SendError(Exception):
    pass
