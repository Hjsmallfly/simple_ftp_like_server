# coding=utf-8
__author__ = 'smallfly'

"""
多线程的简单FTP SERVER
功能:
    解析命令:
        1. ls 返回当前目录内容
        2. rm <文件名> 删除文件
        3. open <文件名> 打开并读取文件内容
        4. put <文件名> 接收文件到当前目录
        5. get <文件名> 传送文件到客户端
        6. cd <目录> 进入目录
"""

from ftp_client_handler import FTPClientHandler

import socket
import threading

class FTPServer:

    def __init__(self, host, port, backlog):
        """
        初始化Server
        :param host: 地址名
        :param port: 端口
        :param backlog: 最大等待数量
        :return:
        """

        self.host = host
        self.port = port
        self.backlog = backlog
        # 存储已经连接的客户端
        self.clients = []
        # socket
        # 设置成 TCP , 面向连接
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEPORT
        # https://my.oschina.net/miffa/blog/390931
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # 绑定socket
        self.sock.bind((self.host, self.port))

        # 用于停止服务
        self.__stop = False

    def listen(self):
        # 开启监听
        print("Server: start listening")
        self.sock.listen(self.backlog)

    def accept_connections(self, client_handler, new_threading=False, daemon=True):
        """
        开始监听
        :param client_handler: 处理和客户端的通信的类, 需要有recv方法
        :param new_threading: 是否在新进程中运行
        :param daemon: 是否是后台线程
        :return:
        """
        print("Server: start accepting connections")
        if not callable(client_handler):
            raise TypeError("client_handler must be callable")
        while not self.__stop:
            handler = client_handler()
            # 接收请求
            client, address = self.sock.accept()
            print("new client:", address)
            # 添加client到list中
            self.clients.append(client)
            # 设置超时时间
            # client.settimeout(60 * 10)
            # 是否开启新的线程
            if not new_threading:
                client_handler(client, address)
            else:
                # 在另外一个线程中进行服务
                threading.Thread(target=handler.recv, args=(client, address)).start()

    def stop(self):
        self.__stop = True
        for client in self.clients:
            client.close()

    def _test_handler(self, client, address):
        # 读取的字节数
        size = 1024
        while True:
            try:
                data = client.recv(size)
                if data:
                    print("client {}:".format(address), data.decode("UTF-8"))
                else:
                    print("client {}: disconnected".format(address))
                    return
            except Exception as e:
                print(e)
                client.close()
                return

if __name__ == '__main__':
    server = FTPServer("", 50000, 5)
    server.listen()
    server.accept_connections(FTPClientHandler, True)
