import zmq
import json

def start_registry():
    context = zmq.Context()
    # Socket REP (Responde a perguntas)
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5550") # Porta padrão do Registry

    # Banco de dados temporário de brokers ativos
    # Formato: {"ID": {"ip": "127.0.0.1", "port": "5555", "status": "online"}}
    brokers_disponiveis = {}

    print("[Registry] Aguardando brokers e clientes na porta 5550...")

    while True:
        try:
            # Recebe o pedido (JSON)
            mensagem = socket.recv_json()

            # Um broker avisando que ligou
            if mensagem.get("type") == "Register":
                b_id = mensagem["id"]
                brokers_disponiveis[b_id] = {
                    "ip": mensagem["ip"],
                    "port": mensagem["port"],
                    "status": "online"
                }
                socket.send_string("Registrado_com_sucesso")
                print(f"[Registry] Broker {b_id} conectado em {mensagem['ip']}:{mensagem['port']}")

            # Um cliente pedindo um broker para conectar
            elif mensagem.get("type") == "Get_broker":
                # Retorna a lista de brokers que estão online
                socket.send_json(brokers_disponiveis)
                print("[Registry] Lista de brokers enviada para um cliente.")

        except Exception as e:
            print(f"Erro no registry: {e}")

if __name__ == "__main__":
    start_registry()
