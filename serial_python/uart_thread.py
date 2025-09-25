import threading
import time
import queue
import struct
from typing import List, Callable, Any
from uart import Uart, ColorPrint


class UartThread__(Uart):
    def __init__(self, uart_length=8, send_frequency_hz=300.0):
        """
        初始化多线程串口类
        :param uart_length: 每帧数据长度
        :param send_frequency_hz: 发送频率（Hz）
        
        """
        super().__init__(uart_length)
        
        # 配置参数
        self.send_frequency_hz = send_frequency_hz  
        self.enable_show_read = True
        self.enable_show_write = True
        
        # 线程相关
        self.thread_read_uart = None
        self.thread_write_uart = None
        self.thread_check_serial = None
        
        # 线程控制标志
        self.flag_thread_read_uart = False
        self.flag_thread_write_uart = False
        self.flag_thread_check_serial = False
        
        # 线程同步
        self.mutex_write_uart = threading.Lock()
        self.mutex_write_uart_queue = threading.Lock()
        self.cv_write_uart_queue = threading.Condition(self.mutex_write_uart_queue)
        self.write_buff_queue = queue.Queue()
        
        # 启动检查串口线程
        self._start_check_serial_thread()
    
    def init_with_threads(self, uart_port: str, enable_thread_read=False, 
                         enable_thread_write=False, baudrate=115200):
        """
        初始化串口并可选择开启线程
        :param uart_port: 串口端口
        :param enable_thread_read: 是否开启读串口线程
        :param enable_thread_write: 是否开启写串口线程
        :param baudrate: 波特率
        """
        # 串口初始化
        if not self.init_serial_port(uart_port, baudrate):
            return False
        
        # 开启读串口线程
        if enable_thread_read:
            self.enable_thread_read_uart()
        
        # 开启写串口线程
        if enable_thread_write:
            self.enable_thread_write_uart()
        
        return True
    
    def _thread_read_uart(self):
        """读串口线程函数"""
        while self.flag_thread_read_uart:
            try:
                # 读取串口
                read_length = self.read_buffer()
                
                if self.enable_show_read:
                    self.show_read_buff()
                    print(f"read length {read_length}")
                
                # 读取到串口后将数据送入队列
                self.push_read_buff_to_queue(read_length)
                
                # 从队列中获取正确的数据
                ret, aligned_data = self.get_aligned_from_queue()
                if ret == 1:
                    # 从队列中获取正确的数据成功
                    self._process_received_data(aligned_data)
                elif ret == -1:
                    # 从队列中获取正确的数据失败
                    ColorPrint.red("Failed to get aligned data from queue")
                    if self.enable_show_read:
                        self.show_read_buff()
                
                time.sleep(0.001)  # 短暂休眠避免CPU占用过高
                
            except Exception as e:
                print(f"Read thread error: {str(e)}")
                time.sleep(0.1)
    
    def _process_received_data(self, data: bytearray):
        """
        处理接收到的数据
        :param data: 接收到的对齐数据
        """
        if len(data) < 3:
            return
        
        if data[2] == 0x01:
            # 任务1
            if len(data) >= 7:
                X = struct.unpack('<I', data[3:7])[0]  # 小端序32位无符号整数
                if self.enable_show_read:
                    print(f"X: {X}")
                    print("Receive Mission 1:")
                    self.show_read_buff()
                
                # 可以在这里添加任务1的处理逻辑
                self._on_mission1_received(X)
        
        elif data[2] == 0x02:
            # 任务2
            if len(data) >= 8:
                X = struct.unpack('<I', data[4:8])[0]  # 小端序32位无符号整数
                if self.enable_show_read:
                    print(f"X: {X}")
                    print("Receive Mission 2:")
                    self.show_read_buff()
                
                # 可以在这里添加任务2的处理逻辑
                self._on_mission2_received(X)
    
    def _on_mission1_received(self, X: int):
        """任务1数据接收回调（可重写）"""
        pass
    
    def _on_mission2_received(self, X: int):
        """任务2数据接收回调（可重写）"""
        pass
    
    def _thread_write_uart(self):
        """写串口线程函数"""
        while self.flag_thread_write_uart:
            try:
                # 等待队列有数据
                with self.cv_write_uart_queue:
                    while self.write_buff_queue.empty() and self.flag_thread_write_uart:
                        self.cv_write_uart_queue.wait(timeout=1.0)
                    
                    if not self.flag_thread_write_uart:
                        break
                    
                    # 获取队列中的所有数据
                    local_write_buff = []
                    while not self.write_buff_queue.empty():
                        local_write_buff.append(self.write_buff_queue.get())
                
                # 频率检查
                expected_queue_size = int(self.send_frequency_hz)
                if len(local_write_buff) >= expected_queue_size * self.uart_length:
                    ColorPrint.red("Uart Send Frequency isn't Match! The Queue is Overflow!!")
                    break
                
                # 发送数据
                i = 0
                while i < len(local_write_buff):
                    write_buff = bytearray()
                    for j in range(self.uart_length):
                        if i + j < len(local_write_buff):
                            write_buff.append(local_write_buff[i + j])
                        else:
                            write_buff.append(0)
                    
                    if len(write_buff) == self.uart_length:
                        self.write_buffer(write_buff)
                        
                        if self.enable_show_write:
                            self.show_write_buff(write_buff)
                        
                        # 控制发送频率
                        sleep_time = 1.0 / self.send_frequency_hz
                        time.sleep(sleep_time)
                    
                    i += self.uart_length
                
            except Exception as e:
                print(f"Write thread error: {str(e)}")
                time.sleep(0.1)
    
    def _start_check_serial_thread(self):
        """启动串口检查线程"""
        self.flag_thread_check_serial = True
        self.thread_check_serial = threading.Thread(target=self._thread_check_serial, daemon=True)
        self.thread_check_serial.start()
    
    def _thread_check_serial(self):
        """检测串口是否在线线程"""
        while self.flag_thread_check_serial:
            try:
                if self.serial_port is None:
                    time.sleep(1)
                    continue
                
                if not self.is_serial_port_online():
                    self.disable_thread_write_uart()
                    self.disable_thread_read_uart()
                    
                    time.sleep(1)
                    ColorPrint.red("Uart Select Error!")
                    
                    # 串口断线处理
                    self._on_serial_disconnected()
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Check serial thread error: {str(e)}")
                time.sleep(1)
    
    def _on_serial_disconnected(self):
        """串口断开连接回调（可重写）"""
        pass
    
    def enable_thread_read_uart(self):
        """开启读串口线程"""
        if not self.flag_thread_read_uart:
            self.flag_thread_read_uart = True
            self.thread_read_uart = threading.Thread(target=self._thread_read_uart, daemon=True)
            self.thread_read_uart.start()
    
    def enable_thread_write_uart(self):
        """开启写串口线程"""
        if not self.flag_thread_write_uart:
            self.flag_thread_write_uart = True
            self.thread_write_uart = threading.Thread(target=self._thread_write_uart, daemon=True)
            self.thread_write_uart.start()
    
    def disable_thread_read_uart(self):
        """关闭读串口线程"""
        self.flag_thread_read_uart = False
        if self.thread_read_uart and self.thread_read_uart.is_alive():
            self.thread_read_uart.join(timeout=2.0)
    
    def disable_thread_write_uart(self):
        """关闭写串口线程"""
        self.flag_thread_write_uart = False
        with self.cv_write_uart_queue:
            self.cv_write_uart_queue.notify_all()
        if self.thread_write_uart and self.thread_write_uart.is_alive():
            self.thread_write_uart.join(timeout=2.0)
    
    def mission_send(self, assignment_func: Callable, *args, **kwargs):
        """
        任务发送串口模板函数
        :param assignment_func: 为write_buff赋值的函数
        :param args: 函数参数
        :param kwargs: 函数关键字参数
        """
        with self.mutex_write_uart:
            # 清空写串口缓冲区
            self.clear_write_buff()
            
            # 为写串口缓冲区赋值
            assignment_func(self, *args, **kwargs)
            
            if not self.flag_thread_write_uart:
                # 直接写入串口
                self.write_buffer(self.write_buff)
            else:
                # 加入写入队列
                with self.mutex_write_uart_queue:
                    for byte in self.write_buff:
                        self.write_buff_queue.put(byte)
                    self.cv_write_uart_queue.notify()
            
            if self.enable_show_write:
                print("Mission Send:", end=" ")
                self.show_write_buff(self.write_buff)
    
    def mission_send_vofa_just_float(self, data: List[float]):
        """
        发送兼容Vofa JustFloat协议的串口数据
        :param data: 待发送的浮点数数据
        """
        # 转换Vofa JustFloat协议
        buffer = bytearray()
        for value in data:
            buffer.extend(struct.pack('<f', value))  # 小端序浮点数
        
        # 添加协议尾部标识
        buffer.extend([0x00, 0x00, 0x80, 0x7f])
        
        if self.enable_show_write:
            print("Mission Vofa Send:", end=" ")
            for byte in buffer:
                print(f"{byte:02x}", end=" ")
            print()
        
        # 写入串口时上锁保护
        with self.mutex_write_uart:
            self.write_vofa_just_float(data)
    
    def close(self):
        """关闭串口和所有线程"""
        # 停止所有线程
        self.flag_thread_check_serial = False
        self.disable_thread_write_uart()
        self.disable_thread_read_uart()
        
        # 等待线程结束
        if self.thread_check_serial and self.thread_check_serial.is_alive():
            self.thread_check_serial.join(timeout=2.0)
        
        # 关闭串口
        super().close()


# 预定义的赋值函数
class UartThreadSpace:
    """存放一些任务发送串口线程要用到的函数"""
    
    @staticmethod
    def mission1_assignment(uart_ptr: UartThread__, X: int):
        """
        任务1赋值串口函数
        :param uart_ptr: 赋值的串口对象
        :param X: 任务1执行完毕后的数据
        """
        print("Mission1 Send!")
        
        # 为写串口缓冲区赋值
        uart_ptr.write_buff[2] = 0x01
        struct.pack_into('<I', uart_ptr.write_buff, 3, X)  # 小端序32位无符号整数
    
    @staticmethod
    def mission2_assignment(uart_ptr: UartThread__, X: int, Y: float):
        """
        任务2赋值串口函数
        :param uart_ptr: 赋值的串口对象
        :param X: 任务2执行完毕后的数据
        :param Y: 任务2执行完毕后的数据
        """
        print("Mission2 Send!")
        
        # 为写串口缓冲区赋值
        uart_ptr.write_buff[2] = 0x02
        struct.pack_into('<H', uart_ptr.write_buff, 3, X)  # 小端序16位无符号整数
        struct.pack_into('<f', uart_ptr.write_buff, 5, Y)  # 小端序浮点数
    