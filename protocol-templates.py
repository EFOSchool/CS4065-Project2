import json

"""
    This file contains a general protocol template for the 
    various requests and responses sent between the client and
    server. 
    
    These were meant to somewhat mimic HTTP request and response
    messages with a header section and a body section. I also included
    group information since we will eventually extend to Part 2.
    
    Source: https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages
    
    General Layout of Requests:
    
    {
        "header": {
            "command": <command>,
            "username": <username>,
            "group": <group>,
        },
        "body": {
            <data>
        }
    }
    
    General Layout of Responses:
    
    {
        "header": {
            "status": <status>,
        },
        "body": {
            <data>    
        }
    }
    
"""

"""
    Below are the templates for Part 1
"""

# Template for a connection request
connectionRequest = {
    "header": {
        "command": "connect",
        "username": "",
        "group": ""
    },
    "body": {
        "data": ""
    }
}

# Template for a connection response
connectionResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a join command to join a single message board
joinRequest = {
    "header": {
        "command": "join",
        "username": "",
    },
    "body": {}
}

# Template for a join response
joinResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a post message command
# Holds subject and content of the message
postMessageRequest = {
    "header": {
        "command": "post",
        "username": "",
        "group": "",
    },
    "body": {
        "subject": "",
        "content": ""
    }
}

# Template for a post message response
postMessageResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a users command to retrieve a list of users in the single group
usersRequest = {
    "header": {
        "command": "users",
        "username": "",
        "group": "",
    },
    "body": {}
}

# Template for a users response
usersResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "users": [],
    }
}

# Template for the leave command to leave the single group
leaveRequest = {
    "header": {
        "command": "leave",
        "username": "",
        "group": "",
    },
    "body": {}
}

# Template for the leave response
leaveResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a message command to retrieve a single message via Message ID
messageRequest = {
    "header": {
        "command": "message",
        "username": "",
        "group": "",
    },
    "body": {
        "messageID": ""
    }
}

# Template for a message response (returning content)
messageResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template of exit command to exit client program
exitRequest = {
    "header": {
        "command": "exit",
        "username": "",
        "group": "",
    },
    "body": {}
}

# Template for a exit response
exitResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

"""
    Below are the templates for Part 2
"""

# Template for a group command to list all the groups to join
groupRequest = {
    "header": {
        "command": "group",
        "username": "",
    },
    "body": {}
}

# Template for a group response
groupResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "groups": [],
    }
}

# Template for a groupjoin command via group ID or name
groupJoinRequest = {
    "header": {
        "command": "groupjoin",
        "username": "",
    },
    "body": {
        "groupID": "",
        "groupName": "",
    }
}

# Template for a groupjoin response
groupJoinResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a group post command. Takes group id/name, message subject and content
# and would only post to the specific group
groupPostRequest = {
    "header": {
        "command": "grouppost",
        "username": "",
    },
    "body": {
        "groupID": "",
        "groupName": "",
        "subject": "",
        "content": ""
    }
}

# Template for a group post response
groupPostResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a group users command to retrieve a list of users in the group using
# ID or the group name
groupUsersRequest = {
    "header": {
        "command": "groupusers",
        "username": "",
    },
    "body": {
        "groupID": "",
        "groupName": "",
    }
}

# Template for a group users response
groupUsersResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "users": [],
    }
}

# Template for a group leave command to leave a group using ID or name
groupLeaveRequest = {
    "header": {
        "command": "groupleave",
        "username": "",
    },
    "body": {
        "groupID": "",
        "groupName": "",
    }
}

# Template for a group leave response
groupLeaveResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}

# Template for a group message command that uses group ID/name and a message ID
# to get te content of a message owned by a specific group
groupMessageRequest = {
    "header": {
        "command": "groupmessage",
        "username": "",
    },
    "body": {
        "groupID": "",
        "groupName": "",
        "messageID": ""
    }
}

# Template for a group message response
groupMessageResponse = {
    "header": {
        "status": "",
    },
    "body": {
        "message": "",
    }
}