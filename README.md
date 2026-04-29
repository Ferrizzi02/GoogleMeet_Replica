# GoogleMeet_Replica

Trabalho para Sistemas Distribuídos 2026 - Ferramenta de Videoconferência com Áudio, Vídeo e Texto.

## Objetivo do Projeto

Desenvolver uma ferramenta de videoconferência (Vídeo, Áudio e Texto) que permita usuários simultâneos em ligações individuais e em grupo, utilizando Python 3 e ZeroMQ para comunicação assíncrona.

## TODO - Próximos Passos

Baseado nos requisitos do professor:

- [x] **Linguagem e Bibliotecas**: Uso de Python 3 e ZeroMQ para comunicação assíncrona (PUB/SUB).
- [x] **Broker Central**: Entidade centralizada com canais separados unidirecionais para Áudio, Vídeo e Texto.
- [x] **Funcionalidades Básicas**: Suporte a Vídeo, Áudio e Texto em ligações individuais e em grupo.
- [x] **Concorrência Assíncrona**: Uso de threads para captura de mídia, envio, recepção e renderização.
- [x] **Identidade e Sessão**: Login simples com ID único, controle de presença e entrada/saída de salas (grupos).
- [x] **Service Discovery Básico**: Registro dinâmico de brokers via registry simples.
- [x] **Fault Tolerance Parcial**: Heartbeat para detecção de falha e reconexão automática.
- [x] **Vídeo Múltiplo**: Suporte a vídeo de múltiplos usuários na GUI (grade 3x3).
- [ ] **Múltiplos Brokers**: Implementar cluster de N brokers cooperando com comunicação via ROUTER/DEALER.
- [ ] **Service Discovery Avançado**: Seleção inteligente de broker (round-robin, menor latência, broadcast).
- [ ] **Fault Tolerance Completa**: Manutenção de sessão com mínimo impacto na reconexão.
- [ ] **QoS por Mídia**: Buffer/retry para texto; baixa latência/drop para áudio/vídeo; taxa adaptativa.
- [ ] **Testes e Demonstração**: Simular cenários de falha, reconexão e comunicação entre brokers.
- [ ] **Documentação Técnica**: Detalhar arquitetura distribuída, padrões ZeroMQ e estratégias.

## Instalação e Execução

### Pré-requisitos
```bash
pip install -r requirements.txt
```

### Ordem de Inicialização
1. **Registry** (descoberta de serviços):
   ```bash
   python registry.py
   ```

2. **Broker** (servidor de mensagens):
   ```bash
   python broker.py --id BROKER1
   ```

3. **Clientes** (GUI para usuários):
   ```bash
   python gui.py  # Executar múltiplas instâncias para simular usuários
   ```

### Teste do Registry
```bash
python test_registy.py
```

## Arquitetura Técnica

### Padrões ZeroMQ Utilizados
- **XPUB/XSUB**: Para canais de mensagens (TXT, AUD, VID).
- **PUB/SUB**: Para heartbeat e notificações.
- **REQ/REP**: Para comunicação com registry.

### Estratégia de Tolerância a Falhas
- **Heartbeat**: Clientes monitoram brokers via PUB/SUB.
- **Failover**: Reconexão automática ao registry para novo broker.
- **Timeout**: 5 segundos sem heartbeat → broker considerado offline.

### Módulos do Código
- `registry.py`: Serviço de descoberta.
- `broker.py`: Broker central com proxies para cada mídia.
- `client.py`: Cliente com threads para envio/recepção.
- `gui.py`: Interface gráfica e integração de mídia.
- `audio.py`: Classe para captura/reprodução de áudio.
- `camera.py`: Classe para captura de vídeo.

---

> [!NOTE]
> Projeto em desenvolvimento ativo.