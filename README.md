# GoogleMeet_Replica
Trabalho feito para Sistemas distribuídos 2026.

> [!WARNING]
> CUIDADO: homens trabalhando

**TO DO:**
- [x] Texto
- [ ] Audio
- [ ] Video
- [ ] Função para reconectar com o broker
- [ ] ID unico para os brokers
- [ ] Comunicação entre brokers

## Arquitetura:
1 Broker ... N clients.
XPUB/XSUB

### Canais
Mensagens: `localhost:5555/TXT`
Audio: `localhost:5557/AUD`
Video: `localhost:5558/VID`
Heartbeat `localhost:5559/VID`

## Instalação
Instação de pacotes
```bash
pip install -r requirements.txt
```

Ordem de execução: registry.py -> broker.py -> gui.py


Rodar broker.py
```bash
python broker.py
```

Para cada usuario rodar o gui.py