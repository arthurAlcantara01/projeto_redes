import socket
import threading
import getpass

host = '192.168.56.1'
port = 2006

userName = getpass.getuser()

def recieve_mensages(client_socket):
    while 1:
        try: 
            data = client_socket.recv(5000)
            if not data:
                break

            mensage = data.decode('utf-8')
            print(f"{mensage}")
        except:
            print(f"[Error] Server falled")
            client_socket.close()
            break

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Client trying to connect server")
client.connect((host, port))
client.send(userName.encode('utf-8'))
print("Connected! You can to send mensages")

thread = threading.Thread(target=recieve_mensages, args=(client,))
thread.start()

while 1:
    try:
        mensage_client = input("") 

        client.send(mensage_client.encode('utf-8'))
    except KeyboardInterrupt:
        print('Leaving the room...')
        client.close()
        break