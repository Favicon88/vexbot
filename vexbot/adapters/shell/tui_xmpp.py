import urwid

from vexbot.adapters.shell.tui_address import Address


def button_press():
    pass


def main():
    blank = urwid.Divider()
    content = [urwid.Edit('Service Name: '),
            blank,
            urwid.Edit('Password: '),
            blank,
            urwid.Edit('Local: '),
            blank,
            urwid.Edit('Bot Nick: '),
            blank,
            urwid.Edit('Room: '),
            blank,
            urwid.Edit('Domain: '),
            blank,
            *Address('Subscribe Address').content,
            blank,
            *Address('Publish Address').content,
            blank,
            urwid.GridFlow(
                [urwid.AttrWrap(urwid.Button(txt, button_press),
                    'buttn', 'buttnf') for txt in ['Ok', 'Cancel']],
                13, 3, 1, 'center'),
            ]



    header = urwid.AttrWrap(urwid.Text("Edit XMPP Settings", 'center'), 'header')
    listbox = urwid.ListBox(urwid.SimpleFocusListWalker(content))
    frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'), header=header)
    loop = urwid.MainLoop(frame)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()