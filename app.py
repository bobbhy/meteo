from asyncio.windows_events import NULL
from flask import Flask
from flask_mqtt import Mqtt
import requests
from datetime import datetime
import json
from RainConverter import selector as EtatMeteo

app = Flask(__name__)

API_URL = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=271d1234d3f497eed5b1d80a07b3fcd1'
LONGITUDE = 1.858686
LATITUDE = 50.95129
ORDER = [
    "EtatMeteo",
    "Pression", 
    "VentDeg",
    "VentVitesse", 
    "Datetime"
]
app.config['MQTT_BROKER_URL'] = '192.168.96.219'
app.config['MQTT_USERNAME'] = 'pi'
app.config['MQTT_PASSWORD'] = 'raspberrypi'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_REFRESH_TIME'] = 1.0
mqtt = Mqtt(app)
temp1 = NULL
temp2 = NULL
hum1 = NULL
hum2 = NULL

# Conversion du Fahrenheit au Celcius
def F2C(F):
    return (F - 32) * 5 / 9

def get_get():
    request = requests.get(API_URL.format("calais"))
    request = request.json()
    # La reponse qu'on va donner 
    response = {}
    # Traitement sur temperature
    response["Ressentie"] = F2C(request["main"]["feels_like"])
    response["Temperature"] = F2C(request["main"]["temp"])
    response["TemperatureMax"] = F2C(request["main"]["temp_max"])
    response["TemperatureMin"] = F2C(request["main"]["temp_min"])

    # Pression
    response["Pression"] = request["main"]["pressure"]

    # Humidity
    response["Humidite"] = request["main"]["humidity"]
    # Temps de mesure
    response["Datetime"] = datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")

    # Vent
    response["VentDeg"] = request["wind"]["deg"]
    response["VentVitesse"] = request["wind"]["speed"]

    # Météo
    if request["weather"][0]["id"] in EtatMeteo.keys():
        response["EtatMeteo"] = EtatMeteo[request["weather"][0]["id"]]
    else:
        response["EtatMeteo"] = "Non définit"
    response = eval(json.dumps(response, indent = 4))
    return response

def writing(response):
    with open("tmp.txt", "a") as f:
        for i in range(len(ORDER)):
            f.write(str(response[ORDER[i]]) + "\n")

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp1/dht/temperature')
    mqtt.subscribe('esp1/dht/humidity')
    mqtt.subscribe('esp2/dht/temperature')
    mqtt.subscribe('esp2/dht/humidity')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global temp1, temp2, hum1, hum2
    if message.topic == 'esp1/dht/temperature':
        temp1 = float(message.payload.decode())
    if message.topic == 'esp2/dht/temperature':
        temp2 = float(message.payload.decode())
    if message.topic == 'esp1/dht/humidity':
        hum1 = float(message.payload.decode())
    if message.topic == 'esp2/dht/humidity':
        hum2 = float(message.payload.decode())
    if temp1 != NULL and temp2 != NULL and hum1 != NULL and hum2 != NULL:
        with open("tmp.txt","w") as fi:
            fi.write(str(temp1)+"\n"+str(temp2)+"\n"+str(hum1)+"\n"+str(hum2)+"\n")
        writing(get_get())
        temp1 = NULL
        temp2 = NULL
        hum1 = NULL
        hum2 = NULL
    
if __name__ == "__main__":
  app.run()
