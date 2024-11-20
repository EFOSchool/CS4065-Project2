from socket import *
import threading
import json
from protocol import Protocol

class Client:
    

    def __init__(self):
        """Client constructor to set up host, port and socket"""

        # Initialize all variables to None type as they will be defined in the connect command
        self.host = None
        self.port = None
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.username = None
        self.running = True


    def run(self):
        """
        Prompt the user to input the connection details and establishes a connection to the server.
        NOTE: The default serve connect is addr = 'localhost' and port 6789
        """

        # Get the user input to establish a connection and ensure the input follows the correct format for connection
        user_in = input('>> ')
        while not user_in.startswith('%connect') or len(user_in.split()) != 3:
            print('ERROR: Must establish connection using the format, %connect <addr> <port>, before doing anything else')
            user_in = input('>> ')
        
        # Split the input and extract the server address and port number 
        parts = user_in.split()
        addr = parts[1]
        port = int(parts[2])

        # Establish connection with the specified address adn port
        client.connect(addr, port)
    
    def connect(self, host, port):
        """Connect to the bulletin board server"""

        try:
            # Set host and port for the connection
            self.host = host
            self.port = port

            # Establish connection to the server
            self.socket.connect((self.host, self.port))
            print(f'Connected to the server at {self.host}: port {self.port}')

            # Start a thread to listen for incoming messages from the server
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            # Send username to the server
            self.username = input("Enter your username: ")
            conncetion_request = Protocol.build_request('connect', self.username)
            self.socket.send(conncetion_request.encode())

            # Start sending messages
            self.send_messages()

        except Exception as e:
            print('Problem connecting and interacting with the server. Make sure it is running')
            print(f'Error encountered: {e}')
        
        finally:
            self.socket.close() # Close the socket connection when done

    
    def receive_messages(self):
        """Listen for incoming messages from the server"""

        # Buffer to hold incomplete messages
        buffer = ""

        while self.running:
            try:
                # Receive a message from the server
                data = self.socket.recv(1024).decode()
                if not data:
                    continue

                buffer += data
                while '\n' in buffer:
                    # Split the buffer at the newline character
                    message, buffer = buffer.split('\n', 1)

                    # If a message exist, evaluate it to determine what actions to take
                    if message:
                        # Convert from the JSON string to a dictionary
                        message_dict = json.loads(message)

                        # Safely grab the header and body dictionaries within the read message
                        header = message_dict.get('header')
                        body = message_dict.get('body')

                        # If a status value exists in the header, a response has been read, handle accordingly
                        if header.get('status'):
                            # Safely grab the command and status values
                            command = header.get('command')
                            status = header.get('status')

                            # Display to the client the response (OK or FAIL) to their request
                            print(f"\r'{command}' Response: {status}\n>> ", end='')

                            # If the response is for the connect command, data will contain the last 2 messages in the group joined
                            if command == 'connect':
                                data = body.get('data')
                                print(f'\r{data}\n>> ', end='')

                        # If the command is 'notify all' (a broadcast signal) display the message it contains in data
                        elif header.get('command') == 'notify all':
                            message = body.get('data')
                            if message:
                                print(f'\r{message}\n>> ', end='')

            except Exception as e:
                # Only through an error if the client is still running
                # This is added to address that recieve messages will still be running when the socket closes
                if self.running:
                    print('Error receiving message or connection to the server may have been lost')
                    print(f'Error encountered: {e}')
                break

    
    def send_messages(self):
        """Prompt user and send messages to the server"""

        try:
            while True:
                # Prompt for user input and send the message 
                message = input('>> ')

                # If the user types '%exit', send it to the server and break the loop
                if message == '%exit':
                    message = Protocol.build_request('exit', self.username)
                    self.socket.send(message.encode())
                    break

                # Otherwise, send the typed message to the server
                message = Protocol.build_request('message', self.username, message)
                self.socket.send(message.encode())

        except KeyboardInterrupt:
            print('\nExiting...')
            message = Protocol.build_request('exit', self.username)
            self.socket.send(message.encode()) # Send exit command to server

        finally:
            self.shutdown()

    def shutdown(self):
        """Clean up resources and stop the client."""
        # Set the class flag of whether the server is running or not to False
        self.running = False

        try:
            # Close the socket
            self.socket.close()
            print("Disconnected from the server.")
        except Exception as e:
            print(f"Error during shutdown: {e}")


if __name__ == "__main__":
    # Initialize the client object and run it
    client = Client()        
    client.run()