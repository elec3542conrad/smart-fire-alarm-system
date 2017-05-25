from sense_hat import SenseHat
import threading
import time
import sys
import paho.mqtt.client as mqtt

sense = SenseHat()
led_onoff = True
sensor_onoff = True
led_color = "green"

smoke = False
humidity = sense.get_humidity()
temperature = sense.get_temperature()

humidity_warning = 20 
temperature_limit = 100

alert = ""

client_id = "1"

broker_address="172.27.0.2"
client = mqtt.Client("C" + client_id)

def smoke_detect(): # simulation
	return False

def humidity_detect():
	return sense.get_humidity()

def temperature_detect():
	return  sense.get_temperature()

def led(color, flash=0):
	if color == "yellow":
		sense.low_light = False
		sense.clear((255,255,0))
		time.sleep(flash)

	elif color == "red":
		sense.low_light = False
		sense.clear((255,0,0))
		time.sleep(flash)

	elif color == "green":
		sense.low_light = True
		sense.clear((0,255,0))
		time.sleep(flash)

	else:
		sense.clear()
		time.sleep(flash)


class ledThread (threading.Thread):  #handle LED color change
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		while (led_onoff):
			if (alert == ""):
				if(led_color == "green"):
					led("green", 1)
					led("", 3)
				elif(led_color == "red"):			
					led("red", 0.5)
					led("", 0.5) 
				elif(led_color =="yellow"):
					led("yellow", 1)
					led("", 1)   
				else:
					led("", 1)   
			else:
				print("Alert!!!")
				sense.show_message(alert, text_colour=[255, 0, 0])
				os.system('mpg321 alarm.mp3 &')


class sensorThread (threading.Thread): # Sense the environment peroidically
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		global smoke
		global humidity
		global temperature
		while (sensor_onoff):
			smoke = smoke_detect()
			humidity = humidity_detect()
			temperature = temperature_detect()
			print("smoke: " + str(smoke))
			print("humidity: " + str(humidity))
			print("temperature: " + str(temperature))
			time.sleep(3)

class logicThread (threading.Thread): # Issue messages and decide the led color base on the environment
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		while (sensor_onoff):
			if(humidity < humidity_warning):
				led_color = "yellow"
			if (temperature > temperature_limit):
				led_color = "red"
				client.publish("pj", client_id+":T:"+str(temperature))
			if (smoke):
				led_color = "red"
				client.publish("pj", client_id+":S:"+str(smoke))
			else:
				led_color = "green"
			time.sleep(1)



def on_connect(client, userdata, flags, rc):
	m="Connected flags"+str(flags)+"result code " +str(rc)+"client_id  "+str(client)
	print(m)

def on_message(client, userdata, message):
	global alert
	m = str(message.payload.decode("utf-8"))
	print("message received:  "  , m)	
	m_list = m.split(":")
	if (m_list[0] != client_id): #ignore message sent by itself
		if(m_list[1] == "T"):
			alert = "C" + m_list[0] + ":T" + m_list[2]
		elif(m_list[1] == "S"):
			alert = "C" + m_list[0] + ":S"

try:
	client.on_connect = on_connect
	client.on_message = on_message  
	time.sleep(1)
	client.connect(broker_address)
except:
	print("connection error")
	sys.exit(0)

thread1 = ledThread(1, "ledThread")
thread2 = sensorThread(2, "sensorThread")
thread3 = logicThread(3, "logicThread")
thread4 = logicThread(4, "mqttThread")
thread1.start()
thread2.start()
thread3.start()
thread4.start()

client.loop_start() 
client.subscribe("pj")

time.sleep(60)
led_onoff = False
sensor_onoff = False
thread1.join()
thread2.join()
thread3.join()
thread4.join()
client.disconnect()
client.loop_stop()