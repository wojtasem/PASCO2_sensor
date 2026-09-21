import serial
import time

PORT = 'COM3'
BAUD_RATE = 9600#115200

def check_and_read_sensor():
    print(f"Inicjalizacja połączenia z sensorem na porcie {PORT} (Baudrate: {BAUD_RATE})...")
    
    try:
        # Weryfikacja połączenia i otwarcie portu
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        
        if ser.is_open:
            print(f"[SUKCES] Port {PORT} został pomyślnie otwarty.")
            print("Nasłuchiwanie danych z sensora (naciśnij Ctrl+C, aby przerwać)...\n")
        else:
            print("[BŁĄD] Nie udało się otworzyć portu.")
            return

        # Odczyt danych w pętli
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Odczyt: {line}")
            
            time.sleep(0.05)

    except serial.SerialException as e:
        print(f"[BŁĄD KRYTYCZNY] Problem z portem szeregowym: {e}")
    except KeyboardInterrupt:
        print("\nPrzerwano działanie programu przez użytkownika.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Zamknięto połączenie z portem COM.")

if __name__ == "__main__":
    check_and_read_sensor()