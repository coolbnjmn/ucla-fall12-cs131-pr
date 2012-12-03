#!/usr/bin/python

'''
TODO DOCUMENTATION
'''

import datetime
import sys

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import reactor

def send_to_peer(protocol, message_to_pass):
	'''
	TODO DOCUMENTATION
	'''
	protocol.send_message(message_to_pass)

class Session(LineReceiver):

	def __init__(self, factory):
		'''
		TODO DOCUMENTATION
		'''
		self.factory = factory

	def connectionMade(self):
		'''
		TODO DOCUMENTATION
		'''
		self.factory.logInfo('Connection made: {0}'.format(self.transport.getHost()))

	def connectionLost(self, reason):
		'''
		TODO DOCUMENTATION
		'''
		self.factory.logInfo('Connection lost.')

	def lineReceived(self, message):
		'''
		TODO DOCUMENTATION
		'''
		self.factory.logInfo('Received message: {0}'.format(message))

		if message.startswith('IAMAT'):
			self.handle_IAMAT(message)
		elif message.startswith('AT'):
			self.handle_AT(message)
		elif message.startswith('WHATSAT'):
			self.handle_WHATSAT(message)
		elif message.startswith('PEER'):
			self.handle_PEER(message)
		else:
			self.handle_unknown_command(message)

	def handle_IAMAT(self, command):
		'''
		TODO DOCUMENTATION
		'''
		tokens = command.split()

		if not len(tokens) == 4:
			self.factory.logError('IAMAT command malformed, number of tokens =/= 4: {0}'.format(command))
			self.handle_unknown_command(command)
			return

		command_name, client_name, client_location, client_posix_time = tokens
		self.factory.logInfo('Parsed client name: {0}'.format(client_name))
		self.factory.logInfo('Parsed location: {0}'.format(client_location))

		# TODO: Actually parse location, but unnecessary for prototype

		try:
			client_posix_time = float(client_posix_time)
			client_time = datetime.datetime.utcfromtimestamp(client_posix_time)
		except Exception as e:
			self.factory.logError('IAMAT command has malformed POSIX time: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed POSIX time: {0}'.format(client_time.isoformat()))

		# calculate time difference
		system_time = datetime.datetime.utcnow()
		time_difference = system_time - client_time
		self.factory.logInfo('Calculated time difference: {0!r}'.format(time_difference.total_seconds()))

		# store client information
		self.factory.users[client_name] = (client_location, client_time, system_time, tokens)
		self.factory.logInfo('Updated client info: {0} {1} {2} {3}, {4}'.format(client_name, client_location, client_time, system_time, ' '.join(tokens)))

		# respond with client information
		location_echo_message = 'AT {0} {1!r} {2}'.format(self.factory.server_name, time_difference.total_seconds(), ' '.join(tokens[1:]))
		self.send_message(location_echo_message)

		# send client information to peers
		self.factory.logInfo('Number of peers: {0}'.format(len(self.factory.peers.keys())))
		for peer_name in self.factory.peers.keys():
			self.factory.logInfo('Sending location information to peer: {0}'.format(peer_name))
			peer_info = self.factory.peers[peer_name]
			peer_name, protocol, host_name, port_number = peer_info
			self.factory.logInfo('Peer info: {0} {1} {2} {3}'.format(peer_name, protocol, host_name, port_number))

			end_point = None
			if protocol == 'tcp':
				end_point = TCP4ClientEndpoint(reactor, host_name, port_number)
				self.factory.logInfo('Endpoint created: {0!s}'.format(end_point))

			if not end_point == None:
				self.factory.logInfo('Connecting to peer: {0} {1} {2} {3}'.format(peer_name, protocol, host_name, port_number))
				connection = end_point.connect(self.factory)
				connection.addCallback(send_to_peer, location_echo_message)

	def handle_AT(self, command):
		'''
		TODO DOCUMENTATION
		'''
		tokens = command.split()

		if not len(tokens) == 6:
			self.factory.logError('AT command malformed, number of tokens =/= 6: {0}'.format(command))
			self.handle_unknown_command(command)
			return

		command_name, server_name, time_difference, client_name, client_location, client_posix_time = tokens

		self.factory.logInfo('Parsed server name: {0}'.format(server_name))

		try:
			time_difference = float(time_difference)
		except Exception as e:
			self.factory.logError('AT command has malformed time difference: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed time difference: {0}'.format(time_difference))

		self.factory.logInfo('Parsed client name: {0}'.format(client_name))

		self.factory.logInfo('Parsed client location: {0}'.format(client_location))

		try:
			client_posix_time = float(client_posix_time)
			client_time = datetime.datetime.utcfromtimestamp(client_posix_time)
		except Exception as e:
			self.factory.logError('AT command has malformed client time: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed client time: {0}'.format(client_time.isoformat()))

		system_time = datetime.datetime.utcnow()

		# check if the information is stale
		update_user = True
		if self.factory.users.has_key(client_name):
			last_client_location, last_client_time, last_system_time, last_tokens = self.factory.users[client_name]
			if last_client_time >= client_time:
				self.factory.logInfo('Last client location time is equal or more recent: {0}, {1} >= {2}'.format(client_name, last_client_time, client_time))
				update_user = False

		# store client information
		if update_user:
			self.factory.users[client_name] = (client_location, client_time, system_time, tokens)
			self.factory.logInfo('Updated client info: {0} {1} {2} {3}, {4}'.format(client_name, client_location, client_time, system_time, ' '.join(tokens)))

			# send client information to peers
			self.factory.logInfo('Number of peers: {0}'.format(len(self.factory.peers.keys())))
			for peer_name in self.factory.peers.keys():
				if peer_name == server_name:
					continue

				self.factory.logInfo('Sending location information to peer: {0}'.format(peer_name))
				peer_info = self.factory.peers[peer_name]
				peer_name, protocol, host_name, port_number = peer_info
				self.factory.logInfo('Peer info: {0} {1} {2} {3}'.format(peer_name, protocol, host_name, port_number))

				end_point = None
				if protocol == 'tcp':
					end_point = TCP4ClientEndpoint(reactor, host_name, port_number)
					self.factory.logInfo('Endpoint created: {0!s}'.format(end_point))

				if not end_point == None:
					self.factory.logInfo('Connecting to peer: {0} {1} {2} {3}'.format(peer_name, protocol, host_name, port_number))
					connection = end_point.connect(self.factory)
					connection.addCallback(send_to_peer, 'AT {0} {1} {2} {3} {4}'.format(self.factory.server_name, time_difference, client_name, client_location, client_posix_time))

	def handle_WHATSAT(self, command):
		'''
		TODO DOCUMENTATION
		'''
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

		self.send_message('AT {0} {1}\n{2}'.format(self.factory.server_name, ' '.join(client_last_tokens[1:]), self.find_tweets(client_location, radius_km, max_num_of_tweets)))
	
	def find_tweets(self, client_location, radius_km, max_num_of_tweets):
		'''
		TODO DOCUMENTATION
		'''
		# TODO: Use twittytwister to find a list of public tweets that will be filtered based on their geographic location.
		return '''{"results":[{"location":"Ever","profile_image_url":"http://a3.twimg.com/profile_images/524342107/avatar_normal.jpg","created_at":"Fri, 16 Nov 2012 07:38:34 +0000","from_user":"C_86","to_user_id":null,"text":"RT @ionmobile: @SteelCityHacker everywhere but nigeria // LMAO!","id":5704386230,"from_user_id":34011528,"geo":null,"iso_language_code":"en","source":"&lt;a href=&quot;http://socialscope.net&quot; rel=&quot;nofollow&quot;&gt;SocialScope&lt;/a&gt;"},{"location":"Ever","profile_image_url":"http://a3.twimg.com/profile_images/524342107/avatar_normal.jpg","created_at":"Fri, 16 Nov 2012 07:37:16 +0000","from_user":"C_86","to_user_id":null,"text":"RT @ionmobile: 25 minutes left! RT Who will win????? Follow @ionmobile","id":5704370354,"from_user_id":34011528,"geo":null,"iso_language_code":"en","source":"&lt;a href=&quot;http://socialscope.net&quot; rel=&quot;nofollow&quot;&gt;SocialScope&lt;/a&gt;"}],"max_id":5704386230,"since_id":5501341295,"refresh_url":"?since_id=5704386230&q=","next_page":"?page=2&max_id=5704386230&rpp=2&geocode=27.5916%2C86.564%2C100.0km&q=","results_per_page":2,"page":1,"completed_in":0.090181,"warning":"adjusted since_id to 5501341295 (2012-11-07 07:00:00 UTC), requested since_id was older than allowed -- since_id removed for pagination.","query":""}'''

	def handle_PEER(self, command):
		'''
		TODO DOCUMENTATION
		'''
		tokens = command.split()

		if not len(tokens) == 5:
			self.factory.logError('PEER command malformed, number of tokens =/= 5: {0}'.format(command))
			self.handle_unknown_command(command)
			return

		command_name, peer_name, protocol, host_name, port_number = tokens
		self.factory.logInfo('Parsed peer name: {0}'.format(peer_name))
		self.factory.logInfo('Parsed protocol: {0}'.format(protocol))
		self.factory.logInfo('Parsed host name: {0}'.format(host_name))

		try:
			port_number = int(port_number)
		except Exception as e:
			self.factory.logError('PEER command has malformed port number: {0}'.format(command))
			self.handle_unknown_command(command)
			return
		self.factory.logInfo('Parsed port number: {0}'.format(port_number))

		if self.factory.peers.has_key(peer_name):
			self.factory.logInfo('Peer already exists: {0}'.format(peer_name))
		else:
			self.factory.peers[peer_name] = (peer_name, protocol, host_name, port_number)
			self.factory.logInfo('Peer added: {0} {1} {2} {3} {4}'.format(self.factory.server_name, peer_name, protocol, host_name, port_number))

			self.factory.logInfo('Connecting with peer: {0}'.format(peer_name))
			end_point = None
			if protocol == 'tcp':
				end_point = TCP4ClientEndpoint(reactor, host_name, port_number)
				self.factory.logInfo('Endpoint created: {0!s}'.format(end_point))
			if not end_point == None:
				self.factory.logInfo('Connecting to peer: {0} {1} {2} {3}'.format(peer_name, protocol, host_name, port_number))
				connection = end_point.connect(self.factory)
				connection.addCallback(send_to_peer, 'PEER {0} tcp {1} {2}'.format(self.factory.server_name, self.factory.host_name, self.factory.port_number))

		self.factory.logInfo('Number of peers: {0}'.format(len(self.factory.peers.keys())))

	def handle_unknown_command(self, command):
		'''
		TODO DOCUMENTATION
		'''
		self.send_message('?')
	
	def send_message(self, message):
		'''
		TODO DOCUMENTATION
		'''
		self.sendLine(message)
		self.factory.logInfo('Sent message: {0}'.format(message))
		self.transport.loseConnection()

class SessionFactory(Factory):

	def __init__(self, server_name, host_name, port_number):
		'''
		TODO DOCUMENTATION
		'''
		self.server_name = server_name
		self.host_name = host_name
		self.port_number = port_number
		self.users = {}
		self.peers = {}
		self.log_stream = open('{0}_{1}.log'.format(self.server_name, datetime.datetime.utcnow().isoformat().replace(':', '_').replace('T', '_')), 'w')
		self.logInfo('Server opening.')
	
	def stopFactory(self):
		'''
		TODO DOCUMENTATION
		'''
		self.logInfo('Server closing.')
		self.log_stream.close()

	def buildProtocol(self, addr):
		'''
		TODO DOCUMENTATION
		'''
		self.logInfo('Protocol built for address: {0!s}'.format(addr))
		return Session(self)
	
	def logInfo(self, message):
		'''
		TODO DOCUMENTATION
		'''
		self._log('INFO: {0!s}'.format(message))
	
	def logWarning(self, message):
		'''
		TODO DOCUMENTATION
		'''
		self._log('WARNING: {0!s}'.format(message))
	
	def logError(self, message):
		'''
		TODO DOCUMENTATION
		'''
		self._log('ERROR: {0!s}'.format(message))
	
	def _log(self, message):
		'''
		TODO DOCUMENTATION
		'''
		message = '{0}: {1}: {2}'.format(self.server_name, datetime.datetime.utcnow().isoformat(), message)
		print(message)
		try:
			self.log_stream.write(message+'\n')
		except ValueError as e:
			print('Could not log to file, file stream has been closed.')

if __name__ == '__main__':
	assert(len(sys.argv) == 4)
	server_name = sys.argv[1]
	host_name = sys.argv[2]
	port_number = int(sys.argv[3])
	session_factory = SessionFactory(server_name, host_name, port_number)
	reactor.listenTCP(port_number, session_factory)
	reactor.run()

