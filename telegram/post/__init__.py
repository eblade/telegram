

class Message(object):
    def __init__(self, headers, content, status_code=200):
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.content = content
        self.status_code = status_code

        self.telegram_from = self.headers.get('x-telegram-from')
        self.telegram_to = self.headers.get('x-telegram-to')
        self.telegram_sign = self.headers.get('x-telegram-sign')
        self.content_type = self.headers.get('content-type', 'text/plain')

    def __repr__(self):
        return '<telegram.post.Message [%i] %s -> %s/>' % (
            self.status_code, str(self.telegram_from), str(self.telegram_to))

class SystemMessage(Message):
    def __init__(self, username, content, status_code=200):
        self.content = content
        self.status_code = status_code

        self.telegram_from = 'system'
        self.telegram_to = username
        self.telegram_sign = '<sign>'
        self.content_type = 'text/plain'
