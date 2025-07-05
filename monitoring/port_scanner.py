"""
Example of usage:
    # Scan common ports on localhost
    python3 port_scanner.py 127.0.0.1

    # Scan custom range with higher timeout
    python3 port_scanner.py scanme.nmap.org -s 20 -e 100 -t 1.0

    # Increase thread count for faster scan
    python3 port_scanner.py 192.168.1.1 -th 200
"""

import socket
import threading
import argparse
import time

# Default services (limited mapping for demo)
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt",
}


def scan_port(host, port, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                print(f"[+] Port {port}/tcp is OPEN ({service})")
    except socket.error:
        pass  # Ignore unreachable hosts or ports


def resolve_target(target):
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        print(f"[Error] Cannot resolve host: {target}")
        exit(1)


def main():
    parser = argparse.ArgumentParser(description="Fast TCP Port Scanner")
    parser.add_argument("target", help="Target IP or hostname")
    parser.add_argument(
        "-s", "--start", type=int, default=1, help="Start port (default: 1)"
    )
    parser.add_argument(
        "-e", "--end", type=int, default=1024, help="End port (default: 1024)"
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=0.5,
        help="Timeout in seconds (default: 0.5)",
    )
    parser.add_argument(
        "-th",
        "--threads",
        type=int,
        default=100,
        help="Number of threads (default: 100)",
    )

    args = parser.parse_args()
    host = resolve_target(args.target)

    print(f"\nScanning {host} from port {args.start} to {args.end}...")
    print(f"Timeout: {args.timeout}s | Threads: {args.threads}\n")

    start_time = time.time()
    thread_list = []

    for port in range(args.start, args.end + 1):
        thread = threading.Thread(target=scan_port, args=(host, port, args.timeout))
        thread_list.append(thread)
        thread.start()

        if len(thread_list) >= args.threads:
            for t in thread_list:
                t.join()
            thread_list = []

    # Final batch
    for t in thread_list:
        t.join()

    print(f"\nScan complete in {time.time() - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()
