import tkinter as tk
from tkinter import scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import cv2
import numpy as np
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
        self.audio = Audio()
        self.camera = Camera()
        self.username = ""
        self.after_id = None

        # tela inicial
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
            self.username = nickname
            self.client = Cliente(
                nickname,
                room,
                lambda u, m: self.root.after(0, self.add_chat_message, u, m),
                lambda u, d: self.root.after(0, self.receive_audio, u, d),
                lambda u, d: self.root.after(0, self.receive_video, u, d),
                lambda vivo: self.root.after(0, self.on_broker_status, vivo),
            )

            self.login_frame.pack_forget()
            self.setup_videocall_ui(nickname, room)
            self.camera = Camera()
            self.client.threadEscuta()
            self.start_media()

            self.client.enviarMsg("Entrou na ligação")
            self.add_chat_message(nickname, "Bem-vindo")

    def setup_videocall_ui(self, nick, room):
        self.main_container = tb.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=True, padx=10, pady=10)

        video_side = tb.Frame(self.main_container)
        video_side.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        # Local video on top
        self.local_video_display = tb.Label(
            video_side,
            text=f"{nick}",
            font=("Helvetica", 12),
            bootstyle=SECONDARY,
            anchor=CENTER,
            compound=CENTER,
        )
        self.local_video_display.pack(fill=BOTH, expand=False)

        # Remote videos in 3x3 grid
        remote_frame = tb.Frame(video_side)
        remote_frame.pack(fill=BOTH, expand=True, pady=(10, 0))

        self.remote_displays = {}
        self.available_displays = []
        for i in range(3):
            for j in range(3):
                label = tb.Label(
                    remote_frame,
                    text="Aguardando...",
                    font=("Helvetica", 10),
                    bootstyle=SECONDARY,
                    anchor=CENTER,
                    compound=CENTER,
                )
                label.grid(row=i, column=j, sticky="nsew", padx=2, pady=2)
                self.available_displays.append(label)

        # Configure grid weights
        for i in range(3):
            remote_frame.grid_rowconfigure(i, weight=1)
            remote_frame.grid_columnconfigure(i, weight=1)

        btn_frame = tb.Frame(video_side)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, text="Sair da ligação", bootstyle=DANGER, command=self.quit_app).pack()

        chat_side = tb.Frame(self.main_container, width=350, bootstyle=DARK)
        chat_side.pack(side=RIGHT, fill=Y)
        chat_side.pack_propagate(False)

        tb.Label(chat_side, text=f"SALA: {room}", font=("Helvetica", 12, "bold"), bootstyle=INFO).pack(pady=10)

        self.chat_text = scrolledtext.ScrolledText(
            chat_side,
            wrap=tk.WORD,
            bg="#1a1a1a",
            fg="white",
            font=("Helvetica", 10),
            state=DISABLED,
        )
        self.chat_text.pack(expand=True, fill=BOTH, padx=10, pady=5)

        self.chat_text.tag_config("sistema", foreground="#00FF00", font=("Helvetica", 10, "bold"))
        self.chat_text.tag_config("sair", foreground="#FF3300", font=("Helvetica", 10, "bold"))

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
        threading.Thread(target=self.send_audio_loop, daemon=True).start()
        self.update_frame()

    def update_frame(self):
        if self.video_running:
            frame = self.camera.get_frame(self.username or "User")
            if frame is not None:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                img = img.resize((400, 200))
                imgtk = ImageTk.PhotoImage(image=img)
                self.local_video_display.imgtk = imgtk
                self.local_video_display.configure(image=imgtk, text=self.username)

                if self.client:
                    try:
                        encoded = cv2.imencode('.jpg', frame)[1].tobytes()
                        self.client.enviarVideo(encoded)
                    except Exception as e:
                        print(f"[GUI] Erro ao codificar vídeo local: {e}")

        self.after_id = self.root.after(100, self.update_frame)

    def send_audio_loop(self):
        while self.audio_running and self.client:
            try:
                data = self.audio.read(1024)
                self.client.enviarAudio(data)
            except Exception as e:
                print(f"[GUI] Erro de áudio: {e}")
            time.sleep(0.01)

    def quit_app(self):
        self.video_running = False
        self.audio_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if self.client:
            self.client.desconectar()
            self.client = None
        self.camera.release()
        self.main_container.destroy()
        self.login_frame = tb.Frame(self.root)
        self.setup_login_ui()

    def receive_audio(self, user, data):
        if self.audio:
            self.audio.write(data)

    def receive_video(self, user, data):
        try:
            arr = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img = img.resize((200, 150))
                imgtk = ImageTk.PhotoImage(image=img)
                
                if user not in self.remote_displays:
                    if self.available_displays:
                        display = self.available_displays.pop(0)
                        self.remote_displays[user] = display
                    else:
                        return  # No available displays
                
                display = self.remote_displays[user]
                display.imgtk = imgtk
                display.configure(image=imgtk, text=user)
        except Exception as e:
            print(f"[GUI] Erro ao decodificar vídeo remoto: {e}")

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
                bootstyle=WARNING,
            ).pack(expand=True)
        else:
            if hasattr(self, "reconect_popup") and self.reconect_popup.winfo_exists():
                self.reconect_popup.destroy()


if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = VideoCallApp(root)
    root.mainloop()

#end