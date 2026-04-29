import tkinter as tk
from tkinter import scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import cv2
from PIL import Image, ImageTk
from client import Cliente
from audio import Audio
from camera import Camera 

class VideoCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Teams remake")
        self.root.geometry("1200x800")
        
        self.style = tb.Style(theme="darkly")
        
        self.client = None
        self.video_running = False
        self.audio_running = False
        self.cap = None
        self.audio = Audio()
        self.camera = Camera()
        
        #tela inicial
        self.login_frame = tb.Frame(self.root)
        self.setup_login_ui()
        
    def setup_login_ui(self):
        self.login_frame.pack(fill=BOTH, expand=True)
        
        center = tb.Frame(self.login_frame)
        center.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        tb.Label(center, text="Teams remake", font=("Helvetica", 35, "bold"), bootstyle=LIGHT).pack(pady=30)
        
        self.ent_nick = tb.Entry(center, font=("Helvetica", 12), width=30)
        self.ent_nick.insert(0, "Nickname")
        self.ent_nick.pack(pady=10)

        self.ent_room = tb.Entry(center, font=("Helvetica", 12), width=30)
        self.ent_room.insert(0, "SALA")
        self.ent_room.pack(pady=10)
        
        tb.Button(center, text="Entrar", bootstyle=SUCCESS, width=20, command=self.join_room).pack(pady=30)

    def join_room(self):
        nickname = self.ent_nick.get().strip()
        room = self.ent_room.get().strip()
        
        if nickname and room:
            self.client = Cliente(nickname, room, lambda u, m: self.root.after(0, self.add_chat_message, u, m),
                                  lambda u, d: self.root.after(0, self.receive_audio, u, d),
                                  lambda u, d: self.root.after(0, self.receive_video, u, d),
                                  lambda vivo: self.root.after(0, self.on_broker_status, vivo))
            
            #troca interf
            self.login_frame.pack_forget()
            self.setup_videocall_ui(nickname, room)

            # escuta
            self.client.threadEscuta()

            self.start_media()
            
            self.client.enviarMsg("Entrou na ligação")
            self.add_chat_message(nickname, "Bem-vindo")


    def setup_videocall_ui(self, nick, room):
        self.main_container = tb.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

        video_side = tb.Frame(self.main_container)
        video_side.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        self.video_display = tb.Label(video_side, text="inicializando camera...", font=("Helvetica", 14), 
                                     bootstyle=SECONDARY, anchor=CENTER)
        self.video_display.pack(expand=True, fill=BOTH)

        # Controles de video
        btn_frame = tb.Frame(video_side)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, text="Sair da ligação", bootstyle=DANGER, command=self.quit_app).pack()


        chat_side = tb.Frame(self.main_container, width=350, bootstyle=DARK)
        chat_side.pack(side=RIGHT, fill=Y)
        chat_side.pack_propagate(False) 

        tb.Label(chat_side, text=f"SALA: {room}", font=("Helvetica", 12, "bold"), bootstyle=INFO).pack(pady=10)

        # Historico do Chat
        self.chat_text = scrolledtext.ScrolledText(chat_side, wrap=tk.WORD, bg="#1a1a1a", fg="white", 
                                                 font=("Helvetica", 10), state=DISABLED)
        self.chat_text.pack(expand=True, fill=BOTH, padx=10, pady=5)

        self.chat_text.tag_config("sistema", foreground="#00FF00", font=("Helvetica", 10, "bold"))
        self.chat_text.tag_config("sair", foreground="#FF3300", font=("Helvetica", 10, "bold"))

        # --- INPUT---
        input_container = tb.Frame(chat_side)
        input_container.pack(fill=X, padx=10, pady=10)

        self.msg_entry = tb.Entry(input_container, font=("Helvetica", 11))
        self.msg_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        self.msg_entry.bind("<Return>", lambda e: self.send_chat())

        tb.Button(input_container, text="Enviar", bootstyle=PRIMARY, command=self.send_chat).pack(side=RIGHT)

    def send_chat(self):
        msg = self.msg_entry.get().strip()
        if msg and self.client:
            self.client.enviarMsg(msg)
            self.add_chat_message("Eu", msg)
            self.msg_entry.delete(0, END)

    def add_chat_message(self, user, msg, tag=None):
        self.chat_text.config(state=NORMAL)

        if "Entrou na ligação" in msg:
            tag = "sistema"
        elif "saiu da ligação" in msg:
            tag = "sair"

        self.chat_text.insert(END, f"[{user}]: {msg}\n", tag)
        self.chat_text.see(END)
        self.chat_text.config(state=DISABLED)

    def start_media(self):
        self.video_running = True
        self.audio_running = True
        self.cap = cv2.VideoCapture(0)
        self.update_frame()
        threading.Thread(target=self.send_audio_loop, daemon=True).start()

    def update_frame(self):
        if self.video_running:
            ret, frame = self.cap.read()
            if ret:
                # Enviar frame
                if self.client:
                    frame_data = cv2.imencode('.jpg', frame)[1].tobytes()
                    self.client.enviarVideo(frame_data)

                # modificar para a logica /vid/{sala}
                frame = cv2.flip(frame, 1)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((700, 500)) 
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_display.imgtk = imgtk
                self.video_display.configure(image=imgtk)
            
            self.root.after(100, self.update_frame)  # Aumentar intervalo para reduzir carga

    def send_audio_loop(self):
        while self.audio_running and self.client:
            data = self.audio.read(1024)
            self.client.enviarAudio(data)
            # Pequena pausa para não sobrecarregar
            time.sleep(0.01)

    def quit_app(self):
        self.video_running = False
        self.audio_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.client:
            self.client.desconectar()
            self.client = None

        self.main_container.destroy()
        self.login_frame = tb.Frame(self.root)
        self.setup_login_ui()

    def receive_audio(self, user, data):
        if self.audio:
            self.audio.write(data)

    def receive_video(self, user, data):
        pass

    def on_broker_status(self, vivo):
        if not vivo:
            self.reconect_popup = tk.Toplevel(self.root)
            self.reconect_popup.title("")
            self.reconect_popup.geometry("250x100")
            self.reconect_popup.resizable(False, False)
            self.reconect_popup.grab_set()
            tb.Label(
                self.reconect_popup,
                text="Reconectando...",
                font=("Helvetica", 14, "bold"),
                bootstyle=WARNING
            ).pack(expand=True)
        else:
            if hasattr(self, "reconect_popup") and self.reconect_popup.winfo_exists():
                self.reconect_popup.destroy()
        if not vivo:
            self.reconect_popup = tk.Toplevel(self.root)
            self.reconect_popup.title("")
            self.reconect_popup.geometry("250x100")
            self.reconect_popup.resizable(False, False)
            self.reconect_popup.grab_set()
            tb.Label(
                self.reconect_popup,
                text="Reconectando...",
                font=("Helvetica", 14, "bold"),
                bootstyle=WARNING
            ).pack(expand=True)
        else:
            if hasattr(self, "reconect_popup") and self.reconect_popup.winfo_exists():
                self.reconect_popup.destroy()

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = VideoCallApp(root)
    root.mainloop()

#end