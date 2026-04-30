# tem q instsalar o portaudio19-dev no ubuntu

# Source - https://stackoverflow.com/a/64823047
# Posted by sawyermclane
# Retrieved 2026-04-23, License - CC BY-SA 4.0

#sudo apt install portaudio19-dev


import pyaudio

class Audio:
    def __init__(self):
        self._p = pyaudio.PyAudio()
        self._stream = None
        self.can_read = False
        self.can_write = False

        # Tenta abrir Full Duplex (Input + Output)
        try:
            self._stream = self._p.open(
                format=pyaudio.paInt16,
                channels=2,
                rate=44100,
                output=True,
                input=True
            )
            self.can_read = True
            self.can_write = True
            print("[Audio] Stream Full Duplex aberto com sucesso.")
        except Exception as e:
            print(f"[Audio] Erro ao abrir Full Duplex (possível conflito de mic): {e}")
            
            # Fallback: Tenta abrir apenas Output (para poder ouvir os outros)
            try:
                self._stream = self._p.open(
                    format=pyaudio.paInt16,
                    channels=2,
                    rate=44100,
                    output=True,
                    input=False
                )
                self.can_write = True
                print("[Audio] Fallback: Apenas Output aberto.")
            except Exception as e2:
                print(f"[Audio] Erro crítico ao abrir Output: {e2}")

    def write(self, data: bytes):
        if self.can_write and self._stream:
            try:
                self._stream.write(data)
            except Exception:
                pass
    
    def read(self, size=1024) -> bytes:
        if self.can_read and self._stream:
            try:
                return self._stream.read(size, exception_on_overflow=False)
            except Exception:
                pass
        return b'\x00' * (size * 4) # Silêncio se não puder ler (2 canais * 2 bytes/sample)

    def release(self):
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        if self._p:
            try:
                self._p.terminate()
            except Exception:
                pass
        self.can_read = False
        self.can_write = False
        self._stream = None
        self._p = None


if __name__ == "__main__":
    audio = Audio()

    #while True:
    #    audio.write(audio.read(1024))

    import wave
    with wave.open('test-audio.wav', 'rb') as wf:
        while len(data := wf.readframes(1024)):  # Requires Python 3.8+ for :=
            audio.write(data)