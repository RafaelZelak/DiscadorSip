import tkinter as tk

class ToggleSwitch(tk.Canvas):
    def __init__(self, master=None, width=60, height=30, file_name="toggle_state.txt", **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.file_name = file_name
        self.is_on = self.read_state_from_file()
        self.bind("<Button-1>", self.toggle)

        self.radius = self.height // 2

        # Cores acinzentadas escuras
        self.dark_gray_red = "#4C3B3B"
        self.dark_gray_green = "#3B4C3B"

        # Desenha o fundo arredondado
        if self.is_on:
            self.create_rounded_background(self.dark_gray_green)
            x_pos = self.width - self.height
        else:
            self.create_rounded_background(self.dark_gray_red)
            x_pos = 2
        self.circle = self.create_oval(x_pos, 2, x_pos + self.height - 4, self.height - 2, outline="black", fill="white", tags="circle")

    def create_rounded_background(self, color):
        # Limpa o fundo existente
        self.delete("background")

        # Desenha apenas os contornos arredondados
        self.create_arc((0, 0, self.height, self.height), start=90, extent=180, fill=color, outline="", tags="background")
        self.create_arc((self.width-self.height, 0, self.width, self.height), start=270, extent=180, fill=color, outline="", tags="background")
        self.create_rectangle((self.radius, 0, self.width-self.radius, self.height), fill=color, outline="", tags="background")

        # Sempre traz o círculo para frente após atualizar o fundo
        self.tag_raise("circle")

    def toggle(self, event=None):
        self.is_on = not self.is_on
        if self.is_on:
            self.move_circle(self.width - self.height)
            self.create_rounded_background(self.dark_gray_green)
        else:
            self.move_circle(2)
            self.create_rounded_background(self.dark_gray_red)

        # Escreve o estado em um arquivo de texto
        with open(self.file_name, 'w') as file:
            file.write(str(self.is_on))

    def move_circle(self, x):
        current_pos = self.coords("circle")
        target_pos = [x, 2, x + self.height - 4, self.height - 2]
        steps = 10

        dx = (target_pos[0] - current_pos[0]) / steps
        for _ in range(steps):
            self.move("circle", dx, 0)
            self.update()
            self.after(10)

        self.coords("circle", target_pos)

    def read_state_from_file(self):
        try:
            with open(self.file_name, 'r') as file:
                state = file.read()
                if state.strip().lower() == 'true':
                    return True
                elif state.strip().lower() == 'false':
                    return False
                else:
                    return False  # Caso o arquivo não contenha "true" ou "false", assume-se como False
        except FileNotFoundError:
            return False  # Se o arquivo não existir, assume-se como False

    def get_state(self):
        return self.is_on

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Toggle Switch Example")

    toggle_switch = ToggleSwitch(root)
    toggle_switch.pack(pady=20)

    root.mainloop()
