# CS4065-Project2: Simple Bulletin Board Using Socket Programming

## Team Members:
* Matthew Goldsberry
* Hannah Krzywkowski
* Emma O'Brien

## Overview
This is a simple bulletin board using socket programming for the course CS4065 - Computer Networks and Networked Computing. Users are able to connect to a server, join public and private message boards, and can send and receive messages within those boards. 

## Compilation Instructions
1. Clone the Repository
   
   `git clone https://github.com/EFOSchool/CS4065-Project2.git`
   
    `cd CS4065-Project2`
2. Run the server
   
   `python server.py`
3. While the server is running, open a new terminal and run the client
   
   `python client.py`

4. To connect and begin interacting with the message boards, type

   `%connect localhost 6789`

## Description of Major Issues and Their Solutions

An initial issue that was a very major aspect of the whole framework of the project was building a protocol. We have to build an design a protocol that we felt best served the purpose needed in this project. We laid out an idea of what all of the protocols would look like (or rather how we imaged they would look like) before starting the code. With this we had an solid foundation for the protocol that would be used to communicate between the server and client. With that we decided to make a seperate `Protocol` class (found in `protocol.py`) with two methods, one to build a request message and one to build a response message, both in a json format. This proved to be a very beneficial implementation becasue it allowed us to start with the bare minimum in terms of headers when we started and add/remove headers as we progressed through building capabilities into the server/client communication. 

There were several issues that arose during the development of the `%users` and `%message` commands as well as their group counterparts. The user command in Part One was handled by appending each user to a list on their joining of the group, and removal on their leaving of the group. However, Part Two required a clear separation of users between groups. Rather than a single global list, in this part we decided to map the usernames to their groups using a dictionary and verifying the current group before access was granted. For the `%groupmessage` command we attempted the same method with mapping the messages and having IDs be unique to each group, however, we soon decided to have a universal ID system. IDs were set the same across each group and instead access depended on an attached attribute to each message stating which group the message was posted in. 

A big issue that was ran into was the graceful shutdown of the client when the user enters the `%exit` command. At first this seemed easy because when you think about it, the user types the command and then you shutdown the client, but it ended up bein much more troublesome than that. Since the server remains running even after the client ends you have to make sure that both the server and the client close the connect, not just the client. This is where the probelm arose. When we tried to do a "bang-bang" solution where we send the request to the server to close its connection, and then close the client socket. The problem is that the client socket would always close before the server could handle the request, leading to errors on the server side. So we had to come up with a solution that would allow the server to close its connection to the socket, then the client socket closing. This becomes tricky becasue you want to send a response to the client saying that the server has shutdown its connection, but this response has to be sent before the server shuts down the connection or else it would not be able to be sent to the client. This then leads to the problem that you cannot guarantee that by the time you get the response that the server has completed close the connection yet. So instead we ended up settling on a solution where the client gives the server plenty of time to process the request and close the connection (we found .1 seconds to be plenty of time, but chose .2 to be extra safe) and after that wait, a check is done to see if the reading side of the client recieved a `OK` response from the server for the `exit` command (done by checking to see if Boolean flag, `exit_confirmed` is set or not). By waiting and only breaking when the server sends an `OK` response, we ensure a gracefully exit of the client from the server.