# coding=utf-8
__author__ = 'smallfly'

import socket
from ctypes import c_int32, c_int8

def send_text(sock, type_, data):
    bytes_sent = 0

    type_ = bytes(c_int8(type_))

    data = data.encode("UTF-8")

    data_size = bytes(c_int32(len(data)))

    bytes_to_send = type_ + data_size + data

    print("Type:", type_, "data size:", data_size)

    while bytes_sent < len(bytes_to_send):
        # 继续发送数据
        num = sock.send(bytes_to_send[bytes_sent: ])
        if num > 0:
            bytes_sent += num
        else:
            print("Lost connection")
            sock.close()
            return
    reply = sock.recv(1024)
    print("reply: ", reply.decode("UTF-8"))
    # print("all data sent")

if __name__ == '__main__':
    sock = socket.socket()
    sock.connect(("", 50000))
    while True:
        cmd = input("command:")
        send_text(sock, 1, cmd)
    sock.close()