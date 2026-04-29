# GoogleMeet_Replica

Trabalho para Sistemas Distribuídos 2026 - Ferramenta de Videoconferência com Áudio, Vídeo e Texto.

## Objetivo do Projeto

Desenvolver uma ferramenta de videoconferência (Vídeo, Áudio e Texto) que permita usuários simultâneos em ligações individuais e em grupo, utilizando Python 3 e ZeroMQ para comunicação assíncrona.

## TODO - Próximos Passos

Baseado nos requisitos do professor:

- [ ] **Múltiplos Brokers**: Implementar cluster com comunicação entre brokers (ROUTER/DEALER).
- [ ] **QoS por Mídia**: Buffer, retry para texto; drop para vídeo; baixa latência para áudio.
- [ ] **Service Discovery Avançado**: Round-robin, broadcast, seleção por latência.
- [ ] **Fault Tolerance Completa**: Manutenção de sessão, impacto mínimo na reconexão.
- [ ] **Vídeo Múltiplo**: Suporte a vídeo de múltiplos usuários na GUI (grade ou seletor).
- [ ] **Testes e Demonstração**: Simular cenários de falha e recuperação.
- [ ] **Documentação Técnica**: Detalhar arquitetura, padrões e estratégias.


## Requisitos Implementados

### ✅ Linguagem e Bibliotecas
- **Python 3**: Linguagem principal do projeto.
- **ZeroMQ**: Comunicação assíncrona via modelo PUB/SUB.
- **Broker Central**: Entidade centralizada para distribuição de mensagens em canais separados (Texto, Áudio, Vídeo).

### ✅ Funcionalidades Básicas
- **Texto**: Chat em tempo real entre participantes.
- **Áudio**: Captura e transmissão de áudio via pyaudio.
- **Vídeo**: Captura de webcam e transmissão de frames via OpenCV.
- **Interface Desktop**: GUI completa com ttkbootstrap, tkinter e PIL.

### ✅ Arquitetura Atual
- **1 Broker Central** com múltiplos clientes.
- **Canais Separados**:
  - Mensagens (TXT): `localhost:5555/5556`
  - Áudio (AUD): `localhost:5557/5558`
  - Vídeo (VID): `localhost:5559/5560`
  - Heartbeat (HB): `localhost:5561`
- **Modelo XPUB/XSUB** para roteamento eficiente.

### ✅ Concorrência e Processamento Assíncrono
- **Threads obrigatórias** para:
  - Captura de mídia (áudio/vídeo)
  - Envio de dados
  - Recepção e renderização
- **Processamento paralelo** para evitar bloqueios na GUI.

### ✅ Identidade e Sessão
- **Login simples**: Nickname único por usuário.
- **Salas (Grupos)**: Entrada em salas por nome (ex: "SALA").
- **Controle básico**: Entrada/saída com notificações.

### 🔄 Arquitetura Distribuída com Múltiplos Brokers
- **Status**: Parcialmente implementado (1 broker, mas preparado para expansão).
- **Implementado**: Registry para descoberta de brokers.
- **Pendente**: Cluster de N brokers cooperando, roteamento entre brokers via ROUTER/DEALER.

### 🔄 Descoberta de Serviços (Service Discovery)
- **Status**: Básico implementado.
- **Implementado**: Registry simples com registro dinâmico de brokers.
- **Pendente**: Seleção inteligente (round-robin, menor latência), broadcast via ZeroMQ.

### 🔄 Tolerância a Falhas (Fault Tolerance)
- **Status**: Parcialmente implementado.
- **Implementado**: Heartbeat via PUB/SUB, detecção de falha, reconexão automática.
- **Pendente**: Manutenção de sessão com mínimo impacto, timeout + failover robusto.

### ❌ Controle de Qualidade (QoS)
- **Status**: Não implementado.
- **Pendente**:
  - **Texto**: Garantia de entrega (retry).
  - **Áudio**: Baixa latência (pode perder pacotes).
  - **Vídeo**: Taxa adaptativa, buffer simples, drop de frames.

### ✅ Demonstração
- **Simulação atual**: Múltiplos clientes conectados ao broker central.
- **Pendente**: Simulação de falha de broker, reconexão automática, comunicação entre brokers.

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