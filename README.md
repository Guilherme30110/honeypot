```markdown
# 🛡️ SSH Honeypot - Simulador de Shell Falso & Monitoramento de Logs

Este é um projeto prático de caráter **estritamente educacional e experimental** que desenvolvi para explorar os conceitos de *Cyber Threat Intelligence*, engenharia de *fake shells* e análise comportamental de atacantes. 

O script implementa um servidor SSH de baixa/média interação (*Low-to-Medium Interaction Honeypot*) capaz de simular um ambiente vulnerável, capturar tentativas de autenticação e registrar em tempo real as ações executadas por agentes maliciosos ou ferramentas automatizadas de varredura (*bots*).

---

## 📊 Visão Geral do Projeto

A ferramenta intercepta conexões na porta configurada e entrega um ambiente emulado baseado em uma estrutura de arquivos mantida exclusivamente em memória. Com isso, é possível induzir o atacante ao erro, permitindo coletar dados cruciais sobre TTPs (*Tactics, Techniques, and Procedures*) sem expor o sistema operacional real.

### ⚙️ Arquitetura e Componentes Técnicos
O desenvolvimento foi estruturado utilizando bibliotecas nativas do Python e o framework criptográfico **Paramiko**:
* **`socket` & `threading`:** Gerenciamento de sockets de rede e concorrência multithread, permitindo lidar com múltiplas conexões simultâneas de forma assíncrona.
* **`paramiko.ServerInterface`:** Customização completa do handshake SSH, negociação de chaves RSA e emulação dos canais de requisição de terminal (*pty* e *shell*).
* **Virtual File System (VFS):** Um dicionário em memória que mapeia arquivos fictícios de sistema, mitigando completamente o risco de modificações ou escapes para o host real.

---

## 🚀 Recursos Principais

* **🔑 Captura Universal de Credenciais:** O mecanismo de autenticação aceita qualquer par de usuário/senha. O objetivo é registrar exaustivamente dicionários de *brute-force* utilizados na internet.
* **📂 Shell Emulado Interativo:** O terminal falso simula um prompt do Windows/Linux que aceita comandos essenciais de navegação e reconhecimento (`ls`, `dir`, `cat`, `pwd`, `whoami`).
* **🌐 Engenharia Social via `curl`:** Se o atacante tentar baixar um malware usando o comando `curl`, o script exibe uma barra de progresso perfeitamente emulada e injeta um script fictício (`script.sh` ou `index.html`) no sistema de arquivos virtual para manter o engajamento do invasor.
* **💾 Chave Criptográfica Persistente:** Armazena a chave privada RSA gerada (`honeypot.key`) localmente, garantindo que o fingerprint do servidor não mude entre reinicializações, o que levantaria suspeitas em bots mais avançados.

---

## 🪵 Inteligência de Logs: O Diferencial Analítico

O grande destaque deste projeto está na estrutura métrica do sistema de auditoria. Cada interação é registrada no arquivo `honeypot.txt` com um tratamento de telemetria temporal:

| Campo do Log | Descrição | Utilidade Analítica |
| :--- | :--- | :--- |
| **`Timestamp`** | Data e hora exata do evento | Linha do tempo da intrusão. |
| **`IP`** | Endereço de origem do atacante | Mapeamento geográfico e listas de bloqueio (IOCs). |
| **`Comando`** | String exata digitada no prompt | Identificação do objetivo do ataque (reconhecimento, pivoting, download). |
| **`Intervalo`** | Tempo decorrido (em segundos) desde o último comando | **Diferencial comportamental:** Permite distinguir se a ação foi tomada por um script/bot automatizado (milissegundos) ou por um operador humano (segundos/minutos). |

### Exemplo de Saída do Log:
```text
[2026-07-12 12:00:01] IP: 192.168.1.50 | Comando: 'whoami' | Intervalo: 0.12s
[2026-07-12 12:00:05] IP: 192.168.1.50 | Comando: 'cat passwords.txt' | Intervalo: 4.35s

```

---

## 🛠️ Instalação e Execução

### 1. Pré-requisitos

Certifique-se de ter o Python 3.x instalado em seu ambiente. A única dependência externa necessária é o `paramiko`:

```bash
pip install paramiko

```

### 2. Executando o Honeypot

Por padrão, o servidor está configurado para escutar na porta de alta numeração `2222` (evitando a necessidade de privilégios de root/administrador):

```bash
python honeypot.py

```

### 3. Simulando um Ataque (Ambiente de Teste)

Para validar o funcionamento a partir de uma máquina cliente na mesma rede:

```bash
ssh qualquer_usuario@<IP_DO_HONEYPOT> -p 2222

```

*Insira qualquer senha quando solicitado para ganhar acesso ao prompt emulado.*

---

## 🔒 Notas de Segurança e Isenção de Responsabilidade

> ⚠️ **AVISO CRÍTICO DE SEGURANÇA:** Este Honeypot foi desenvolvido exclusivamente para fins de estudo, laboratórios controlados e demonstrações de portfólio de conceitos básicos.
> Ele **NÃO** possui mecanismos avançados de isolamento de processos (*hardened sandboxing*), proteção contra ataques de negação de serviço (DoS) na camada de socket, ou validações robustas contra fuzzing avançado do protocolo SSH.
> Portanto, **não recomendo e não me responsabilizo** pela exposição deste script diretamente na internet pública (WAN) sem que ele esteja devidamente isolado dentro de um ambiente Docker dedicado, instâncias de nuvem descartáveis ou sub-redes/VLANs restritas de laboratório. O uso indevido deste código é de inteira responsabilidade do usuário.

```

```
