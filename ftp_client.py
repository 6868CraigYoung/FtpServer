# python C:\PycharmProjects\begin\ftp_client\ftp_client.py -P 8889 -S 127.0.0.1
import optparse  # 解析获得的命令行参数
import socket
import json  # 传输
import os
import sys
import hashlib  # 对上传下载文件的 md5 校验

# 用数字代表一些特定字符，可以减少发送的字符，不过我只用到了几个
STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    258: "md5 verification",

    800: "the file exist,but not enough ,is continue? ",
    801: "the file exist !",
    802: " ready to receive datas",

    900: "md5 valdate success"

}


# 输入启动命令：python C:\PycharmProjects\begin\ftp_client\ftp_client.py -P 8889 -S 127.0.0.1
# 定义一个类，实例化在最下面
class ClientHandler:
    def __init__(self):  # 解析参数
        self.op = optparse.OptionParser()
        self.op.add_option('-S', '--server', dest='server')
        self.op.add_option('-P', '--port', dest='port')
        self.op.add_option('-U', '--username', dest='username')
        self.op.add_option('-p', '--password', dest='password')
        self.options, self.args = self.op.parse_args()
        # print(self.options)
        # print(self.args)
        self.verify_args()  # 检测输入是否合法
        self.make_connect()  # 建立连接
        self.mainPath = os.path.dirname(os.path.abspath(__file__))  # 获得文件的执行路径，上传下载时需要用到

    # 检测输入的是否合法，我这里只检测了端口值
    def verify_args(self):
        if int(self.options.port) > 0 and int(self.options.port) < 65535:
            return True
        else:
            exit('port is error')

    # 建立连接，传入元组形式的 ip 地址和端口值，（要先启动服务器）
    def make_connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.options.server, int(self.options.port)))
        print('connect successful')

    def get_response(self):
        data = self.s.recv(1024)
        data = json.loads(data.decode('utf-8'))
        return data

    # 通信开始，用的也是反射
    def interactive(self):
        if self.authenticate():
            print('pass')
            while True:
                cmd_info = input('[%s]' % self.current_dir).strip()
                if len(cmd_info) == 0: continue  # 如果输入为空，重新输入一遍，TCP协议不能发送空
                cmd_list = cmd_info.split()
                if hasattr(self, cmd_list[0]):
                    func = getattr(self, cmd_list[0])
                    func(*cmd_list)
                else:
                    print('please input again')

    def ls(self, *cmd_list):
        data = {
            'action': 'ls'
        }
        self.s.sendall(json.dumps(data).encode('utf-8'))  # 把 data 转成json字符串发送给服务器
        msg = self.s.recv(1024).decode('utf-8')
        if msg != 'empty':  # 用 empty 代替发送为空
            print(msg)

    def cd(self, *cmd_list):
        cmd_list = list(cmd_list)
        if len(cmd_list) == 1:  # 如果命令中只有一个 cd 时，返回最上级目录，也就是 home 下的家目录
            cmd_list.append('top')
        if len(cmd_list) != 2:  # cmd_list 的长度不等于2，就是输入出错了
            print('please input again')
            return
        data = {
            'action': 'cd',
            'dirname': cmd_list[1]
        }
        self.s.sendall(json.dumps(data).encode('utf-8'))
        msg = self.s.recv(1024).decode('utf-8')
        if msg != 'no':
            self.current_dir = msg[msg.find('libai', 10):]  #
            # libai 是我定义的账号名称，在home 下会有一个libai的文件作为家目录
            # print(self.current_dir)
        else:
            print('no this dir')

    def put(self, *cmd_list):
        print('put')
        # put 12.jpg image 命令形式
        s = hashlib.md5()  # 实例一个 md5，检查文件是否传输无误
        action, local_path, target_path = cmd_list
        local_path = os.path.join(self.mainPath, local_path)
        # 把 self.mainPath 和 image 合成一个完整目录

        file_name = os.path.basename(local_path)  # 这句好像是多余的，额
        file_size = os.stat(local_path).st_size

        data = {
            'action': 'put',
            'file_name': file_name,
            'file_size': file_size,
            'target_path': target_path
        }
        self.s.send(json.dumps(data).encode('utf-8'))

        ###############################################
        has_send = 0
        is_exit = self.s.recv(1024).decode('utf-8')

        if is_exit == '800':
            # 文件不完整
            choice = input('the file is exist, but no enough, is continue? [Y/N  ]').strip()
            if choice.upper() == 'Y':  # 是否续传
                self.s.sendall('Y'.encode('utf-8'))
                has_send = int(self.s.recv(1024).decode('utf-8'))  # 获得已经传输的文件大小
            else:
                self.s.sendall('N'.encode('utf-8'))
        elif is_exit == '801':
            # 文件存在，就直接返回了
            print('the file is exist')
            return
        # 如果文件已经传输了一部分，需要续传，重新计算md5 的值，
        print('send filename: %s, filesize: %s' % (file_name, file_size))
        f = open(local_path, 'r+b')
        has_send_b = has_send
        if has_send > 0:
            while True:
                if has_send - 1024 > 0:
                    s.update(f.read(1024))  # 更新md5
                    has_send = has_send - 1024
                else:
                    s.update(f.read(has_send))
                    break
        f.seek(has_send_b)  # 这句好像也是多余的额，
        print('has_send_b = ', has_send_b)
        while has_send_b < file_size:
            data = f.read(1024)
            s.update(data)  # 更新md5
            self.s.sendall(data)
            has_send_b += len(data)
            self.show_progress(has_send_b, file_size)  # 这是一个进度条函数
        f.close()

        self.s.sendall(str(s.hexdigest()).encode('utf-8'))  # 收发client和server的md5
        server_md5 = self.s.recv(1024).decode('utf-8')
        if server_md5 == s.hexdigest():
            print('\nMd5 checksum succeeded, Uploaded successfully')
        else:
            print('\nMd5 check failed ,upload failed')

        # time.sleep(20)

    # 下载和上传也是差不多了，我不写了
    def downloads(self, *cmd_list):
        # downloads 12.jpg
        s = hashlib.md5()
        if len(cmd_list) != 2:
            print('please input again')
            return
        data = {
            'action': 'downloads',
            'file_name': cmd_list[1],
        }

        self.s.sendall(json.dumps(data).encode('utf-8'))
        msg = self.s.recv(1024).decode('utf-8')
        print(msg)
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, cmd_list[1]).replace('\\', '/')
        has_send = 0

        if msg == 'exist this file':
            if os.path.exists(path):
                print('you want to continue transmission?')
                choice = input('[Y/N]').upper()
                if choice == 'Y':
                    has_send = os.stat(path).st_size
                    f = open(path, 'r+b')  # keep going
                else:
                    f = open(path, 'r+b')  # downloading
            else:
                f = open(path, 'wb')
        else:
            print(msg)  # bu cun zai wen jian
            return
        file_size = int(self.s.recv(1024).decode('utf-8'))
        self.s.sendall(str(has_send).encode('utf-8'))
        print('downloading')
        has_send_b = has_send
        f.seek(0)
        if has_send > 0:
            while True:
                if has_send - 1024 > 0:
                    mess = f.read(1024)
                    s.update(mess)
                    has_send = has_send - 1024
                else:
                    s.update(f.read(has_send))
                    break
        f.seek(has_send_b)
        print('has_send = ', has_send)
        while has_send_b < file_size:
            message = self.s.recv(1024)
            f.write(message)
            s.update(message)
            has_send_b += len(message)
            self.show_progress(has_send_b, file_size)
        f.close()
        self.s.sendall(str(s.hexdigest()).encode('utf-8'))
        server_md5 = self.s.recv(1024).decode('utf-8')
        if server_md5 == s.hexdigest():
            print('\nMd5 checksum succeeded, Uploaded successfully')
        else:
            print('\nMd5 check failed ,upload failed')

        # print('downloads data = ', data)
        # self.s.sendall(json.dumps(data).encode('utf-8'))
        # msg = self.s.recv(1024)
        # print(msg)

    # 创建文件夹
    def mkdir(self, *cmd_list):
        if len(cmd_list) != 2:
            print('please input again')
            return
        data = {
            'action': 'mkdir',
            'dirname': cmd_list[1]
        }
        self.s.sendall(json.dumps(data).encode('utf-8'))
        msg = self.s.recv(1024).decode('utf-8')
        print(msg)

    # 删除文件夹或文件
    def rm(self, *cmd_list):
        if len(cmd_list) != 2:
            print('please input again')
            return
        data = {
            'action': 'rm',
            'dirname': cmd_list[1]
        }
        self.s.sendall(json.dumps(data).encode('utf-8'))
        msg = self.s.recv(1024).decode('utf-8')
        print(msg)

    # 这个是进度条函数
    def show_progress(self, has_send, file_size):
        procentage = int(float(has_send) / file_size * 100)
        sys.stdout.write('%s%% %s\r' % (procentage, '*' * procentage))

    # 这个是检测你是否输入了用户名和密码，如果没有，会提示你输入的
    def authenticate(self):
        if self.options.username == None or self.options.password == None:
            username = input('username : ')
            password = input('password : ')
            return self.get_auth_result(username, password)
        return self.get_auth_result(self, self.options.username, self.options.password)

    # 校验你的用户名和密码对不对
    def get_auth_result(self, username, password):
        data = {
            'action': 'auth',
            'username': username,
            'password': password
        }
        self.s.send(json.dumps(data).encode('utf-8'))
        response = self.get_response()

        print(response)
        print('status_code : ', response['status_code'])
        if response['status_code'] == 254:
            self.username = username
            self.current_dir = username
            print(STATUS_CODE[254])
            return True
        else:
            print(STATUS_CODE[response['status_code']])


ch = ClientHandler()  # 实例化的同时，连接上服务器
ch.interactive()  # 通信开始
