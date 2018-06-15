import RPi.GPIO as gpio
import time
import cv2
import threading
import requests
import glob
import base64
import json
from pygame import *
##GPIO Ports Setup---------------------------------
gpio.setmode(gpio.BCM)
gpio.setup(23, gpio.IN, pull_up_down = gpio.PUD_UP)
gpio.setup(17, gpio.OUT)
gpio.setup(27, gpio.OUT)
##-------------------------------------------------
cam = cv2.VideoCapture(0)
headers = {
    'Content-Type':'application/json',
    "app_id": "14f1948c",
    "app_key": "PROTECTED"#API Key for face recognition
}

def getImage(callback=None):
    'Function that gets an image from webcam and then saves it and calls callback'
    global cam
    r, img = cam.read()
    img = cv2.flip(img, 1)
    if r:#Only if an image is received
        cv2.imshow('webcam', img)
        cv2.imwrite('img.png', img)
        if callback:
            return threading.Thread(target=callback).start()#Run in thread to not block further event recieves
        return True
    else:
        print 'ERROR'
    return False
def enroll():
    'Enroll image to KAIROS API'
    encoded = base64.b64encode(open('img.png', "rb").read()).decode('utf-8')#Read and convert binary to base64 then to string
    payload = {"image": encoded,"subject_id":"James","gallery_name":"testing"}
    url = "http://api.kairos.com/enroll"

    # make request
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    print r.content.decode()#Result, either suceeded or failed
def recognize():
    'Check if image is in data base'
    encoded = base64.b64encode(open('img.png', "rb").read()).decode('utf-8')#Read and convert binary to base64 then to string
    payload = {"image": encoded,"gallery_name":"testing"}
    url = "http://api.kairos.com/recognize"
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    print(r.content.decode())
    try:
        confidence = json.loads(r.content.decode())['images'][0]['transaction']['confidence']
        print(confidence)
        if confidence > 0.6:
            print(1)
            return light_on()
    except:#There will be a KeyError if a face is not found
        pass
    return False
def light_on():
    'Turn on LED when face recognition succeeds'
    render = f.render('SUCCESS', True, (255,0,0))
    screen.blit(, (400-render.get_width()//2,200))
    display.flip()
    for i in range(5):
        #Blink LED a few times
        gpio.output(17, True)
        time.wait(0.1)
        gpio.output(17, False)
def press():
    'Sets LED to on if button is pressed'
    gpio.output(27, True)
running = True
screen = display.set_mode((800,600))
font.init()
t = font.SysFont('Arial', 72)
f = font.SysFont('Arial', 32)
color = (0,255,0)#Color changes on hover
while running:
    click = False
    hover = False
    for e in event.get():
        if e.type == QUIT:
            running = False
        elif e.type == MOUSEBUTTONDOWN and e.button == 1:
            click = True
    mx,my = mouse.get_pos()
    if Rect(400-120, 500, 240, 50).collidepoint((mx,my)):#Check if hover
        color = (255,0,0)
        hover = True
    else:
        color = (0,255,0)
    img = image.load('img.png').convert()#Load image that getImage has saved
    screen.blit(img, (400-img.get_width()//2,160))
    title = t.render('Face Recognition', True, (255,255,255))
    screen.blit(title, (400-title.get_width()//2,50))
    button_text = f.render('Take Picture', True, (255,255,255))
    draw.rect(screen, color, (400-120, 500, 240, 50), 1)
    screen.blit(button_text, (400-button_text.get_width()//2,525-button_text.get_height()//2))
    state = gpio.input(23)
    if not state or (click and hover):#Either button press or click screen button triggers actions
        print 'pressed'
        press()
        getImage(recognize)
        time.wait(1000)
    else:#Reset to off each time
        gpio.output(27, False)
        gpio.output(17, False)
    display.flip()
quit()
