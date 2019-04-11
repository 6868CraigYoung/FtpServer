import optparse
import socketserver
from optparse import OptionParser as OptionParser
# 在启动文件中已经加入了环境变量，不需要再添加了
from conf import setting
from core import server


# 启动 ftp_server 的命令：python C:\PycharmProjects\begin\ftp_server\bin\ftp_server.py start
# 运行 test 会首先运行 test 的构造方法 __init__，解析命令行参数，
# 用反射，可以十分方便的增添函数，
class test(object):
    def __init__(self):
        #self.op = OptionParser()
        #options, args = self.op.parse_args()
        #print(options)
        #print(args)
        #if hasattr(self, args[0]):  # 传入的参数是 start ，用 hasattr 检测类是否有 start 方法，有返回True
            #func = getattr(self, args[0])  # 存在 start 方法，用 getattr 获取，加括号运行
            # print(type(func))
        #func()
        pass
        

    def controllink(self):
        print('waiting for connect')  # 连接
        # 用 socketserver 内置的类实例化 s ，并传入自定义的 server 文件中的 ServerHandler 类
        s = socketserver.ThreadingTCPServer((setting.IP, setting.PORT), server.ServerHandler)
        # 启动 实例化的 s 对象
        s.serve_forever()
    def datalink(self,IP,PORT):
        s = socketserver.ThreadingTCPServer((IP, PORT), server.DataHandler)
        # 启动 实例化的 s 对象
        s.handle_request()
    
    
