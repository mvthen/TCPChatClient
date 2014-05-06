import sys
import time
import select
import socket

BLOCK_TIME = 60 
LAST_HOUR = 60*60
TIME_OUT = 20
online_users = []
socket_list = []
online_socket = dict()
content = dict()
timeout = dict()
time_online = dict()
blocked = dict()
offline_message = dict()


#open textfile and read into dict called content
with open('user_pass.txt') as file:
	for line in file:
		(key, val) = line.split()
		content[key]=val

#login method
def login(sock, addr):
	try:
		#prompts user for username
		incorrect = 1
		sock.send('Username: ')
		username = sock.recv(1024)
		newuser=username.split()
		mod_user = newuser[0]
		
		#checks if users are still timedout for 30 secs
		if mod_user in timeout:
			if addr[0] in timeout[mod_user]:
				current_time = time.time()
				total_time = current_time - timeout[mod_user][1]
				if total_time < BLOCK_TIME:
					timeout_message = 'You are still blocked. Please wait '+ str(round(60-(total_time), 2)) +' more seconds.\n\n'
					sock.send(timeout_message)	
					sock.send('Username: ')
					username = sock.recv(1024)
					newuser=username.split()
					mod_user = newuser[0]				
				
		#checks if users are already online or incorrect
		while((not content.has_key(newuser[0])) or (newuser[0] in online_users)):
			wrong_username = 'Incorrect or duplicate username, please try again: '
			sock.send(wrong_username)			
			username = sock.recv(1024)
			newuser=username.split()

		#prompts for password
		sock.send('Password: ')
		password = sock.recv(1024)
			
		#checks three times for passwords if incorrect	
		while (incorrect < 3):
			newpass=password.split()
			if not newpass[0] == content.get(newuser[0]):
				wrongpassword = 'Incorrect password, you have '+ str(3-incorrect) + ' attempt(s) left. Please try again: '
				incorrect +=1
				sock.send(wrongpassword)
				password = sock.recv(1024)
				newpass = password.split()
			else:
				#logged in successfully, adds users to several dictionaries
				sock.send("\nLogged in. Welcome to the simple chat server!\n")
				online_users.append(newuser[0])
				online_socket[newuser[0]] = sock

				logged = time.time()
				time_online[newuser[0]] = logged

				#checks if user had offline messages
				if newuser[0] in offline_message:
					sock.send('\n')
					for item in offline_message[newuser[0]]:
						sock.send(item)
					del offline_message[newuser[0]]

				incorrect=0
				sock.send('\nCommand: ')
				return True
			
		#timeout user if pass entered incorrectly three times
		if incorrect != 0:
			end = time.time()
			timeout[newuser[0]] = [addr[0], end]
			sock.close()
			return False
	except:
		sock.close()

#shows who else is online
def whoelse(sock):
	#gets current user from their socket
	currentuser = [key for (key, val) in online_socket.items() if val == sock]

	#sends who else is online based off of 'online_users' dictionary
	if len(online_users) == 1:
		sock.send('You are the only user online.\n')
	else:
		for socket in socket_list:
			if socket != serverSocket and socket != sock:
				for item in online_users:
					if item != currentuser[0]:
						sock.send(item)
						sock.send('\n')

	#update last time user was active
	current_time = time.time()
	time_online[currentuser[0]] = current_time
	sock.send('\nCommand: ')

#shows who else was online in the last hour
def wholasthr(sock):
	#find present time
	present = time.time()
	currentuser = [key for (key, val) in online_socket.items() if val == sock]
	current_time = time.time()
	time_online[currentuser[0]] = current_time
	#if time elapsed is less than 60 mins, send to user
	for key in time_online:
		elapsed = present - time_online[key]
		if elapsed < LAST_HOUR:
			if key != currentuser[0]:
				sock.send(key)
				sock.send('\n')

	sock.send('\nCommand: ')
	
#broadcasts messages to all users
def broadcast(sock, message):
	currentuser = [key for (key, val) in online_socket.items() if val == sock]
	#based on socketlist, send out message to everyone
	for socket in socket_list:
		if socket != serverSocket:
			socket.send(currentuser[0]+': '+message+'\n')
			socket.send('\nCommand: ')
	current_time = time.time()
	time_online[currentuser[0]] = current_time
	
#send private message to one user
def privatemessage(sock, message, user):
	currentuser = [key for (key, val) in online_socket.items() if val == sock]
	s = online_socket.get(user)

	current_time = time.time()
	time_online[currentuser[0]] = current_time

	#checks if recipient exists
	if user not in content:
		sock.send('Recipient does not exist. Please try again.\n')
		sock.send('\nCommand: ')
		return
	#checks if user is sending message to themselves
	if user == currentuser[0]:
		sock.send('You cannot send a private message to yourself.\n')
		sock.send('\nCommand: ')
		return
	#checks if recipient is blocking sender
	if user in blocked:
		if currentuser[0] in blocked[user]:
			sock.send('You cannot send any message to '+user+'. You have been blocked by the user.\n')
			sock.send('\nCommand: ')
			return
	#if recipient is not online, store message and recipient in dictionary until they login
	if user not in online_users:
		if user not in offline_message:
			offline_message[user] = [currentuser[0]+': '+message]
			sock.send('\nCommand: ')
			return
		else:
			(offline_message[user]).append(currentuser[0]+': '+message)
			sock.send('\nCommand: ')
			return
	
	s.send(currentuser[0]+': '+message+'\n')
	sock.send('\nCommand: ')

#blocks one user at a time from sending messages
def block(blocked_user, sock):
	blocked_peer = blocked_user.split()
	currentuser = [key for (key, val) in online_socket.items() if val == sock]
	mod_currentuser = currentuser[0]
	#checks if they are blocking themselves
	if blocked_peer[0] == currentuser[0]:
		sock.send('Error! You cannot block yourself.\n')
	#checks if current user is already blocked
	elif mod_currentuser not in blocked:
		blocked[mod_currentuser] = [blocked_peer[0]]
		sock.send('You have successfully blocked '+blocked_peer[0]+' from sending you messages.\n')
	else: 
		#checks if the user exists
		if not content.has_key(blocked_peer[0]):
			sock.send('Error! This user does not exist.\n')
		elif len(blocked[mod_currentuser]) == 0:
			# print blocked
			blocked[mod_currentuser] = [blocked_peer[0]]
			sock.send('You have successfully blocked '+blocked_peer[0]+' from sending you messages.\n')
		else:
			if blocked_peer[0] not in blocked[mod_currentuser]:
				(blocked[mod_currentuser]).append(blocked_peer[0])
				sock.send('You have successfuly blocked '+ blocked_peer[0] +' from sending you messages.\n')
			else:
				#checks if users are already blocked
				sock.send('You have already blocked ' + blocked_peer[0]+'.\n')

	sock.send('\nCommand: ')
	current_time = time.time()
	time_online[currentuser[0]] = current_time

#unblocks previously blocked users
def unblock(blocked_user, sock):
	blocked_peer = blocked_user.split()
	currentuser = [key for (key, val) in online_socket.items() if val == sock]
	mod_currentuser = currentuser[0]
	#unblocks user if they are in the 'blocked' dictionary
	if blocked_peer[0] in blocked[mod_currentuser]:
		(blocked[mod_currentuser]).remove(blocked_peer[0])
		sock.send('You have successfuly unblocked '+ blocked_peer[0] +' from sending you messages.\n')
		# print blocked
	else:
		#checks if user is originally blocked
		sock.send('You have not blocked ' + blocked_peer[0]+'.\n')
		print blocked

	current_time = time.time()
	time_online[currentuser[0]] = current_time
	sock.send('\nCommand: ')

#logs out users
def logout(sock):
	currentuser = [key for (key, val) in online_socket.items() if val == sock]
	#close socket
	sock.close()
	#remove from several dictionaries
	online_users.remove(currentuser[0])
	del online_socket[currentuser[0]]
	socket_list.remove(sock)

#main method
if __name__ == '__main__':

	#check number of arguments
	if (len(sys.argv) != 2):
		print ('Incorrect usage: python TCPServer.py <port>.')
		sys.exit()
	#takes in argument as port number and binds to a socket, then listens
	serverPort = int(sys.argv[1])
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind(('', serverPort))
	serverSocket.listen(50)
	socket_list.append(serverSocket)

	print 'The chat server is ready to receive messages on port ' + str(serverPort)
	
	while 1:
		#checks for active sockets
		read_soc, write_soc, error_sock = select.select(socket_list, [], [])

		#for each active socket, create connection and login
		for sock in read_soc:
			if sock == serverSocket:
					connectionSocket, addr = serverSocket.accept()
					boolean=login(connectionSocket, addr)
					if boolean:
						socket_list.append(connectionSocket)
			
			else:
				try:
					data = sock.recv(1024)
					#parse commands
					command = data.split(' ', 1)
					if command[0] == '\n':
						sock.send('')
						break
					if command[0] == 'broadcast':
						message = command[1]
						broadcast(sock, message)
						break
					if command[0] == 'block':
						blocked_user = command[1]
						block(blocked_user, sock)
						break
					if command[0] == 'unblock':
						blocked_user = command[1]
						unblock(blocked_user, sock)
						break
					command = data.split(' ', 2)
					if command[0] == 'message':
						if len(command) < 3:
							sock.send('Incorrect usage, please try again.')
							sock.send('\nCommand: ')
							break
						user = command[1]
						message = command [2]
						privatemessage(sock, message, user)
						break
					command=data.split()
					if command[0] == 'whoelse':
						whoelse(sock)
						break
					if command[0] == 'wholasthr':
						wholasthr(sock)
						break
					if command[0] == 'logout':
						sock.send('Logging out...')
						logout(sock)
						break
					
					sock.send('\nCommand not recognized, please try again: ')

				except:
					#catches exceptions
					currentuser = [key for (key, val) in online_socket.items() if val == sock]
					sock.close()
					online_users.remove(currentuser[0])
					del online_socket[currentuser[0]]
					socket_list.remove(sock)
					continue


	serverSocket.close()

