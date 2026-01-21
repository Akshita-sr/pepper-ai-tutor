# test_connection.py (Python 3)
import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

# Send test command
command = {"action": "say", "data": {"text": "Hello from test!"}}
socket.send_json(command)

# Receive response
response = socket.recv_json()
print("Response:", response)
