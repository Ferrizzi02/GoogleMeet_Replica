import zmq
import threading
import sys

def escutarMsg(identity, room):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5556")

    #se increve no topico texto
    #OBS: Não sei se a logica tá certa, seria melhor por IDs de usuarios eu acho 
    topico = f"TXT/{room}"
    subscriber.setsockopt_string(zmq.SUBSCRIBE, topico)

    print(f"[CLIENTE] incrito na sala {room}")

    while True:
        #recebe msg completa
        message = subscriber.recv_string()
        _, user, msg = message.split("|", 2)
        if user != identity:
            print(f"\n[{user}]: {msg}")

def enviarMsg(identity, room):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)
    publisher.connect("tcp://localhost:5555")

    while True:
        msg = input(f"[{identity}] ...")
        msgPraEnviar = f"TXT/{room}|{identity}|{msg}"
        publisher.send_string(msgPraEnviar)


UserID = input("[Registro] Nickname:")
roomID = input("[Registro] Sala:")

thread_recv = threading.Thread(target=escutarMsg, args=(UserID, roomID), daemon=True)
thread_recv.start()
    
enviarMsg(UserID, roomID)