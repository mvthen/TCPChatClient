import sys
import select
import socket
import threading
import time

#not_active method, used in thread for timeout of inactive users
def not_active(sock):
	#cancel thread, logout, close system
	time_method.cancel()
	sock.send('logout')
	sys.exit


if __name__ == '__main__':
	
	if (len(sys.argv) != 3):
			print ('Incorrect usage: python TCPClient.py <ip> <port>.')
			sys.exit()

	TIME_OUT = 30*60

	#takes in ip address and port number as arguments, binds and connections
	serverName = sys.argv[1]
	serverPort = int(sys.argv[2])
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientSocket.connect((serverName, serverPort))
	logged_in = False

	while 1:

		socket_list=[sys.stdin, clientSocket]
		read_soc, write_soc, error_sock = select.select(socket_list, [], [])
		
		for sock in read_soc:
			try: 
				#checks if unique connection to server has been made
				if sock == clientSocket:
					response = clientSocket.recv(1024)
					#checks if disconnected
					if not response:
						print 'Disconnected from chat server.\n'
						time_method.cancel()
						sys.exit()				
					else:
						#checks if logged in, starts inactive timer
						if 'Logged in. Welcome to the simple chat server!\n' in response:
							print response
							logged_in=True
							time_method = threading.Timer(TIME_OUT, not_active, [clientSocket])
							time_method.start()

						else:
							print response

				else:
					#sends response back to server
					respond_back = sys.stdin.readline()
					clientSocket.send(respond_back)
					#everytime response is sent back, reset timer
					if logged_in == True:
						time_method.cancel()
						time_method = threading.Timer(TIME_OUT, not_active, [clientSocket])
						time_method.start()

			except:
				#catches exceptions gracefully
				# time_method.cancel()
				clientSocket.send('logout')
				sys.exit()

	clientSocket.close()