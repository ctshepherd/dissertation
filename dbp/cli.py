from dbp.core import DBP
from twisted.internet import stdio, reactor
from twisted.protocols import basic
from twisted.internet.error import ConnectionLost


class DBPProtocol(basic.LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        self.dbp = DBP()
        self.sendLine("DBP console. Type 'help' for help.")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line: return

        # Parse the command
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Dispatch the command to the appropriate method.  Note that all you
        # need to do to implement a new command is add another do_* method.
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError, e:
            self.sendLine('Error: no such command.')
        else:
            try:
                method(*args)
            except Exception, e:
                self.sendLine('Error: ' + str(e))

    def do_help(self, command=None):
        """help [command]: List commands, or show help on the given command"""
        if command:
            self.sendLine(getattr(self, 'do_' + command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.sendLine("Valid commands: " +" ".join(commands))

    def do_quit(self):
        """quit: Quit this session"""
        self.sendLine('Goodbye.')
        self.transport.loseConnection()

    def do_list(self):
        """list: Output the contents of the database"""
        self.sendLine(str(self.dbp.db._db))

    def do_assign(self, s):
        """assign key=val: Set key to val in the database"""
        self.dbp.execute(s).addCallback(
            self.__checkSuccess).addErrback(
            self.__checkFailure)

    def __checkSuccess(self, res):
        self.sendLine("Success: %r." % res)

    def __checkFailure(self, failure):
        self.sendLine("Failure: " + failure.getErrorMessage())

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        if reason.check(ConnectionLost):
            pass
        else:
            reactor.stop()

def main():
    stdio.StandardIO(DBPProtocol())
    reactor.run()
