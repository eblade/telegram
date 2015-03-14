


from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
from kivy.core.window import Window
from kivy.metrics import dp


class _Spacer(Widget):
    # Internal class, not documented.
    pass


class LoginPopup(Widget):
    '''Login popup widget
    '''

    title = StringProperty('<No title set>')
    '''Title of the setting, defaults to '<No title set>'.
    '''

    value = ObjectProperty(None)
    '''Value of the token according to the :class:`~kivy.config.ConfigParser`
    instance. Any change to this value will trigger a
    :meth:`Settings.on_config_change` event.
    '''

    popup = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current popup when it's shown.
    '''

    textinput = ObjectProperty(None)
    '''(internal) Used to store the current textinput from the popup and
    to listen for changes.
    '''

    callback = ObjectProperty(None)
    '''(internal) callback(result), called with None if dismissed, value
    otherwise
    '''
    
    ok = BooleanProperty(False)
    '''(internal) set to True if a password was given, for _dismiss to know
    if to run callback(None)
    '''

    def _dismiss(self, *largs):
        if self.textinput:
            self.textinput.focus = False
        if self.popup:
            self.popup.dismiss()
        self.popup = None
        if not self.ok:
            self.callback(None)

    def _validate(self, instance):
        self.ok = True
        self._dismiss()
        value = self.textinput.text.strip()
        self.value = value
        self.callback(value)

    def _focus(self, instance):
        self.textinput.focus = True

    def create_popup(self, callback):
        # value setup
        self.value = ''
        self.callback = callback
        self.ok = False

        # create popup layout
        content = BoxLayout(orientation='vertical', spacing='5dp')
        popup_width = min(0.95 * Window.width, dp(500))
        self.popup = popup = Popup(
            title=self.title, content=content, size_hint=(None, None),
            size=(popup_width, '250dp'), on_open=self._focus)

        # create the textinput used for numeric input
        self.textinput = textinput = TextInput(
            text=self.value, font_size='24sp', multiline=False,
            size_hint_y=None, height='42sp', password=True)
        textinput.bind(on_text_validate=self._validate)
        self.textinput = textinput

        # construct the content, widget are used as a spacer
        content.add_widget(Widget())
        content.add_widget(textinput)
        content.add_widget(Widget())
        content.add_widget(_Spacer())

        # 2 buttons are created for accept or cancel the current value
        btnlayout = BoxLayout(size_hint_y=None, height='50dp', spacing='5dp')
        btn = Button(text='Ok')
        btn.bind(on_release=self._validate)
        btnlayout.add_widget(btn)
        btn = Button(text='Cancel')
        btn.bind(on_release=self._dismiss)
        btnlayout.add_widget(btn)
        content.add_widget(btnlayout)

        # all done, open the popup !
        popup.open()
