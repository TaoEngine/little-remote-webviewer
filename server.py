import asyncio
import base64
import numpy as np
import win32gui
import win32con
import win32ui
import win32print
import cv2
from websockets import serve
import socket

def capture_screen():
    # 获取主屏幕的句柄
    hwin = win32gui.GetDesktopWindow()
    hDC = win32gui.GetDC(0)
    # 获取主屏幕的宽度和高度
    width = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    height = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    left = 0
    top = 0

    # 创建设备上下文对象
    hwndDC = win32gui.GetWindowDC(hwin)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    # 创建一个空白的位图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)

    # 将位图对象与设备上下文关联
    saveDC.SelectObject(saveBitMap)

    # 使用 BitBlt 函数进行截屏操作
    saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)

    # 将位图数据转换为 numpy 元组
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = np.fromstring(bmpstr, dtype='uint8')
    img.shape = (bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4)

    # 释放资源
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwin, hwndDC)

    # 返回 numpy 元组
    return img

async def capture_screenshot():
    img_np = capture_screen()
    # 将图像转换为JPEG格式并返回字节序列
    success, jpeg = cv2.imencode('.jpg', img_np)
    if not success:
        print('远程桌面解析失败！')
    return jpeg.tobytes()

async def send_screenshots(websocket, path):
    while True:
        try:
            # 获取屏幕截图，并将其转换为Base64编码的字符串
            screenshot = await capture_screenshot()
            data = base64.b64encode(screenshot).decode('utf-8')

            # 发送Base64编码的字符串到客户端
            await websocket.send(data)

        except Exception as e:
            print(f"发现错误了: {e}")
            break

async def main():
    async with serve(send_screenshots, socket.gethostbyname(socket.gethostname()), 24331):
        print("远程桌面服务已经启动啦！")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())