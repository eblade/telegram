var ws = new WebSocket("ws://" + document.location.host + "/socket");
ws.onopen = function() {
    ws.send(JSON.stringify({request: "new"}));
};
ws.onmessage = function (evt) {
    var
        data = JSON.parse(evt.data);

    if (data.request == 'new' && data.status == 200) {
        var
            sender = data.headers['x-telegram-from'],
            receiver = data.headers['x-telegram-to'],
            body = data.body;

        print_message(sender, receiver, body);
    }
};
ws.onclose = function (evt) {
    ws.send('{"request":"close"}');
};

function reconnect_if_needed() {
    if (ws.readyState == 0 || ws.readyState == 1) {
        return;
    } else {
        ws = new WebSocket("ws://" + document.location.host + "/socket");
    }
};

window.onbeforeunload = function() {
    ws.send('{"request":"close"}');
    ws.onclose = function () {}; // disable onclose handler first
    ws.close()
};

function handle_logout(e) {
    ws.send('{"request": "close"}');
    ws.onclose = function () {}; // disable onclose handler first
    ws.close();

    document.location = 'logout';

    return false;
}

function handle_messagebox(e) {
    var
        message_box = e.target,
        key=e.keyCode || e.which;

    if (key === 13) {
        var
            receiver = document.getElementById("receiver_textbox").value,
            message = message_box.value,
            matches = message.match(/^@([A-Za-z0-9_\.]+)$/);
        
        if (message == '') {
            return false;
        } else if (matches !== null && matches.length == 2) {
            change_receiver(matches[1]);
        } else {
            reconnect_if_needed();
            ws.send(JSON.stringify({
                request: "proxy",
                headers: {
                    "X-Telegram-To": receiver,
                },
                body: message,
                'content-type': 'text/plain',
            }));

            print_message(null, receiver, message);
        }
        message_box.value = '';

    } else if (key === 58) { // colon
        var
            message = message_box.value,
            matches = message.match(/^@([A-Za-z0-9_\.]+)$/);

        if (matches.length == 2) {
            change_receiver(matches[1]);
            e.preventDefault();
            message_box.value = '';
        }
    }

    return false;
}

function print_message(sender, receiver, message) {
    var
        messages = document.getElementById("messages"),
        newMessage = document.createElement('div');

    newMessage.className = "message";
    if (sender === null) {
        newMessage.innerHTML = '<span class="address">To <span class="person" onclick=\'change_receiver("' + receiver + '")\'>' + receiver + '</span></span><br />' + message;
        newMessage.className += " from_me";
    } else {
        newMessage.innerHTML = '<span class="address">From <span class="person" onclick=\'change_receiver("' + sender + '")\'>' + sender + '</span> to <span class="person" onclick=\'change_receiver("' + receiver + '")\'>' + receiver + '</span></span><br />' + message;
        newMessage.className += " to_me";
    }
    messages.appendChild(newMessage);
}

function change_receiver(receiver) {
    var
        receiver_textbox = document.getElementById("receiver_textbox");

    receiver_textbox.value = receiver;
    $(receiver_textbox).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
}
