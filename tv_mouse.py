import av
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import HandLandmarkerOptions, HandLandmarker
import numpy as np
import argparse
import urllib.request
import os
import time
import ctypes
import platform
from pynput.mouse import Button, Controller

parser = argparse.ArgumentParser(description="TV Mouse Otimizado (PyAV + Tasks API)")
parser.add_argument('--camera', type=str, required=True, help='Nome EXATO da câmera')
parser.add_argument('--kando', type=float, default=3.0, help='Sensibilidade do movimento')
parser.add_argument('--headless', action='store_true', help='Desativa a janela de vídeo')
args = parser.parse_args()

mouse = Controller()
pf = platform.system()

def get_virtual_screen():
    if pf == 'Windows':
        SM_XVIRTUALSCREEN  = 76
        SM_YVIRTUALSCREEN  = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79
        gm = ctypes.windll.user32.GetSystemMetrics
        return (gm(SM_XVIRTUALSCREEN), gm(SM_YVIRTUALSCREEN),
                gm(SM_CXVIRTUALSCREEN), gm(SM_CYVIRTUALSCREEN))
    return (0, 0, 1920, 1080)

virt_x, virt_y, virt_w, virt_h = get_virtual_screen()
screenRes = (virt_x + virt_w, virt_y + virt_h)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'

def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print(f'Baixando modelo mediapipe em {MODEL_PATH} ...')
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print('Download concluído.')

def capture_frames_windows(device_name):
    container = None
    try:
        container = av.open(
            f'video={device_name}', 
            format='dshow', 
            options={'framerate': '30', 'video_size': '640x480'}
        )
        stream = container.streams.video[0]
        stream.thread_type = "AUTO" 
        
        for frame in container.decode(stream):
            yield frame.to_ndarray(format='bgr24')
            
    except Exception as e:
        print(f"Erro fatal na captura: {e}")
        exit(1)
    finally:
        if container:
            container.close()

def calculate_distance(l1, l2):
    return np.linalg.norm(np.array([l1.x, l1.y]) - np.array([l2.x, l2.y]))

def draw_circle(image, x, y, roundness, color):
    cv2.circle(image, (int(x), int(y)), roundness, color, thickness=5, lineType=cv2.LINE_8)

def main():
    ensure_model()

    options = HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp_vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.7,
        min_tracking_confidence=0.7
    )
    detector = HandLandmarker.create_from_options(options)

    dis = 0.7
    preX, preY = 0, 0
    nowCli, preCli = 0, 0
    norCli, prrCli = 0, 0
    douCli = 0
    i, k, h = 0, 0, 0
    LiTx, LiTy = [], []
    nowUgo = 1
    start, c_start = float('inf'), float('inf')
    ran = 3

    print(f"Iniciando controle rápido. Pressione Ctrl+C no terminal para encerrar.")

    for image in capture_frames_windows(args.camera):
        p_s = time.perf_counter()
        
        image = cv2.flip(image, 1)
        image_height, image_width, _ = image.shape

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(p_s * 1000)
        
        result = detector.detect_for_video(mp_image, timestamp_ms)

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]
            
            absKij = calculate_distance(lm[0], lm[1])
            absUgo = calculate_distance(lm[8], lm[12]) / absKij
            absCli = calculate_distance(lm[4], lm[6]) / absKij

            if i == 0:
                preX, preY = lm[8].x, lm[8].y
                for _ in range(ran):
                    LiTx.append(lm[8].x)
                    LiTy.append(lm[8].y)
                i += 1

            LiTx.append(lm[8].x)
            LiTy.append(lm[8].y)
            if len(LiTx) > ran:
                LiTx.pop(0)
                LiTy.pop(0)

            posx, posy = mouse.position
            nowX = sum(LiTx) / ran
            nowY = sum(LiTy) / ran
            
            dx = args.kando * (nowX - preX) * image_width
            dy = args.kando * (nowY - preY) * image_height
            dx += 0.5
            dy += 0.5
            
            preX, preY = nowX, nowY

            if posx + dx < virt_x: dx = virt_x - posx
            elif posx + dx > screenRes[0]: dx = screenRes[0] - posx
            if posy + dy < virt_y: dy = virt_y - posy
            elif posy + dy > screenRes[1]: dy = screenRes[1] - posy

            if absCli < dis:
                nowCli = 1
                draw_circle(image, lm[8].x * image_width, lm[8].y * image_height, 20, (0, 250, 250))
            else:
                nowCli = 0

            if np.abs(dx) > 5 and np.abs(dy) > 5:
                k = 0

            if nowCli == 1 and np.abs(dx) < 5 and np.abs(dy) < 5:
                if k == 0:
                    start = time.perf_counter()
                    k += 1
                if time.perf_counter() - start > 1.5:
                    norCli = 1
                    draw_circle(image, lm[8].x * image_width, lm[8].y * image_height, 20, (0, 0, 250))
            else:
                norCli = 0

            if absUgo >= dis and nowUgo == 1:
                mouse.move(dx, dy)
                draw_circle(image, lm[8].x * image_width, lm[8].y * image_height, 8, (250, 0, 0))

            if nowCli == 1 and nowCli != preCli:
                if h == 1: h = 0
                elif h == 0: mouse.press(Button.left)

            if nowCli == 0 and nowCli != preCli:
                mouse.release(Button.left)
                k = 0
                if douCli == 0:
                    c_start = time.perf_counter()
                    douCli += 1
                if 10 * (time.perf_counter() - c_start) > 5 and douCli == 1:
                    mouse.click(Button.left, 2)
                    douCli = 0

            if norCli == 1 and norCli != prrCli:
                mouse.press(Button.right)
                mouse.release(Button.right)
                h = 1

            if lm[8].y - lm[5].y > -0.06:
                mouse.scroll(0, -dy / 50)
                draw_circle(image, lm[8].x * image_width, lm[8].y * image_height, 20, (0, 0, 0))
                nowUgo = 0
            else:
                nowUgo = 1

            preCli = nowCli
            prrCli = norCli

        if not args.headless:
            p_e = time.perf_counter()
            elapsed = p_e - p_s
            fps = str(int(1 / elapsed)) if elapsed > 0 else '?'
            cv2.putText(image, "FPS:" + fps, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            
            cv2.imshow("TV Mouse Otimizado", image)
            if cv2.waitKey(1) & 0xFF == 27: 
                break

    cv2.destroyAllWindows()
    detector.close()

if __name__ == "__main__":
    main()