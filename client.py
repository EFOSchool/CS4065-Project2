from socket import *
import threading

class Client:
    

    def __init__(self):
        """Client constructor to set up host, port and socket"""

        # Initialize all variables to None type as they will be defined in the connect command
        self.host = None
        self.port = None
        self.socket = socket(AF_INET, SOCK_STREAM)

    
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
            username = input("Enter your username: ")
            self.socket.send(username.encode())

            # Start sending messages
            self.send_messages()

        except Exception as e:
            print('Problem connecting and interacting with the server. Make sure it is running')
            print(f'Error encountered: {e}')
        
        finally:
            self.socket.close() # Close the socket connection when done

    
    def receive_messages(self):
        """Listen for incoming messages from the server"""

        while True:
            try:
                # Recieve a message from the server, decode it, then print it
                message = self.socket.recv(1024).decode()
                if message: print(f'\r{message}\n>> ', end='')

            except Exception as e:
                print('Error recieving message or connection to the server may have be losted')
                print(f'Error encountered: {e}')

    
    def send_messages(self):
        """Prompt user and send messages to the server"""

        try:
            while True:
                # Prompt for user input and send the message 
                message = input('>> ')

                # If the user types '%exit', send it to the server and break the loop
                if message == '%exit':
                    self.socket.send(message.encode())
                    break


                # Otherwise, send the typed message to the server
                self.socket.send(message.encode())

        except KeyboardInterrupt:
            print('\nExiting...')
            self.socket.send('%exit'.encode()) # Send exit command to server

        finally:
            self.socket.close() # Close the socket when done


if __name__ == "__main__":
    """
    Prompt the user to input the connection details and establishes a connection to the server.
    NOTE: The default serve connect is addr = 'localhost' and port 6789
    """

    # Initialize the client object
    client = Client()        

    # Get teh user input to establish a connection and ensure the input follows the correct format for connection
    user_in = input('>> ')
    while not user_in.startswith('%connect') or len(user_in.split()) != 3:
        print('ERROR: Must establish connection using the format, %connect <addr> <port>, before doing anything else')
        user_in = input('>> ')
    
    # Split the input and extract the server address and port number 
    parts = user_in.split()
    addr = parts[1]
    port = int(parts[2])

    # Establish connection with the specified address adn port
    client.connect(addr, 6789)