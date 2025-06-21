import serial
import time

# Configurações
PORT = '/dev/ttyACM0'    # Porta do Mega (verifique com ls /dev/ttyACM*)
BAUDRATE = 115200
REQUEST_CHAR = b'R'
INTERVAL = 1.0           # segundos entre requisições

def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    time.sleep(2)  # espera o Mega resetar
    print(f"Conectado em {PORT} @ {BAUDRATE} baud\n")
    try:
        while True:
            ser.write(REQUEST_CHAR)               # envia 'R'
            line = ser.readline().decode().strip()
            if line:
                vals = line.split(';')
                print("Leituras:")
                for i, v in enumerate(vals):
                    print(f"  Sensor {i}: {v} cm")
            else:
                print("Sem resposta ou timeout.")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nFechando porta serial…")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
