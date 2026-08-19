import cv2
def list_cameras():
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"Câmera encontrada no índice {i}")
            cap.release()
list_cameras()