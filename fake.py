from faker import Faker

fake = Faker()

def generate_info():
    nome = fake.name()
    ip = "192.168.15.252"
    username = "1" + str(fake.random_int(0, 1999)).zfill(3)
    extension = username
    password = fake.password()

    return {
        "nome": nome,
        "ip": ip,
        "username": username,
        "extension": extension,
        "password": password
    }

# Exemplo de uso
info = generate_info()
print("Nome:", info["nome"])
print("IP:", info["ip"])
print("Username:", info["username"])
print("Extension:", info["extension"])
print("Password:", info["password"])
