import socket
import threading
import paramiko
import time
import sys
from datetime import datetime  
import os


# ==========================================
#  CONFIGURAÇÕES E SISTEMA DE ARQUIVOS (VFS)
# ==========================================

# Nome do arquivo onde a chave permanente será salva
KEY_FILE = "honeypot.key"

# Se o arquivo já existir, ele usa a mesma chave de antes
if os.path.exists(KEY_FILE):
    HOST_KEY = paramiko.RSAKey.from_private_key_file(KEY_FILE)
else:
    # Se não existir (primeira execução), ele gera uma e salva no arquivo
    print("[*] Gerando chave SSH persistente...")
    HOST_KEY = paramiko.RSAKey.generate(2048)
    HOST_KEY.write_private_key_file(KEY_FILE)

VFS = {
    'passwords.txt': 'admin:123456\nroot:toor\nbackup:admin123\n',
    'config.ini': '[DEFAULT]\nDebug=False\nSecretKey=super_secret_key_123\n',
    'flag.txt': 'CTF{h0n3yp0t_1s_w0rk1ng}\n'
}

# ==========================================
# SERVIDOR SSH (SHELL FALSO)
# ==========================================

class FakeSSHServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        print(f"[*] ALERTA SSH: Login capturado -> Usuário: '{username}' | Senha: '{password}'")
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_ssh_client(client_socket, addr):
    ip_atacante = addr[0]
    print(f"[*] Nova conexão SSH recebida de {ip_atacante}:{addr[1]}")
    
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        server = FakeSSHServer()
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            print("[-] Erro na negociação SSH.")
            return 
        channel = transport.accept(20)
        if channel is None:
            print("[-] Canal não pôde ser aberto.")
            return
        server.event.wait(10)
        if not server.event.is_set():
            print("[-] Cliente não solicitou um shell.")
            return
        
        channel.send("Microsoft Windows [versão 10.0.26200.8737] (c) Microsoft Corporation. Todos os direitos reservados.\r\n\r\n")
        channel.send("root@server:~# ")
        
        command = ""
        # Inicializa o marcador de tempo do último comando (começa contando do login)
        ultimo_comando_tempo = time.time()

        while True:
            char = channel.recv(1024).decode('utf-8')
            if not char:
                break
            if char in ('\x08', '\x7f'): 
                if len(command) > 0:
                    command = command[:-1]
                    channel.send('\b \b')
                continue
            channel.send(char)
            
            if char == '\r':
                channel.send('\n')
                full_command = command.strip()
                
                # --- SISTEMA DE LOGS ---
                agora = time.time()
                tempo_decorrido = agora - ultimo_comando_tempo
                ultimo_comando_tempo = agora  # Atualiza para o comando atual
                
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Grava no arquivo honeypot.txt sem travar a execução
                with open("honeypot.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(
                        f"[{timestamp}] IP: {ip_atacante} | "
                        f"Comando: '{full_command}' | "
                        f"Intervalo: {tempo_decorrido:.2f}s\n"
                    )
                # ------------------------

                cmd_parts = full_command.split()
                if not cmd_parts:
                    # Correção: Se pressionar Enter vazio, redefine e limpa sem quebrar o script
                    command = ""
                    channel.send("root@server:~# ")
                    continue

                base_cmd = cmd_parts[0].lower()
                
                if base_cmd == 'exit':
                    channel.send("logout\r\n")
                    break
                elif base_cmd in ['dir', 'ls']:
                    files = "  ".join(VFS.keys())
                    channel.send(files + "\r\n")
                elif base_cmd == 'cat':
                    if len(cmd_parts) > 1:
                        filename = cmd_parts[1]
                        if filename in VFS:
                            channel.send(VFS[filename] + "\r\n")
                        else:
                            channel.send(f"cat: {filename}: No such file or directory\r\n")
                    else:
                        channel.send("cat: missing operand\r\n")
                elif base_cmd == 'curl':
                    if len(cmd_parts) == 1:
                        channel.send("curl: try 'curl --help' for more information\r\n")
                    elif cmd_parts[1] in ['-h', '--help']:
                        help_menu = """\r
Usage: curl [options...] <url>
-d, --data <data>            HTTP POST data
-f, --fail                   Fail fast with no output on HTTP errors
-I, --head                   Show document info only
-H, --header <header/@file>  Pass custom header(s) to server
-h, --help <subject>         Get help for commands
-o, --output <file>          Write to file instead of stdout
-O, --remote-name            Write output to file named as remote file
-i, --show-headers           Show response headers in output
-s, --silent                 Silent mode
-T, --upload-file <file>     Transfer local FILE to destination
-u, --user <user:password>   Server user and password
-A, --user-agent <name>      Send User-Agent <name> to server
-v, --verbose                Make the operation more talkative
-V, --version                Show version number and quit

This is not the full help; this menu is split into categories.
Use "--help category" to get an overview of all categories, which are:
auth, connection, curl, deprecated, dns, file, ftp, global, http, imap, lda, output, pop3, post, proxy, scp, sftp,smtp, ssh, telnet, tftp, timeout, tls, upload, verbose.
Use "--help all" to list all options\r\n"""
                        channel.send(help_menu.replace('\n', '\r\n'))
                    else:
                        url = cmd_parts[1]
                        clean_url = url.rstrip('/')
                        filename = clean_url.split('/')[-1] if '/' in clean_url else "index.html"
                        
                        if not filename or '.' not in filename:
                            if "sh" in url:
                                filename = "script.sh"
                            else:
                                filename = "index.html"
                        
                        channel.send("\r\n")
                        time.sleep(0.2)
                        curl_progress = (
                            "  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\r\n"
                            "                                 Dload  Upload   Total   Spent    Left  Speed\r\n"
                            "100  1024  100  1024    0     0   4096      0 --:--:-- --:--:-- --:--:--  4112\r\n\r\n"
                        )
                        channel.send(curl_progress)
                        VFS[filename] = '#!/bin/bash\necho "Malware executed successfully!"\n'
                elif base_cmd == 'whoami':
                    channel.send("root\r\n")
                elif base_cmd == 'pwd':
                    channel.send("/root\r\n")
                else:
                    channel.send(f"{base_cmd}: command not found\r\n")
                
                command = ""
                channel.send("root@server:~# ")
            elif char == '\x03':
                channel.send("^C\r\nroot@server:~# ")
                command = ""
            else:
                command += char
    except Exception as e:
        print(f"[-] Erro na conexão com {addr[0]}: {e}")
    finally:
        client_socket.close()

def iniciar_ssh(host='0.0.0.0', port=2222):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   
    try:
        server_socket.bind((host, port))
        server_socket.listen(100)
        print(f"[+] Servidor SSH escutando em {host}:{port}")      
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_ssh_client, args=(client_socket, addr))
            client_thread.start()        
    except Exception as e:
        print(f"[-] Falha ao iniciar o honeypot SSH: {e}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    try:
        print("[*] Iniciando Honeypot...")
        iniciar_ssh()
    except KeyboardInterrupt:
        print("\nEncerrado")