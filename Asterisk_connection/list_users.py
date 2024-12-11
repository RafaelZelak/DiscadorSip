import socket

# Configurações do servidor Asterisk
ASTERISK_HOST = '192.168.15.252'
ASTERISK_PORT = 5038
ASTERISK_USERNAME = 'admin'
ASTERISK_PASSWORD = 'ER3ehdjhdjjf5688sdy@3asrdgbfd7'

# Comando para listar os ramais
command = 'Action: Command\r\nCommand: sip show peers\r\n\r\n'

# Conectar ao servidor Asterisk
asterisk_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
asterisk_socket.connect((ASTERISK_HOST, ASTERISK_PORT))

# Login no Asterisk Manager
login_command = 'Action: Login\r\nUsername: {}\r\nSecret: {}\r\n\r\n'.format(ASTERISK_USERNAME, ASTERISK_PASSWORD)
asterisk_socket.send(login_command.encode())

# Receber a resposta do login
response = asterisk_socket.recv(1024).decode()

# Verificar se o login foi bem-sucedido
if 'Authentication accepted' in response:
    # Envie o comando para listar os ramais
    asterisk_socket.send(command.encode())
    
    # Receba e imprima a resposta
    response = asterisk_socket.recv(4096).decode()
    print(response)
else:
    print('Login falhou.')

# Feche a conexão
asterisk_socket.close()
