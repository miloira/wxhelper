# WxHelper

## 简介

WxHelper是一个基于dll注入实现的python微信机器人框架，支持多种接口、高扩展性、多线程消息处理，让你轻松应对海量消息，为你的需求实现提供便捷灵活的支持。

支持的接口
1. 设置消息回调
2. 取消消息回调
3. hook日志
4. 取消hook日志
5. 检查登录状态
6. 登录用户信息
7. 发送文本消息
8. 发送图片消息
9. 发送文件消息
10. 发送群at消息
11. 发送app消息
12. 发送拍一拍消息
13. 转发消息
14. 转发公众号消息
15. 转发公众号消息通过svrid
16. 撤回消息
17. 获取好友列表
18. 获取联系人（好友/群）昵称
19. 获取联系人头像
20. 修改联系人备注
21. 获取群详情
22. 获取群成员列表
23. 获取群成员资料
24. 获取群成员昵称
25. 删除群成员
26. 增加群成员
27. 邀请群成员
28. 修改账号在指定群的昵称
29. 置顶群消息
30. 取消置顶群消息
31. 搜索好友
32. 添加好友
33. 验证好友请求
34. 获取数据库句柄
35. 查询数据库
36. 解码图片
37. 识别图片文本内容
38. 下载消息附件
39. 获取语音消息
40. 获取朋友圈第一页
41. 获取朋友圈下一页
42. 确认收款
43. 拒绝收款
44. 获取登录二维码
45. 退出登录
  
## 微信版本下载
- [WeChatSetup3.9.2.23.exe](https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.9.2.23/WeChatSetup-3.9.2.23.exe)

## 安装

```bash
pip install wxhelper
```

## 使用示例

```python
# import os
# os.environ["WXHELPER_LOG_LEVEL"] = "INFO" # 修改日志输出级别
# os.environ["WXHELPER_LOG_FORMAT"] = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{message}</level>" # 修改日志输出格式
from wxhelper import Bot
from wxhelper import events
from wxhelper.model import Event


def on_login(bot: Bot, event: Event):
    print("登录成功之后会触发这个函数")


def on_start(bot: Bot):
    print("微信客户端打开之后会触发这个函数")


def on_stop(bot: Bot):
    print("关闭微信客户端之前会触发这个函数")


def on_before_message(bot: Bot, event: Event):
    print("消息事件处理之前")


def on_after_message(bot: Bot, event: Event):
    print("消息事件处理之后")


bot = Bot(
    # faked_version="3.9.10.19", # 解除微信低版本限制
    on_login=on_login,
    on_start=on_start,
    on_stop=on_stop,
    on_before_message=on_before_message,
    on_after_message=on_after_message
)


# 消息回调地址
# bot.set_webhook_url("http://127.0.0.1:8000")

@bot.handle(events.TEXT_MESSAGE)
def on_message(bot: Bot, event: Event):
    bot.send_text("filehelper", "Hello, World!")


bot.run()
```
QQ交流群:625920216

## 感谢项目

https://github.com/ttttupup/wxhelper
