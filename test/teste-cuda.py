import os
import sys

os.environ["OPENCV_LOG_LEVEL"] = "DEBUG"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "1"

try:
    import cv2
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_VERBOSE)
except ImportError as e:
    print(f"Falha ao importar OpenCV: {e}")
    sys.exit(1)

def test_cuda():
    print("\n---Verificando Suporte CUDA ---\n")
    try:
        count = cv2.cuda.getCudaEnabledDeviceCount()
        print(f"Dispositivos CUDA detectados")
        if count > 0:
            device_name = cv2.cuda.printCudaDeviceInfo(0)
            print(f"Dispositivo 0 configurado com sucesso.")
    except Exception as e:
        print(F"Erro ao testar CUDA (comum em falhas de driver/compatibilidade): {e}")

def run_webcam():
    print("\n--- Iniciando Teste de Webcam ---\n")
    
    backend = cv2.CAP_ANY 
    print(f"Tentando abrir a câmera com backend: {backend}")
    
    cap = cv2.VideoCapture(0, backend)
    
    if not cap.isOpened():
        print("Não foi possível abrir a webcam.")
        return

    print("Webcam aberta. Pressione 'Q' na janela de vídeo para sair.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("ALERTA - Falha ao capturar frame da webcam.")
                break
            
            try:
                cv2.imshow("Teste Quadro OpenCV", frame)
            except Exception as e:
                print(f"Falha ao renderizar janela. Você está em ambiente headless? Erro: {e}")
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except Exception as e:
        print(f" Erro durante o loop de captura: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Recursos liberados e janelas fechadas.")

if __name__ == "__main__":
    test_cuda()
    run_webcam()
