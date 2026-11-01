import socket
import threading

host = '0.0.0.0'
port = 2006

serverInGame = False

connected_clients = {}
board = None
turn = None

def clear_board():
    return [['-','-','-'],['-','-','-'],['-','-','-']]

def game_end(client_socket, opponent):
    global turn
    global board
    global serverInGame

    turn = None
    serverInGame = False
    user_clear(client_socket)
    user_clear(opponent)
    board = clear_board()

def user_clear(client_socket):
    connected_clients[client_socket]["playing"] = False
    connected_clients[client_socket]["opponent_socket"] = None
    connected_clients[client_socket]["pending_challenge"] = False
    connected_clients[client_socket]["symbol"] = None


def show_board():
    global board
    message = "\n"
    for i in range(3):
        for j in range(3):
            message += board[i][j]
            if j != 2:
                message += " | "
        if i != 2:
            message += "\n"
    broadcastServer(message)

def broadcastServer(message):
    print(message)
    for client in connected_clients:
        try:
            client.send(f"[System]: {message}".encode('utf-8'))
        except:
            continue

def broadcast(client_socket, message):
    writer = connected_clients[client_socket]["name"]
    for client in connected_clients:
        if client != client_socket:
            try:
                client.send(f"[{writer}]: {message}".encode('utf-8'))
            except:
                continue

def toDirect_command(message, client_socket): 
    global serverInGame
    global turn
    array = message.strip().split(" ", 1)
    command = array[0]
    arg = array[1] if len(array) > 1 else ""

    if command.lower() == "/changename":
        if not arg:
            client_socket.send("The new name missing".encode('utf-8'))
            return

        if arg == connected_clients[client_socket]["name"]:
            client_socket.send("This name already is your name".encode('utf-8'))
            return

        for client in connected_clients:
            if connected_clients[client]["name"] == arg:
                client_socket.send("[System] Username already exists".encode('utf-8'))
                return
        
        last_name = connected_clients[client_socket]["name"]
        connected_clients[client_socket]["name"] = arg
       
        broadcast(client_socket, f"The user with name {last_name} changed your username to {arg}")

    elif command.lower() == "/help":
        client_socket.send("Description of commands:\n/changename <new_name> - used to change your username\n/listusers - used to list all users connected in the room\n/challenge <username> - used to challenge a player to tic-tac-toe\n/accept - used to accept a pending challenge".encode('utf-8'))

    elif command.lower() == "/listusers":
        mensageUser = ""
        for client in connected_clients:
            if(client == client_socket):
                mensageUser += connected_clients[client]["name"]+"(You)\n"
            else:
                mensageUser += connected_clients[client]["name"]+"\n"

        client_socket.send(mensageUser.encode('utf-8'))

    elif command.lower() == "/challenge":
        if not arg:
            client_socket.send("The new name missing")
            return
        
        ver = False
        for client in connected_clients:
            if connected_clients[client]["name"] == arg:
                ver = True
                userChallenged_socket = client
                break
        if ver:
            if connected_clients[client_socket]["name"] == connected_clients[userChallenged_socket]["name"]:
                client_socket.send("You can't to challenge yourself to game".encode('utf-8'))
                return

            if connected_clients[userChallenged_socket]["pending_challenge"]:
                client_socket.send("Challenged user already has a challenge".encode('utf-8'))
                return

            connected_clients[client_socket]["opponent_socket"] = userChallenged_socket
            connected_clients[userChallenged_socket]["opponent_socket"] = client_socket
            connected_clients[userChallenged_socket]["pending_challenge"] = True

            userChallenged_socket.send(f"{connected_clients[client_socket]["name"]} is challenging you to a game of tic-tac-toe".encode('utf-8'))
            client_socket.send("[System] User Exists, challenge thrown, waiting...".encode('utf-8'))
            print("User Exists, challenge thrown")
        else:
            client_socket.send("User don't Exists".encode('utf-8'))
            print("User don't Exists")

    elif command.lower() == "/accept":
        if connected_clients[client_socket]["pending_challenge"]:
            connected_clients[client_socket]["pending_challenge"] = False
        else:
            client_socket.send("You wasn't challenged".encode('utf-8'))
            return
        
        opponent_socket = connected_clients[client_socket]["opponent_socket"]

        connected_clients[client_socket]['symbol'] = 'O'
        connected_clients[opponent_socket]['symbol'] = 'X' #challenger

        client_socket.send("You accepted the challenge".encode('utf-8'))
        opponent_socket.send("The challenged player accepted the challenge".encode('utf-8'))
        
        connected_clients[client_socket]["playing"] = True
        connected_clients[opponent_socket]["playing"] = True

        nameOpponent = connected_clients[opponent_socket]["name"]

        turn = opponent_socket

        broadcastServer(f"[System] A game is starting between {nameOpponent} and {connected_clients[client_socket]["name"]}, {nameOpponent} start")
        show_board()
        #Global varriable below 
        serverInGame = True

def check_game(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != '-':
            return 1

        if board[0][i] == board[1][i] == board[2][i] != '-':
            return 1

    if board[0][0] == board[1][1] == board[2][2] != '-':
        return 1

    if board[0][2] == board[1][1] == board[2][0] != '-':
        return 1

    for row in board:
        if '-' in row:
            return 0 

    return -1

def move(client_socket, message):
    global board
    global turn
    
    opponent = connected_clients[client_socket]["opponent_socket"]
    
    array = message.strip().split(" ")
#
    if len(array) != 2 or not (array[0].isdigit() and array[1].isdigit()):
        client_socket.send("[System] Invalid format! Send coordinates like: 1 2\n".encode('utf-8'))
        return

    row = int(array[0])
    column = int(array[1])

    if board[row][column] == '-':
        board[row][column] = connected_clients[client_socket]['symbol']
    else:
        client_socket.send("Choose another local on the board".encode('utf-8'))
        return

    show_board()

    check = check_game(board)

    if check == 1:
        broadcastServer(f"The user {connected_clients[client_socket]["name"]} wins, the server is open for all messages")
        game_end(client_socket, opponent)
        return
    elif check == -1: 
        broadcastServer(f"The game ended in a draw, the server is open for all massages")
        game_end(client_socket, opponent)
        return
    
    turn = opponent    
    opponent.send("Your turn".encode('utf-8'))


def doorwaiter_to_client(client_socket, client_address):
    while 1:
        userName = client_socket.recv(1024).decode('utf-8')
        ver = False
        for client in connected_clients:
            if connected_clients[client]["name"] == userName:
                ver = True
                break
        if ver:
            client_socket.send("Username already exists, enter another name below".encode('utf-8'))
        else:
            break
            
    broadcastServer(f"New connection - {userName} joined in room")
    
    connected_clients[client_socket] = {"name": userName,"address": client_address, "playing": False, "opponent_socket": None, "pending_challenge": False, "symbol": None}

    while 1:
        try:
            data = client_socket.recv(5000)

            if not data:
                break

            message = data.decode('utf-8')

            if serverInGame:
                if connected_clients[client_socket]["playing"]:
                    if client_socket == turn:
                        move(client_socket, message)
                        continue
                    else:
                        client_socket.send("Isn't your turn, wait!".encode('utf-8'))
                        continue

                else:
                    client_socket.send("You can't send messages while players are playing".encode('utf-8'))
                    continue
            
            print(f"[{connected_clients[client_socket]["name"]}]: {message}")

            if message.startswith('/'):
                toDirect_command(message, client_socket)
            else:            
                broadcast(client_socket, message)
        except:
            broadcastServer(f"[Desconected] {connected_clients[client_socket]["name"]} leave the room because of an error")
            break

    
    broadcastServer(f"[Desconected] {connected_clients[client_socket]["name"]} leave the room")

    if connected_clients[client_socket]["playing"]:
        opponent = connected_clients[client_socket]["opponent_socket"]
        try: #I placed the try/except because if the two players desconnected can appears an error
            opponent.send("[System] Your opponent disconnected\n".encode('utf-8'))
        except:
            pass
        broadcastServer(f"The game ended because {userName} disconnected, the server is open for all messages")
        game_end(client_socket, opponent)

    connected_clients.pop(client_socket)
    client_socket.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
server.settimeout(1.0)
print(f"Server working and it waiting for connections {host}:{port}")
board = clear_board()

try:
    while 1:
        try:
            client_socket, client_address = server.accept()
            thread = threading.Thread(target=doorwaiter_to_client, args=(client_socket, client_address), daemon=True)
            thread.start()
        except socket.timeout:
            continue
except:
    server.close()