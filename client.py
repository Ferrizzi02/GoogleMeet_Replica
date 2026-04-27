import zmq
import threading
import sys

class Cliente:
    def __init__(self, identity, room, msgCallBack):
        self.identity = identity
        self.room = room
        self.msgCallBack = msgCallBack
        self.context = zmq.Context()

        self.pub = self.context.socket(zmq.PUB)
        self.pub.connect("tcp://localhost:5555")        

    def threadEscuta(self):
        thread_recv = threading.Thread(target=self.escutarMsg, args=(UserID, roomID), daemon=True)
        thread_recv.start()

    def escutarMsg(self):
        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect("tcp://localhost:5556")

        #se increve no topico texto
        #OBS: Não sei se a logica tá certa, seria melhor por IDs de usuarios eu acho 
        topico = f"TXT/{self.room}"
        subscriber.setsockopt_string(zmq.SUBSCRIBE, topico)

        #print(f"[CLIENTE] incrito na sala {room}") #tem que virar confirmação no gui

        while True:
            #recebe msg completa
            message = subscriber.recv_string()
            _, user, msg = message.split("|", 2)
            if user != self.identity:
                #print(f"\n[{user}]: {msg}")
                self.msgCallBack(user,msg) #para a gui

    def enviarMsg(self):
        msgPraEnviar = f"TXT/{self.room}|{self.identity}|{self.msg}"
        self.pub.send_string(msgPraEnviar)

