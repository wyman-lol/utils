# -*- coding: utf-8 -*-
"""
# FileName: ssh.py
# Desc    :
# Author  : Wyman
# Data    : 2020/2/6
"""
from typing import Tuple

import paramiko
import logging


class SSH(object):
    """
    通过paramiko远程操作，其实本质也分为两种：1、只用SSHClient 2、自己创建一个transport
    这里通过 transport 创建远程连接来执行 command 和 sftp 传送文件
    """

    def __init__(self, host: str, port: int, user: str, password: str, logger: logging.Logger = None) -> None:
        """
        初始化
        :param host: ssh 连接的主机地址
        :param port: ssh 连接的端口
        :param user: ssh 登录的用户
        :param password: ssh 对应的密码
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        self.transport: paramiko.Transport = self.connect()
        self.client: paramiko.SSHClient = self.get_client()

        self.logger: logging.Logger = self.get_logger(logger)

    def __enter__(self):
        """上下文管理器入口，返回值将赋给 as target，没有返回值不能用 as target"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理出口，返回True时候不会把异常向上层抛出，需要在__exit__自行处理异常，返回 False 或 None 时异常会向上层抛出"""
        del self

    def __del__(self):
        try:
            self.transport.close()
        except Exception as e:
            self.logger.debug(e)

    def connect(self) -> paramiko.Transport:
        """
        创建一个 transport
        :return: transport 对象
        """
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.user, password=self.password)
        return transport

    def get_client(self) -> paramiko.SSHClient:
        """
        获取一个ssh连接客户端
        :return: ssh_client
        """
        ssh_client = paramiko.SSHClient()
        ssh_client._transport = self.transport
        return ssh_client

    def get_logger(self, logger: logging.Logger) -> logging.Logger:
        if logger:
            return logger
        else:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)

            stream_handler = logging.StreamHandler()
            # stream_handler.setFormatter(fmt)
            stream_handler.setLevel(logging.DEBUG)
            logger.addHandler(stream_handler)
            return logger

    def exec_command(self, command: str, timeout=None) -> Tuple[
        paramiko.channel.ChannelStdinFile, paramiko.channel.ChannelFile, paramiko.channel.ChannelStderrFile]:
        """
        用于执行远程命令
        :param command: 需要执行的命令
        :param timeout: 等待命令超时时间
        :return: stdin, stdout, stderr
        """
        return self.client.exec_command(command, timeout=timeout)

    def exec(self, command: str, timeout=None) -> str:
        """
        封装一层打日志
        :param command:需要执行的命令
        :param timeout:等待命令超时时间
        :return: output
        """
        self.logger.info("execute command:{}".format(command))
        _, stdout, _ = self.exec_command(command, timeout)
        output = stdout.read().decode('utf-8')
        self.logger.info("execute result:{}".format(output))
        return output

    def upload(self, local_path: str, remote_path: str) -> bool:
        """
        用于上传文件到远程服务器，如果目标已经存在会覆盖
        :param local_path: 本地文件路径
        :param remote_path: 需要上传到的目标路径
        :return: True
        """
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(local_path, remote_path)
        return True

    def download(self, remote_path: str, local_path: str) -> bool:
        """
        用于下载文件到本地服务器，如果目标已经存在会覆盖
        :param remote_path: 远程服务器文件路径
        :param local_path: 下载到本地的路径
        :return:
        """
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.get(remote_path, local_path)
        return True


if __name__ == "__main__":
    # test
    with SSH("localhost", 22, "root", "123456") as s:
        s.exec("ls -al")
