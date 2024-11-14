# import necessary libraries
from socket import *
import threading
from datetime import datetime
import json


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


    def run(self):
        """Start the server and listen for incoming connections"""

        # Bind socket to the specified host and port
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f'Server started on host {self.host}: port {self.port}')
    
        try:
            # Continuously accept new connections 
            while True:
                # Accept new connection
                client_socket, addr = self.socket.accept()
                print(f'New client connection from {addr}')

                # Add cleint socket to the clients list
                self.clients.append(client_socket)

                # Start new thread to handle client request
                threading.Thread(self.processRequest, args=(client_socket, addr))

    # NOTE: This keyboard interrupt method is not working... might have to implemetn a signal handler :(
        except KeyboardInterrupt:
            # Allow manual interruption for server shutdown
            print('\nKeyboard Interrupt: Shutting Server Down...')

        finally:
            # Close the socket when server shuts down
            self.socket.close()


    def processRequest(self, client_socket, addr):
        """Handle Client Requests"""

        try:
            # Recieve username sent by client and decode it
            username = client_socket.recv(1024).decode().strip()
            if not username: 
                client_socket.close() # close its socket if it doesn't send username
                return
            print(f'{username} connected')

            # Notify all clients in message board about new connection
            self.notify_all(f'{username} has joined the board', sender=None)
            
            # Send the last two messages in the board's history, if available
            for message in (self.messages[-2:] if len(self.messages) >= 2 else self.messages):
                client_socket.send(message.encode())

            # Continously recieve messages from the client
            while True:
                message = client_socket.recv(1024).decode().strip()

                # If the client sends the '%exit' command, break and disconnect
                if message == '%exit':
                    break

        # NOTE: This is probably where a function would be called to act on messages sent in the future
                # Add client's message to the boards history
                self.add_message(username, message)

                # Notify all in the board of the new message with the sender specified
                self.notify_all(f'{username}: {message}', sender=client_socket)

        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {addr}: {e}')

        finally:
            # Remove the client and close connection after exiting try block
            self.remove_client(client_socket, username)


    def notify_all(self, message, sender=None):
        """Broadcast message to all connected clients expect the specified sender"""

        # Iterate through each client (skipping the sender) and send the encoded message
        for client in self.clients:
            if client == sender: continue
            try: 
                client.send(message.encode())
            except Exception as e:
                print(f'Failed to send message to a client ({client}): {e}')
    

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


    def remove_client(self, client_socket, username=None):
        """Remove a client from the client list and close its connection"""

        # Remove the client socket from connected clients list and close the socket connection 
        self.clients.remove(client_socket)
        client_socket.close()

        # If there is a username, notify all (including the server) that <username> has left
        if username:
            self.notify_all(f'{username} has left the board')
            print(f'{username} disconnected')


if __name__ == "__main__":
    server = BulletinBoardServer('', 6789)
    server.run()