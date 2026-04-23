import socket
import threading

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8080

# ---------- utils ----------

def relay(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try:
            src.close()
            dst.close()
        except:
            pass

# ---------- HTTP proxy ----------

def handle_client(client):
    try:
        request = client.recv(8192)
        if not request:
            client.close()
            return

        header = request.decode(errors="ignore")
        first_line = header.split("\r\n")[0]

        # ---------- HTTPS (CONNECT) ----------
        if first_line.startswith("CONNECT"):
            _, target, _ = first_line.split()
            host, port = target.split(":")
            port = int(port)

            remote = socket.create_connection((host, port))
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

            t1 = threading.Thread(target=relay, args=(client, remote), daemon=True)
            t2 = threading.Thread(target=relay, args=(remote, client), daemon=True)
            t1.start()
            t2.start()
            return

        # ---------- HTTP ----------
        else:
            lines = header.split("\r\n")
            host = None
            for line in lines:
                if line.lower().startswith("host:"):
                    host = line.split(":", 1)[1].strip()
                    break

            if not host:
                client.close()
                return

            if ":" in host:
                host, port = host.split(":")
                port = int(port)
            else:
                port = 80

            remote = socket.create_connection((host, port))
            remote.sendall(request)

            relay(remote, client)

    except Exception as e:
        print("Client error:", e)
        try:
            client.close()
        except:
            pass

# ---------- server ----------

def start_proxy():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((LISTEN_HOST, LISTEN_PORT))
    s.listen(200)

    print(f"[+] HTTP proxy listening on {LISTEN_HOST}:{LISTEN_PORT}")

    while True:
        client, _ = s.accept()
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

# ---------- main ----------

if __name__ == "__main__":
    start_proxy()
