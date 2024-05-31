import tkinter as tk
import os
import sqlite3

DB_PATH = "config.db"
CONFIG_FILE = "config.cfg"

def initialize_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sip_config (
            id INTEGER PRIMARY KEY,
            sip_server TEXT NOT NULL,
            username TEXT NOT NULL,
            extension TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """)
        conn.commit()

        # Adicionar a coluna 'name' se ela não existir
        cursor.execute("PRAGMA table_info(sip_config)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'name' not in columns:
            cursor.execute("ALTER TABLE sip_config ADD COLUMN name TEXT DEFAULT NULL")
            conn.commit()

        # Verificar se existem registros e adicionar um se não houver
        cursor.execute("SELECT COUNT(*) FROM sip_config")
        if cursor.fetchone()[0] == 0:
            SIP_SERVER = "Null"
            USERNAME = "Null"
            EXTENSION = "Null"
            PASSWORD = "Null"
            NAME = "Null"
            cursor.execute("""
            INSERT INTO sip_config (sip_server, username, extension, password, name) 
            VALUES (?, ?, ?, ?, ?)
            """, (SIP_SERVER, USERNAME, EXTENSION, PASSWORD, NAME))
        conn.commit()

def save_to_config_file(config):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"Name: {config[0]}\n")
        f.write(f"SIP Server: {config[1]}\n")
        f.write(f"Username: {config[2]}\n")
        f.write(f"Extension: {config[3]}\n")
        f.write(f"Password: {config[4]}\n")

def on_item_select(event):
    if listbox.curselection():
        selected_index = listbox.curselection()[0]
        selected_name = users[selected_index][0]
        config = load_config_by_name(selected_name)
        save_to_config_file(config)

def load_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sip_config")
        return cursor.fetchall()

def load_config_by_name(name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, sip_server, username, extension, password FROM sip_config WHERE name=?", (name,))
        return cursor.fetchone()

def open_add_window():
    add_window = tk.Toplevel(root)
    add_window.title("Adicionar Novo Registro")

    # Definindo as variáveis dos campos
    name_var = tk.StringVar()
    sip_server_var = tk.StringVar()
    username_var = tk.StringVar()
    extension_var = username_var
    password_var = tk.StringVar()

    # Função para adicionar o registro
    def add_record():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sip_config (name, sip_server, username, extension, password) 
            VALUES (?, ?, ?, ?, ?)
            """, (name_var.get(), sip_server_var.get(), username_var.get(), extension_var.get(), password_var.get()))
            conn.commit()
        # Atualizar a lista de usuários
        users.clear()
        users.extend(load_users())
        listbox.delete(0, tk.END)
        for user in users:
            listbox.insert(tk.END, user[0])
        add_window.destroy()

    # Componentes da janela de adição
    tk.Label(add_window, text="Name:").pack()
    tk.Entry(add_window, textvariable=name_var).pack()
    tk.Label(add_window, text="SIP Server:").pack()
    tk.Entry(add_window, textvariable=sip_server_var).pack()
    tk.Label(add_window, text="Username:").pack()
    tk.Entry(add_window, textvariable=username_var).pack()
    tk.Label(add_window, text="Password:").pack()
    tk.Entry(add_window, textvariable=password_var).pack()

    tk.Button(add_window, text="Adicionar", command=add_record).pack()

def delete_record():
    if listbox.curselection():
        selected_index = listbox.curselection()[0]
        selected_name = users[selected_index][0]
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sip_config WHERE name=?", (selected_name,))
            conn.commit()
        # Atualizar a lista de usuários
        users.clear()
        users.extend(load_users())
        listbox.delete(0, tk.END)
        for user in users:
            listbox.insert(tk.END, user[0])
        # Remover conteúdo do arquivo de configuração, se necessário
        with open(CONFIG_FILE, "w") as f:
            f.write("")

initialize_db()
users = load_users()

def fechar_e_abrir():
    # Fecha a tela atual do Tkinter
    root.destroy()

# Criando a janela principal
root = tk.Tk()
root.title("Exemplo de Botão")

# Criando um frame para os botões
button_frame = tk.Frame(root, bg="#333333")
button_frame.pack(fill=tk.X)

# Criando o botão para fechar a janela
config_button = tk.Button(button_frame, text="Fechar", command=fechar_e_abrir, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0)
config_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Botão para adicionar novo registro
add_button = tk.Button(button_frame, text="Adicionar Novo", command=open_add_window)
add_button.pack(side=tk.LEFT, padx=10, pady=10)

# Botão para apagar registro
delete_button = tk.Button(button_frame, text="Apagar Registro", command=delete_record)
delete_button.pack(side=tk.LEFT, padx=10, pady=10)

# Criando um frame para a lista de usuários
list_frame = tk.Frame(root, bg="#333333")
list_frame.pack(fill=tk.BOTH, expand=True)

# Criando a lista de usuários com estilos personalizados
listbox = tk.Listbox(list_frame, bg="#333333", fg="#ffffff", selectbackground="#555555", selectforeground="#ffffff", font=("Arial", 12), bd=0, highlightthickness=0)
for user in users:
    listbox.insert(tk.END, user[0])
listbox.bind("<<ListboxSelect>>", on_item_select)
listbox.pack(fill=tk.BOTH, expand=True)

# Roda o loop principal
largura = 300
altura = 500
root.configure(bg="#333333")
root.geometry(f"{largura}x{altura}")
root.mainloop()