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
        self.board_users = []

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
                try:
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
                        self.handle_join(client_socket, username)
                    
                    # Handle the message command
                    elif command == 'message':
                        self.client_message(client_socket, username, data)
                        if not username or not data:
                            continue

                    # Handle the leave command
                    elif command == 'leave':
                        self.handle_leave(client_socket, username)

                    # Handle the exit command
                    elif command == 'exit':
                        self.client_exit(client_socket, username)
                        return

                    else:
                        # Respond with an error for unrecognized commands
                        response = Protocol.build_response(command, "FAIL", "Unknown command.")
                        client_socket.send((response + '\n').encode())

                except ConnectionResetError:
                    print(f'Connection reset by {addr}')
                    break

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
            
            # Respond with a success message to the client
            response = Protocol.build_response("connect", "OK", "Connected successfully")
            client_socket.send((response + '\n').encode())
        
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("connect", "FAIL")
            client_socket.send((response + '\n').encode())

    def handle_join(self, client_socket, username):
        if username in self.board_users:
            response = Protocol.build_response("join", "FAIL", "User already in the board.")
        else:
            self.board_users.append(username)
            response = Protocol.build_response("join", "OK", f"{username} joined the message board.")
            
            # Notify all connected clients about the new user
            self.notify_board(f"{username} has joined the message board.", username)

            # Send the last two messages in the board's history, if available
            if len(self.messages) > 0:
                history_data = []
                for message in (self.messages[-2:] if len(self.messages) >= 2 else self.messages):
                    history_data.append(message)
                response = Protocol.build_response("join", "OK", history_data)
            else:
                response = Protocol.build_response("join", "OK", "There are no messages on the board yet.")
        
        # Send the response to the client
        client_socket.send((response + '\n').encode())
    
    def client_message(self, client_socket, username, data):
        try:
            # Check for valid data and return fail if not
            if not username or not data:
                response = Protocol.build_response("message", "FAIL")
                client_socket.send((response + '\n').encode())

            # Add client's message to the board's history
            self.add_message(username, data)

            # Notify all in the board of the new message with the sender specified
            self.notify_all(f'{username}: {data}', username, sender=client_socket)

            # Send Response
            response = Protocol.build_response("message", "OK")
            client_socket.send((response + '\n').encode())

        # Send Bad Response
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("message", "FAIL")
            client_socket.send((response + '\n').encode())

    def handle_leave(self, client_socket, username):
        """Handle the leave command."""
        if username not in self.board_users:
            response = Protocol.build_response("leave", "FAIL", "User not in the board.")
        else:
            # Notify only remaining users in the board
            self.notify_board(f"{username} has left the message board.", username)
            
            # Remove the user from the board_users list
            self.board_users.remove(username)
            
            response = Protocol.build_response("leave", "OK", f"{username} left the message board.")

        # Send the response to the client    
        client_socket.send((response + '\n').encode())
    
    def client_exit(self, client_socket, username=None):
        """Remove a client from the client list and close its connection after recieving exit command"""

        try:
            # Notify all connected clients about the user exiting the server
            if username:
                self.notify_all(f'{username} has disconnected from the server.', username)

            # Log disconnection and send a response
            print(f'{username} disconnected')

            # Send a success response to the client for the exit command
            response = Protocol.build_response("exit", "OK")
            client_socket.send((response + '\n').encode())

            # Remove the client socket from connected clients list
            if client_socket in self.clients:
                self.clients.remove(client_socket)

            # Remove the user from the board_users list if still present
            if username in self.board_users:
                self.board_users.remove(username)

            # Close down the socket
            client_socket.close()
            
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("exit", "FAIL")
            client_socket.send((response + '\n').encode())


    def notify_all(self, message, username=None, sender=None):
        """Broadcast message to all connected clients except the sender."""
        notification_payload = Protocol.build_request("notify all", username, message)
        encoded_message = (notification_payload + '\n').encode()

        # Send to all clients except the sender
        for client in self.clients:
            if client == sender:
                continue
            try:
                client.send(encoded_message)
            except Exception as e:
                print(f"Failed to send message to a client ({client}): {e}")
    

    def notify_board(self, message, username=None, sender=None):
        """Broadcast message to all connected clients who are part of the message board."""
        notification_payload = Protocol.build_request("notify all", username, message)
        encoded_message = (notification_payload + '\n').encode()

        # Iterate through clients in board_users to ensure correct filtering
        for client in self.clients:
            # Skip the sender or clients not in `board_users`
            if client == sender:
                continue
            try:
                client.send(encoded_message)
            except Exception as e:
                print(f"Failed to send message to a client ({client}): {e}")


    def add_message(self, sender, message):
        """Add message to the server's message history"""

        # Get the current timestamp and format into a readable form
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create a dictionary (that will be converted to JSON) to represent the message
        formatted_message = {
            'id': len(self.messages) + 1,
            'sender': sender,
            'timestamp': timestamp,
            'message': message
        }

        # Convert the dictionary to JSON-formatted string and append to message history
        self.messages.append(json.dumps(formatted_message))


if __name__ == "__main__":
    server = BulletinBoardServer('', 6789)
    server.run()