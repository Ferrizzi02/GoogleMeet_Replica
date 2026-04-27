import zmq
import time
import threading

class Broker:
    def __init__(self):
        self.context = zmq.Context()

        #clientes postan XSUB
        self.frontend = self.context.socket(zmq.XSUB)
        self.frontend.bind("tcp://*:5555")

        #backend onde os clientes se inscreven.
        self.backend = self.context.socket(zmq.XPUB)
        self.backend.bind("tcp://*:5556")
        print("[Broker] Broker ativo, recebe no 5555 e reparte no 5556")

        #heartbeat na porta 5559
        self.heartbeatsocket = self.context.socket(zmq.PUB)
        self.heartbeatsocket.bind("tcp://*:5559")
        #proxy

        #MODIFICAAAAAR 
        self.id = f"BROKER{1}"
        self.running = True
        
        
    def heartbeat(self):
        #thread pra isso
        def heartbeatLoop():
            print(f"[{self.id}] heartbeat ... <3")
            while self.running:
                self.heartbeatsocket.send_string(f"HB/{self.id}|ALIVE")
                time.sleep(2)

        thread = threading.Thread(target=heartbeatLoop, daemon=True)
        thread.start()

    def start(self):
        self.heartbeat()

        try:
            zmq.proxy(self.frontend,self.backend)
        except zmq.ZMQError as e:
            print(e)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.frontend.close()
            self.backend.close()
            self.heartbeatsocket.close()
            self.context.term()

if __name__ == "__main__":
    broker = Broker()
    broker.start()

#end