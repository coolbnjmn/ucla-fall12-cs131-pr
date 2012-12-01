from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import datetime
import sys

class Session(LineReceiver):

	def __init__(self, factory):
		self.factory = factory

	def connectionMade(self):
		pass

	def connectionLost(self, reason):
		pass

	def lineReceived(self, message):
		self.factory.logInfo('Received message: {0}'.format(message))

		if message.startswith('IAMAT'):
			self.handle_IAMAT(message)
		elif message.startswith('AT'):
			self.handle_AT(message)
		elif message.startswith('WHATSAT'):
			self.handle_WHATSAT(message)
		elif message.startswith('ITSAT'):
			self.handle_ITSAT(message)
		else:
			self.handle_unknown_command(message)

	def handle_IAMAT(self, command):
		tokens = command.split()

		if not len(tokens) == 4:
			self.factory.logError('IAMAT command malformed: {0}'.format(command))

		command_name, client_name, location, posix_time = tokens

		# TODO: Actually parse location, but unnecessary for prototype
		try:
			posix_time = float(posix_time)
			command_time = datetime.datetime.utcfromtimestamp(posix_time)
		except Exception as e:
			self.factory.logError('IAMAT command has malformed POSIX time: {0}'.format(command))
			self.handle_unknown_command(command)
			return

		system_time = datetime.datetime.utcnow()
		time_difference = system_time - command_time

		self.respond('AT {0} {1!r} {2}'.format(self.factory.server_name, time_difference.total_seconds(), ' '.join(tokens[1:])))

	def handle_AT(self, command):
		self.sendLine(self.factory.server_name+'AT: '+command)

	def handle_WHATSAT(self, command):
		self.sendLine(self.factory.server_name+'WHATSAT: '+command)

	def handle_ITSAT(self, command):
		self.sendLine(self.factory.server_name+'ITS AT: '+command)

	def handle_unknown_command(self, command):
		self.respond('?')
	
	def respond(self, response):
		self.sendLine(response)
		self.factory.logInfo('Responded with: {0}'.format(response))


class SessionFactory(Factory):

	def __init__(self, server_name):
		self.server_name = server_name
		self.log_stream = open('{0}_{1}.log'.format(self.server_name, datetime.datetime.utcnow().isoformat().replace(':', '_').replace('T', '_')), 'w')
		self.logInfo('Server opening.')
	
	def stopFactory(self):
		self.logInfo('Server closing.')
		self.log_stream.close()

	def buildProtocol(self, addr):
		self.logInfo('Protocol built for address: {0!s}'.format(addr))
		return Session(self)
	
	def logInfo(self, message):
		self._log('INFO: {0!s}'.format(message))
	
	def logWarning(self, message):
		self._log('WARNING: {0!s}'.format(message))
	
	def logError(self, message):
		self._log('ERROR: {0!s}'.format(message))
	
	def _log(self, message):
		message = '{0}: {1}'.format(datetime.datetime.utcnow().isoformat(), message)
		print(message)
		self.log_stream.write(message+'\n')


if __name__ == '__main__':
	assert(len(sys.argv) == 3)
	reactor.listenTCP(int(sys.argv[2]), SessionFactory(sys.argv[1]))
	reactor.run()
