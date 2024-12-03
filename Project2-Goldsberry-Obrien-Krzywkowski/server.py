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
        self.messages = \
            {
                "public board": [],
                "group one": [],
                "group two": [],
                "group three": [],
                "group four": [],
                "group five": []
            }
        self.message_board_clients = []
        self.message_board_users = []
        self.private_group_clients = \
            {
                "group one": [],
                "group two": [],
                "group three": [],
                "group four": [],
                "group five": []
            }
        self.private_group_users = \
            {
                "group one": [],
                "group two": [],
                "group three": [],
                "group four": [],
                "group five": []
            }

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
                
                # print(f"Received message from {addr}: {message}")  # Debug log

                # Parse the message using the Protocol class
                try:
                    request = json.loads(message)
                    header = request.get('header')
                    command = header.get('command')
                    username = header.get('username')
                    group = header.get('group')
                    body = request.get('body')
                    data = body.get('data')

                except json.JSONDecodeError:
                    # Invalid JSON sent by the client
                    response = Protocol.build_response("error", "FAIL", "Invalid request format.")
                    client_socket.send((response + '\n').encode())
                    continue

                # Handle the connect command
                if command == 'connect':
                    self.client_connection(client_socket, username)
                    if not username:
                        return

                # Handle the join command
                elif command == 'join':
                    self.client_join(client_socket, username)

                elif command == 'groupjoin':
                    self.client_groupjoin(client_socket, username, group)
                    print(f"Processing groupjoin request for group: {group}")

                # Handle the post command
                elif command == 'post':
                    self.client_post(client_socket, username, data)
                    if not username or not data:
                        continue
                    
                # Handle the users command
                elif command == 'users':
                    self.get_users(client_socket)
                    
                # Handle the message command
                elif command == 'message':
                    self.get_message(client_socket, data)

                elif command == 'groupleave':
                    self.client_groupleave(client_socket, username, group)

                # Handle the leave command
                elif command == 'leave':
                    self.client_leave(client_socket, username)

                # Handle the exit command
                elif command == 'exit':
                    self.client_exit(client_socket, username)
                    return
                
                # Handle the groups command
                elif command == 'groups':
                    self.client_groups(client_socket)

                elif command == 'grouppost':
                    self.client_post(client_socket, username=username, data=data, group=group)

                # Handle the groupusers command
                elif command == 'groupusers':
                    self.get_users(client_socket, username=username, group=group)
                    
                # Handle the groupmessage command
                elif command == 'groupmessage':
                    self.get_message(client_socket, data=data, group=group, username=username)

                else:
                    # Command not recognized
                    response = Protocol.build_response("error", "FAIL", f"Unknown command: {command}")
                    client_socket.send((response + '\n').encode())  

        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {addr}: {e}')

    
    def client_connection(self, client_socket, username):
        # If there is not a username then a failure occurs
        if not username:
            response = Protocol.build_response("connect", "FAIL", "Username is required to connect.")
            client_socket.send((response + '\n').encode())
            client_socket.close()
            return

        try:
            # Display that a user has connected
            print(f'{username} connected')

            # Notify all clients in message board about new connection
            self.notify(f'{username} has joined the server', clients=self.clients)

            # Build and Send Response
            response = Protocol.build_response("connect", "OK")
            client_socket.send((response + '\n').encode())
        
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("connect", "FAIL")
            client_socket.send((response + '\n').encode())

    
    def client_join(self, client_socket, username):
        """Handle a client joining the message board."""
        if client_socket in self.message_board_clients:
            response = Protocol.build_response("join", "FAIL", "You are already connected to the message board.")
            client_socket.send((response + '\n').encode())
            return

        # Add the client to the message board list
        self.message_board_clients.append(client_socket)
        print(f"{username} joined the message board.")
        
        # Add the username to the default board users list
        self.message_board_users.append(username)

        # Send the last two messages in the message history
        if len(self.messages["public board"]) > 0:
            history_data = [json.loads(msg) for msg in (self.messages["public board"][-2:] if len(self.messages["public board"]) >= 2 else self.messages["public board"])]
            response = Protocol.build_response("join", "OK", history_data)
        else:
            response = Protocol.build_response("join", "OK", "There are no messages on the board yet.")
        client_socket.send((response + '\n').encode())

        # Notify others on the board
        self.notify(f"{username} has joined the message board.", clients=self.message_board_clients, sender=client_socket)


    def client_groupjoin(self, client_socket, username, group):
        group = group.strip().lower()  # Clean up input

        """Handle a client joining a private group."""
        # Check if the user has joined the public message board
        if client_socket not in self.message_board_clients:
            response = Protocol.build_response("groupjoin", "FAIL", "You are not a member of the public message board.")
            client_socket.send((response + '\n').encode())
            return

        if not group or group not in self.private_group_users:
            response = Protocol.build_response("groupjoin", "FAIL", "The specified group does not exist.")
            client_socket.send((response + '\n').encode())
            return

        # Check if already in the group
        if client_socket in self.private_group_clients[group]:
            response = Protocol.build_response("groupjoin", "FAIL", "You are already a member of this group.")
            client_socket.send((response + '\n').encode())
            return

        # Add the client to the group
        self.private_group_clients[group].append(client_socket)
        print(f"{username} joined {group}.")
        
        # Add the username to the private group users list
        self.private_group_users[group].append(username)

        # Send group history or no messages notice
        group_messages = [json.loads(msg) for msg in self.messages[group]]
        if group_messages:
            response = Protocol.build_response("groupjoin", "OK", group_messages[-2:])
        else:
            response = Protocol.build_response("groupjoin", "OK", "There are no messages in this group yet.")
        client_socket.send((response + '\n').encode())

        # Notify other group members
        self.notify(f"{username} has joined {group}.", clients=self.private_group_clients[group], sender=client_socket)


    def client_post(self, client_socket, username, data, group=None):
        """Add the post to the history and notify all that a message has been posted"""
        try:
            # Make sure the command being sent in response directly correlates to if it is a group post or just a post
            command = "grouppost" if group else "post"

            # Check for valid data and return fail if not
            if not username or not data:
                response = Protocol.build_response(command, "FAIL", "Invalid message. Please ensure both username and message are provided.")
                client_socket.send((response + '\n').encode())
                return

            # Grab the subject and message out of data field
            # The subject and content are seperated by a newline in the data field
            parts = data.split('\n', 1) # split on first instance of \n

            if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
                # Ensure both subject and message exist and are non-empty
                response = Protocol.build_response(command, "FAIL", "Invalid message format. Both subject and content are required.")
                client_socket.send((response + '\n').encode())
                return
            
            # Now that the subject and message are separated they get stored in subject and message variables
            subject, message = parts[0].strip(), parts[1].strip()

            # Check if the user has joined the public message board
            if client_socket not in self.message_board_clients:
                response = Protocol.build_response(command, "FAIL", "You are not a member of the public message board.")
                client_socket.send((response + '\n').encode())
                return

            # Check if the the user is in the specified private group
            if group and group not in self.private_group_users:
                response = Protocol.build_response(command, "FAIL", "You are not a member of the specified group.")
                client_socket.send((response + '\n').encode())
                return

            # Add client's message to the board's history
            message_id, timestamp = self.add_message(sender=username, subject=subject, message=message, group=group)

            # Notify all in the board or group of the new message with the sender specified
            board = group if group else 'public board'
            clients = self.private_group_clients[group] if group else self.message_board_clients
            self.notify(f'{board}; Message ID: {message_id}, Sender: {username}, Time Posted: {timestamp}, Subject: {subject}\n\t{message}', clients=clients)

            # Send Response
            response = Protocol.build_response(command, "OK")
            client_socket.send((response + '\n').encode())

        # Send Bad Response
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response(command, "FAIL", "Invalid Message")
            client_socket.send((response + '\n').encode())


    def client_groupleave(self, client_socket, username, group):
        """Handle a client leaving a private group."""
        group = group.strip().lower()  # Clean up input

        # Check if the group exists
        if not group or group not in self.private_group_users:
            response = Protocol.build_response("groupleave", "FAIL", "Invalid group name. The group does not exist.")
            client_socket.send((response + '\n').encode())
            return

        # Check if the client is a member of the group
        if client_socket not in self.private_group_clients[group]:
            response = Protocol.build_response("groupleave", "FAIL", "You are not a member of this group.")
            client_socket.send((response + '\n').encode())
            return

        # Remove the client from the group
        self.private_group_clients[group].remove(client_socket)
        print(f"{username} left {group}.")
        
        # Remove the username from the private group users list
        self.private_group_users[group].remove(username)

        # Notify the user that they have successfully left the group
        confirmation = Protocol.build_response("groupleave", "OK", f"You have left {group}.")
        client_socket.send((confirmation + '\n').encode())

        # Notify other group members
        self.notify(f"{username} has left {group}.", clients=self.private_group_clients[group], sender=client_socket)

        # Add the client back to the main message board
        if client_socket not in self.message_board_clients:
            self.message_board_clients.append(client_socket)
            if username not in self.message_board_users:  
                self.message_board_users.append(username)
            print(f"{username} rejoined the message board.")


    def client_leave(self, client_socket, username):
        """Handle a client leaving the message board."""
        if client_socket not in self.message_board_clients:
            response = Protocol.build_response("leave", "FAIL", "You are not currently connected to the message board.")
            client_socket.send((response + '\n').encode())
            return

        # Remove the client from the message board list
        self.message_board_clients.remove(client_socket)
        print(f"{username} left the message board.")
        
        # Remove the username from the default board list
        self.message_board_users.remove(username)

        # Notify the leaving client
        response = Protocol.build_response("leave", "OK", "You have left the message board.")
        client_socket.send((response + '\n').encode())

        # Notify others on the board
        self.notify(f"{username} has left the message board.", clients=self.message_board_clients, sender=client_socket)

    
    def client_exit(self, client_socket, username=None):
        """Remove a client from the client list and close its connection after recieving exit command"""
        try:
            # If there is a username, notify all (including the server) that <username> has left
            if username:
                self.notify(f'{username} has left the server', clients=self.clients, sender=client_socket)
                print(f'{username} disconnected')

            # Remove the client socket and username from any lists they may be in
            if client_socket in self.message_board_clients:
                self.message_board_clients.remove(client_socket)
            if username in self.message_board_users:
                self.message_board_users.remove(username)
            for key in self.private_group_clients.keys():
                if client_socket in self.private_group_clients.get(key, []):
                    self.private_group_clients[key].remove(client_socket)
                if username in self.private_group_users.get(key, []):
                    self.private_group_users[key].remove(username)

            # Send a success response to the client for the exit command
            response = Protocol.build_response("exit", "OK", "You have successfully exited.")
            client_socket.send((response + '\n').encode())

            # Remove the client socket from connected clients list
            self.clients.remove(client_socket)

            # Close down the socket
            client_socket.close()
            
        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling request from {username}: {e}')
            response = Protocol.build_response("exit", "FAIL", f"An error occurred while processing the exit request: {e}")
            client_socket.send((response + '\n').encode())


    def client_groups(self, client_socket):
        """Display a lists of groups"""
        try:
            # Grab the list of groups and format into a string seperated by commas
            groups = [key for key in self.private_group_users.keys()]
            formatted_groups = ", ".join(groups)

            # Build and send a response containing the string list of the groups
            response = Protocol.build_response("groups", "OK", formatted_groups)
            client_socket.send((response + '\n').encode())

        except Exception as e:
            # If any point in the process above failed, send a FAIL response
            response = Protocol.build_response("groups", "FAIL", f"An error occurred while retrieving group information: {e}")
            client_socket.send((response + '\n'))


    def notify(self, data, clients, sender=None):
        """Broadcast message to a selected group of clients except the sender."""
        escaped_data = data.replace('\n', '\\n')
        notification_payload = Protocol.build_request("notify", data=escaped_data)
        encoded_message = (notification_payload + '\n').encode()

        # Iterate through each client and send the encoded message
        for client in clients:
            if client != sender: 
                try: 
                    client.send(encoded_message)
                except Exception as e:
                    print(f'Failed to send message to a client ({client}): {e}')
    

    def add_message(self, sender, subject, message, group=None):
        """Add message to the server's message history"""

        # Get the current timestamp and format into a readable form
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Determine the key to use for access the message history dictionary
        group = 'public board' if not group else group

        # Create a dictionary (that will be converted to JSON) to represent the message
        formatted_message = {
            'id': len(self.messages[group]) + 1,
            'sender': sender,
            'timestamp': timestamp,
            'subject': subject,
            'message': message
        }

        # Convert the dictionary to JSON-formatted string and append to message history
        self.messages[group].append(json.dumps(formatted_message))

        return formatted_message['id'], timestamp

    def get_users(self, client_socket, username=None, group=None):
        """ 
        Retrieve a list of users in the same group.
        If they aren't in a group, get the list of users
        from the default (public) board. 
        """
        
        try:
            # Check if the client is in the message board clients list
            if client_socket not in self.message_board_clients:
                response = Protocol.build_response("users", "FAIL", "Current user is not in a message board.")
                client_socket.send((response + '\n').encode())
                return

            # If a group is specified, retrieve users in that group
            if group:
                # Strip any surrounding quotes from the group name for searching
                group = group.strip('"').strip().lower()

                # Check if the group exists
                if group not in self.private_group_users:
                    response = Protocol.build_response("users", "FAIL", "Group does not exist.")
                    client_socket.send((response + '\n').encode())
                    return
                              
                # If the current user is not in the group, return a failure response
                # based on username
                if username not in self.private_group_users[group]:
                    response = Protocol.build_response("users", "FAIL", "Current user is not in the group. Access Denied.")
                    client_socket.send((response + '\n').encode())
                    return

                # Retrieve the list of users in the specified group
                group_users = self.private_group_users[group]
                user_list = ', '.join(group_users)
            else:
                # Retrieve the list of users in the default group
                user_list = ', '.join(self.message_board_users)

            # Build response from users list
            response = Protocol.build_response("users", "OK", user_list)

            # Send response
            client_socket.send((response + '\n').encode())

        except Exception as e:
            # Notify if any error occurs within this function
            print(f'Error when handling users request: {e}')

            # Send a failure response
            response = Protocol.build_response("users", "FAIL")
            client_socket.send((response + '\n').encode())
            
    def get_message(self, client_socket, data, group=None, username=None):
        """ 
        Retrieve a message via ID from the message history
        from the message board or a specific group.
        """
        
        try:
            # Ensure the data is an integer
            message_id = int(data)

            # Check if the client is in the message board clients list
            if client_socket not in self.message_board_clients:
                response = Protocol.build_response("message", "FAIL", "Current user is not in a message board.")
                client_socket.send((response + '\n').encode())
                return

            # If a group is specified, check if the client is a member of the group
            if group:
                group = group.strip('"').strip().lower()

            # Check if there is an invalid ID given
            message_group = 'public board' if not group else group
            if message_id < 0 or message_id > len(self.messages[message_group]):
                # Return a failure response
                response = Protocol.build_response("message", "FAIL", "Invalid message ID.")
                client_socket.send((response + '\n').encode())
                return

            # Search through messages for the message with the given id
            for message in self.messages[message_group]:
                # Format the message into a dictionary for ease of use
                message_dict = json.loads(message)
                # Search by ID
                if int(message_dict['id']) == message_id:
                    if group and username not in self.private_group_users[message_group]:
                        # search in the group for the current username to check their access
                        # if they are not in the group return an error
                        response = Protocol.build_response("message", "FAIL", "Current user is not in the group. Access Denied.")
                        client_socket.send((response + '\n').encode())
                        return
                    formatted_message = f"Subject: {message_dict['subject']}\nMessage: {message_dict['message']}"
                    response = Protocol.build_response("message", "OK", formatted_message)
                    client_socket.send((response + '\n').encode())
                    return

        except ValueError:
            # If the data represents a non-integer
            response = Protocol.build_response("message", "FAIL", "Invalid message ID.")
            client_socket.send((response + '\n').encode())
        except Exception as e:
            print(f'Error when handling message request: {e}')
            response = Protocol.build_response("message", "FAIL")
            client_socket.send((response + '\n').encode())
        

if __name__ == "__main__":
    server = BulletinBoardServer('', 6789)
    server.run()