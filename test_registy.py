"""
Rode este script com o registry.py já ativo para verificar conectividade.
python test_registry.py
"""
import zmq

context = zmq.Context()
req = context.socket(zmq.REQ)
req.connect("tcp://localhost:5550")
req.setsockopt(zmq.RCVTIMEO, 3000)

print("Enviando Get_broker para o registry...")
try:
    req.send_json({"type": "Get_broker"})
    resp = req.recv_json()
    print(f"Resposta: {resp}")
except zmq.Again:
    print("TIMEOUT — registry não respondeu. Verifique se registry.py está rodando.")
except Exception as e:
    print(f"Erro: {e}")
finally:
    req.close()
    context.term()