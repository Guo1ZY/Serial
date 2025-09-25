# Python串口通信库

author:Guo1ZY

Date:2025/9/25

基于Python实现的多线程串口通信库，支持自定义协议和多种数据格式传输。

## 特性

- 多线程串口通信（独立的读写线程）
- 自定义环形队列数据缓存
- 支持自定义协议格式
- 线程安全的数据传输
- Vofa JustFloat协议支持
- 串口连接状态监控
- 可扩展的消息处理框架
- 彩色控制台输出

## 文件结构

```
├── queue_t.py           # 自定义环形队列
├── uart.py              # 串口基础类
├── uart_thread.py       # 多线程串口类
├── main.py              # 使用示例
└── README.md           # 说明文档
```

## 安装依赖

```bash
pip install pyserial
```

## 快速开始

### 基本使用

```python
from uart_thread import UartThread__, UartThreadSpace

# 创建串口对象
uart = UartThread__(uart_length=8, send_frequency_hz=10)

# 初始化串口
if uart.init_with_threads("/dev/ttyUSB0", enable_thread_write=True):
    # 发送数据
    uart.mission_send(UartThreadSpace.mission1_assignment, 12345)
    
    # 关闭串口
    uart.close()
```

### 双串口通信示例

```python
# 发送端
uart_tx = UartThread__(uart_length=8, send_frequency_hz=10)
uart_tx.init_with_threads("/dev/ttyUSB0", enable_thread_write=True)

# 接收端  
uart_rx = UartThread__(uart_length=8)
uart_rx.init_with_threads("/dev/ttyUSB1", enable_thread_read=True)

# 循环发送数据
for i in range(1, 21):
    uart_tx.mission_send(UartThreadSpace.mission1_assignment, i)
    time.sleep(1)
```

## 核心类说明

### UartThread__

主要的多线程串口类，提供以下功能：

#### 构造函数

```python
def __init__(self, uart_length=8, send_frequency_hz=300.0):
    """
    :param uart_length: 每帧数据长度
    :param send_frequency_hz: 发送频率（Hz）
    """
```

#### 主要方法

- `init_with_threads(uart_port, enable_thread_read, enable_thread_write, baudrate=115200)`
  - 初始化串口并可选择开启读写线程
- `mission_send(assignment_func, *args, **kwargs)`
  - 发送自定义格式数据
- `mission_send_vofa_just_float(data)`
  - 发送Vofa JustFloat协议数据
- `close()`
  - 关闭串口和所有线程

### UartThreadSpace

预定义的数据格式处理函数集合：

- `mission1_assignment(uart_ptr, X)` - 任务1数据格式
- `mission2_assignment(uart_ptr, X, Y)` - 任务2数据格式

## 数据帧格式

默认数据帧格式（8字节）：

```
[0] [1] [2] [3] [4] [5] [6] [7]
'?' '!' CMD  DATA DATA DATA  '!'
```

- 字节0-1：帧头 `?!`
- 字节2：命令类型
- 字节3-6：数据内容
- 字节7：帧尾 `!`

## 自定义消息格式

```python
def custom_assignment(uart_ptr: UartThread__, msg_type: int, value: int):
    """自定义消息格式"""
    uart_ptr.write_buff[2] = msg_type & 0xFF
    struct.pack_into('<I', uart_ptr.write_buff, 3, value)

# 使用自定义格式发送
uart.mission_send(custom_assignment, 0x99, 12345)
```

## 接收数据处理

通过继承UartThread__类并重写回调函数来处理接收到的数据：

```python
class MyUartThread(UartThread__):
    def _on_mission1_received(self, X: int):
        print(f"接收到任务1数据: {X}")
    
    def _on_mission2_received(self, X: int):
        print(f"接收到任务2数据: {X}")
    
    def _on_serial_disconnected(self):
        print("串口断开连接")
```

## 线程说明

该库使用三个主要线程：

1. **读线程** (`_thread_read_uart`)
   - 持续读取串口数据
   - 数据队列缓存和对齐
   - 调用相应的数据处理回调
2. **写线程** (`_thread_write_uart`)
   - 从写队列获取数据
   - 控制发送频率
   - 处理队列溢出检测
3. **监控线程** (`_thread_check_serial`)
   - 检测串口连接状态
   - 处理断线重连逻辑

## 配置选项

### 调试输出控制

```python
uart.enable_show_read = False   # 关闭读取调试信息
uart.enable_show_write = False  # 关闭写入调试信息
```

### 发送频率设置

```python
# 创建时设置
uart = UartThread__(send_frequency_hz=100)  # 100Hz发送频率
```

### 数据帧长度

```python
# 自定义帧长度
uart = UartThread__(uart_length=16)  # 16字节帧长度
```

## Vofa集成

支持Vofa JustFloat协议，用于数据可视化：

```python
# 发送浮点数数组到Vofa
float_data = [1.23, 4.56, 7.89, 10.11]
uart.mission_send_vofa_just_float(float_data)
```

## 错误处理

库提供多层错误处理：

- 串口连接错误自动重试
- 线程异常保护
- 队列溢出检测
- 数据对齐验证

## 注意事项

1. **串口权限**：确保有足够权限访问串口设备

   ```bash
   sudo chmod 666 /dev/ttyUSB0
   ```

2. **设备名称**：根据系统修改串口设备名

   - Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`
   - Windows: `COM1`, `COM2`

3. **线程安全**：所有发送操作都是线程安全的

4. **资源释放**：使用完毕后调用`close()`方法释放资源

## 示例场景

### 传感器数据采集

```python
uart = UartThread__(uart_length=8, send_frequency_hz=10)
uart.init_with_threads("/dev/ttyUSB0", enable_thread_write=True)

# 定期发送传感器查询命令
for sensor_id in range(1, 6):
    uart.mission_send(UartThreadSpace.mission1_assignment, sensor_id)
    time.sleep(0.1)
```

### 设备控制

```python
def control_command(uart_ptr, device_id, action, value):
    uart_ptr.write_buff[2] = 0x10  # 控制命令
    uart_ptr.write_buff[3] = device_id
    uart_ptr.write_buff[4] = action
    struct.pack_into('<H', uart_ptr.write_buff, 5, value)

uart.mission_send(control_command, 1, 2, 500)  # 设备1，动作2，值500
```

## 许可证

本项目基于原C++串口库移植，保持相同的功能特性和API设计理念。
