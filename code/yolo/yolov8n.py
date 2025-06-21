from ultralytics import YOLO
from track import Track
import cv2

# Carregar o modelo treinado
model = YOLO('best.pt')  #caminho do modelo YOLOv8n treinado

# Inicializar a câmera 
camera = cv2.VideoCapture(0)

class YOLOv8n:
  while True:
      ret, frame = camera.read()
      if not ret:
          break

      # Fazer a inferência com YOLOv8n
      results = model(frame)

      # Iterar sobre as detecções
      for r in results:
          for box in r.boxes:
              cls = int(box.cls[0])  # classe detectada (esperamos que seja peixe = 0)
              conf = float(box.conf[0])  # confiança
              x1, y1, x2, y2 = map(int, box.xyxy[0])  # coordenadas da caixa

              # Calcular centro da caixa
              cx = int((x1 + x2) / 2)
              cy = int((y1 + y2) / 2)

              # Desenhar retângulo e centro
              cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
              cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

              # Mostrar texto com coordenadas
              text = f"Peixe: {conf:.2f} | Centro: ({cx}, {cy})"
              cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

      # Mostrar o frame
      cv2.imshow("Rastreamento de Peixe", frame)

      if cv2.waitKey(1) & 0xFF == ord('q'):
          break

  # Encerrar
  camera.release()
  cv2.destroyAllWindows()

 def track_fps(self):
        """
        Call once per frame. Returns (instant_fps, median_fps_or_None),
        logging median only every fps_window_s seconds.
        """
      now = time.time()
        # instantaneous
      inst = 1.0/(now - self.prev_time) if now>self.prev_time else 0.0
      self.prev_time = now

        # history
      self.fps_history.append((now, inst))
      while self.fps_history and now - self.fps_history[0][0] > self.fps_window_s:
          self.fps_history.popleft()

        # median every window
      med = None
      if now - self.last_median_log >= self.fps_window_s:
          vals = [f for (_,f) in self.fps_history]
          if vals:
              med = median(vals)
              logging.info(f"Median FPS (last {self.fps_window_s}s): {med:.1f}")
          self.last_median_log = now

return inst, med
