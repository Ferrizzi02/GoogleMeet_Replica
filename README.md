# GoogleMeet_Replica
Trabalho feito para Sistemas distribuídos 2026.

> [!WARNING]
> CUIDADO: homens trabalhando

**TO DO:**
- [x] Texto
- [ ] Audio
- [ ] Video
- [ ] Comunicação entre brokers

## Arquitetura:
1 Broker ... N clients.
XPUB/XSUB

### Canais
Mensagens: `localhost:5555/TXT`
Audio: `localhost:5555/AUD`
Video: `localhost:5555/VID`

## Instalação
Instação de pacotes
```bash
pip install -r requirements.txt
```

Rodar broker.py
```bash
python broker.py
```

Para cada usuario rodar o gui.py