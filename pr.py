from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import sys

class Session(LineReceiver):

	def __init__(self, factory):
		self.factory = factory

	def connectionMade(self):
		pass

	def connectionLost(self, reason):
		pass

	def lineReceived(self, command):
		if command.startswith('IAMAT'):
			self.handle_IAMAT(command)
		elif command.startswith('AT'):
			self.handle_AT(command)
		elif command.startswith('WHATSAT'):
			self.handle_WHATSAT(command)
		elif command.startswith('ITSAT'):
			self.handle_ITSAT(command)
		else:
			self.handle_unknown_command(command)

	def handle_IAMAT(self, command):
		self.sendLine(self.factory.server_name+'YOU ARE AT: '+command)

	def handle_AT(self, command):
		self.sendLine(self.factory.server_name+'AT: '+command)

	def handle_WHATSAT(self, command):
		self.sendLine(self.factory.server_name+'WHATSAT: '+command)

	def handle_ITSAT(self, command):
		self.sendLine(self.factory.server_name+'ITS AT: '+command)

	def handle_unknown_command(self, command):
		self.sendLine('?')


class SessionFactory(Factory):

	def __init__(self, server_name):
		self.server_name = server_name

	def buildProtocol(self, addr):
		return Session(self)


if __name__ == '__main__':
	assert(len(sys.argv) == 3)
	reactor.listenTCP(int(sys.argv[2]), SessionFactory(sys.argv[1]))
	reactor.run()
