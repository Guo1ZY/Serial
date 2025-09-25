import serial
import time
import struct
import os
from typing import Optional, List
from queue_t import Queue_T


class ColorPrint:
    """控制台颜色输出"""
    RED = '\033[1;31m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[1;34m'
    PURPLE = '\033[1;35m'
    CYAN = '\033[1;36m'
    WHITE = '\033[1;37m'
    END = '\033[0m'
    
    @staticmethod
    def red(text):
        print(f"{ColorPrint.RED}{text}{ColorPrint.END}")
    
    @staticmethod
    def green(text):
        print(f"{ColorPrint.GREEN}{text}{ColorPrint.END}")
    
    @staticmethod
    def blue(text):
        print(f"{ColorPrint.BLUE}{text}{ColorPrint.END}")


class Uart:
    def __init__(self, uart_length=16):
        """
        初始化串口基类
        :param uart_length: 每帧数据长度
        """
        self.uart_length = uart_length
        self.serial_port: Optional[serial.Serial] = None
        self.uart_dev = ""
        
        # 缓冲区
        self.write_buff = bytearray(uart_length)
        self.read_buff = bytearray(uart_length)
        
        # 读线程队列
        self.read_buff_queue = Queue_T()
    
    def init_serial_port(self, dev: str, baudrate: int = 115200, 
                        timeout: float = 1.0) -> bool:
        """
        串口初始化
        :param dev: 串口设备名
        :param baudrate: 波特率
        :param timeout: 超时时间
        :return: True成功，False失败
        """
        ColorPrint.blue("SerialPort Connecting ..")
        
        self.uart_dev = dev
        
        try:
            self.serial_port = serial.Serial(
                port=dev,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            if self.serial_port.is_open:
                ColorPrint.green(f"Open Port {dev} Success!")
                return True
            else:
                ColorPrint.red(f"Error!! Open Port {dev} Failed!")
                return False
                
        except Exception as e:
            ColorPrint.red(f"Error!! Open Port {dev} Failed! {str(e)}")
            return False
    
    def is_serial_port_online(self) -> bool:
        """
        检测串口是否在线
        :return: True在线，False离线
        """
        if self.serial_port is None:
            return False
        
        return self.serial_port.is_open and os.path.exists(self.uart_dev)
    
    def read_buffer(self) -> int:
        """
        读串口
        :return: 读取的字节数
        """
        if self.serial_port is None or not self.serial_port.is_open:
            return 0
        
        try:
            data = self.serial_port.read(self.uart_length)
            self.read_buff = bytearray(data)
            # 如果读取长度不足，用0填充
            while len(self.read_buff) < self.uart_length:
                self.read_buff.append(0)
            return len(data)
        except Exception as e:
            print(f"Read buffer error: {str(e)}")
            return 0
    
    def write_buffer(self, write_buff: bytearray) -> int:
        """
        写串口
        :param write_buff: 写入的数据
        :return: 写入的字节数
        """
        if self.serial_port is None or not self.serial_port.is_open:
            return 0
        
        try:
            return self.serial_port.write(write_buff)
        except Exception as e:
            print(f"Write buffer error: {str(e)}")
            return 0
    
    def write_vofa_just_float(self, data: List[float]) -> int:
        """
        发送兼容Vofa JustFloat协议的串口数据
        :param data: 待发送的浮点数数据
        :return: 写入的字节数，-1表示失败
        """
        if not data:
            return -1
        
        # 转换Vofa JustFloat协议
        buffer = bytearray()
        for value in data:
            buffer.extend(struct.pack('<f', value))  # 小端序浮点数
        
        # 添加协议尾部标识
        buffer.extend([0x00, 0x00, 0x80, 0x7f])
        
        return self.write_buffer(buffer)
    
    def show_read_buff(self):
        """打印读到的串口数据"""
        print("readBuff: ", end="")
        for byte in self.read_buff:
            print(f"{byte:02x} ", end="")
        print()
    
    def show_write_buff(self, write_buff: bytearray):
        """打印写的串口数据"""
        print("writeBuff: ", end="")
        for byte in write_buff:
            print(f"{byte:02x} ", end="")
        print()
    
    def clear_write_buff(self):
        """清空writeBuff并加上头尾帧"""
        # 清空
        self.write_buff = bytearray(self.uart_length)
        
        # 头帧
        self.write_buff[0] = ord('?')
        self.write_buff[1] = ord('!')
        
        # 尾帧
        self.write_buff[self.uart_length - 1] = ord('!')
    
    def push_read_buff_to_queue(self, read_length: int = 0):
        """
        将收到的串口帧加入队列
        :param read_length: 读到的串口数据长度，默认为0则把所有readBuff加入队列
        """
        if read_length == 0:
            for i in range(self.uart_length):
                self.read_buff_queue.push(self.read_buff[i])
        else:
            for i in range(read_length):
                self.read_buff_queue.push(self.read_buff[i])
    
    def get_aligned_from_queue(self) -> tuple:
        """
        从队列中提取对齐好的数据
        :return: (状态码, 数据数组) 
                状态码: 0表示队列长度不足，-1表示提取失败，1表示提取成功
        """
        if self.uart_length > self.read_buff_queue.size():
            return 0, None
        
        # 判断队列长度与数据帧长度
        while self.uart_length <= self.read_buff_queue.size():
            if (self.read_buff_queue[0] == ord('?') and
                self.read_buff_queue[1] == ord('!') and
                self.read_buff_queue[self.uart_length - 1] == ord('!')):
                
                # 队列中存在合法数据，赋值并返回
                data = bytearray()
                for i in range(self.uart_length):
                    data.append(self.read_buff_queue.pop())
                
                return 1, data
            else:
                # 队首的数据不合法，出队
                self.read_buff_queue.pop()
        
        return -1, None
    
    def close(self):
        """关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            ColorPrint.green(f"Serial port {self.uart_dev} closed.")