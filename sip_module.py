# -*- coding: utf-8 -*-
# sip_module.py
import pjsua2 as pj
import socket

def ler_configuracoes_do_arquivo(arquivo):
    configuracoes = {}
    with open(arquivo, 'r') as file:
        for line in file:
            key, value = line.strip().split(': ')
            configuracoes[key.strip()] = value.strip()
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

class MyCall(pj.Call):
    def __init__(self, account, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, account, call_id)
    
    def onCallState(self, prm):
        call_info = self.getInfo()
        print("Call state changed to", call_info.stateText)
        if call_info.state == pj.PJSIP_INV_STATE_DISCONNECTED:
            print("Call disconnected")
            
    def onCallMediaState(self, prm, ep):
        call_info = self.getInfo()
        for mi in call_info.media:
            if mi.type == pj.PJMEDIA_TYPE_AUDIO and (mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE):
                media = self.getMedia(mi.index)
                audio_media = pj.AudioMedia.typecastFromMedia(media)
                ep.audDevManager().getCaptureDevMedia().startTransmit(audio_media)
                ep.audDevManager().getPlaybackDevMedia().startTransmit(audio_media)
                print("Audio transmission started")

class MyAccount(pj.Account):
    def __init__(self):
        pj.Account.__init__(self)
    
    def onRegState(self, prm):
        if prm.code == 200:
            print("Registrado com sucesso!")
        else:
            print("Falha no registro.")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port):
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def create_transport():
    ep = pj.Endpoint()
    ep.libCreate()
    ep_cfg = pj.EpConfig()
    ep_cfg.logConfig.level = 0  # Configuração para desativar todos os logs
    ep.libInit(ep_cfg)

    transport_cfg = pj.TransportConfig()
    transport_cfg.port = find_available_port(5060)

    try:
        transport = ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, transport_cfg)
        ep.libStart()
    except pj.Error as e:
        print(f"Erro ao criar transporte: {e}")
        return None, None

    return ep, transport

def create_account(ep):
    acc_cfg = pj.AccountConfig()
    acc_cfg.idUri = f"sip:{EXTENSION}@{SIP_SERVER}"
    acc_cfg.regConfig.registrarUri = f"sip:{SIP_SERVER}"
    acc_cfg.sipConfig.authCreds.append(pj.AuthCredInfo("digest", "*", USERNAME, 0, PASSWORD))

    # Configurando codecs
    acc_cfg.codecIds = pj.StringVector()
    for codec in CODECS:
        acc_cfg.codecIds.push_back(codec)

    account = MyAccount()
    account.create(acc_cfg)

    return account

def make_call(account, destination_number):
    destination = f"sip:{destination_number}@{SIP_SERVER}"
    call = MyCall(account)
    prm = pj.CallOpParam()
    prm.opt.audioCount = 1
    prm.opt.videoCount = 0
    call.makeCall(destination, prm)
    return call
