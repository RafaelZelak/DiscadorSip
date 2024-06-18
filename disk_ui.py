import tkinter as tk
from tkinter import messagebox
import sip_module as sip
import pjsua2 as pj
import os
from PIL import Image, ImageTk
import asyncio
import sqlite3
import time

# Variaveis globais
root = tk.Tk()
root.title("SoftPhone")
fonte = ("Roboto", 20)
max_caracteres = 14
is_calling = False
call = None
status = "#8a7070"
call_state_var = False
timer = 0
close_event = asyncio.Event()
DB_PATH = 'config.db'
CONFIG_FILE = 'call.txt'


# Funções para database

def initialize_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY,
            Atendido BOOLEAN,
            Numero TEXT,
            inicio_ligacao DATETIME,
            fim_ligacao DATETIME
        )
        """)
        conn.commit()

        cursor.execute("PRAGMA table_info(atendimentos)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'name' not in columns:
            cursor.execute("ALTER TABLE atendimentos ADD COLUMN name TEXT DEFAULT NULL")
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM atendimentos")
        if cursor.fetchone()[0] == 0:
            ATENDIDO = None
            NUMERO = None
            INICIO_LIGACAO = None
            FIM_LIGACAO = None
            cursor.execute("""
            INSERT INTO atendimentos (Atendido, Numero, inicio_ligacao, fim_ligacao) 
            VALUES (?, ?, ?, ?)
            """, (ATENDIDO, NUMERO, INICIO_LIGACAO, FIM_LIGACAO))
        conn.commit()

async def add_record():
    estado = 'esperando_atendido' 

    while True:
        with open('call.txt', 'r') as file:
            lines = file.readlines()

        lines = [line.strip() for line in lines]

        if len(lines) >= 5:
            if estado == 'esperando_atendido' and lines[0].lower() == 'true':
                estado = 'esperando_encerrado'

            if estado == 'esperando_encerrado' and lines[4].lower() == 'encerrado':
                atendido, numero, inicio_ligacao, fim_ligacao = lines[:4]

                atendido = True if atendido.lower() == 'true' else False

                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute("SELECT COUNT(*) FROM atendimentos WHERE Numero = ? AND fim_ligacao = ?", (numero, fim_ligacao))
                    count = cursor.fetchone()[0]

                    if count == 0:
                        cursor.execute("""
                                        INSERT INTO atendimentos (Atendido, Numero, inicio_ligacao, fim_ligacao) 
                                        VALUES (?, ?, ?, ?)
                                        """, (atendido, numero, inicio_ligacao, fim_ligacao))
                        conn.commit()

                estado = 'esperando_atendido'

        await asyncio.sleep(0.5)
      
def verifica_conexao():
    try:
        with open('estado_ligacao.txt', 'r') as arquivo:
            conteudo = arquivo.read().strip()
            if conteudo == 'conectada':
                return True
            elif conteudo == 'desconectada':
                return False
            else:
                raise ValueError("O conteúdo do arquivo não é válido. Esperado 'conectada' ou 'desconectada'.")
    except FileNotFoundError:
        print("Arquivo não encontrado.")
        return False
    except ValueError as e:
        print(e)
        return False

def draw_circle(canvas, x, y, radius):
    global status
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=status, width=2, fill=status)

# Funções relacionadas as ligação

async def check_call_status():
    global is_calling, call
    while not close_event.is_set():
        if verifica_conexao() == False:
            call_button.config(text="Ligar", bg="#718a70")
            is_calling = False
            sip.rebeber_ligação('False')
            sip.atualizar_estado_ligacao('desconectada')
        elif verifica_conexao() == True:
            call_button.config(text="Encerrar", bg="#8a7070")
            is_calling = True
            sip.rebeber_ligação('True')
            sip.atualizar_estado_ligacao('conectada')
        
        await asyncio.sleep(.5)
   
async def check_timer():
    global timer
    timer = 0

    while True:
        if verifica_conexao():
            minutes = timer // 60
            seconds = timer % 60
            timer_str = f"{minutes:02}:{seconds:02}"
            label.config(text=timer_str)
            
            await asyncio.sleep(1)
            timer += 1

        else:
            timer = 0
            label.config(text="Número de Destino:")
            await asyncio.sleep(1)

async def monitor_caller_file():
    connection_was_active = False 

    while not close_event.is_set():
        try:
            with open('caller.txt', 'r') as file:
                content = file.read().strip()
                if content:
                    entry_var.set(content)
        except FileNotFoundError:
            print("Arquivo caller.txt não encontrado.")

        if not verifica_conexao():
            if connection_was_active:
                entry_var.set("")
                connection_was_active = False 
        else:
            connection_was_active = True 

        await asyncio.sleep(0.5)
  
async def check_config_status():
    global status,call
    while not close_event.is_set():
        try:
            with open('config.cfg', 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith("login:"):
                        login_status = line.split(":")[-1].strip()
                        if login_status == '1':
                            status = "#6A9D69"
                        elif login_status == '0':
                            status = "#9D5F5F"
                        else:
                            print("Status inválido no arquivo.")
                        break
                else:
                    print("Login não encontrado no arquivo de configuração.")
        except FileNotFoundError:
            print("Arquivo de configuração não encontrado.")

        canvas.delete("all")
        draw_circle(canvas, x, y, radius)
        await asyncio.sleep(2)

def on_call_button_click(event=None):
    global is_calling, call, destination_number
    
    destination_number = entry_var.get().replace("-", "").replace("(", "").replace(")", "")
    if len(destination_number) >= 3:  
        if destination_number[2] in ['6', '7', '8', '9']:
            if len(destination_number) == 10:
                destination_number = destination_number[:2] + '9' + destination_number[2:]
        else:
            pass
    else:
        pass
    if not verifica_conexao():
        if destination_number:
            try:
                if not is_calling:
                    call = sip.make_call(account, destination_number)
                    call_button.config(text="Encerrar", bg="#8a7070")
                    sip.atualizar_estado_ligacao('conectada')
                    
                    is_calling = True
                else:
                    if call:
                        prm = pj.CallOpParam()
                        call.hangup(prm)
                        call_button.config(text="Ligar", bg="#718a70")
                        sip.atualizar_estado_ligacao('desconectada')
                        is_calling = False
                    else:
                        print("FATAL ERROR")
                        
            except Exception as e:
                if not is_calling:
                    print(f'Call info: {call} \nAccount: {account} \nNumber: {destination_number}')
                    
                    messagebox.showerror("Erro", f"Erro ao fazer a chamada: {e}")
                else:
                    call_button.config(text="Ligar", bg="#718a70")
                    is_calling = False
        else:
            error_msg()
    else:
        call = sip.incoming_call
        if is_calling:
            if call:
                prm = pj.CallOpParam()
                call.hangup(prm) 
                call_button.config(text="Ligar", bg="#718a70")
                sip.atualizar_estado_ligacao('desconectada')
                print('Ligação Externa')
                is_calling = False
            else:
                sip.atualizar_estado_ligacao('desconectada')

        else:
            messagebox.showwarning("Aviso", "Você está conectado. Não é possível fazer uma nova chamada.")


# Funções para formatação


def fade_in(widget, alpha=0):
    alpha += 0.2
    if alpha <= 1:
        r = int(51 + (138 - 51) * alpha)
        g = int(51 + (112 - 51) * alpha)
        b = int(51 + (112 - 51) * alpha)
        color = f"#{r:02x}{g:02x}{b:02x}"
        widget.configure(fg=color)
        root.after(50, fade_in, widget, alpha)

def fade_out(widget, alpha=1):
    alpha -= 0.2
    if alpha >= 0:
        r = int(51 + (138 - 51) * alpha)
        g = int(51 + (112 - 51) * alpha)
        b = int(51 + (112 - 51) * alpha)
        color = f"#{r:02x}{g:02x}{b:02x}"
        widget.configure(fg=color)
        root.after(50, fade_out, widget, alpha)
    else:
        widget.destroy()

def error_msg():
    destination_number_error = tk.Label(root, text="Favor digitar um número válido", bg="#333333", fg="#333333")
    destination_number_error.place(relx=0.5, rely=0.82, anchor='center')
    fade_in(destination_number_error)
    root.after(2500, lambda: fade_out(destination_number_error))



def select_character():
    entry_widget.after_idle(lambda: entry_widget.icursor(tk.END))

def formatar_numero(entrada):
    entrada = ''.join(filter(str.isdigit, entrada)) 
    if len(entrada) >= 5:
        entrada = f"({entrada[:2]}){entrada[2:]}" 
    if '-' not in entrada:
        if len(entrada) > 8:
            entrada = f"{entrada[:8]}-{entrada[8:]}" 
            if '-' in entrada and len(entrada) == 14:
                entrada = entrada.replace('-', '')
                entrada = f"{entrada[:9]}-{entrada[9:]}"
    if len(entrada) != 3:
        entry_widget.after_idle(lambda: entry_widget.icursor(5))
    if len(entrada) > 4:
        select_character()
    return entrada

def limitar_caracteres(*args):
    global max_caracteres

    entry_text = entry_var.get()


    if len(entry_text) > max_caracteres:
        entry_var.set(entry_text[:max_caracteres])
        entry_text = entry_var.get()

    if len(entry_text) == 4:
        label_baixo.config(text="Ramal")
    elif len(entry_text) >= 13:
        fixo = entry_text[5]
        if fixo in ['2', '3', '4', '5']: 
            label_baixo.config(text="Telefone Fixo")
        elif fixo in ['6', '7', '8', '9']:
            label_baixo.config(text="Telefone Celular")
    elif len(entry_text) != 11:
        label_baixo.config(text="Sem formato")

    entry_text = formatar_numero(entry_text)

    entry_var.set(entry_text)
    
def on_number_button_click(number):
    current_text = entry_widget.get()
    new_text = current_text + str(number)
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, new_text)

# Funções para carregar telas

def show_config_screen():
    tooltip.destroy()
    os.system("python3 config_ui.py")

def show_hist_screen():
    tooltip.destroy()
    os.system("python3 hist_ui.py")

def show_tooltip(event, button, tooltip_text):
    global tooltip 

    tooltip = tk.Toplevel(root)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry("+%d+%d" % (event.x_root + 5, event.y_root + 5))
    label = tk.Label(tooltip, text=tooltip_text, background="#ffffff", foreground="#000000")
    label.pack()

def hide_tooltip(event):
    tooltip.destroy()
    
# Interface Gráfica (UI)

img_config = Image.open("img/config_ico.png")
img_config = img_config.resize((25, 25))
img_config_tk = ImageTk.PhotoImage(img_config)
config_button = tk.Button(root, command=show_config_screen, image=img_config_tk, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0, bg="#333333", activebackground="#333333")
config_button.place(relx=0.92, rely=0.03, anchor='center', relwidth=0.1, relheight=0.06)

img_hist = Image.open("img/hist_ico.png")
img_hist = img_hist.resize((25, 25))
img_hist_tk = ImageTk.PhotoImage(img_hist)
hist_button = tk.Button(root, command=show_hist_screen, image=img_hist_tk, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0, bg="#333333", activebackground="#333333")
hist_button.place(relx=0.92, rely=0.102, anchor='center', relwidth=0.1, relheight=0.06)

config_tooltip_text = "Configurações"
hist_tooltip_text = "Histórico"

config_button.bind("<Enter>", lambda event: show_tooltip(event, config_button, config_tooltip_text))
config_button.bind("<Leave>", hide_tooltip)

hist_button.bind("<Enter>", lambda event: show_tooltip(event, hist_button, hist_tooltip_text))
hist_button.bind("<Leave>", hide_tooltip)

label = tk.Label(root, text="Número de Destino:", bg="#333333", fg="#F0F0F0")
label.place(relx=0.5, rely=0.05, anchor='center')

entry_var = tk.StringVar()
entry_var.trace_add("write", limitar_caracteres)

entry_widget = tk.Entry(root, textvariable=entry_var, bg="#333333", fg="#F0F0F0", insertbackground="#F0F0F0", borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0, font=fonte, justify="center")
entry_widget.place(relx=0.5, rely=0.15, anchor='center', relwidth=0.8, relheight=0.1)
entry_widget.focus()
entry_widget.bind("<Return>", on_call_button_click)

label_baixo = tk.Label(root, text="Sem formato", bg="#333333", fg="#F0F0F0")
label_baixo.place(relx=0.5, rely=0.25, anchor='center')

canvas = tk.Canvas(root, width=20, height=20, bg="#333333", borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0)
canvas.pack()
canvas.place(relx=0.04, rely=0.974, anchor='center')

x = 10
y = 10
radius = 7

# Teclado numérico
buttons = [
    ('1', 0.25, 0.34), ('2', 0.5, 0.34), ('3', 0.75, 0.34),
    ('4', 0.25, 0.45), ('5', 0.5, 0.45), ('6', 0.75, 0.45),
    ('7', 0.25, 0.56), ('8', 0.5, 0.56), ('9', 0.75, 0.56),
    ('*', 0.25, 0.67), ('0', 0.5, 0.67), ('#', 0.75, 0.67),
]

for (text, relx, rely) in buttons:
    button = tk.Button(root, text=text, command=lambda t=text: on_number_button_click(t), bg="#555555", fg="#F0F0F0", highlightthickness=0, highlightbackground="#333333", bd=0)  # Remoção da borda
    button.place(relx=relx, rely=rely, anchor='center', relwidth=0.235, relheight=0.1)

call_button = tk.Button(root, text="Ligar", command=on_call_button_click, bg="#718a70", fg="#F0F0F0", borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0)
call_button.place(relx=0.5, rely=0.9, anchor='center', relwidth=0.78, relheight=0.1)

# Função para limpar recursos SIP

def clean_up():
    global ep, transport, account, call
    sip.atualizar_estado_ligacao('desconectada')
    try:
        if call:
            call.hangup(pj.CallOpParam())
    except Exception as e:
        print(f"Erro ao encerrar a chamada: {e}")
    try:
        if account:
            account.delete()
            account = None
    except Exception as e:
        print(f"Erro ao limpar a conta: {e}")
    try:
        if transport:
            transport = None
    except Exception as e:
        print(f"Erro ao limpar o transporte: {e}")
    try:
        if ep:
            ep.libDestroy()
            ep = None
    except Exception as e:
        print(f"Erro ao destruir o endpoint: {e}")

# Capturar o evento de fechamento da janela para limpar recursos

def on_close_window():
    print("Limpando recursos SIP...")
    clean_up()
    print("Destruindo endpoint SIP...")
    close_event.set()
    root.destroy()
    os._exit(0)

root.protocol("WM_DELETE_WINDOW", on_close_window)

# Configuração SIP

ep, transport = sip.create_transport()
if ep is None or transport is None:
    print("Erro ao iniciar aplicação SIP")
else:
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    account = sip.create_account(ep)
    largura = 300
    altura = 500
    pos_x = 0
    pos_y = screen_height - altura
    root.configure(bg="#333333")
    root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    root.wm_maxsize(420, 700)
    root.wm_minsize(230, 400)

    async def main_loop():
        asyncio.create_task(check_config_status())
        asyncio.create_task(check_call_status()) 
        asyncio.create_task(add_record())    
        asyncio.create_task(check_timer())
        asyncio.create_task(monitor_caller_file())
        
        while not close_event.is_set():
            if not root.winfo_exists(): 
                break
            root.update()
            try:
                ep.libHandleEvents(50) 
            except pj.Error as e:
                print(f"Erro ao manipular eventos SIP: {e}")
            await asyncio.sleep(0.01)

    try:
        asyncio.run(main_loop())
    finally:
        clean_up()

