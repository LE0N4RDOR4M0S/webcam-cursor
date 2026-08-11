import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import HandLandmarkerOptions, HandLandmarker
import numpy as np
import time
import tkinter as tk
from pynput.mouse import Button, Controller
import platform
import urllib.request
import os
import ctypes

pf = platform.system()
mouse = Controller()

# Área virtual total de todos os monitores
def get_virtual_screen():
    """Retorna (x_origin, y_origin, largura_total, altura_total) de todos os monitores."""
    if pf == 'Windows':
        SM_XVIRTUALSCREEN  = 76
        SM_YVIRTUALSCREEN  = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79
        gm = ctypes.windll.user32.GetSystemMetrics
        return (
            gm(SM_XVIRTUALSCREEN),
            gm(SM_YVIRTUALSCREEN),
            gm(SM_CXVIRTUALSCREEN),
            gm(SM_CYVIRTUALSCREEN),
        )
    else:
        # Fallback: tkinter (monitor primário)
        root = tk.Tk()
        root.withdraw()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        return (0, 0, w, h)

virt_x, virt_y, virt_w, virt_h = get_virtual_screen()
screenRes = (virt_x + virt_w, virt_y + virt_h)   # limites máximos do cursor

# ---------------------------------------------------------------------------
# Baixa o modelo se não existir
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
MODEL_URL = (
    'https://storage.googleapis.com/mediapipe-models/hand_landmarker/'
    'hand_landmarker/float16/latest/hand_landmarker.task'
)

def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print(f'Baixando modelo mediapipe em {MODEL_PATH} ...')
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print('Download concluído.')

# ---------------------------------------------------------------------------
# Desenho dos landmarks (substitui mp_drawing.draw_landmarks)
# ---------------------------------------------------------------------------
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17),
]

def draw_landmarks_manual(image, landmarks, image_width, image_height):
    pts = [
        (int(lm.x * image_width), int(lm.y * image_height))
        for lm in landmarks
    ]
    for a, b in HAND_CONNECTIONS:
        cv2.line(image, pts[a], pts[b], (0, 255, 0), 2)
    for pt in pts:
        cv2.circle(image, pt, 4, (255, 255, 255), -1)

# ---------------------------------------------------------------------------

def tk_arg():
    root = tk.Tk()
    root.title("First Setup")
    root.geometry("300x320")
    Val1 = tk.IntVar()
    Val2 = tk.IntVar()
    Val4 = tk.IntVar()
    Val4.set(30)
    place = ['Normal', 'Above', 'Behind']
    tk.Label(text='Camera').grid(row=1)
    for i in range(3):
        tk.Radiobutton(root, value=i, variable=Val1,
                       text=f'Device{i}').grid(row=2, column=i * 2)
    tk.Label(text='     ').grid(row=3)
    tk.Label(text='How to place').grid(row=4)
    for i in range(3):
        tk.Radiobutton(root, value=i, variable=Val2,
                       text=f'{place[i]}').grid(row=5, column=i * 2)
    tk.Label(text='     ').grid(row=6)
    tk.Label(text='Sensitivity').grid(row=7)
    tk.Scale(root, orient='h', from_=1, to=100,
             variable=Val4).grid(row=8, column=2)
    tk.Label(text='     ').grid(row=9)
    tk.Button(text="continue", command=root.destroy).grid(row=10, column=2)
    root.mainloop()
    cap_device = Val1.get()
    mode = Val2.get()
    kando = Val4.get() / 10
    return cap_device, mode, kando


def draw_circle(image, x, y, roundness, color):
    cv2.circle(image, (int(x), int(y)), roundness, color,
               thickness=5, lineType=cv2.LINE_8, shift=0)


def calculate_distance(l1, l2):
    v = np.array([l1.x, l1.y]) - np.array([l2.x, l2.y])
    return np.linalg.norm(v)


# ---------------------------------------------------------------------------
# Landmark simples para compatibilidade com calculate_distance
# ---------------------------------------------------------------------------
class _LM:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


def main(cap_device, mode, kando):
    ensure_model()

    dis = 0.7
    preX, preY = 0, 0
    nowCli, preCli = 0, 0
    norCli, prrCli = 0, 0
    douCli = 0
    i, k, h = 0, 0, 0
    LiTx = []
    LiTy = []
    nowUgo = 1
    cap_width = 1280
    cap_height = 720
    start, c_start = float('inf'), float('inf')
    c_text = 1

    window_name = 'NonMouse'
    cv2.namedWindow(window_name)
    cap = cv2.VideoCapture(cap_device)
    cfps = int(cap.get(cv2.CAP_PROP_FPS))
    if cfps < 30:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cap_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_height)
        cfps = int(cap.get(cv2.CAP_PROP_FPS))
    ran = max(int(cfps / 10), 1)

    # Nova API mediapipe 1.x
    options = HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp_vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.8,
        min_hand_presence_confidence=0.8,
        min_tracking_confidence=0.8,
    )
    detector = HandLandmarker.create_from_options(options)

    while cap.isOpened():
        p_s = time.perf_counter()
        success, image = cap.read()
        if not success:
            continue

        if mode == 1:
            image = cv2.flip(image, 0)
        elif mode == 2:
            image = cv2.flip(image, 1)

        image = cv2.flip(image, 1)
        image_height, image_width, _ = image.shape

        # Converte para RGB e processa
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(mp_image)

        hand_landmarks_list = result.hand_landmarks  # lista de listas de NormalizedLandmark

        if hand_landmarks_list:
            landmarks_raw = hand_landmarks_list[0]  # primeira mão

            # Converte para objetos com .x .y para reutilizar funções existentes
            lm = [_LM(p.x, p.y, p.z) for p in landmarks_raw]

            # Desenha esqueleto
            draw_landmarks_manual(image, lm, image_width, image_height)

            # Sempre ativo — sem necessidade de pressionar hotkey
            can = 1
            c_text = 0

            if can == 1:
                if i == 0:
                    preX = lm[8].x
                    preY = lm[8].y
                    for _ in range(ran):
                        LiTx.append(lm[8].x)
                        LiTy.append(lm[8].y)
                    i = +1

                absKij = calculate_distance(lm[0], lm[1])
                absUgo = calculate_distance(lm[8], lm[12]) / absKij
                absCli = calculate_distance(lm[4], lm[6]) / absKij

                LiTx.append(lm[8].x)
                LiTy.append(lm[8].y)
                if len(LiTx) > ran:
                    LiTx.pop(0)
                    LiTy.pop(0)

                posx, posy = mouse.position
                nowX = sum(LiTx) / ran
                nowY = sum(LiTy) / ran
                dx = kando * (nowX - preX) * image_width
                dy = kando * (nowY - preY) * image_height
                if pf == 'Windows' or pf == 'Linux':
                    dx = dx + 0.5
                    dy = dy + 0.5
                preX = nowX
                preY = nowY

                # Clamp dentro da área virtual de todos os monitores
                if posx + dx < virt_x:
                    dx = virt_x - posx
                elif posx + dx > screenRes[0]:
                    dx = screenRes[0] - posx
                if posy + dy < virt_y:
                    dy = virt_y - posy
                elif posy + dy > screenRes[1]:
                    dy = screenRes[1] - posy

                if absCli < dis:
                    nowCli = 1
                    draw_circle(image, lm[8].x * image_width,
                                lm[8].y * image_height, 20, (0, 250, 250))
                elif absCli >= dis:
                    nowCli = 0

                if np.abs(dx) > 5 and np.abs(dy) > 5:
                    k = 0

                if nowCli == 1 and np.abs(dx) < 5 and np.abs(dy) < 5:
                    if k == 0:
                        start = time.perf_counter()
                        k += 1
                    end = time.perf_counter()
                    if end - start > 1.5:
                        norCli = 1
                        draw_circle(image, lm[8].x * image_width,
                                    lm[8].y * image_height, 20, (0, 0, 250))
                else:
                    norCli = 0

                if absUgo >= dis and nowUgo == 1:
                    mouse.move(dx, dy)
                    draw_circle(image, lm[8].x * image_width,
                                lm[8].y * image_height, 8, (250, 0, 0))

                if nowCli == 1 and nowCli != preCli:
                    if h == 1:
                        h = 0
                    elif h == 0:
                        mouse.press(Button.left)

                if nowCli == 0 and nowCli != preCli:
                    mouse.release(Button.left)
                    k = 0
                    if douCli == 0:
                        c_start = time.perf_counter()
                        douCli += 1
                    c_end = time.perf_counter()
                    if 10 * (c_end - c_start) > 5 and douCli == 1:
                        mouse.click(Button.left, 2)
                        douCli = 0

                if norCli == 1 and norCli != prrCli:
                    mouse.press(Button.right)
                    mouse.release(Button.right)
                    h = 1

                if lm[8].y - lm[5].y > -0.06:
                    mouse.scroll(0, -dy / 50)
                    draw_circle(image, lm[8].x * image_width,
                                lm[8].y * image_height, 20, (0, 0, 0))
                    nowUgo = 0
                else:
                    nowUgo = 1

                preCli = nowCli
                prrCli = norCli
                c_text = 0

        if c_text == 1:
            cv2.putText(image, "Aguardando mao...", (20, 450),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        cv2.putText(image, "cameraFPS:" + str(cfps), (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        p_e = time.perf_counter()
        elapsed = float(p_e) - float(p_s)
        fps = str(int(1 / elapsed)) if elapsed > 0 else '?'
        cv2.putText(image, "FPS:" + fps, (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        dst = cv2.resize(image, dsize=None, fx=0.4, fy=0.4)
        cv2.imshow(window_name, dst)
        if (cv2.waitKey(1) & 0xFF == 27) or \
                (cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) == 0):
            break

    cap.release()
    detector.close()


if __name__ == "__main__":
    cap_device, mode, kando = tk_arg()
    main(cap_device, mode, kando)
