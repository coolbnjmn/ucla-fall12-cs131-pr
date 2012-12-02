from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

import datetime
import sys

class Session(LineReceiver):

	def __init__(self, factory):
		self.factory = factory

	def connectionMade(self):
		self.factory.logInfo('Connection made: {0!s}'.format(self))

	def connectionLost(self, reason):
		self.factory.logInfo('Connection lost: {0!s}'.format(self))

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
			self.factory.logError('IAMAT command malformed, number of tokens =/= 4: {0}'.format(command))
			self.handle_unknown_command(command)
			return

		command_name, client_name, location, posix_time = tokens
		self.factory.logInfo('Parsed client name: {0}'.format(client_name))
		self.factory.logInfo('Parsed location: {0}'.format(location))

		# TODO: Actually parse location, but unnecessary for prototype
		try:
			posix_time = float(posix_time)
			command_time = datetime.datetime.utcfromtimestamp(posix_time)
		except Exception as e:
			self.factory.logError('IAMAT command has malformed POSIX time: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed POSIX time: {0}'.format(command_time.isoformat()))

		system_time = datetime.datetime.utcnow()
		time_difference = system_time - command_time

		self.factory.logInfo('Calculated time difference: {0!r}'.format(time_difference.total_seconds()))

		self.factory.users[client_name] = (location, command_time, system_time, tokens)

		self.respond('AT {0} {1!r} {2}'.format(self.factory.server_name, time_difference.total_seconds(), ' '.join(tokens[1:])))

	def handle_AT(self, command):
		self.sendLine(self.factory.server_name+'AT: '+command)

	def handle_WHATSAT(self, command):
		tokens = command.split()

		if not len(tokens) == 4:
			self.factory.logError('WHATSAT command malformed, number of tokens =/= 4: {0}'.format(command))
			self.handle_unknown_command(command)
			return

		command_name, client_name, radius_km, max_num_of_tweets = tokens
		self.factory.logInfo('Parsed client name: {0}'.format(client_name))

		try:
			radius_km = float(radius_km)
		except Exception as e:
			self.factory.logError('WHATSAT command has malformed radius: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed radius (in km): {0}'.format(radius_km))
		
		try:
			max_num_of_tweets = int(max_num_of_tweets)
		except Exception as e:
			self.factory.logError('WHATSAT command has malformed max. number of tweets: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed max. number of tweets: {0}'.format(max_num_of_tweets))

		if not self.factory.users.has_key(client_name):
			self.factory.logError('Unable to find user: {0}'.format(client_name))
			self.handle_unknown_command(command)
			return

		client_info = self.factory.users[client_name]
		client_location, client_command_time, client_system_time, client_last_tokens = client_info

		self.respond('AT {0} {1}\n{2}'.format(self.factory.server_name, ' '.join(client_last_tokens[1:]), self.find_tweets(client_location, radius_km, max_num_of_tweets)))
	
	def find_tweets(self, client_location, radius_km, max_num_of_tweets):
		return '''{"results":[{"location":"Ever","profile_image_url":"http://a3.twimg.com/profile_images/524342107/avatar_normal.jpg","created_at":"Fri, 16 Nov 2012 07:38:34 +0000","from_user":"C_86","to_user_id":null,"text":"RT @ionmobile: @SteelCityHacker everywhere but nigeria // LMAO!","id":5704386230,"from_user_id":34011528,"geo":null,"iso_language_code":"en","source":"&lt;a href=&quot;http://socialscope.net&quot; rel=&quot;nofollow&quot;&gt;SocialScope&lt;/a&gt;"},{"location":"Ever","profile_image_url":"http://a3.twimg.com/profile_images/524342107/avatar_normal.jpg","created_at":"Fri, 16 Nov 2012 07:37:16 +0000","from_user":"C_86","to_user_id":null,"text":"RT @ionmobile: 25 minutes left! RT Who will win????? Follow @ionmobile","id":5704370354,"from_user_id":34011528,"geo":null,"iso_language_code":"en","source":"&lt;a href=&quot;http://socialscope.net&quot; rel=&quot;nofollow&quot;&gt;SocialScope&lt;/a&gt;"}],"max_id":5704386230,"since_id":5501341295,"refresh_url":"?since_id=5704386230&q=","next_page":"?page=2&max_id=5704386230&rpp=2&geocode=27.5916%2C86.564%2C100.0km&q=","results_per_page":2,"page":1,"completed_in":0.090181,"warning":"adjusted since_id to 5501341295 (2012-11-07 07:00:00 UTC), requested since_id was older than allowed -- since_id removed for pagination.","query":""}'''

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
		self.users = {}
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
		try:
			self.log_stream.write(message+'\n')
		except ValueError as e:
			print('Could not log to file, file stream has been closed.')

if __name__ == '__main__':
	assert(len(sys.argv) == 3)
	reactor.listenTCP(int(sys.argv[2]), SessionFactory(sys.argv[1]))
	reactor.run()

