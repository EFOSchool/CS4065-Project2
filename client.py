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
        # Print Welcome Message
        welcome_message = \
        """
        Welcome to the Bulletin Board Client-Side.
        Use '%connect <addr> <port>' to connect to the server.
        The default <addr> is 'localhost' and the <port> is '6789'.
        Type '%help' to see a list of commands.
        """
        print(welcome_message)

        while True:
            # Get the user input to establish a connection and ensure the input follows the correct format for connection
            user_in = input('>> ').strip()
            if user_in.startswith('%connect') and len(user_in.split()) == 3:
                # Split the input and extract the server address and port number 
                parts = user_in.split()
                addr = parts[1]
                port = int(parts[2])

                # Establish connection with the specified address adn port
                self.connect(addr, port)
                break  # Exit loop once connection is successful
            
            else:   
                print('ERROR: Must establish connection using the format, %connect <addr> <port>, before doing anything else')
            
    
    def connect(self, host, port):
        """Connect to the bulletin board server"""

        try:
            while True: # Loop until a valid connection is established
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
                connection_request = Protocol.build_request('connect', self.username)
                self.socket.send(connection_request.encode())

                # Wait for the server's response
                response = self.socket.recv(1024).decode().strip()
                if response:
                    response_dict = json.loads(response)
                    status = response_dict['header'].get('status')
                    message = response_dict['body'].get('data')

                    if status == 'OK':
                        print("Successfully connected to the server!")
                        break  # Exit the loop if the connection is successful
                    elif status == 'FAIL':
                        print(f"FAILURE: {message}")
                        self.socket.close()  # Close the socket and restart the process
                        self.socket = socket(AF_INET, SOCK_STREAM)
                else:
                    print("No response from the server. Retrying...")
                    self.socket.close()
                    self.socket = socket(AF_INET, SOCK_STREAM)

            # Start sending messages after successful connection
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
                            data = body.get('data')

                            # Display to the client the response (OK or FAIL) to their request
                            # print(f"\r'{command}' Response: {status}\n", end='')

                            # If the response is a failure output the message
                            if status == 'FAIL':
                                # Display Error Message from the Server
                                print(f'\rFAILURE: {data}\n', end='')

                            # # If the response is for the connect command, data will contain the last 2 messages in the group joined
                            # if command == 'join' and status == 'OK':
                            #     # Display join confirmation
                            #     print(f'\r{data}\n>> ', end='')
                            
                            elif command == 'history':
                                # Display the message history or "no messages" notice
                                if isinstance(data, list):  # Display the last two messages if available
                                    print('Last two messages:')
                                    for msg in data:
                                        print(f'\rMessage ID: {msg["id"]}, Sender: {msg["sender"]}, '
                                            f'Time Posted: {msg["timestamp"]}, Subject: {msg["subject"]}\n>> ', end='')
                                else:
                                    print(f'\r{data}\n>> ', end='')
                                    
                            # elif command == 'users':
                            #     # Display the list of users/error message if available
                            #     print(f'\r{data}\n>> ', end='')
                                
                            # elif command == 'message':
                            #     # Display the message requested by the user
                            #     print(f'\r{data}\n>> ', end='')

                            # elif command == 'leave' and status == 'OK':
                            #     print(f'\r{data}\n>> ', end='')

                            # elif command == 'groups' and status == 'OK':
                            #     print(f'\r{data}\n>> ', end='')
                                
                            # elif command == 'groupusers':
                            #     # Display the list of users in the group or error is available
                            #     print(f'\r{data}\n>> ', end='')
                            
                            # elif command == 'groupmessage':
                            #     # Display the message requested by the user (group specific)
                            #     print(f'\r{data}\n>> ', end='')

                            elif command == 'exit':
                                # Shutdown the Client Side
                                print('\rShutting down client...')
                                self.shutdown()
                                break

                            elif data:
                                # Display the data contained in the response 
                                print(f'\r{data}\n>> ', end='')

                        # If the command is 'notify' (a broadcast signal) display the message it contains in data
                        elif header.get('command') == 'notify':
                            message = body.get('data')
                            message = message.replace('\\n', '\n')
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
            while self.running:
                # Prompt for user input and send the message 
                message = input('>> ')

                if not message:
                    continue  # Ignore empty input

                if message.startswith('%join'):
                    join_request = Protocol.build_request('join', self.username)
                    self.socket.send(join_request.encode())

                elif message.startswith('%groupjoin'):
                    group_name = message.split(maxsplit=1)[1].strip('"').strip("'")
                    join_request = Protocol.build_request('groupjoin', self.username, group=group_name)
                    self.socket.send(join_request.encode())

                elif message.startswith('%groupleave'):
                    group_name = message.split(maxsplit=1)[1].strip('"').strip("'")
                    leave_request = Protocol.build_request('groupleave', self.username, group=group_name)
                    self.socket.send(leave_request.encode())

                elif message.startswith('%leave'):
                    leave_request = Protocol.build_request('leave', self.username)
                    self.socket.send(leave_request.encode())
                    
                elif message.startswith('%users'):
                    users_request = Protocol.build_request('users', self.username)
                    self.socket.send(users_request.encode())
                    
                elif message.startswith('%message'):
                    parts = message.split()
                    if len(parts) < 2:
                        print("ERROR: Must use the format, %message <message_id>")
                    else:
                        # build protocol with the ID given by the user
                        message_id = message.split()[1]
                        message_request = Protocol.build_request('message', self.username, data=message_id)
                        self.socket.send(message_request.encode())
                
                # If the user types '%exit', send it to the server and break the loop
                elif message == '%exit':
                    message = Protocol.build_request('exit', self.username)
                    self.socket.send(message.encode())
                    sleep(.1) # Short wait to allow for server and client to handle request/response before ending
                    break

                # If the user's prompt starst with '%post', call the post_helper method to handle it
                elif message.startswith('%post'):
                    self.post_helper(message)

                # If the user types '%groups', send it to the server
                elif message == '%groups':
                    message = Protocol.build_request('groups')
                    self.socket.send(message.encode())

                # If the user's prompt starst with '%post', call the post_helper method to handle it
                elif message.startswith('%grouppost'):
                    self.post_helper(message, group=True)
                    
                # find users based on groups
                elif message.startswith('%groupusers'):
                    parts = message.split(' ', 1)
                    # Prevent formatting issues
                    if len(parts) < 2:
                        print("ERROR: Must use the format, %groupusers <group>")
                    else:
                        group = parts[1]
                        groupusers_request = Protocol.build_request('groupusers', username=self.username, group=group)
                        self.socket.send((groupusers_request + '\n').encode())
                    
                # find message based on groups and an ID
                elif message.startswith('%groupmessage'):
                    match = re.match(r'%groupmessage\s+"([^"]+)"\s+(\d+)', message)
                    if not match:
                        print("ERROR: Must use the format, %groupmessage <group> <message_id>")
                    else:
                        group = match.group(1)
                        message_id = match.group(2)
                        groupmessage_request = Protocol.build_request('groupmessage', username=self.username, group=group, data=message_id)
                        self.socket.send((groupmessage_request + '\n').encode())

                elif message == '%help':
                    self.help()

                else:
                    print("ERROR: Unknown command. Type '%help' for the list of available commands.")

        except Exception as e:
            print(f'Error sending message "{message}: {e}')

        except KeyboardInterrupt:
            print('\nExiting...')
            message = Protocol.build_request('exit', self.username)
            self.socket.send(message.encode()) # Send exit command to server
            sleep(.1) # Short wait to allow for server and client to handle request/response before ending


    def post_helper(self, message, group=False):
        """Helper function to format data passed in post command into a request"""
        """
            Example post command format:
                >> %post "Hello Everyone" "I am a new user"
                
            Example grouppost command format:
                >> %grouppost "group four" "Hello Everyone" "I am a new user"
        """

        if not group:
            try:
                # Regular expression to capture quoted parts (subject and content)
                # This will handle 2 quoted strings like "Hello Everyone" and "I am a new user"
                post_match = re.match(r'%post\s+"([^"]+)"\s+"([^"]+)"', message)

                # Extract the subject and content from the match
                subject = post_match.group(1)
                content = post_match.group(2)
                
                # Build the data field where the subject and content is seperated by a newline
                data = f'{subject}\n{content}'
            
            except:
                # If any of the above fails, likely invalid input
                print('ERROR: Must use the format, %post "<subject>" "<content>"')

            # Build the request for the post command and send to server
            request = Protocol.build_request('post', self.username, data=data)
            self.socket.send(request.encode())

        elif group:
            try:
                # Regular expression to capture quoted parts (subject and content)
                # This will handle 3 quote strings like "Group Four", "Hello Everyone", and "I am a new user"
                grouppost_match = re.match(r'%grouppost\s+"([^"]+)"\s+"([^"]+)"\s+"([^"]+)"', message)

                # Extract the subject and content from the match
                group = grouppost_match.group(1)
                subject = grouppost_match.group(2)
                content = grouppost_match.group(3)
                
                # Build the data field where the subject and content is seperated by a newline
                data = f'{subject}\n{content}'
            
            except:
                # If any of the above fails, likely invalid input
                print('ERROR: Must use the format, %grouppost "<group>" "<subject>" "<content>"')

            # Build the request for the post command and send to server
            request = Protocol.build_request('grouppost', self.username, group, data)
            self.socket.send(request.encode())

        else:
            # Something with the message format was wrong, let the user know
            print('Invalid message format, make sure it is:\n- %post "<subject>" "<content>"\n\tOR\n-%grouppost "<group>" "<subject>" "<content>"')
            return
        
    
    def help(self):
        """Display a help menu"""
        help_menu = \
        """
        Available Commands:

        - %connect <addr> <port>
        Connect to a server at the specified address and port.

        - %post "<subject>" "<content>"
        Post a message to the main bulletin board.

        - %grouppost "<group>" "<subject>" "<content>"
        Post a message to a specific group.

        - %join
        Join the main bulletin board.

        - %groupjoin "<group>"
        Join a specific group.

        - %leave
        Leave the main bulletin board.

        - %groupleave "<group>"
        Leave a specific group.

        - %groups
        List all available groups.

        - %users
        Show all users in the main bulletin board.

        - %groupusers <group>
        Show all users in a specific group.

        - %message "<message id>"
        View details of a specific message in the main bulletin board.

        - %groupmessage "<group>" "<message id>"
        View details of a specific message in a group.

        - %exit
        Exit the client application.
        """
        print(help_menu)


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