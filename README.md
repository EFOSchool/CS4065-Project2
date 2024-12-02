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

There were several issues that arose during the development of the `%users` and `%message` commands as well as their group counterparts. The user command in Part One was handled by appending each user to a list on their joining of the group, and removal on their leaving of the group. However, Part Two required a clear separation of users between groups. Rather than a single global list, in this part we decided to map the usernames to their groups using a dictionary and verifying the current group before access was granted. For the `%groupmessage` command we attempted the same method with mapping the messages and having IDs be unique to each group, however, we soon decided to have a universal ID system. IDs were set the same across each group and instead access depended on an attached attribute to each message stating which group the message was posted in. 

Another challenge we faced during the project was team members sometimes worked on separate parts of the project, making integration challenging due to differences in structure, dependencies, and data format assumptions. We addressed this by establishing a standard protocol for data communication and formatting early on. During integration, we resolved mismatches with collaborative debugging sessions and documented guidelines to maintain consistency. Furthermore, different coding styles made understanding and integrating code difficult, causing delays. To resolve this, we adopted a shared coding standard and conducted regular code reviews to improve readability and ensure consistency. Additonally, scheduling conflicts slowed decision-making and integration. Weekly check-ins helped address roadblocks, and GitHub facilitated task assignments, issue tracking, and asynchronous communication.

Also, implementing communication protocols with raw sockets led to issues like connection mismanagement and race conditions. To overcome this, our team members studied simpler socket examples before starting the project. Furthermore, client-server interactions behaved unpredictably on different systems. We used virtualized and containerized environments for consistent setups and conducted regular testing to identify and fix cross-platform issues.
