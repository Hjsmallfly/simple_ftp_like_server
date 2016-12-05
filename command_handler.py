# coding=utf-8
__author__ = 'smallfly'

import ctypes
import subprocess
import shlex
import os

ROOT_DIRNAME = "ftp"
ROOT_PATH = os.path.dirname( os.path.realpath(__file__) ) + "/" + ROOT_DIRNAME + "/"

class FTPCommandHandler:

    def __init__(self, callback_table):
        """
        初始化FTPCommandHandler
        :param callback_table: 回调函数表
        :return:
        """
        self.callback_table = callback_table

    def handle(self, client, address, command):
        print("Command:", command)
        # 解析args
        args = shlex.split(command)
        if len(args) == 0:
            reply = FTPCommandHandler.make_response(1, "invalid command")
            self.send_data(client, address, reply)
            return

        # 命令名
        cmd = args[0]

        if not cmd in self.callback_table:
            reply = FTPCommandHandler.make_response(1, "Command '{}' doesn't exist.".format(cmd))
        else:
            code, stdout, stderr = self.callback_table[cmd](args)
            if code != 0:
                reply = FTPCommandHandler.make_response(code, stderr)
            else:
                reply = FTPCommandHandler.make_response(code, stdout)

        self.send_data(client, address, reply)


    def send_data(self, client, address, data):
        size_sent = 0
        size_to_send = len(data)
        while size_sent < size_to_send:
            # 数据还没有发送完毕的时候
            # 发送剩余部分的数据
            try:
                num = client.send(data[size_sent:])
            except Exception as e:
                print(e)
                return
            if num > 0:
                size_sent += num
            else:
                print("client {} disconnected.".format(address))
                return

    @staticmethod
    def make_response(status_code, message):
        if not isinstance(message, bytes):
            message = bytes(message, encoding="UTF-8")
        data_size = bytes(ctypes.c_int32(len(message)))
        return bytes(ctypes.c_int8(status_code)) + data_size + message

def system_call(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return p.returncode, out, err

def restrain_dir(args):
    """
    限制绝对路径和相对路径到程序指定的位置
    :param args:
    :return:
    """
    if len(args) > 1:
        abs_paths = []
        rel_paths = []
        opts = []
        for arg in args[1:]:
            if arg.startswith("-"):
                opts.append(arg)
            elif arg.startswith("/"):
                # 用限定过的根目录替换根
                arg = arg.replace("/", ROOT_PATH, 1)
                abs_paths.append(arg)
            else:
                rel_paths.append(ROOT_PATH + arg)

        args = [ args[0] ] + abs_paths + rel_paths + opts

        if len(abs_paths) == 0 and len(rel_paths) == 0:
            args.insert(1, ROOT_PATH)
        print("altered:", args)


    return args

def ls_callback(args):
    if len(args) == 0:
        args = [args[0], ROOT_PATH]
    else:
        args = restrain_dir(args)

    return system_call(args)

def open_callback(args):
    if len(args) > 2:
        return 1, b'', b"can't open multiple files at the same time"
    elif len(args) < 2:
        return 2, b'', b"please specify a single file name."
    args = restrain_dir(args)
    args[0] = "cat"
    return system_call(args)