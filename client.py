from socket import *
import threading
import json
import re
from time import sleep
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
        self.connect(addr, port)
    
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
                            if command == 'join' and status == 'OK':
                                # Display join confirmation
                                data = body.get('data')
                                print(f'\r{data}\n>> ', end='')
                            
                            elif command == 'history' and status == 'OK':
                                # Display the message history or "no messages" notice
                                data = body.get('data')
                                if isinstance(data, list):  # Display the last two messages if available
                                    for msg in data:
                                        print(f'\rMessage ID: {msg["id"]}, Sender: {msg["sender"]}, '
                                            f'Time Posted: {msg["timestamp"]}, Subject: {msg["subject"]}\n>> ', end='')
                                else:
                                    print(f'\r{data}\n>> ', end='')

                            elif command == 'leave' and status == 'OK':
                                data = body.get('data')
                                print(f'\r{data}\n>> ', end='')

                            if command == 'exit' and status == 'OK':
                                print('\rShutting down client...')
                                self.shutdown()
                                break

                        # If the command is 'notify all' (a broadcast signal) display the message it contains in data
                        elif header.get('command') == 'notify all':
                            message = body.get('data')
                            if message:
                                print(f'\r{message}\n>> ', end='')

                        # Handle 'notify board' for messages visible only to board participants
                        elif header.get('command') == 'notify board':
                            message = body.get('data')
                            if message:
                                print(f'\r[Board] {message}\n>> ', end='')

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
            while self.running:
                # Prompt for user input and send the message 
                message = input('>> ')

                if message.startswith('%join'):
                    join_request = Protocol.build_request('join', self.username)
                    self.socket.send(join_request.encode())

                elif message.startswith('%leave'):
                    leave_request = Protocol.build_request('leave', self.username)
                    self.socket.send(leave_request.encode())
                
                # If the user types '%exit', send it to the server and break the loop
                elif message == '%exit':
                    message = Protocol.build_request('exit', self.username)
                    self.socket.send(message.encode())
                    sleep(.1) # Short wait to allow for server and client to handle request/response before ending
                    break

                # If the user's prompt starst with '%post', call the post_helper method to handle it
                elif message.startswith('%post'):
                    self.post_helper(message)

                # # Otherwise, send the typed message to the server
                # message = Protocol.build_request('message', self.username, message)
                # self.socket.send(message.encode())

        except Exception as e:
            print(f'Error sending message "{message}: {e}')

        # except KeyboardInterrupt:
        #     print('\nExiting...')
        #     message = Protocol.build_request('exit', self.username)
        #     self.socket.send(message.encode()) # Send exit command to server


    def post_helper(self, message):
        """Helper function to format data passed in post command into a request"""
        """
            Example command format:
                >> %post "Hello Everyone" "I am a new user"
        """
        # Regular expression to capture quoted parts (subject and content)
        # This will handle quoted strings like "Hello Everyone" and "I am a new user"
        match = re.match(r'%post\s+"([^"]+)"\s+"([^"]+)"', message)

        if not match:
            print("Invalid message format")
            return  # or handle error as needed

        # Extract the subject and content from the match
        subject = match.group(1)
        content = match.group(2)
        
        # Build the data field where the subject and content is seperated by a newline
        data = f'{subject}\n{content}'

        # Build the request for the post command and send to server
        request = Protocol.build_request('post', self.username, data)
        self.socket.send(request.encode())


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