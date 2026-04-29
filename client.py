import zmq
import threading
import time

REGISTRY_HOST = "localhost"
REGISTRY_PORT = 5550
BROKER_TIMEOUT = 5   # segundos sem heartbeat → broker considerado morto

class Cliente:
    def __init__(self, identity: str, room: str,
                 msgCallBack,
                 brokerStatusCallBack=None,
                 registry_host: str = REGISTRY_HOST,
                 registry_port: int = REGISTRY_PORT):

        self.identity = identity
        self.room = room
        self.msgCallBack = msgCallBack
        self.brokerStatusCallBack = brokerStatusCallBack
        self.registry_host = registry_host
        self.registry_port = registry_port

        self.context = zmq.Context()
        self.running = True

        # Estado do broker atual
        self.broker_ip   = None
        self.broker_port = None   # porta de publicação (XSUB do broker)
        self.broker_sub_port = None  # porta de assinatura (XPUB do broker)
        self.broker_hb_port  = None

        self.ultimoHeartbeat = time.time()
        self.brokerVivo = False

        # Socket de publicação — será (re)criado em _conectar_broker
        self.pub = None
        self._pub_lock = threading.Lock()

        # Conecta em background — não bloqueia a GUI
        threading.Thread(target=self._descobrir_e_conectar, daemon=True).start()

    # ------------------------------------------------------------------
    # Service discovery — consulta o Registry
    # ------------------------------------------------------------------
    def _consultar_registry(self) -> dict | None:
        req = self.context.socket(zmq.REQ)
        req.setsockopt(zmq.RCVTIMEO, 3000)  # 3s timeout na resposta
        req.setsockopt(zmq.LINGER, 0)
        req.connect(f"tcp://{self.registry_host}:{self.registry_port}")
        try:
            req.send_json({"type": "Get_broker"})
            resp = req.recv_json()
            if resp.get("status") == "ok":
                return resp["broker"]
            else:
                print(f"[Cliente] Registry sem brokers: {resp.get('msg')}")
                return None
        except zmq.ZMQError as e:
            # EAGAIN = timeout expirou (registry offline ou sem resposta)
            if e.errno == zmq.EAGAIN:
                print(f"[Cliente] Registry não respondeu (timeout). Tentando novamente...")
            else:
                print(f"[Cliente] Erro consultando registry: {e}")
            return None
        finally:
            # Sempre fecha e descarta o socket REQ — não reutilizar após erro
            req.close()

    # ------------------------------------------------------------------
    # Conexão / reconexão a um broker
    # ------------------------------------------------------------------
    def _conectar_broker(self, ip: str, pub_port: int, sub_port: int, hb_port: int):
        """(Re)cria o socket PUB apontando para o novo broker."""
        with self._pub_lock:
            if self.pub:
                self.pub.close()
            self.pub = self.context.socket(zmq.PUB)
            self.pub.connect(f"tcp://{ip}:{pub_port}")

        self.broker_ip       = ip
        self.broker_port     = pub_port
        self.broker_sub_port = sub_port
        self.broker_hb_port  = hb_port
        self.ultimoHeartbeat = time.time()
        self.brokerVivo      = True
        print(f"[Cliente] Conectado ao broker {ip}:{pub_port}")

    def _descobrir_e_conectar(self):
        for attempt in range(10):
            broker = self._consultar_registry()
            if broker:
                self._conectar_broker(
                    ip=broker["ip"],
                    pub_port=int(broker["port"]),
                    sub_port=int(broker.get("sub_port", int(broker["port"]) + 1)),
                    hb_port=int(broker.get("hb_port", 5559)),
                )
                return
            print(f"[Cliente] Nenhum broker disponível (tentativa {attempt+1}). Aguardando...")
            time.sleep(2)
        print("[Cliente] Não foi possível conectar a nenhum broker.")

    # ------------------------------------------------------------------
    # Threads de escuta
    # ------------------------------------------------------------------
    def threadEscuta(self):
        threading.Thread(target=self._escutar_txt,       daemon=True).start()
        threading.Thread(target=self._escutar_heartbeat, daemon=True).start()
        threading.Thread(target=self._monitor_broker,    daemon=True).start()

    def _escutar_txt(self):
        # Aguarda até ter um broker disponível
        while self.running and self.broker_ip is None:
            time.sleep(0.2)
        if not self.running:
            return

        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect(f"tcp://{self.broker_ip}:{self.broker_sub_port}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, f"TXT/{self.room}")

        while self.running:
            try:
                if subscriber.poll(timeout=500):
                    message = subscriber.recv_string(zmq.NOBLOCK)
                    partes = message.split("|", 2)
                    if len(partes) == 3:
                        _, user, msg = partes
                        if user != self.identity:
                            self.msgCallBack(user, msg)
            except zmq.ZMQError as e:
                if self.running:
                    print(f"[Cliente] Erro TXT: {e}")

        subscriber.close()

    def _escutar_heartbeat(self):
        # Aguarda até ter um broker disponível
        while self.running and self.broker_ip is None:
            time.sleep(0.2)
        if not self.running:
            return

        subscriber = self.context.socket(zmq.SUB)
        subscriber.connect(f"tcp://{self.broker_ip}:{self.broker_hb_port}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "HB/")

        while self.running:
            try:
                if subscriber.poll(timeout=500):
                    subscriber.recv_string(zmq.NOBLOCK)
                    self.ultimoHeartbeat = time.time()
            except zmq.ZMQError as e:
                if self.running:
                    print(f"[Cliente] Erro HB: {e}")

        subscriber.close()

    # ------------------------------------------------------------------
    # Monitor de broker — detecta falha e faz failover
    # ------------------------------------------------------------------
    def _monitor_broker(self):
        while self.running:
            morto = (time.time() - self.ultimoHeartbeat) > BROKER_TIMEOUT

            if morto and self.brokerVivo:
                self.brokerVivo = False
                print(f"[Cliente] Broker perdido. Tentando failover...")
                if self.brokerStatusCallBack:
                    self.brokerStatusCallBack(False)
                self._failover()

            elif not morto and not self.brokerVivo:
                self.brokerVivo = True
                print(f"[Cliente] Broker reconectado.")
                if self.brokerStatusCallBack:
                    self.brokerStatusCallBack(True)

            time.sleep(1)

    def _failover(self):
        """Consulta o registry e troca para outro broker disponível."""
        for attempt in range(20):
            if not self.running:
                return
            broker = self._consultar_registry()
            if broker:
                new_ip   = broker["ip"]
                new_port = int(broker["port"])
                # Evita reconectar no mesmo broker que acabou de cair
                if new_ip == self.broker_ip and new_port == self.broker_port:
                    print(f"[Cliente] Registry retornou o mesmo broker offline. Aguardando...")
                else:
                    self._conectar_broker(
                        ip=new_ip,
                        pub_port=new_port,
                        sub_port=int(broker.get("sub_port", new_port + 1)),
                        hb_port=int(broker.get("hb_port", 5559)),
                    )
                    # Notifica GUI que voltou
                    if self.brokerStatusCallBack:
                        self.brokerStatusCallBack(True)
                    return
            time.sleep(3)
        print("[Cliente] Failover esgotado. Sem brokers disponíveis.")

    # ------------------------------------------------------------------
    # Envio de mensagem
    # ------------------------------------------------------------------
    def enviarMsg(self, msg: str):
        if not msg:
            return
        payload = f"TXT/{self.room}|{self.identity}|{msg}"
        with self._pub_lock:
            if self.pub:
                try:
                    self.pub.send_string(payload)
                except zmq.ZMQError as e:
                    print(f"[Cliente] Erro ao enviar mensagem: {e}")

    # ------------------------------------------------------------------
    # Desconexão
    # ------------------------------------------------------------------
    def desconectar(self):
        self.running = False
        self.enviarMsg("saiu da ligação")
        time.sleep(0.5)
        with self._pub_lock:
            if self.pub:
                self.pub.close()
                self.pub = None
        self.context.term()

# end