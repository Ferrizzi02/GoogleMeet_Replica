import zmq
import time
import threading
import argparse

REGISTRY_HOST = "localhost"
REGISTRY_PORT = 5550

class Broker:
    def __init__(self, broker_id: str, host: str = "localhost",
                 pub_port: int = 5555, sub_port: int = 5556,
                 aud_pub_port: int = 5557, aud_sub_port: int = 5558,
                 vid_pub_port: int = 5559, vid_sub_port: int = 5560,
                 hb_port: int = 5561,
                 registry_host: str = REGISTRY_HOST,
                 registry_port: int = REGISTRY_PORT):

        self.id = broker_id
        self.host = host
        self.pub_port = pub_port   # XSUB — clientes publicam TXT aqui
        self.sub_port = sub_port   # XPUB — clientes assinam TXT aqui
        self.aud_pub_port = aud_pub_port  # XSUB — clientes publicam AUD aqui
        self.aud_sub_port = aud_sub_port  # XPUB — clientes assinam AUD aqui
        self.vid_pub_port = vid_pub_port  # XSUB — clientes publicam VID aqui
        self.vid_sub_port = vid_sub_port  # XPUB — clientes assinam VID aqui
        self.hb_port  = hb_port    # PUB heartbeat

        self.registry_host = registry_host
        self.registry_port = registry_port

        self.context = zmq.Context()

        # TXT: Clientes postam aqui (XSUB)
        self.frontend = self.context.socket(zmq.XSUB)
        self.frontend.bind(f"tcp://*:{pub_port}")

        # TXT: Clientes assinam aqui (XPUB)
        self.backend = self.context.socket(zmq.XPUB)
        self.backend.bind(f"tcp://*:{sub_port}")

        # AUD: Clientes postam aqui (XSUB)
        self.aud_frontend = self.context.socket(zmq.XSUB)
        self.aud_frontend.bind(f"tcp://*:{aud_pub_port}")

        # AUD: Clientes assinam aqui (XPUB)
        self.aud_backend = self.context.socket(zmq.XPUB)
        self.aud_backend.bind(f"tcp://*:{aud_sub_port}")

        # VID: Clientes postam aqui (XSUB)
        self.vid_frontend = self.context.socket(zmq.XSUB)
        self.vid_frontend.bind(f"tcp://*:{vid_pub_port}")

        # VID: Clientes assinam aqui (XPUB)
        self.vid_backend = self.context.socket(zmq.XPUB)
        self.vid_backend.bind(f"tcp://*:{vid_sub_port}")

        # Heartbeat
        self.hb_socket = self.context.socket(zmq.PUB)
        self.hb_socket.bind(f"tcp://*:{hb_port}")

        self.running = True

        print(f"[{self.id}] Broker ativo — TXT:{pub_port}/{sub_port} AUD:{aud_pub_port}/{aud_sub_port} VID:{vid_pub_port}/{vid_sub_port} HB:{hb_port}")

    # ------------------------------------------------------------------
    # Registro no registry
    # ------------------------------------------------------------------
    def _register(self):
        """Envia registro ao Registry com retries."""
        req = self.context.socket(zmq.REQ)
        req.setsockopt(zmq.RCVTIMEO, 3000)   # timeout 3s
        req.setsockopt(zmq.LINGER, 0)
        req.connect(f"tcp://{self.registry_host}:{self.registry_port}")

        payload = {
            "type": "Register",
            "id": self.id,
            "ip": self.host,
            "port": self.pub_port,
            "sub_port": self.sub_port,
            "aud_pub_port": self.aud_pub_port,
            "aud_sub_port": self.aud_sub_port,
            "vid_pub_port": self.vid_pub_port,
            "vid_sub_port": self.vid_sub_port,
            "hb_port": self.hb_port,
        }

        for attempt in range(5):
            try:
                req.send_json(payload)
                resp = req.recv_json()
                if resp.get("status") == "ok":
                    print(f"[{self.id}] Registrado no Registry com sucesso.")
                    req.close()
                    return
                else:
                    print(f"[{self.id}] Registry respondeu erro: {resp}")
            except zmq.ZMQError as e:
                print(f"[{self.id}] Tentativa {attempt+1} de registro falhou: {e}")
                time.sleep(2)

        print(f"[{self.id}] Não foi possível registrar no Registry. Continuando mesmo assim.")
        req.close()

    # ------------------------------------------------------------------
    # Heartbeat loop
    # ------------------------------------------------------------------
    def _heartbeat_loop(self):
        print(f"[{self.id}] Heartbeat iniciado ♥")
        while self.running:
            self.hb_socket.send_string(f"HB/{self.id}|ALIVE")
            time.sleep(2)

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------
    def start(self):
        # Registra no registry antes de começar
        threading.Thread(target=self._register, daemon=True).start()

        # Heartbeat em thread separada
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

        # Proxies em threads separadas
        threading.Thread(target=self._proxy_txt, daemon=True).start()
        threading.Thread(target=self._proxy_aud, daemon=True).start()
        threading.Thread(target=self._proxy_vid, daemon=True).start()

        print(f"[{self.id}] Proxies iniciados.")

        # Mantém vivo
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown()

    def _proxy_txt(self):
        print(f"[{self.id}] Proxy TXT iniciado.")
        try:
            zmq.proxy(self.frontend, self.backend)
        except zmq.ZMQError as e:
            if self.running:
                print(f"[{self.id}] Erro no proxy TXT: {e}")

    def _proxy_aud(self):
        print(f"[{self.id}] Proxy AUD iniciado.")
        try:
            zmq.proxy(self.aud_frontend, self.aud_backend)
        except zmq.ZMQError as e:
            if self.running:
                print(f"[{self.id}] Erro no proxy AUD: {e}")

    def _proxy_vid(self):
        print(f"[{self.id}] Proxy VID iniciado.")
        try:
            zmq.proxy(self.vid_frontend, self.vid_backend)
        except zmq.ZMQError as e:
            if self.running:
                print(f"[{self.id}] Erro no proxy VID: {e}")

    def _shutdown(self):
        self.running = False
        self.frontend.close()
        self.backend.close()
        self.aud_frontend.close()
        self.aud_backend.close()
        self.vid_frontend.close()
        self.vid_backend.close()
        self.hb_socket.close()
        self.context.term()
        print(f"[{self.id}] Encerrado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inicia um broker ZMQ.")
    parser.add_argument("--id",       type=str, default="BROKER1")
    parser.add_argument("--host",     type=str, default="localhost")
    parser.add_argument("--pub-port", type=int, default=5555)
    parser.add_argument("--sub-port", type=int, default=5556)
    parser.add_argument("--aud-pub-port", type=int, default=5557)
    parser.add_argument("--aud-sub-port", type=int, default=5558)
    parser.add_argument("--vid-pub-port", type=int, default=5559)
    parser.add_argument("--vid-sub-port", type=int, default=5560)
    parser.add_argument("--hb-port",  type=int, default=5561)
    parser.add_argument("--registry-host", type=str, default=REGISTRY_HOST)
    parser.add_argument("--registry-port", type=int, default=REGISTRY_PORT)
    args = parser.parse_args()

    broker = Broker(
        broker_id=args.id,
        host=args.host,
        pub_port=args.pub_port,
        sub_port=args.sub_port,
        aud_pub_port=args.aud_pub_port,
        aud_sub_port=args.aud_sub_port,
        vid_pub_port=args.vid_pub_port,
        vid_sub_port=args.vid_sub_port,
        hb_port=args.hb_port,
        registry_host=args.registry_host,
        registry_port=args.registry_port,
    )
    broker.start()