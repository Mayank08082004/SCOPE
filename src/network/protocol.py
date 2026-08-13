import json
import struct

def send_message(sock, message_dict):
    """
    Sends a dictionary as a JSON string over the socket.
    Prefixes the message with a 4-byte header containing the message length.
    """
    payload = json.dumps(message_dict).encode('utf-8')
    header = struct.pack('!I', len(payload))
    try:
        sock.sendall(header + payload)
        return True
    except Exception:
        return False

def receive_message(sock):
    """
    Reads a 4-byte header to get the message length, then reads the JSON payload.
    Returns the parsed dictionary or None if connection is closed/errors.
    """
    try:
        header = recvall(sock, 4)
        if not header:
            return None
        msg_len = struct.unpack('!I', header)[0]
        
        payload = recvall(sock, msg_len)
        if not payload:
            return None
            
        return json.loads(payload.decode('utf-8'))
    except Exception:
        return None

def recvall(sock, n):
    """Helper to read exactly n bytes from a socket."""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data
