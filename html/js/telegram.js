var ws = new WebSocket("ws://" + document.location.host + "/socket");
ws.onopen = function() {
    ws.send(JSON.stringify({request: "new"}));
};
ws.onmessage = function (evt) {
    var
        data = evt.data;
};

function handle_messagebox(e) {
    var
        key=e.keyCode || e.which;

    if (key === 13) {
        var
            receiver = document.getElementById("receiver_textbox").value,
            message_box = document.getElementById("message_textbox"),
            message = message_box.value;

        ws.send(JSON.stringify({
            request: "proxy",
            headers: {
                "X-Telegram-To": receiver,
            },
            data: message,
            contentType : 'text/plain',
        }));

        message_box.value = '';
        print_message(null, receiver, message);
    }

    return false;
}

function print_message(sender, receiver, message) {
    var
        messages = document.getElementById("messages"),
        newMessage = document.createElement('div');

    newMessage.className = "message";
    if (sender === null) {
        newMessage.innerHTML = '<span class="person">' + receiver + '</span><br />' + message;
        newMessage.className += " from_me";
    } else {
        newMessage.innerHTML = '<span class="person">' + sender + '</span>:<br />' + message;
        newMessage.className += " to_me";
    }
    messages.appendChild(newMessage);
}

function change_receiver(receiver) {
    var
        receiver_textbox = document.getElementById("receiver_textbox");

    receiver_textbox.value = receiver;
}
