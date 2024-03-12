import socket
import ssl
import select
import threading

PROXY_SERVER = "127.0.0.1"
PROXY_PORT = 53
DOT_SERVER = "1.1.1.1"
DOT_PORT = 853
BUFFER_SIZE = 4096
TIMEOUT = 5
DOT_UDP_PORT = 53


def dns_with_tls_manage(client_socket):
    client_data = client_socket.recv(BUFFER_SIZE)
    if client_data:
        print("Received DNS query from Client")

        print("Establishing TCP connection with TLS to DOT Server")

        with socket.create_connection((DOT_SERVER, DOT_PORT), timeout=TIMEOUT) as dot_tcp_socket:
            try:
                context = ssl.create_default_context()
                with context.wrap_socket(dot_tcp_socket, server_hostname=DOT_SERVER) as dot_tls_socket:
                    print(f"DOT Accepted connection")
                    dot_tls_socket.sendall(client_data)
                    dot_response_data = dot_tls_socket.recv(BUFFER_SIZE)
                    print(f"Received response from DOT: {dot_response_data}")
                    client_socket.sendall(dot_response_data)
            except (socket.timeout, ssl.SSLError) as e:
                print(f"Error communicating with DOT server over TLS: {e}")
                raise


def dns_with_udp_manage(proxy_server_socket_udp):
    client_data, client_address = proxy_server_socket_udp.recvfrom(BUFFER_SIZE)
    if client_data:
        print(f"Received DNS query from {client_address} with socket info {None}")
        print("Establishing UDP connection with DOT Server")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dot_udp_socket:
            try:
                dot_udp_socket.sendto(client_data, (DOT_SERVER, DOT_UDP_PORT))
                data, address = dot_udp_socket.recvfrom(BUFFER_SIZE)
                print(f"Received response from DOT: {data} {address}")
                proxy_server_socket_udp.sendto(data, client_address)
            except socket.error as e:
                print(f'Error communicating with DOT server over UDP: {e}')
                raise


def main():
    proxy_server_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server_socket_tcp.bind((PROXY_SERVER, PROXY_PORT))
    proxy_server_socket_tcp.listen()
    print(f"TCP Proxy server listening on {PROXY_SERVER}:{PROXY_PORT}...")

    proxy_server_socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    proxy_server_socket_udp.bind((PROXY_SERVER, PROXY_PORT))
    print(f"UDP Proxy server listening on {PROXY_SERVER}:{PROXY_PORT}...")

    try:
        while True:
            proxyreadablesocket, _, _ = select.select([proxy_server_socket_tcp, proxy_server_socket_udp], [], [],
                                                      TIMEOUT)
            for sockettype in proxyreadablesocket:
                if sockettype is proxy_server_socket_tcp:
                    client_socket, client_address = sockettype.accept()
                    with client_socket:
                        client_tcp_thread = threading.Thread(target=dns_with_tls_manage(client_socket))
                        client_tcp_thread.start()

                elif sockettype is proxy_server_socket_udp:
                    client_udp_thread = threading.Thread(target=dns_with_udp_manage(proxy_server_socket_udp))
                    client_udp_thread.start()


    except KeyboardInterrupt:
        pass
    finally:
        proxy_server_socket_tcp.close()
        proxy_server_socket_udp.close()


if __name__ == "__main__":
    main()
