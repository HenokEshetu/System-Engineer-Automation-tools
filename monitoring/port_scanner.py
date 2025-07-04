import socket

host = input("Enter target host (e.g., 127.0.0.1): ")
for port in range(1, 1025):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    if s.connect_ex((host, port)) == 0:
        print(f"Port {port} is open")
    s.close()
