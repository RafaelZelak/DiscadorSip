import tkinter as tk
from tkinter import messagebox
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
    # Fechando o arquivo disk_ui.py
    os.system("pkill -f disk_ui.py")

    # Escrevendo no arquivo de configuração
    with open(CONFIG_FILE, "w") as f:
        f.write(f"Name: {config[0]}\n")
        f.write(f"SIP Server: {config[1]}\n")
        f.write(f"Username: {config[2]}\n")
        f.write(f"Extension: {config[3]}\n")
        f.write(f"Password: {config[4]}\n")

    # Abrindo o arquivo disk_ui.py
    os.system("python3 disk_ui.py &")
    root.destroy()


def on_item_select(event):
    global previous_selection
    global initial_load
    if listbox.curselection():
        selected_index = listbox.curselection()[0]
        selected_name = users[selected_index][0]

        if not initial_load and previous_selection is not None and previous_selection != selected_index:
            if messagebox.askyesno("Confirmação", "Gostaria de trocar de usuário?"):
                config = load_config_by_name(selected_name)
                save_to_config_file(config)
            else:
                listbox.selection_clear(0, tk.END)
                listbox.selection_set(previous_selection)
                listbox.activate(previous_selection)
                return

        previous_selection = selected_index
        initial_load = False

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
    add_window.configure(bg="#555555")
    add_window.geometry("200x300")  # Definindo as dimensões da janela

    name_var = tk.StringVar()
    sip_server_var = tk.StringVar()
    username_var = tk.StringVar()
    extension_var = username_var
    password_var = tk.StringVar()

    def add_record():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sip_config (name, sip_server, username, extension, password) 
            VALUES (?, ?, ?, ?, ?)
            """, (name_var.get(), sip_server_var.get(), username_var.get(), extension_var.get(), password_var.get()))
            conn.commit()
        users.clear()
        users.extend(load_users())
        listbox.delete(0, tk.END)
        for user in users:
            listbox.insert(tk.END, user[0])
        add_window.destroy()

    tk.Label(add_window, text="Name:", bg="#555555", fg="#F0F0F0").pack(pady=5)
    tk.Entry(add_window, textvariable=name_var, bg="#555555", fg="#F0F0F0").pack(padx=10, pady=5)
    tk.Label(add_window, text="SIP Server:", bg="#555555", fg="#F0F0F0").pack(pady=5)
    tk.Entry(add_window, textvariable=sip_server_var, bg="#555555", fg="#F0F0F0").pack(padx=10, pady=5)
    tk.Label(add_window, text="Username:", bg="#555555", fg="#F0F0F0").pack(pady=5)
    tk.Entry(add_window, textvariable=username_var, bg="#555555", fg="#F0F0F0").pack(padx=10, pady=5)
    tk.Label(add_window, text="Password:", bg="#555555", fg="#F0F0F0").pack(pady=5)
    tk.Entry(add_window, textvariable=password_var, bg="#555555", fg="#F0F0F0").pack(padx=10, pady=5)

    tk.Button(add_window, text="Adicionar", command=add_record, bg="#555555", fg="#F0F0F0").pack(pady=10)

def delete_record():
    if listbox.curselection():
        if messagebox.askyesno("Confirmação", "Tem certeza que deseja apagar o ramal?"):
            selected_index = listbox.curselection()[0]
            selected_name = users[selected_index][0]
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sip_config WHERE name=?", (selected_name,))
                conn.commit()
            users.clear()
            users.extend(load_users())
            listbox.delete(0, tk.END)
            for user in users:
                listbox.insert(tk.END, user[0])
            with open(CONFIG_FILE, "w") as f:
                f.write("")

initialize_db()
users = load_users()

def fechar_e_abrir():
    root.destroy()
    
def read_config_file():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            lines = f.readlines()
            config = {}
            for line in lines:
                parts = line.strip().split(": ")
                if len(parts) == 2:
                    key, value = parts
                    config[key] = value
                else:
                    print(f"Warning: Line skipped in config file: {line.strip()}")
            return config
    return {}

root = tk.Tk()
root.title("Exemplo de Botão")
root.configure(bg="#333333")

button_frame = tk.Frame(root, bg="#333333")
button_frame.pack(fill=tk.X)

buttons = [
    ("Fechar", fechar_e_abrir),
    ("Novo", open_add_window),
    ("Apagar", delete_record)
]

button_width = 10

for idx, (text, command) in enumerate(buttons):
    button = tk.Button(button_frame, text=text, command=command, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0, bg="#555555", fg="#F0F0F0", width=button_width)
    button.grid(row=0, column=idx, padx=10, pady=10)

for i in range(len(buttons)):
    button_frame.grid_columnconfigure(i, weight=1)

list_frame = tk.Frame(root, bg="#333333")
list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

previous_selection = None
initial_load = True

listbox = tk.Listbox(list_frame, bg="#333333", fg="#ffffff", selectbackground="#ffffff", selectforeground="#333333", font=("Arial", 12), bd=0, highlightthickness=0)
for user in users:
    listbox.insert(tk.END, user[0])
listbox.bind("<<ListboxSelect>>", on_item_select)
listbox.pack(fill=tk.BOTH, expand=True)

config = read_config_file()
if "Name" in config and config["Name"]:
    try:
        selected_index = [user[0] for user in users].index(config["Name"])
        listbox.select_set(selected_index)
        listbox.event_generate("<<ListboxSelect>>")
        previous_selection = selected_index
    except ValueError:
        pass

largura = 280
altura = 480
root.geometry(f"{largura}x{altura}")
root.mainloop()