import tkinter as tk
from tkinter import messagebox
import sip_module as sip
import pjsua2 as pj
import os
from PIL import Image, ImageTk
import asyncio

# Variaveis
root = tk.Tk()
root.title("Fazer Chamada SIP")
fonte = ("Roboto", 20)
max_caracteres = 14
is_calling = False
call = None
status = "#8a7070"
call_state_var = False

# Evento para sinalizar que a janela foi fechada
close_event = asyncio.Event()

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

async def check_call_status():
    global is_calling, call
    while not close_event.is_set():
        if verifica_conexao() == False:  # Verifica se a conexão está ativa
            call_button.config(text="Ligar", bg="#718a70")
            is_calling = False
        await asyncio.sleep(.5)

async def check_config_status():
    global status

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

        # Atualizar o círculo no canvas
        canvas.delete("all")  # Limpar o canvas
        draw_circle(canvas, x, y, radius)
        await asyncio.sleep(2)  # Aguardar 2 segundos antes de verificar novamente


# Modificar a função para aceitar um argumento de evento
def on_call_button_click(event=None):
    global is_calling, call

    destination_number = entry_var.get().replace("-", "").replace("(", "").replace(")", "")
    if destination_number[2] in ['6', '7', '8', '9']:
        if len(destination_number) == 10:
            destination_number = destination_number[:2] + '9' + destination_number[2:]

    if verifica_conexao() == False:
        if destination_number:
            try:
                if not is_calling:  # Se não estiver em uma chamada, faça uma nova chamada
                    call = sip.make_call(account, destination_number)
                    call_button.config(text="Encerrar", bg="#8a7070")
                    is_calling = True
                else:  # Se já estiver em uma chamada, encerre-a
                    prm = pj.CallOpParam()
                    call.hangup(prm) 
                    call_button.config(text="Ligar", bg="#718a70")
                    is_calling = False
            except Exception as e:
                if not is_calling:
                    messagebox.showerror("Erro", f"Erro ao fazer a chamada: {e}")
                else:
                    # Se já estiver em uma chamada e ocorrer um erro, trate o erro aqui
                    call_button.config(text="Ligar", bg="#718a70")
                    is_calling = False
        else:
            messagebox.showwarning("Aviso", "Por favor, insira um número de destino.")
    else:
        # Se já estiver em uma chamada, encerre-a
        if is_calling:
            prm = pj.CallOpParam()
            call.hangup(prm) 
            call_button.config(text="Ligar", bg="#718a70")
            is_calling = False
        else:
            messagebox.showwarning("Aviso", "Você está conectado. Não é possível fazer uma nova chamada.")



def select_character():
    entry_widget.after_idle(lambda: entry_widget.icursor(tk.END))

def formatar_numero(entrada):
    entrada = ''.join(filter(str.isdigit, entrada))  # Remove todos os caracteres não numéricos
    if len(entrada) >= 2:
        entrada = f"({entrada[:2]}){entrada[2:]}"  # Adiciona parênteses nos primeiros dois dígitos
    if '-' not in entrada:
        if len(entrada) > 8:
            entrada = f"{entrada[:8]}-{entrada[8:]}"  # Adiciona o hífen após o sexto dígito
            if '-' in entrada and len(entrada) == 14:
                entrada = entrada.replace('-', '')
                entrada = f"{entrada[:9]}-{entrada[9:]}"
    if len(entrada) != 3:
        entry_widget.after_idle(lambda: entry_widget.icursor(3))
    if len(entrada) > 4:
        select_character()
    return entrada

def limitar_caracteres(*args):
    global max_caracteres

    entry_text = entry_var.get()

    # Verifique se o texto excede o limite máximo de caracteres
    if len(entry_text) > max_caracteres:
        entry_var.set(entry_text[:max_caracteres])
        entry_text = entry_var.get()

    # Verifique outras condições e atualize o label_baixo conforme necessário
    if len(entry_text) >= 13:
        fixo = entry_text[5]
        if fixo in ['2', '3', '4', '5']:  # Comparar com strings
            label_baixo.config(text="Telefone Fixo")
        elif fixo in ['6', '7', '8', '9']:  # Comparar com strings
            label_baixo.config(text="Telefone Celular")
    elif len(entry_text) != 4 and len(entry_text) != 11:
        label_baixo.config(text="Sem formato")

    entry_text = formatar_numero(entry_text)

    entry_var.set(entry_text)

def on_number_button_click(number):
    current_text = entry_widget.get()
    new_text = current_text + str(number)
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, new_text)


# Função para trocar para a tela de configurações
def show_config_screen():
    tooltip.destroy()
    os.system("python3 config_ui.py")

img_config = Image.open("img/config_ico.png")
img_config = img_config.resize((25, 25))
img_config_tk = ImageTk.PhotoImage(img_config)
config_button = tk.Button(root, command=show_config_screen, image=img_config_tk, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0, bg="#333333", activebackground="#333333")
config_button.place(relx=0.95, rely=0.03, anchor='center', relwidth=0.1, relheight=0.06)

img_hist = Image.open("img/hist_ico.png")
img_hist = img_hist.resize((25, 25))
img_hist_tk = ImageTk.PhotoImage(img_hist)
hist_button = tk.Button(root, command=show_config_screen, image=img_hist_tk, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0, bg="#333333", activebackground="#333333")
hist_button.place(relx=0.95, rely=0.102, anchor='center', relwidth=0.1, relheight=0.06)

# Define os textos das dicas de ferramentas
config_tooltip_text = "Configurações"
hist_tooltip_text = "Histórico"

# Define as funções de exibição e ocultação de dicas de ferramentas
def show_tooltip(event, button, tooltip_text):
    global tooltip  # Declara tooltip como uma variável global

    # Cria uma janela pop-up com o texto da dica de ferramenta
    tooltip = tk.Toplevel(root)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry("+%d+%d" % (event.x_root + 5, event.y_root + 5))  # Define manualmente a posição da janela pop-up
    label = tk.Label(tooltip, text=tooltip_text, background="#ffffff", foreground="#000000")
    label.pack()

def hide_tooltip(event):
    tooltip.destroy()

# Vincula as funções de exibição e ocultação de dicas de ferramentas aos eventos de entrada e saída do mouse
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

# Bind the Enter key to the on_call_button_click function
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
    try:
        if call:
            call.hangup(pj.CallOpParam())
            call = None
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
    close_event.set()  # Sinaliza o fechamento da janela
    root.destroy()
    os._exit(0)

root.protocol("WM_DELETE_WINDOW", on_close_window)

# Configuração SIP
ep, transport = sip.create_transport()
if ep is None or transport is None:
    print("Erro ao iniciar aplicação SIP")
else:
    account = sip.create_account(ep)
    largura = 300
    altura = 500
    root.configure(bg="#333333")
    root.geometry(f"{largura}x{altura}")

    # Função para integrar o loop do Tkinter com o asyncio
    async def main_loop():
        asyncio.create_task(check_config_status())  # Iniciar a tarefa assíncrona dentro do loop
        asyncio.create_task(check_call_status())  # Iniciar a tarefa assíncrona para verificar o status da chamada
        while not close_event.is_set():
            if not root.winfo_exists():  # Verifica se a janela ainda existe
                break
            root.update()
            try:
                ep.libHandleEvents(50)  # Manipular eventos SIP
            except pj.Error as e:
                print(f"Erro ao manipular eventos SIP: {e}")
            await asyncio.sleep(0.01)

    # Dentro do loop principal
    try:
        asyncio.run(main_loop())
    finally:
        clean_up()

