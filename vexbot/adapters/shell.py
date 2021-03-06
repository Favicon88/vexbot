import cmd
import atexit
from time import sleep

from threading import Thread

import zmq
from vexmessage import decode_vex_message

from vexbot import __version__
from vexbot.argenvconfig import ArgEnvConfig
from vexbot.adapters.messaging import ZmqMessaging
from vexbot.command_managers import CommandManager

from vexbot.commands.start_vexbot import start_vexbot as _start_vexbot
# from vexbot.commands.call_editor import call_editor


class Shell(cmd.Cmd):
    def __init__(self,
                 context=None,
                 prompt_name='vexbot',
                 publish_address=None,
                 subscribe_address=None,
                 **kwargs):

        super().__init__()
        self.messaging = ZmqMessaging('shell',
                                      publish_address,
                                      subscribe_address,
                                      'shell')

        self.command_manager = CommandManager(self.messaging)
        # FIXME
        self.command_manager._commands.pop('commands')
        self.stdout.write('Vexbot {}\n'.format(__version__))
        if kwargs.get('already_running', False):
            self.stdout.write('vexbot already running\n')
        self.stdout.write("Type \"help\" for command line help or "
                          "\"commands\" for bot commands\n\n")

        self.command_manager.register_command('start_vexbot',
                                              _start_vexbot)

        self.messaging.start_messaging()

        self.prompt = prompt_name + ': '
        self.misc_header = "Commands"
        self._exit_loop = False
        self._set_readline_helper(kwargs.get('history_file'))

    def default(self, arg):
        if not self.command_manager.is_command(arg, call_command=True):
            command, argument, line = self.parseline(arg)

            self.messaging.send_command(command=command,
                                        args=argument,
                                        line=line)

    def _set_readline_helper(self, history_file=None):
        try:
            import readline
        except ImportError:
            return

        try:
            readline.read_history_file(history_file)
        except IOError:
            pass
        readline.set_history_length(1000)
        atexit.register(readline.write_history_file, history_file)

    def run(self):
        frame = None
        while True and not self._exit_loop:
            try:
                # NOTE: not blocking here to check the _exit_loop condition
                frame = self.messaging.sub_socket.recv_multipart(zmq.NOBLOCK)
            except zmq.error.ZMQError:
                pass

            sleep(.5)

            if frame:
                message = decode_vex_message(frame)
                if message.type == 'RSP':
                    self.stdout.write("\n{}\n".format(self.doc_leader))
                    header = message.contents.get('original', 'Response')
                    contents = message.contents.get('response', None)
                    # FIXME
                    if (isinstance(header, (tuple, list))
                            and isinstance(contents, (tuple, list))
                            and contents):

                        for head, content in zip(header, contents):
                            self.print_topics(head, (contents,), 15, 70)
                    else:
                        if isinstance(contents, str):
                            contents = (contents,)
                        self.print_topics(header,
                                          contents,
                                          15,
                                          70)

                    self.stdout.write("vexbot: ")
                    self.stdout.flush()

                else:
                    # FIXME
                    print(message.type,
                          message.contents,
                          'fix me in shell adapter, run function')
                frame = None

    def _create_command_function(self, command):
        def resulting_function(arg):
            self.default(' '.join((command, arg)))
        return resulting_function

    def do_EOF(self, arg):
        self.stdout.write('\n')
        # NOTE: This ensures we exit out of the `run` method on EOF
        self._exit_loop = True
        return True

    def get_names(self):
        return dir(self)

    def do_help(self, arg):
        if arg:
            if self.command_manager.is_command(arg):
                doc = self.command_manager._commands[arg].__doc__
                if doc:
                    self.stdout.write("{}\n".format(str(doc)))
            else:
                self.messaging.send_command(command='help', args=arg)

        else:
            self.stdout.write("{}\n".format(self.doc_leader))
            # TODO: get these from robot?
            self.print_topics(self.misc_header,
                              ['start vexbot\nhelp [foo]', ],
                              15,
                              80)

    def add_completion(self, command):
        setattr(self,
                'do_{}'.format(command),
                self._create_command_function(command))

    """
    def _call_editor(self):
        vexdir = create_vexdir()
        code_output = call_editor(vexdir)
        try:
            code = compile(code_output, '<string>', 'exec')
        except Exception as e:
            print(e)

        local = {}
        exec(code, globals(), local)
        # need to add to commands?
        for k, v in local.items():
            if inspect.isfunction(v):
                self.command_manager.register_command(k, v)
    """


def _get_kwargs():
    config = ArgEnvConfig()
    config.add_argument('--publish_address', default=None)
    config.add_argument('--subscribe_address', default=None)
    config.add_argument('--prompt_name', default='vexbot')
    config.add_argument('--history_file',
                        environ='VEXBOT_SHELL_HISTORY')

    args = config.parse_args()
    return vars(args)


def main(**kwargs):
    if not kwargs:
        kwargs = _get_kwargs()
    shell = Shell(**kwargs)
    cmd_loop_thread = Thread(target=shell.run)
    cmd_loop_thread.daemon = True
    cmd_loop_thread.start()

    shell.cmdloop()


if __name__ == '__main__':
    main()
