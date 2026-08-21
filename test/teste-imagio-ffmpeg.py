import imageio.v3 as iio
import cv2 as cv

try:
    frames = iio.imiter("<video0>")
    
    for frame in frames:
        frame_bgr = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
        
        cv.imshow("Camera ImageIO", frame_bgr)
        
        if cv.waitKey(1) == ord('q'):
            break

except Exception as e:
    print(f"Erro ao capturar: {e}")
finally:
    cv.destroyAllWindows()