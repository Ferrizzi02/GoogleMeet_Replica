import zmq
import threading
import sys
import time

class Cliente:
    def __init__(self, identity, room, msgCallBack, brokerStatusCallBack =None):
        #variaveis para a logica
        self.identity = identity
        self.room = room
        self.msgCallBack = msgCallBack
        self.context = zmq.Context()
        self.ultimoHeartbeat = time.time()
        self.brokerVivo = True
        self.brokerStatusCallBack = brokerStatusCallBack
        self.running = True

        self.pub = self.context.socket(zmq.PUB)
        self.pub.connect("tcp://localhost:5555")        

    #cria uma thread para as mensagens, escutar o heartbeat e outra para o calculo, acho que para audio teria que criar aqui também.
    def threadEscuta(self):
        thread_recv = threading.Thread(target=self.escutarMsg, args=("TXT",), daemon=True)
        thread_recv.start()

        thread_heartbeat = threading.Thread(target=self.escutarMsg, args=("HB",), daemon=True)
        thread_heartbeat.start()

        thread_monitor = threading.Thread(target=self.monitorearBroker, daemon=True)
        thread_monitor.start()


    #Depende do tipo de msg (txt ou hb) tem os tratamentos dele
    def escutarMsg(self, tipo):
        subscriber = self.context.socket(zmq.SUB)
        if tipo == "TXT":
            subscriber.connect("tcp://localhost:5556")
            #se increve no topico texto
            topico = f"TXT/{self.room}"
        else:
            subscriber.connect("tcp://localhost:5559")
            topico = "HB/"

        subscriber.setsockopt_string(zmq.SUBSCRIBE, topico)

        while self.running:
            try:
                message = subscriber.recv_string()

                if message.startswith("HB/"):
                    self.ultimoHeartbeat = time.time()
                else:
                    partes = message.split("|", 2)
                    if len(partes) == 3:
                        _, user, msg = partes
                        if user != self.identity:
                            self.msgCallBack(user, msg)
            except Exception as e:
                if self.running:
                    print(f"Erro na trhead {tipo}: {e}")


    def enviarMsg(self, msg):
        if msg:
            msgPraEnviar = f"TXT/{self.room}|{self.identity}|{msg}"
            self.pub.send_string(msgPraEnviar)

    def monitorearBroker(self):
        while self.running:
            if time.time() - self.ultimoHeartbeat > 5:
                if self.brokerVivo:
                    self.brokerVivo = False
                    #PRECISA DE CHAMAR AQUI UMA FUNÇÃO PARA TROCAR BROKERS
                    if self.brokerStatusCallBack:
                        self.brokerStatusCallBack(False)
            else:
                if not self.brokerVivo:
                    self.brokerVivo = True
                    if self.brokerStatusCallBack:
                        self.brokerStatusCallBack(True)
            time.sleep(1)

    def desconectar(self):
        self.running = False
        self.enviarMsg("saiu da ligação")
        time.sleep(0.5)
        self.pub.close()
        self.context.term()

#end