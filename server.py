# import necessary libraries
from socket import *
import threading
from datetime import datetime
import json
import signal
from protocol import Protocol


class BulletinBoardServer(threading.Thread):
    

    def __init__(self, host='localhost', port=6789):
        """Bulletin Board Server Constructor"""

        # Initialize the thread 
        super().__init__()
        self.daemon = True

        # Initialize host and port for the server
        self.host = host
        self.port = port

        # Create a socket using IPv4 (AF_INET) and TCP (SOCK_STREAM)
        self.socket = socket(AF_INET, SOCK_STREAM)

        # Initialize bulletin board specific lists
        self.clients = []
        self.messages = []
        self.message_board_clients = []
        self.default_board_users = []

        # Boolean flag to help gracefully shutdown server with SIGINT
        self.running = True


    def signal_handler(self, signum, frame):
        """Handle termination signals to stop the server gracefully"""

        print('\nReceived termination signal. Gracefully shutting down the server...')

        # Set flag to stop server loop
        self.running = False

        # Close all client connections
        for client in self.clients:
            client.close()


    def run(self):
        """Start the server and listen for incoming connections"""

        # Bind socket to the specified host and port
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f'Server started on host {self.host}: port {self.port}')

        # Register the signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
    
        try:
            # Continuously accept new connections 
            while self.running:
                # Set a timeout for a non-blocking behavior 
                self.socket.settimeout(1) 

                try:
                    # Accept new connection
                    client_socket, addr = self.socket.accept()
                    print(f'New client connection from {addr}')

                    # Add cleint socket to the clients list
                    self.clients.append(client_socket)

                    # Start new thread to handle client request
                    client_thread = threading.Thread(target=self.processRequest, args=(client_socket, addr))
                    client_thread.start()

                except timeout:
                    # Continue the loop if the a timeout is hit
                    continue
        
        except Exception as e:
            # Display if any error occurs in server loop
            print(f'Server Error: {e}')

        finally:
            # Before exiting out of the server loop completely, close down the server socket
            self.socket.close()


    def processRequest(self, client_socket, addr):
        """Handle Client Requests"""

        # Initialize username to None
        username = None

        try:
            # Continuously receive messages from the client
            while True:
                # Receive and decode the message from the client
                message = client_socket.recv(1024).decode().strip()
                if not message:
                    continue

                # Parse the message using the Protocol class
                request = json.loads(message)
                header = request.get('header')
                command = header.get('command')
                username = header.get('username')
                body = request.get('body')
                data = body.get('data')

                # Handle the connect command
                if command == 'connect':
                    self.client_connection(client_socket, username)
                    if not username:
                        return

                # Handle the join command
                elif command == 'join':
                    self.client_join(client_socket, username)

                # Handle the post command
                elif command == 'post':
                    self.client_post(client_socket, username, data)
                    if not username or not data:
                        continue
                    
                # Handle the users command
                elif command == 'users':
                    self.get_users(client_socket)

                # Handle the leave command
                elif command == 'leave':
                    self.client_leave(client_socket, username)

                # Handle the exit command
                elif command == 'exit':
                    self.client_exit(client_socket, username)
                    return
                    
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {addr}: {e}')

    
    def client_connection(self, client_socket, username):
        # If there is not a username then a failure occurs
        if not username:
            response = Protocol.build_response("connect", "FAIL")
            client_socket.send((response + '\n').encode())
            client_socket.close()
            return

        try:
            # Display that a user has connected
            print(f'{username} connected')

            # Notify all clients in message board about new connection
            self.notify_all(f'{username} has joined the board')
            
            # Send the last two messages in the board's history, if available
            if len(self.messages) > 0:
                history_data = []
                for message in (self.messages[-2:] if len(self.messages) >= 2 else self.messages):
                    history_data.append(message)
                # Build Repsonse
                response = Protocol.build_response("connect", "OK", history_data)
            else:
                # Build Response for no messages being on board
                response = Protocol.build_response("connect", "OK", "There are no messages on the board yet")

            # Send Response
            client_socket.send((response + '\n').encode())
        
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("connect", "FAIL")
            client_socket.send((response + '\n').encode())

    
    def client_join(self, client_socket, username):
        """Handle a client joining the message board."""
        if client_socket in self.message_board_clients:
            response = Protocol.build_response("join", "FAIL", "You are already on the message board.")
            client_socket.send((response + '\n').encode())
            return

        # Add the client to the message board list
        self.message_board_clients.append(client_socket)
        print(f"{username} joined the message board.")
        
        # Add the username to the default board users list
        self.default_board_users.append(username)

        # Notify the client that they have joined
        join_confirmation = Protocol.build_response("join", "OK", "You have joined the message board.")
        client_socket.send((join_confirmation + '\n').encode())

        # Send the last two messages in the message history
        if len(self.messages) > 0:
            history_data = [json.loads(msg) for msg in (self.messages[-2:] if len(self.messages) >= 2 else self.messages)]
            response = Protocol.build_response("history", "OK", history_data)
        else:
            response = Protocol.build_response("history", "OK", "There are no messages on the board yet.")
        client_socket.send((response + '\n').encode())

        # Notify others on the board
        self.notify_board(f"{username} has joined the message board.", sender=client_socket)


    def client_post(self, client_socket, username, data):
        """Add the post to the history and notify all that a message has been posted"""
        try:
            # Check for valid data and return fail if not
            if not username or not data:
                response = Protocol.build_response("message", "FAIL")
                client_socket.send((response + '\n').encode())

            # Grab the subject and message out of data field
            # The subject and content are seperated by a newline in the data field
            parts = data.split('\n', 1) # split on first instance of \n

            if len(parts) < 2:
                # If the split doesn't result in both a subject and content, it's invalid
                response = Protocol.build_response("post", "FAIL")
                client_socket.send((response + '\n').encode())
                return
            
            # Now that the subject and message are separated they get stored in subject and message variables
            subject, message = parts[0], parts[1]

            # Check if both subject and message are non-empty
            if not subject or not message:
                response = Protocol.build_response("post", "FAIL")
                client_socket.send((response + '\n').encode())
                return

            # Add client's message to the board's history
            message_id, timestamp = self.add_message(username, subject, message)

            # Notify all in the board of the new message with the sender specified
            self.notify_all(f'Message ID: {message_id}, Sender: {username}, Time Posted: {timestamp}, Suject {subject}')

            # Send Response
            response = Protocol.build_response("message", "OK")
            client_socket.send((response + '\n').encode())

        # Send Bad Response
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("message", "FAIL")
            client_socket.send((response + '\n').encode())


    def client_leave(self, client_socket, username):
        """Handle a client leaving the message board."""
        if client_socket not in self.message_board_clients:
            response = Protocol.build_response("leave", "FAIL", "You are not on the message board.")
            client_socket.send((response + '\n').encode())
            return

        # Remove the client from the message board list
        self.message_board_clients.remove(client_socket)
        print(f"{username} left the message board.")
        
        # Remove the username from the default board list
        self.default_board_users.remove(username)

        # Notify the leaving client
        response = Protocol.build_response("leave", "OK", "You have left the message board.")
        client_socket.send((response + '\n').encode())

        # Notify others on the board
        self.notify_board(f"{username} has left the message board.", sender=client_socket)

    
    def client_exit(self, client_socket, username=None):
        """Remove a client from the client list and close its connection after recieving exit command"""
        try:
            # If there is a username, notify all (including the server) that <username> has left
            if username:
                self.notify_all(f'{username} has left the board', sender=client_socket)
                print(f'{username} disconnected')

            # Send a success response to the client for the exit command
            response = Protocol.build_response("exit", "OK")
            client_socket.send((response + '\n').encode())

            # Remove the client socket from connected clients list
            self.clients.remove(client_socket)

            # Close down the socket
            client_socket.close()
            
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("exit", "FAIL")
            client_socket.send((response + '\n').encode())


    def notify_board(self, message, sender=None):
        """Broadcast a message to users on the message board."""
        notification_payload = Protocol.build_request("notify board", data=message)
        encoded_message = (notification_payload + '\n').encode()
        for client in self.message_board_clients:
            if client == sender:
                continue
            try:
                client.send(encoded_message)
            except Exception as e:
                print(f"Failed to send message to a client on the board ({client}): {e}")


    def notify_all(self, data, sender=None):
        """Broadcast message to all connected clients except the sender."""
        notification_payload = Protocol.build_request("notify all", data=data)
        encoded_message = (notification_payload + '\n').encode()

        # Iterate through each client and send the encoded message
        for client in self.clients:
            if client == sender: 
                continue
            try: 
                client.send(encoded_message)
            except Exception as e:
                print(f'Failed to send message to a client ({client}): {e}')
    

    def add_message(self, sender, subject, message):
        """Add message to the server's message history"""

        # Get the current timestamp and format into a readable form
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create a dictionary (that will be converted to JSON) to represent the message
        formatted_message = {
            'id': len(self.messages) + 1,
            'sender': sender,
            'timestamp': timestamp,
            'subject': subject,
            'message': message
        }

        # Convert the dictionary to JSON-formatted string and append to message history
        self.messages.append(json.dumps(formatted_message))

        return formatted_message['id'], timestamp

    def get_users(self, client_socket):
        """ 
            Retrieve a list of users in the same group.
            This is for Part 1, where we assume everyone is in 
            the same (default) group.
        """
                
        try:
            # Check if the client is in the message board clients list
            if client_socket not in self.message_board_clients:
                response = Protocol.build_response("users", "FAIL", "Current user is not in a message board.")
                client_socket.send((response + '\n').encode())
                return
            
            # format response
            user_list = ', '.join(self.default_board_users)
            
            # build response from users global list
            response = Protocol.build_response("users", "OK", user_list)
            
            # send response
            client_socket.send((response + '\n').encode())
            
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling users request from FIX THIS: {e}')
            
            # send a failure response
            response = Protocol.build_response("users", "FAIL")
            client_socket.send((response + '\n').encode())
            
        

if __name__ == "__main__":
    server = BulletinBoardServer('', 6789)
    server.run()