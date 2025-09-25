#ifndef __UART_THREAD_HPP
#define __UART_THREAD_HPP

#include "Uart.hpp"

#include <thread>             /*多线程*/
#include <mutex>              /*互斥锁*/
#include <condition_variable> /*条件变量*/
#include <vector>             /*容器*/
#include <queue>              /*队列*/

class Uart_Thread : public Uart
{
private:
/*是否显示原始读串口帧数据*/
#define enable_show_read true
/*是否显示原始写串口帧数据*/
#define enable_show_write true

    /*发送频率，单位：Hz*/
    const float send_frequency_hz = 300.0f;

public:
    /**
     * @brief Construct a new Uart_Thread object
     *
     */
    Uart_Thread();
    /**
     * @brief Construct a new Uart_Thread object
     *
     * @param uart_port 串口端口
     * @param enable_thread_read 是否开启读串口线程，默认不开启
     * @param enable_thread_write 是否开启写串口线程，默认不开启
     */
    Uart_Thread(std::string uart_port, bool enable_thread_read = false, bool enable_thread_write = false);

    /**
     * @brief Destroy the Uart_Thread object
     *
     */
    ~Uart_Thread(){};

    /**
     * @brief 开启读串口线程
     */
    void Enable_Thread_Read_Uart();

    /**
     * @brief 开启写串口线程
     */
    void Enable_Thread_Write_Uart();

    /**
     * @brief 关闭读串口线程
     */
    void Disable_Thread_Read_Uart();

    /**
     * @brief 关闭写串口线程
     */
    void Disable_Thread_Write_Uart();

    /**
     * @brief 任务发送串口模板函数
     * @note 模板函数不能在.h或.hpp中定义，再在.cpp中实现
     *
     * @tparam Args 函数指针的参数
     * @param Assignment_Func 为writeBuff赋值的函数指针
     * @param args Assignment_Func的参数
     */
    template <typename... Args>
    void Mission_Send(void (*Assignment_Func)(Uart_Thread *, Args...), Args... args)
    {
        /*给写入串口进行上锁保护*/
        std::lock_guard<std::mutex> res_lock_write_uart(mutex_write_uart);

        /*清空写串口缓冲区*/
        ClearWriteBuff();

        /*为写串口缓冲区赋值*/
        Assignment_Func(this, args...);

        if (flag_thread_write_uart == false)
        {
            /*写入串口*/
            WriteBuffer(writeBuff);
        }
        else
        {
            /*给写入串口队列进行上锁保护*/
            std::lock_guard<std::mutex> res_lock_write_uart_queue(mutex_write_uart_queue);

            for (size_t i = 0; i < uart_length; i++)
                writeBuff_queue.push(writeBuff[i]);

            /*唤醒写串口线程*/
            cv_write_uart_queue.notify_one();
        }

#if enable_show_write
        printf("Mission Send:");
        ShowWriteBuff(writeBuff);
#endif
    }

    /**
     * @brief 发送兼容Vofa JustFloat协议的串口数据
     *
     * @param data 待发送的浮点数数据
     */
    void Mission_Send_Vofa_JustFloat(std::vector<float> data);

private:
    /*读串口线程*/
    std::thread thread_read_uart;
    /*写串口线程*/
    std::thread thread_write_uart;
    /*检查串口线程*/
    std::thread thread_check_serial;

    /*写串口线程锁*/
    std::mutex mutex_write_uart;
    /*写串口队列所*/
    std::mutex mutex_write_uart_queue;
    /*写串口条件变量*/
    std::condition_variable cv_write_uart_queue;
    /*写串口队列*/
    std::queue<uint8_t> writeBuff_queue;

    /*是否开启读串口线程*/
    volatile bool flag_thread_read_uart = false;
    /*是否开启写串口线程*/
    volatile bool flag_thread_write_uart = false;

    /**
     * @brief 读串口线程函数
     */
    void Thread_Read_Uart();

    /**
     * @brief 写串口线程函数
     */
    void Thread_Write_Uart();

    /**
     * @brief 检测串口是否在线线程
     *
     */
    void Thread_Check_Serial();
};

/**
 * @brief 存放一些任务发送串口线要用到的函数
 *
 */
namespace Uart_Thread_Space
{
    /**
     * 对于Mission_Send函数所接收到的函数指针Assignment_Func，有以下要求：
     * 1. 第一个形参必须为Uart_Thread *uart_ptr
     * 2. 后续形参不指定数量和类型
     * 具体用法可以参考以下几个函数
     */

    /**
     * @brief 任务1赋值串口模板函数
     *
     * @param uart_ptr 赋值的串口
     * @param X 任务1执行完毕后的数据
     */
    void Mission1_Assignment(Uart_Thread *uart_ptr, uint32_t X);

    /**
     * @brief 任务2赋值串口模板函数
     *
     * @param uart_ptr 赋值的串口
     * @param X 任务2执行完毕后的数据
     * @param Y 任务2执行完毕后的数据
     */
    void Mission2_Assignment(Uart_Thread *uart_ptr, uint16_t X, float Y);
    /**
     * @brief 雷达位姿发送
     * 
     * @param uart_ptr 
     * @param X 
     * @param Y 
     * @param Z 
     */
    void Position_Infos(Uart_Thread *uart_ptr, uint8_t pos1, uint8_t pos2, uint8_t pos3, uint8_t pos4, uint8_t pos5, uint8_t pos6);

    void Number_Infos(Uart_Thread *uart_ptr, uint8_t num1, uint8_t num2, uint8_t num3, uint8_t num4, uint8_t num5, uint8_t num6);
};

#endif
