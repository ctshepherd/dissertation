from dbp.core import DBP
from dbp.sql import parse_sql
from twisted.protocols import basic
from twisted.internet.error import ConnectionLost
from twisted.internet import reactor
from pprint import pformat


class DBPProtocol(basic.LineReceiver):
    delimiter = '\n'

    def __init__(self, port=None, bootstrap=None):
        self.port = port
        self.bootstrap = bootstrap

    def connectionMade(self):
        self.dbp = DBP(self.port, self.bootstrap)
        self.sendLine("DBP console. Type 'help' for help.")

    def lineReceived(self, line):
        # Ignore blank lines
        if not line:
            return

        # Parse the command
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Dispatch the command to the appropriate method.  Note that all you
        # need to do to implement a new command is add another do_* method.
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError, e:
            self.sendLine('Error: no such command "%r".' % e)
        else:
            try:
                method(*args)
            except Exception, e:
                if not self.debug:
                    self.sendLine('Error: ' + str(e))
                else:
                    raise


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
        self.sendLine(pformat(self.dbp.db.rows))

    def do_sql(self, s):
        """Perform an SQL statement"""
        if self.dbp.lock_holder is not None and not self.dbp.owns_lock():
            self.sendLine("Unable to assign: lock held by %s" % self.dbp.lock_holder)
        op = parse_sql(s)
        d = op.serialize()
        self.dbp.execute(d).addCallback(
            self.__checkSuccess).addErrback(
            self.__checkFailure)

    def do_read(self):
        self.dbp.execute("nop")

    def do_hosts(self):
        self.sendLine(pformat(self.dbp.manager.node.hosts))

    def do_instances(self):
        self.sendLine(str(self.dbp.manager.node.instances))

    def do_cur_tx(self):
        self.sendLine("Current processed TX: %s" % self.dbp.tx_version)

    def do_begin(self):
        self.sendLine("Lock: Attempting to take lock")
        d = self.dbp.take_lock()
        def won(instance):
            if self.dbp.owns_lock():
                self.sendLine("Lock: lock acquired")
            else:
                self.sendLine("Lock: not able to acquire lock")
        d.addCallback(won)

    def do_commit(self):
        if self.dbp.owns_lock():
            self.dbp.release_lock()
        else:
            self.sendLine("Lock: lock currently not held")

    def do_ehlo(self):
        self.dbp.manager.node.do_ehlo()

    def do_history(self):
        self.sendLine(pformat(self.dbp.history))


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
