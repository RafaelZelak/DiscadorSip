
import pjsua2 as pj
import socket
import datetime
import threading
import tkinter as tk
import time
import re
import pygame
# Variável global para o endpoint
ep = None
call_onoff = False
incoming_call = None
call_number = None
answer_call = False
caller_number = None
root = None 

def treat_caller_number():
    global caller_number, caller_number_treated
    # Remove everything between < > including the symbols and also the double quotes
    cleaned_number = re.sub(r'<[^>]*>', '', caller_number).replace('"', '').strip()
    
    # Check if it is a phone number or a name
    if cleaned_number.isdigit():  # Check if the cleaned_number is a digit (phone number)
        if len(cleaned_number) == 10:  # Fixed line phone number
            caller_number_treated = f'({cleaned_number[:2]}){cleaned_number[2:6]}-{cleaned_number[6:]}'
        elif len(cleaned_number) == 11:  # Mobile phone number
            caller_number_treated = f'({cleaned_number[:2]}){cleaned_number[2:7]}-{cleaned_number[7:]}'
        else:
            caller_number_treated = cleaned_number  # Return the number as is if it does not match expected lengths
    else:  # It's a name
        caller_number_treated = cleaned_number
    
    with open('caller.txt', 'w') as arquivo:
        arquivo.write(caller_number_treated)

def wait_for_user_input():
    global caller_number, answer_call, caller_number_treated
    pygame.mixer.init()
    root = tk.Tk()
    root.title("Chamada")
    pygame.mixer.music.load("sound/CHAMADA.mp3") 
    pygame.mixer.music.play()
    def atender():
        global answer_call
        answer_call = True
        atualizar_estado_ligacao('desconectada')
        pygame.mixer.music.stop()
        root.destroy()

    def recusar():
        global answer_call
        answer_call = False
        atualizar_estado_ligacao('conectada')
        pygame.mixer.music.stop()
        root.destroy()

    def fechar_janela():
        global answer_call
        answer_call = False
        pygame.mixer.music.stop()
        root.destroy()
        

    titulo = tk.Label(root, text="Chamada Recebida:", font=("Verdana", 15), bg="#333333", fg="#F0F0F0")
    titulo.pack(pady=5)
    treat_caller_number()
    chamada = tk.Label(root, text=caller_number_treated, font=("Verdana", 18), bg="#666666", fg="#F0F0F0", padx=190, pady=15)
    chamada.pack(pady=12)
    atender_btn = tk.Button(root, text="Atender", command=atender, bg="#718a70", fg="#F0F0F0", highlightthickness=0, highlightbackground="#333333", bd=0)
    recusar_btn = tk.Button(root, text="Recusar", command=recusar, bg="#8a7070", fg="#F0F0F0", highlightthickness=0, highlightbackground="#333333", bd=0)
    atender_btn.place(relx=0.27, rely=0.75, anchor='center', relwidth=0.43, relheight=0.22)
    recusar_btn.place(relx=0.73, rely=0.75, anchor='center', relwidth=0.43, relheight=0.22)

    largura = 354
    altura = 220
    root.configure(bg="#333333")
    root.geometry(f"{largura}x{altura}")
    root.after(7200, fechar_janela)  # Define um timer para fechar automaticamente após 7.2 segundos
    root.protocol("WM_DELETE_WINDOW", fechar_janela)  # Configura a ação padrão para fechar a janela
    root.mainloop()

    
# Função para ler configurações do arquivo
def ler_configuracoes_do_arquivo(arquivo):
    configuracoes = {}
    with open(arquivo, 'r') as file:
        for line in file:
            line = line.strip()
            if ': ' in line:
                key, value = line.split(': ', 1)
                configuracoes[key.strip()] = value.strip()
            else:
                print(f"Linha ignorada por estar malformada: {line}")
    return configuracoes

# Lendo as configurações do arquivo
configuracoes = ler_configuracoes_do_arquivo('config.cfg')
if not configuracoes:
    print("Erro: Não há configurações no arquivo.")
    exit(1)

SIP_SERVER = configuracoes.get('SIP Server')
USERNAME = configuracoes.get('Username')
EXTENSION = configuracoes.get('Extension')
PASSWORD = configuracoes.get('Password')

# Lista de codecs a serem utilizados
CODECS = ["PCMA/8000"]

# Função para atualizar o estado da ligação em um arquivo
def atualizar_estado_ligacao(estado):
    with open('estado_ligacao.txt', 'w') as file:
        file.write(estado)
        
def rebeber_ligação(estado):
    with open('recebando_licacao.txt', 'w') as file:
        file.write(estado)
    
def atender_ligação(estado):
    with open('atendido.txt', 'w') as file:
        file.write(estado)
         
# Classe para representar uma chamada
class MyCall(pj.Call):
    def __init__(self, account, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, account, call_id)
    
    def onCallState(self, prm):
        global call_info, call_number, answer_call
        call_info = self.getInfo()
        print(f"Call state changed to {call_info.stateText} for call ID: {self.getId()}")
        if call_info.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            print("Call disconnected")
            with open('caller.txt', 'w') as file:
                pass
            answer_call = False
            atualizar_estado_ligacao('desconectada')
            global incoming_call
            global call_number
            incoming_call = None
            now = datetime.datetime.now()
            datetime_string = now.strftime("%Y-%m-%d %H:%M:%S")
            with open('call.txt', 'r+') as file:
                lines = file.readlines()
                if len(lines) >= 4:
                    lines[3] = datetime_string + "\n"
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                else:
                    lines.extend(['\n'] * (4 - len(lines)))  # Adiciona linhas vazias se não houver 5 linhas
                    lines[3] = datetime_string + "\n"
                    file.seek(0)
                    file.writelines(lines)
                if len(lines) >= 5:
                    lines[4] = "Encerrado" + "\n"
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                else:
                    lines.extend(['\n'] * (5 - len(lines)))  # Adiciona linhas vazias se não houver 5 linhas
                    lines[4] = "Encerrado" + "\n"
                    file.seek(0)
                    file.writelines(lines)

        elif call_info.state == pj.PJSIP_INV_STATE_CONFIRMED:
            print("Call connected")
            atualizar_estado_ligacao('conectada')
            print(f"Call number: {call_number}")  # Imprimir o número da chamada conectada
            now = datetime.datetime.now()
            datetime_string = now.strftime("%Y-%m-%d %H:%M:%S")
            with open('call.txt', 'r+') as file:
                lines = file.readlines()
                if len(lines) >= 3:
                    lines[2] = datetime_string + "\n"
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                else:
                    lines.extend(['\n'] * (3 - len(lines)))  # Adiciona linhas vazias se não houver 5 linhas
                    lines[2] = datetime_string + "\n"
                    file.seek(0)
                    file.writelines(lines)
                if len(lines) >= 1:
                    lines[0] = "True" + "\n"
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                else:
                    lines.extend(['\n'] * (1 - len(lines)))  # Adiciona linhas vazias se não houver 5 linhas
                    lines[0] = "True" + "\n"
                    file.seek(0)
                    file.writelines(lines)
                if len(lines) >= 5:
                    lines[4] = "Andamento" + "\n"
                    file.seek(0)
                    file.writelines(lines)
                    file.truncate()
                else:
                    lines.extend(['\n'] * (5 - len(lines)))  # Adiciona linhas vazias se não houver 5 linhas
                    lines[4] = "Andamento" + "\n"
                    file.seek(0)
                    file.writelines(lines)
            
    def onCallMediaState(self, prm):
        global call_onoff
        call_info = self.getInfo()
        for media_info in call_info.media:
            if media_info.type == pj.PJMEDIA_TYPE_AUDIO:
                if media_info.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                    print("Call media active")
                    call_onoff = True
                    # Corrigindo a chamada para getAudioMedia() com índice 0
                    media = self.getAudioMedia(0)
                    if media:
                        # Usando a variável global ep
                        media.startTransmit(ep.audDevManager().getCaptureDevMedia())
                        ep.audDevManager().getPlaybackDevMedia().startTransmit(media)
                elif media_info.status == pj.PJSUA_CALL_MEDIA_REMOTE_HOLD:
                    print("Remote hold")
                    self.answer()
                elif media_info.status == pj.PJSUA_CALL_MEDIA_ERROR:
                    print("Error in call media")
                    self.hangup()

    def answer(self):
        prm = pj.CallOpParam()
        prm.statusCode = pj.PJSIP_SC_OK
        super(MyCall, self).answer(prm)

# Classe para representar uma conta
class MyAccount(pj.Account):
    def __init__(self):
        super().__init__()
    
    def onRegState(self, prm):
        print("Registration status: ", prm.code)
        if prm.code == 200:
            print("Registrado com sucesso!")
            atualizar_login_status(1)
        else:
            print("Falha no registro.")
            print(f"Código de erro: {prm.code}")
            print(f"Razão da falha: {prm.reason}")
            atualizar_login_status(0)
            
    def onIncomingCall(self, prm):
        global incoming_call, call_number, answer_call, caller_number
        call_id = prm.callId
        incoming_call = MyCall(self, call_id)
        answer_call = None
        call_info = incoming_call.getInfo()
        caller_number = call_info.remoteUri
        print(f"Incoming call from: {caller_number}")
        # Use um thread para aguardar a entrada do usuário sem bloquear o loop principal
        threading.Thread(target=wait_for_user_input).start()

        # Bloquear até que o usuário tome uma decisão, mas com sleep para não consumir CPU excessiva
        while answer_call is None:
            time.sleep(0.1)

        if answer_call:
            incoming_call.answer()
        else:
            prm = pj.CallOpParam()
            incoming_call.hangup(prm)



def atualizar_login_status(status):
    with open('config.cfg', 'r') as file:
        lines = file.readlines()
    if len(lines) < 6:
        lines.extend(['\n'] * (6 - len(lines)))
    lines[5] = f'login: {status}\n'
    with open('config.cfg', 'w') as file:
        file.writelines(lines)


incoming_call = None

# Função para verificar se uma porta está em uso
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Função para encontrar uma porta disponível
def find_available_port(start_port):
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

# Função para criar transporte
def create_transport():
    global ep
    ep = pj.Endpoint()
    ep.libCreate()
    ep_cfg = pj.EpConfig()
    ep_cfg.logConfig.level = 0

    try:
        ep.libInit(ep_cfg)
    except pj.Error as e:
        print(f"Erro na inicialização do endpoint: {e}")
        return None, None

    transport_cfg = pj.TransportConfig()
    transport_cfg.port = find_available_port(5060)

    try:
        transport = ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
        ep.libStart()
    except pj.Error as e:
        print(f"Erro ao criar transporte: {e}")
        return None, None

    return ep, transport

# Função para criar uma conta
def create_account(ep):
    acc_cfg = pj.AccountConfig()
    acc_cfg.idUri = f"sip:{EXTENSION}@{SIP_SERVER}"
    acc_cfg.regConfig.registrarUri = f"sip:{SIP_SERVER}"
    acc_cfg.sipConfig.authCreds.append(pj.AuthCredInfo("digest", "*", USERNAME, 0, PASSWORD))

    # Configurando codecs
    acc_cfg.codecIds = pj.StringVector()
    for codec in CODECS:
        acc_cfg.codecIds.push_back(codec)

    try:
        account = MyAccount()
        account.create(acc_cfg)
    except pj.Error as e:
        print(f"Erro ao criar a conta: {e}")
        return None

    return account

# Função principal para organizar a execução do código
def main():
    global ep
    ep, transport = create_transport()
    if not ep or not transport:
        print("Erro ao criar transporte. Verifique as configurações.")
        return

    account = create_account(ep)
    if not account:
        print("Erro ao criar a conta. Verifique as configurações.")
        return

    destination_number = configuracoes.get('Destination Number')
    if destination_number:
        threading.Thread(target=make_call, args=(account, destination_number)).start()
        print(f"Chamada para {destination_number} iniciada.")
    else:
        print("Número de destino não especificado nas configurações.")

    try:
        while True:
            time.sleep(1)  # Reduz a carga da CPU
    except KeyboardInterrupt:
        print("Finalizando...")

    account.shutdown()
    ep.libDestroy()
    atualizar_estado_ligacao('desconectada')
    

# Função para fazer uma chamada
def make_call(account, destination_number):
    global call_number
    if not account:
        print("Conta não está registrada. Não é possível fazer chamada.")
        return

    call_number = destination_number  # Armazenar o número de destino
    destination = f"sip:{destination_number}@{SIP_SERVER}"
    call = MyCall(account)
    prm = pj.CallOpParam()
    prm.opt.audioCount = 1
    prm.opt.videoCount = 0
    call.makeCall(destination, prm)
    atualizar_estado_ligacao('conectada')
    print(f"Chamada para {destination_number} iniciada.")  # Imprimir o número de destino
    return call

# Chamar a função principal
if __name__ == "__main__":
    main()
    