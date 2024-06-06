import pjsua2 as pj
import socket

# Variável global para o endpoint
ep = None
call_onoff = False
incoming_call = None

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

# Classe para representar uma chamada
class MyCall(pj.Call):
    def __init__(self, account, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, account, call_id)
    
    def onCallState(self, prm):
        global call_info
        call_info = self.getInfo()
        print(f"Call state changed to {call_info.stateText} for call ID: {self.getId()}")
        if call_info.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            print("Call disconnected")
            atualizar_estado_ligacao('desconectada')
            global incoming_call
            incoming_call = None

        elif call_info.state == pj.PJSIP_INV_STATE_CONFIRMED:
            print("Call connected")
            atualizar_estado_ligacao('conectada')

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
        pj.Account.__init__(self)
    
    def onRegState(self, prm):
        if prm.code == 200:
            print("Registrado com sucesso!")
            atualizar_login_status(1)
        else:
            print("Falha no registro.")
            print(f"Código de erro: {prm.code}")
            print(f"Razão da falha: {prm.reason}")
            atualizar_login_status(0)
    
    def onIncomingCall(self, prm):
        global incoming_call
        call_id = prm.callId
        atualizar_estado_ligacao('conectada')
        print("Incoming call received. Call ID:", call_id)
        incoming_call = MyCall(self, call_id)
        incoming_call.answer()

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
    # Criar transporte
    global ep
    ep, transport = create_transport()
    if not ep or not transport:
        print("Erro ao criar transporte. Verifique as configurações.")
        return

    # Criar conta
    account = create_account(ep)
    if not account:
        print("Erro ao criar a conta. Verifique as configurações.")
        return

    # Fazer chamada de teste
    destination_number = configuracoes.get('Destination Number')
    if destination_number:
        atualizar_estado_ligacao('conectada')
        call = make_call(account, destination_number)
        print(f"Chamada para {destination_number} iniciada.")
    else:
        print("Número de destino não especificado nas configurações.")

    # Manter o programa em execução para lidar com chamadas
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Finalizando...")

    # Liberação dos recursos do PJSIP
    account.shutdown()
    ep.libDestroy()

# Função para fazer uma chamada
def make_call(account, destination_number):
    if not account:
        print("Conta não está registrada. Não é possível fazer chamada.")
        return

    destination = f"sip:{destination_number}@{SIP_SERVER}"
    call = MyCall(account)
    prm = pj.CallOpParam()
    prm.opt.audioCount = 1
    prm.opt.videoCount = 0
    call.makeCall(destination, prm)
    atualizar_estado_ligacao('conectada')
    return call

# Chamar a função principal
if __name__ == "__main__":
    main()
