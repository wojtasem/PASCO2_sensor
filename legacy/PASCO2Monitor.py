#import psycopg2
import serial
import time

# Windows COM port
SERIAL_DEV = "COM3"      # zmień na właściwy port
BAUDRATE = 9600


def byte_in_ascii_to_int(data):
    try:
        return int(data.decode().strip(), 16)
    except Exception:
        return 0


# # PostgreSQL
# db_conn = psycopg2.connect(
    # database="roomco2",
    # host="localhost",
    # user="postgres",      # zmień jeśli potrzeba
    # password="password",  # zmień jeśli potrzeba
    # port="5432"
# )

try:
    ser_dev = serial.Serial(SERIAL_DEV, BAUDRATE, timeout=12)
    ser_dev.reset_input_buffer()
    print(f"Connected to {SERIAL_DEV}")

except serial.SerialException as e:
    print(f"Cannot open serial port: {e}")
    exit()

try:
    # Idle mode
    ser_dev.write(bytes([0x57, 0x2C, 0x30, 0x34, 0x2C, 0x30, 0x30, 0x0A]))
    print(ser_dev.readline())

    # Measurement rate
    ser_dev.write(bytes([0x57, 0x2C, 0x30, 0x32, 0x2C, 0x30, 0x30, 0x0A]))
    print(ser_dev.readline())

    ser_dev.write(bytes([0x57, 0x2C, 0x30, 0x33, 0x2C, 0x30, 0x41, 0x0A]))
    print(ser_dev.readline())

    # Continuous mode
    ser_dev.write(bytes([0x57, 0x2C, 0x30, 0x34, 0x2C, 0x30, 0x32, 0x0A]))
    print(ser_dev.readline())

    ser_dev.reset_input_buffer()

    ppm = 0

    for _ in range(70):

        # Read status
        ser_dev.write(bytes([0x52, 0x2C, 0x30, 0x37, 0x0A]))
        status = ser_dev.readline()
        print(f"Status: {status}")

        # Read MSB
        ser_dev.write(bytes([0x52, 0x2C, 0x30, 0x35, 0x0A]))
        data_recv = ser_dev.readline()
        print(f"MSB raw: {data_recv}")

        msb = byte_in_ascii_to_int(data_recv)

        # Read LSB
        ser_dev.write(bytes([0x52, 0x2C, 0x30, 0x36, 0x0A]))
        data_recv = ser_dev.readline()
        print(f"LSB raw: {data_recv}")

        lsb = byte_in_ascii_to_int(data_recv)

        ppm = (msb << 8) + lsb

        print(f"CO2 = {ppm} ppm")

        time.sleep(5)

    # if ppm > 0:
        # cur = db_conn.cursor()

        # cur.execute(
            # "INSERT INTO room_co2_ppm (ppm) VALUES (%s)",
            # (ppm,)
        # )

        # db_conn.commit()
        # cur.close()

finally:
    #db_conn.close()
    ser_dev.close()

    print("Connections closed.")
