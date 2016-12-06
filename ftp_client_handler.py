# coding=utf-8
__author__ = 'smallfly'

"""
处理和 ftp client 的数据交互
功能:
    解析命令:
        1. ls 返回当前目录内容
        2. rm <文件名> 删除文件
        3. open <文件名> 打开并读取文件内容
        4. put <文件名> 接收文件到当前目录
        5. get <文件名> 传送文件到客户端
        6. cd <目录> 进入目录
"""

from response_helper import make_response, send_data

class FTPClientHandler:

    # 数据的第一个字节记录类型
    TYPE_SIZE = 1

    # 数据的第2-5字节记录数据大小
    CONTENT_SIZE = 4

    # 命令类型
    TYPE_COMMAND = 1

    # 文件类型
    TYPE_FILE = 2

    # 命令运行成功
    CODE_OKAY = 0

    # 每次读取的字节数
    RECV_SIZE = 1024

    def __init__(self, command_handler, file_handler):

        self.command_handler = command_handler
        self.file_handler = file_handler

        # 数据类型
        self.data_type = -1
        # 数据大小
        self.content_size = -1
        # 记录已经读取了的字节数
        self.received_size = 0
        # 记录已经读取了的字节
        self.received_bytes = b''

        # 记录文件名
        self.filename = ""

    def handle(self, client, address, type_, data):

        data = data[FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE: ]

        if type_ == FTPClientHandler.TYPE_COMMAND:
            # 返回解析过后的命令
            args = self.command_handler.handle(client, address, data.decode("UTF-8"))
            # 如果是上传任务的话
            if len(args) == 2 and args[0] == "put":
                self.filename = args[1]
                print("The file to be uploaded:", self.filename)
        elif type_ == FTPClientHandler.TYPE_FILE:
            print("The file to be uploaded:", self.filename)
            self.file_handler.handle(client, address, self.filename, data)
        else:
            print("unknown type:", type_)
            send_data(client, address, make_response(1, "unknown type:" + str(type_)))
        return

    def reset(self):
        # 数据类型
        self.data_type = -1
        # 数据大小
        self.content_size = -1
        # 记录已经读取了的字节数
        self.received_size = 0
        # 记录已经读取了的字节
        self.received_bytes = b''

    def recv(self, client, address):
        """
        读取客户端的数据, 并处理读取到的数据
        :param client:
        :param address:
        :return:
        """

        while True:
            # 还未读到类型字节
            if self.received_size < FTPClientHandler.TYPE_SIZE:
                status = self.__recv(client, address, FTPClientHandler.TYPE_SIZE - self.received_size)
                if not status:
                    return
            elif self.data_type == -1 and self.received_size == FTPClientHandler.TYPE_SIZE:
                # 记录数据类型
                self.data_type = int.from_bytes(self.received_bytes[: FTPClientHandler.TYPE_SIZE], byteorder="little")

            elif self.received_size < (FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE):
                # 读取数据大小
                status = self.__recv(client, address, FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE - self.received_size)
                if not status:
                    return

            elif self.content_size == -1 and self.received_size == FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE:
                self.content_size = int.from_bytes(self.received_bytes[1: FTPClientHandler.CONTENT_SIZE], byteorder="little")

            elif self.received_size < FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE + self.content_size:
                # 还没有接收完数据
                status = self.__recv(client, address, FTPClientHandler.RECV_SIZE)
                if not status:
                    return
            elif self.received_size == FTPClientHandler.TYPE_SIZE + FTPClientHandler.CONTENT_SIZE + self.content_size:
                # print("received all content")
                print("------------------------handling---------------------")
                self.handle(client, address, self.data_type, self.received_bytes)
                print("------------------------handled---------------------")
                # 清空数据
                self.reset()

    def __recv(self, client, address, size):
        """
        从socket中读取数据
        读到新数据返回 True
        连接断开返回 False
        出现错误返回 None
        :param client: 与客户端连接的socket
        :param address: 地址
        :param size: 读取多少字节
        :return:
        """
        try:
            data = client.recv(size)
            if data:
                self.received_bytes += data
                self.received_size += len(data)
                return True
            else:
                print("client: {} disconnected".format(address))
                client.close()
                return False
        except Exception as e:
            print(repr(e))
            return None
