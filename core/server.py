import socketserver
import json  # 作为传输
import configparser  # 解析存储的账号密码
from conf import setting
import os
import shutil  # 删除文件夹的库
import hashlib
import socket
from . import main

STATUS_CODE = {
    250: "250 Directory successfully changed.\r\n",
    251: "250 Remove directory operation successful.\r\n",
    230: "230 Login successful.\r\n",
    550: "550 Failed to change directory.\r\n",
    551: "550 Failed to open file.\r\n",
    552: "550 Remove directory operation failed.\r\n",
    530: "530 Permission denied.\r\n",
    531: "530 Login incorrect.\r\n",
    220: "220 Welcome to blah FTP service.\r\n",
    200: "200 Always in UTF8 mode.\r\n",
    201: "200 PORT command successful. Consider using PASV.\r\n",
    331: "331 Please specify the password.\r\n",
    150: "150 Here comes the directory listing.\r\n",
    226: "226 Directory send OK.\r\n",
    151: "150 Opening BINARY mode data connection for ",
    227: "226 Transfer complete.\r\n"
}


# 定义一个继承 socketserver.BaseRequestHandler 的类，实例化时自动运行 handle 方法
class ServerHandler(socketserver.BaseRequestHandler):
    def handle(self):

        print(self.request)  # self.request 就是类同与 socket 定义服务器时返回的实例对象
        print("客户端的sockect对象")
        print(self.client_address)  
        print("客户端的地址和IP")
        print(self.server)
        print("服务器端的对象")  

        self.send_response(220) #服务端返回建立连接的响应确认

        while True:
            data = self.request.recv(1024)
            if data == b'OPTS UTF8 ON\r\n':
                break

        self.send_response(200) #确认编码方式的确认

        while True:
            username = self.request.recv(1024)
            username = username.decode().strip('\r\n').split(' ',1)
            if self.authusername(username[1]):
                self.send_response(331)
                password = self.request.recv(1024)
                password = password.decode().strip('\r\n').split(' ',1)
                self.auth(username[1], password[1])
                break
        while True:  #开始进行命令交互
            self.command0 = self.request.recv(1024) #接受字节序信息 可用监听端口 命令名 路径
            self.command = self.command0.decode().strip('\r\n') #除去尾部
            command = self.command.split(' ')  #字符切片
            if command[0] =='PORT': #需要调用20号端口的数据端口发送的
                self.send_response(201) #确认主被动方式
                data = self.request.recv(1024)
                print(data)
                print(data.decode().strip('\r\n'))
                if data.decode().strip('\r\n') == 'NLST': # ls命令的交互
                    print("ls")
                    self.NLST()
                elif data.decode().strip('\r\n').split(' ')[0] == 'RETR': #get命令
                    print(command[1])
                    filename = data.decode().strip('\r\n').split(' ')[1]
                    print(filename)
                    if not self.RETR(filename):
                        self.send_response(551)
            elif command[0] == 'CWD': # cd命令
                if self.CWD(command[1]): #cd 命令的后续路径
                    self.send_response(250) 
                else:
                    self.send_response(550)
            elif command[0] == 'XPWD': #pwd当前路径名
                self.XPWD()
            elif command[0] == 'XMKD': #mkdir创建文件夹
                self.XMKD(command[1])
            elif command[0] == 'XRMD': #删除文件和文件夹
                self.XRMD(command[1])

    def send_response(self, status_code): # 根据编号返送反馈消息
        self.request.send(STATUS_CODE[status_code].encode('utf-8'))

    def auth(self, username,password):
        username = self.authenticate(username, password)
        if username:
            self.send_response(230)  # 正常返回
        else:
            self.send_response(531)  # 用户名或密码错误返回

    def authusername(self,username):# 用于用户名和密码验证
        cfg = configparser.ConfigParser()
        cfg.read(setting.ACCOUNT_PATH)
        if username in cfg.sections():
            return 1
        else:
            print("username is wrong")
            self.send_response(530)
            return 0

    def authenticate(self, username, password):  # 验证用户名了密码，conf/accounts.cfg
        cfg = configparser.ConfigParser()
        cfg.read(setting.ACCOUNT_PATH)
        if username in cfg.sections():
            if password == cfg[username]['Password']:
                print('login successful')
                self.username = username
                self.mainPath = os.path.join(setting.BASE_DIR, 'home', self.username).replace('\\', '/')
                return username 

    def NLST(self):  # 接收到传来的数据 data
        file_list = os.listdir(self.mainPath)  # 列出在当前目录下的所有文件
        file_str = ' '.join(file_list)+'\n'  # 获得的为列表，转成字符串
        if not len(file_list):
            file_str = 'empty\n'
        dataip = self.client_address[0]
        dataport = self.command0.decode().strip('\r\n')
        dataport = dataport.replace(' ',',').split(',',6)
        dataport = int(dataport[5])*16*16+int(dataport[6])
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            s.bind((setting.IP,20))
            s.connect((dataip,dataport))
            self.send_response(150)
            s.sendall(file_str.encode('utf-8'))
            self.send_response(226)
        return

    def XPWD(self):
        result = "257 " + "\"" + self.mainPath + "\"" + " is the current directory\r\n"
        self.request.send(result.encode('utf-8'))


    def RETR(self,filename):  # 接收到传来的数据 data
        STATUS_CODE[151] = "150 Opening BINARY mode data connection for "
        abs_path = os.path.join(self.mainPath, filename).replace('\\', '/')
        if not os.path.isfile(abs_path):
            return 0
        file_size = os.stat(abs_path).st_size
        dataip = self.client_address[0]
        dataport = self.command0.decode().strip('\r\n')
        dataport = dataport.replace(' ',',').split(',',6)
        dataport = int(dataport[5])*16*16+int(dataport[6])
        file_size = os.stat(abs_path).st_size
        STATUS_CODE[151] += (filename + ' (' + str(file_size) + ' bytes).\r\n')
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            s.bind((setting.IP,20))
            s.connect((dataip,dataport))
            self.send_response(151)
            with open(abs_path, 'rb') as f:
                for line in f:
                    #print("size of line : ")
                    #print(len(line))
                    #print("type of line : "+str(type(line)))
                    s.sendall(line)
        self.send_response(227)
        return 1

    def CWD(self, dirname):
        top_directory = 'D:/workspace/FtpServer/home/root'  # 需要用的话要这里要改一下路径啊
        if dirname == 'top':  # 返回顶级目录
            self.mainPath = top_directory
            return 1
        elif dirname == '..':  # 返回上一层目录
            if self.mainPath != top_directory:
                self.mainPath = os.path.dirname(self.mainPath)
                return 1
            else:
                return 0
        elif dirname == '.':
            return 1
        else:  # else 就是进入某某目录了
            back = self.mainPath
            self.mainPath = os.path.join(self.mainPath, dirname).replace('\\', '/')
            if not os.path.isdir(self.mainPath):
                self.mainPath = back
                return 0
            else:
                return 1
    
    def XMKD(self,dirname):
        path = os.path.join(self.mainPath, dirname).replace('\\', '/')
        if not os.path.exists(path):
            if '/' in dirname:
                os.makedirs(path)
            else:
                os.mkdir(path)
            res = '257 ' + "\"" + dirname + "\"" + " create.\r\n"
            self.request.send(res.encode('utf-8'))
        else:
            res = 'create directory operation failed.\r\n'
            self.request.send(res.encode('utf-8'))

    def XRMD(self, filename):
        print('rm')
        path = os.path.join(self.mainPath, filename).replace('\\', '/')
        if not os.path.exists(path):
            print('wen jian bu cun zai')
            self.send_response(552)
        else:
            try:
                shutil.rmtree(path)  # 这个是嵌套删除文件
            except:
                os.remove(path)  # 删除单个文件
            print('delete')
            self.send_response(251)

class DataHandler(socketserver.BaseRequestHandler):
    def handle(self):
        pass