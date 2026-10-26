import sys
import socket
import struct

def rcon_command(host, port, password, command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((host, port))
        auth_data = struct.pack('<iii', len(password) + 10, 1, 3) + password.encode('ascii') + b'\x00\x00'
        s.send(auth_data)
        resp = s.recv(4096)
        
        exec_data = struct.pack('<iii', len(command) + 10, 2, 2) + command.encode('ascii') + b'\x00\x00'
        s.send(exec_data)
        
        out = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                out += chunk
                if len(chunk) < 4096: break
            except socket.timeout:
                break
                
        if len(out) >= 12:
            return out[12:-2].decode('utf-8', errors='ignore')
        return out.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"RCON Error: {e}"
    finally:
        s.close()

if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "status"
    print(rcon_command("81.181.113.120", 27015, "walliez_rcon_2026", cmd))
