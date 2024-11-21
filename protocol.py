import json

class Protocol:
    """Handles message construction according to protocol specifications."""

    def build_request(command, username=None, data=None):
        """Build the JSON request."""
        request = \
        {
            "header": {
                "command": command,
                "username": username,
            },
            "body": {
                "data": data,
            },
        }
        return json.dumps(request)
    
    def build_response(command, status, data=None):
        """Build the JSON response."""
        response = \
        {
            "header" : {
                "status": status,
                "command": command
            },
            "body": {
                "data": data
            }
        }
        return json.dumps(response)