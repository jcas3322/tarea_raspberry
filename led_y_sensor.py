import sys
sys.path.insert(0, '/home/julioaguilar/arq2/arq2python/firebase_admin')
sys.path.insert(0, '/home/julioaguilar/arq2/arq2python/google')
sys.path.insert(0, '/home/julioaguilar/arq2/arq2python/cachetools')
from gpiozero import LED
from time import sleep
import firebase_admin
from firebase_admin import credentials, db
import smbus2
import time

# Configuración del sensor AM2320
bus = smbus2.SMBus(1)
AM2320_ADDR = 0x5C

def read_am2320():
    # Enviar señal de despertar
    try:
        bus.write_i2c_block_data(AM2320_ADDR, 0x00, [])
    except:
        pass  # El sensor puede devolver un error si no está "despierto"

    time.sleep(0.002)  # Esperar a que el sensor esté listo

    # Leer datos del sensor
    bus.write_i2c_block_data(AM2320_ADDR, 0x03, [0x00, 0x04])
    time.sleep(0.002)

    data = bus.read_i2c_block_data(AM2320_ADDR, 0x00, 8)
    humidity = ((data[2] << 8) + data[3]) / 10.0
    temperature = (((data[4] & 0x7F) << 8) + data[5]) / 10.0

    if data[4] & 0x80:  # Comprobar si la temperatura es negativa
        temperature = -temperature

    return humidity, temperature

led = LED(26)

# Inicializa la aplicación de Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://arq2-cffb7-default-rtdb.firebaseio.com/'
})

ref_led = db.reference('ledStatus')
ref_temp = db.reference('temperatura')
ref_hum = db.reference('humedad')

try:
    while True:
        # Obtén el valor del campo ledStatus desde Firebase
        led_status = ref_led.get()
        print(f"Estado del LED desde Firebase: {led_status}")

        # Controla el LED según el valor obtenido
        if led_status == 1:
            led.on()
            print("LED encendido")
        else:
            led.off()
            print("LED apagado")

        # Leer valores del sensor AM2320
        humedad, temperatura = read_am2320()
        print(f"Temperatura: {temperatura}°C, Humedad: {humedad}%")

        # Actualizar los valores en Firebase
        ref_temp.set(temperatura)
        ref_hum.set(humedad)

        # Espera 5 segundos antes de la próxima lectura
        sleep(5)

except KeyboardInterrupt:
    print("Interrupción manual, apagando el LED...")
    led.off()
