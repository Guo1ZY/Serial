"""
Python串口库使用示例
"""

import time
import struct
from uart_thread import UartThread__, UartThreadSpace


class CustomUartThread(UartThread__):
    def _on_mission1_received(self, X: int):
        """重写任务1接收回调"""
        print(f"自定义处理: 接收到任务1数据 X = {X}")
    def _on_serial_disconnected(self):
        print("串口断开连接，尝试重连...")

def example_basic_usage():

    
    # 创建串口对象
    uart = UartThread__(uart_length=8, send_frequency_hz=10)
    uart2 =UartThread__(uart_length=8, send_frequency_hz=10)
    try:
        #Uart2 读串口
        # uart2.init_with_threads("/dev/ttyUSB1", enable_thread_read=True, enable_thread_write=False)
        # 初始化串口（请根据实际情况修改串口名）
        if uart.init_with_threads("/dev/ttyUSB0", enable_thread_read=False, enable_thread_write=True):
            print("串口1初始化成功")
            uart2.init_with_threads("/dev/ttyUSB1", enable_thread_read=True, enable_thread_write=False)
            print("串口2初始化成功")
            X = 1
            while True:
                uart.mission_send(UartThreadSpace.mission1_assignment, X)
                time.sleep(1)
                if X<=20:
                    X += 1
                else:
                    #退出
                    uart.close()
            
        else:
            print("串口初始化失败")
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
    
    finally:
        uart.close()


if __name__ == "__main__":
    example_basic_usage()