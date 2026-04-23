from typing import *
import cv2


class Camera:
    def __init__(self, filename=0):
        self._camera = None

        try:
            self._camera = cv2.VideoCapture(filename)
        except cv2.error:
            print("[!] Não conseguimo abrir a câmera cumpadi!")
    
    def get_frame(self) -> Union[bytes, None]:
        if not self._camera: return None
        ret, frame = self._camera.read()

        if frame is not None:
            return frame.tobytes()

        return None



if __name__ == "__main__":
    camera = Camera()
    print(camera.get_frame())