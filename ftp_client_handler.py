# coding=utf-8
__author__ = 'smallfly'

"""
处理和 ftp client 的数据交互
"""

import os
import ctypes

class FTPClientHandler:

    # 数据的第一个字节记录类型
    TYPE_SIZE = 1

    # 数据的第2-5字节记录数据大小
    CONTENT_SIZE = 4

    # 命令类型
    TYPE_COMMAND = 1

    # 文件类型
    TYPE_FILE = 2

    COMMAND_LIST = ("ls", "rm", "open", "put", "get", "cd")

    def __init__(self):
        # 已经接收到的数据
        # self.received_size = 0
        # self.received_bytes = b''
        pass

    @staticmethod
    def make_response(message):
        message = bytes(message, encoding="UTF-8")
        data_size = bytes(ctypes.c_int32(len(message)))
        return data_size + message

    def handle(self, client, type_, data):
        if type_ == FTPClientHandler.TYPE_COMMAND:
            data = data.decode("UTF-8")
            cmd = data.split(" ")[0][FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE: ]
            print("command:", cmd)
            if not cmd in FTPClientHandler.COMMAND_LIST:
                reply = FTPClientHandler.make_response("command {} not found!".format(cmd))
                client.send(reply)
                return
            if cmd == 'ls':
                return_value = os.popen(cmd).read()
                client.send(bytes(return_value, encoding="UTF-8"))
        elif type_ == FTPClientHandler.TYPE_FILE:
            pass
        print("sent reply")
        return

    def recv(self, client, address):
        # 每次读取的数据大小
        size = 1024
        # 数据类型
        data_type = -1
        # 数据大小
        content_size = -1

        received_size = 0

        received_bytes = b''

        while True:
            try:
                if received_size < FTPClientHandler.TYPE_SIZE:
                    # 需要读取数据类型
                    data = client.recv(FTPClientHandler.TYPE_SIZE - received_size)
                    if data:
                        received_bytes += data
                        received_size += len(data)
                    else:
                        print("client: {} disconnected".format(address))
                        client.close()
                        return
                elif data_type == -1 and received_size == FTPClientHandler.TYPE_SIZE:
                    # 记录数据类型
                    data_type = int.from_bytes(received_bytes[: FTPClientHandler.TYPE_SIZE], byteorder="little")
                    # print("data type:", data_type)
                elif received_size < (FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE):
                    # 读取数据大小
                    data = client.recv(FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE - received_size)
                    if data:
                        received_bytes += data
                        received_size += len(data)
                    else:
                        print("client: {} disconnected".format(address))
                        client.close()
                        return
                elif content_size == -1 and received_size == FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE:
                    content_size = int.from_bytes(received_bytes[1: FTPClientHandler.CONTENT_SIZE], byteorder="little")
                    # print("content size:", content_size)
                elif received_size < FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE + content_size:
                    # 还没有接收完数据
                    data = client.recv(size)
                    if data:
                        received_bytes += data
                        received_size += len(data)
                    else:
                        print("client: {} disconnected".format(address))
                        client.close()
                        return
                elif received_size == FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE + content_size:
                    print("received all content")
                    self.handle(client, data_type, received_bytes)
                    # 清空数据
                    received_bytes = b''
                    received_size = 0
                    data_type = -1
                    content_size = -1

            except Exception as e:
                print(e)
                client.close()
                return

    def send_data(self):
        pass