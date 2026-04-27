import zmq

context = zmq.Context()

#clientes postan XSUB
frontend = context.socket(zmq.XSUB)
frontend.bind("tcp://*:5555")

#backend onde os clientes se inscreven.
backend = context.socket(zmq.XPUB)
backend.bind("tcp://*:5556")

print("[Broker] Broker ativo, recebe no 5555 e reparte no 5556")

#proxy
try:
    zmq.proxy(frontend,backend)
except KeyboardInterrupt:
    pass
finally:
    frontend.close()
    backend.close()
    context.term()