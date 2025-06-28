from ultralytics import YOLO

# Carrega o modelo treinado
model = YOLO('yolov8n.pt')

# Exporta para ONNX
model.export(format='onnx')

