# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import sip_module as sip
import pjsua2 as pj
import os

# Definir o limite de caracteres
root = tk.Tk()
root.title("Fazer Chamada SIP")
fonte = ("Roboto", 20)

max_caracteres = 14

# Variavel global para rastrear o estado da chamada
is_calling = False
call = None

# Função para encerrar a chamada
def end_call():
    global is_calling, call
    if is_calling:
        prm = pj.CallOpParam()
        call.hangup(prm)  # Encerra a chamada usando o metodo hangup()
        call_button.config(text="Ligar", bg="#718a70")
        is_calling = False

# Modificar a função para aceitar um argumento de evento
def on_call_button_click(event=None):
    global is_calling, call
    destination_number = entry_var.get().replace("-", "").replace("(", "").replace(")", "")
    if destination_number[2] in ['6', '7', '8', '9']:
        if len(destination_number) == 10:
            destination_number = destination_number[:2] + '9' + destination_number[2:]
            
    if not is_calling:
        if destination_number:
            try:
                call = sip.make_call(account, destination_number)
                # Mudar texto do botão e atualizar estado da chamada
                call_button.config(text="Encerrar", bg="#8a7070")
                is_calling = True
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao fazer a chamada: {e}")
        else:
            messagebox.showwarning("Aviso", "Por favor, insira um número de destino.")
    else:
        # Se já estiver em uma chamada, encerre-a
        end_call()

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
    os.system("python3 config_ui.py")



config_button = tk.Button(root, command=show_config_screen, borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0)
config_button.place(relx=0.90, rely=0.06, anchor='center', relwidth=0.1, relheight=0.06)

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
    root.mainloop()
