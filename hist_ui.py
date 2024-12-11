import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime

# Função para calcular a duração da ligação
def calcular_duracao(inicio, fim):
    fmt = '%Y-%m-%d %H:%M:%S'
    inicio_dt = datetime.strptime(inicio, fmt)
    fim_dt = datetime.strptime(fim, fmt)
    duracao = fim_dt - inicio_dt
    horas, resto = divmod(duracao.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"

# Função para carregar dados do banco de dados e exibi-los na janela
def carregar_dados():
    # Conecta ao banco de dados
    conn = sqlite3.connect('config.db')
    cursor = conn.cursor()
    
    # Consulta a tabela atendimentos e ordena do mais recente para o mais antigo
    cursor.execute("SELECT Numero, inicio_ligacao, fim_ligacao FROM atendimentos ORDER BY fim_ligacao DESC")
    registros = cursor.fetchall()
    
    ultimo_titulo = ""
    y_position = 20
    
    for registro in registros:
        numero, inicio, fim = registro
        data_fim = fim.split(' ')[0]
        horario_fim = fim.split(' ')[1]
        duracao = calcular_duracao(inicio, fim)
        
        # Converte a data e hora para o formato brasileiro
        data_formatada = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')
        horario_formatado = datetime.strptime(horario_fim, '%H:%M:%S').strftime('%H:%M:%S')
        
        # Adiciona um título com a data se for diferente da última
        if data_formatada != ultimo_titulo:
            canvas.create_rectangle(5, y_position - 15, largura - 5, y_position + 15, fill="#F0F0F0", outline="#F0F0F0")
            canvas.create_text(largura // 2, y_position, text=f"{data_formatada}", fill="#333333", font=("Arial", 12, "bold"))
            y_position += 30
            ultimo_titulo = data_formatada
        
        # Adiciona o registro formatado
        canvas.create_text(largura // 2, y_position, text=f"Número: {numero}", fill="#F0F0F0")
        y_position += 20
        canvas.create_text(largura // 2, y_position, text=f"Horário: {horario_formatado}", fill="#F0F0F0")
        y_position += 20
        canvas.create_text(largura // 2, y_position, text=f"Duração: {duracao}", fill="#F0F0F0")
        y_position += 30
        
        # Adiciona uma linha horizontal para separar os registros
        canvas.create_line(10, y_position, largura-10, y_position, fill="#F0F0F0")
        y_position += 20
    
    # Atualiza o tamanho do canvas
    canvas.config(scrollregion=canvas.bbox("all"))
    
    # Fecha a conexão
    conn.close()

# Cria a janela principal
root = tk.Tk()
root.title("Histórico")

# Configurações da janela
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
largura = 300
altura = 500
pos_x = 0
pos_y = screen_height - altura
root.configure(bg="#333333")
root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
root.wm_maxsize(300, 500)
root.wm_minsize(300, 500)

# Adiciona uma barra de rolagem vertical
scrollbar = ttk.Scrollbar(root, orient="vertical")
scrollbar.pack(side="right", fill="y")

# Cria um canvas
canvas = tk.Canvas(root, bg="#333333", width=largura, height=altura, highlightthickness=0, yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)

# Conecta a barra de rolagem ao canvas
scrollbar.config(command=canvas.yview)

# Adiciona um frame ao canvas para conter os itens
frame = tk.Frame(canvas, bg="#333333")
canvas.create_window((0, 0), window=frame, anchor='nw')

# Chama a função para carregar e exibir os dados
carregar_dados()

# Atualiza a posição do frame quando o tamanho do canvas mudar
frame.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))

# Personaliza a barra de rolagem
style = ttk.Style()
style.theme_use('default')
style.configure("Vertical.TScrollbar", gripcount=100, background="#666666", troughcolor="#333333", bordercolor="#333333", arrowcolor="#333333", borderwidth=0, highlightthickness=0, highlightbackground="#333333", bd=0)
scrollbar.config(style="Vertical.TScrollbar")

# Inicia o loop de eventos
root.mainloop()
