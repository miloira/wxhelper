import os
import json
import typing
import traceback
import socketserver
from functools import lru_cache

import psutil
import pyee
import requests

from .logger import logger
from .events import ALL_MESSAGE
from .model import Event, Account, Contact, Room, RoomMembers, Table, DB, Response, UserInfo, \
    CheckLoginResponse, RoomMemberNicknameResponse, ExecSQLResponse, OCRResponse, NicknameResponse, \
    QRCodeUrlResponse, RoomMember
from .utils import WeChatManager, start_wechat_with_inject, fake_wechat_version, get_pid, parse_event


class RequestHandler(socketserver.BaseRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self):
        try:
            data = b""
            while True:
                chunk = self.request.recv(1024)
                data += chunk
                if len(chunk) == 0 or chunk[-1] == 0xA:
                    break

            bot = getattr(self.server, "bot")
            bot.on_event(data)
            self.request.sendall("200 OK".encode())
        except Exception:
            logger.error(traceback.format_exc())
        finally:
            self.request.close()


class Bot:

    def __init__(
        self,
        on_login: typing.Optional[typing.Callable[["Bot", Event], typing.Any]] = None,
        on_before_message: typing.Optional[typing.Callable[["Bot", Event], typing.Any]] = None,
        on_after_message: typing.Optional[typing.Callable[["Bot", Event], typing.Any]] = None,
        on_start: typing.Optional[typing.Callable[["Bot"], typing.Any]] = None,
        on_stop: typing.Optional[typing.Callable[["Bot"], typing.Any]] = None,
        faked_version: typing.Optional[str] = None
    ):
        self.version = "3.9.2.23"
        self.server_host = "127.0.0.1"
        self.remote_host = "127.0.0.1"
        self.on_start = on_start
        self.on_login = on_login
        self.on_before_message = on_before_message
        self.on_after_message = on_after_message
        self.on_stop = on_stop
        self.faked_version = faked_version
        self.event_emitter = pyee.EventEmitter()
        self.wechat_manager = WeChatManager()
        self.remote_port, self.server_port = self.wechat_manager.get_port()
        self.BASE_URL = f"http://{self.remote_host}:{self.remote_port}/api/"
        self.webhook_url = None
        self.DATA_SAVE_PATH = None
        self.WXHELPER_PATH = None
        self.FILE_SAVE_PATH = None
        self.IMAGE_SAVE_PATH = None
        self.VIDEO_SAVE_PATH = None

        try:
            code, output = start_wechat_with_inject(self.remote_port)
        except Exception:
            code, output = get_pid(self.remote_port)

        if code == 1:
            raise Exception(output)

        self.process = psutil.Process(int(output))

        if self.faked_version is not None:
            if fake_wechat_version(self.process.pid, self.version, faked_version) == 0:
                logger.success(f"wechat version faked: {self.version} -> {faked_version}")
            else:
                logger.error(f"wechat version fake failed.")

        logger.info(f"API Server at 0.0.0.0:{self.remote_port}")
        self.wechat_manager.add(self.process.pid, self.remote_port, self.server_port)
        self.call_hook_func(self.on_start, self)
        self.handle(ALL_MESSAGE, once=True)(self.init_bot)
        self.hook_sync_msg(self.server_host, self.server_port)

    @staticmethod
    def call_hook_func(func: typing.Callable, *args, **kwargs) -> typing.Any:
        if callable(func):
            return func(*args, **kwargs)

    def init_bot(self, bot: "Bot", event: Event) -> None:
        self.DATA_SAVE_PATH = bot.info.dataSavePath
        self.WXHELPER_PATH = os.path.join(self.DATA_SAVE_PATH, "wxhelper")
        self.FILE_SAVE_PATH = os.path.join(self.WXHELPER_PATH, "file")
        self.IMAGE_SAVE_PATH = os.path.join(self.WXHELPER_PATH, "image")
        self.VIDEO_SAVE_PATH = os.path.join(self.WXHELPER_PATH, "video")
        self.call_hook_func(self.on_login, bot, event)
        logger.info(f"login success, {bot.info}")

    def set_webhook_url(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def webhook(self, event: dict) -> None:
        if self.webhook_url is not None:
            try:
                requests.post(self.webhook_url, json=event)
            except Exception:
                pass

    def call_api(self, **kwargs) -> dict:
        return requests.request("POST", self.BASE_URL, **kwargs).json()

    def hook_sync_msg(
        self,
        host: str = "127.0.0.1",
        port: int = 19099,
        enable_http: int = 0,
        callback_url: str = "http://127.0.0.1:8000",
        timeout: str = 30
    ) -> Response:
        """设置消息回调"""
        params = {
            "type": "9"
        }
        data = {
            "port": port,
            "ip": host,
            "enableHttp": enable_http,
        }
        if enable_http == 1:
            data.update({
                "url": callback_url,
                "timeout": timeout
            })
        return Response(**self.call_api(params=params, json=data))

    def unhook_sync_msg(self) -> Response:
        """取消消息回调"""
        params = {
            "type": "10"
        }
        return Response(**self.call_api(params=params))

    def hook_log(self) -> Response:
        """hook日志"""
        params = {
            "type": "35"
        }
        return Response(**self.call_api(params=params))

    def unhook_log(self) -> Response:
        """取消hook日志"""
        params = {
            "type": "36"
        }
        return Response(**self.call_api(params=params))

    def check_login(self) -> CheckLoginResponse:
        """检查登录状态"""
        params = {
            "type": "0"
        }
        return CheckLoginResponse(**self.call_api(params=params))

    @lru_cache
    def get_self_info(self) -> Account:
        """登录用户信息"""
        params = {
            "type": "1"
        }
        return Account(**self.call_api(params=params)["data"])

    def send_text(self, wxid: str, msg: str) -> Response:
        """发送文本消息"""
        params = {
            "type": "2"
        }
        data = {
            "wxid": wxid,
            "msg": msg
        }
        return Response(**self.call_api(params=params, json=data))

    def send_image(self, wxid: str, image_path: str) -> Response:
        """发送图片消息"""
        params = {
            "type": "5"
        }
        data = {
            "wxid": wxid,
            "imagePath": os.path.abspath(image_path)
        }
        return Response(**self.call_api(params=params, json=data))

    def send_file(self, wxid: str, file_path: str) -> Response:
        """发送文件消息"""
        params = {
            "type": "6"
        }
        data = {
            "wxid": wxid,
            "filePath": os.path.abspath(file_path)
        }
        return Response(**self.call_api(params=params, json=data))

    def send_room_at(self, room_id: str, wxids: list[str], msg: str) -> Response:
        """发送群at消息"""
        params = {
            "type": "3"
        }
        data = {
            "chatRoomId": room_id,
            "wxids": ",".join(wxids),
            "msg": msg
        }
        return Response(**self.call_api(params=params, json=data))

    def send_app(self, wxid: str, applet_id: str) -> Response:
        """发送app消息"""
        params = {
            "type": "64"
        }
        data = {
            "wxid": wxid,
            "appletId": applet_id
        }
        return Response(**self.call_api(params=params, json=data))

    def send_pat(self, room_id: str, wxid: str) -> Response:
        """发送拍一拍消息"""
        params = {
            "type": "50"
        }
        data = {
            "chatRoomId": room_id,
            "wxid": wxid
        }
        return Response(**self.call_api(params=params, json=data))

    def forward(self, wxid: str, msg_id: str) -> Response:
        """转发消息"""
        params = {
            "type": "36"
        }
        data = {
            "wxid": wxid,
            "msgid": msg_id
        }
        return Response(**self.call_api(params=params, json=data))

    def forward_public_msg(
        self,
        wxid: str,
        appname: str,
        username: str,
        title: str,
        url: str,
        thumb_url: str,
        digest: str
    ) -> Response:
        """转发公众号消息"""
        params = {
            "type": "62"
        }
        data = {
            "wxid": wxid,
            "appname": appname,
            "username": username,
            "title": title,
            "url": url,
            "thumburl": thumb_url,
            "digest": digest,

        }
        return Response(**self.call_api(params=params, json=data))

    def forward_public_msg_by_svrid(self, wxid: str, msg_id: int) -> Response:
        """转发公众号消息通过svrid"""
        params = {
            "type": "63"
        }
        data = {
            "wxid": wxid,
            "msgId": msg_id
        }
        return Response(**self.call_api(params=params, json=data))

    def revoke_msg(self, msg_id: str) -> Response:
        """撤回消息"""
        params = {
            "type": "61"
        }
        data = {
            "msgId": msg_id
        }
        return Response(**self.call_api(params=params, json=data))

    def get_contacts(self) -> typing.List[Contact]:
        """获取好友列表"""
        params = {
            "type": "46"
        }
        return [Contact(**item) for item in self.call_api(params=params)["data"]]

    def get_contact_nickname(self, wxid: str) -> NicknameResponse:
        """获取联系人（好友/群）昵称"""
        params = {
            "type": "55"
        }
        data = {
            "id": wxid
        }
        return NicknameResponse(**self.call_api(params=params, json=data))

    def get_head_image(self, wxid: str, image_url: str) -> Response:
        """获取联系人头像"""
        params = {
            "type": "66"
        }
        data = {
            "wxid": wxid,
            "imageUrl": image_url
        }
        return Response(**self.call_api(params=params, json=data))

    def modify_contact_remark(self, wxid: str, remark: str) -> Response:
        """修改联系人备注"""
        params = {
            "type": "67"
        }
        data = {
            "wxid": wxid,
            "remark": remark
        }
        return Response(**self.call_api(params=params, json=data))

    def get_room(self, room_id: str) -> Room:
        """获取群详情"""
        params = {
            "type": "47"
        }
        data = {
            "chatRoomId": room_id
        }
        return Room(**self.call_api(params=params, json=data))

    def get_room_members(self, room_id: str) -> RoomMembers:
        """获取群成员列表"""
        params = {
            "type": "25"
        }
        data = {
            "chatRoomId": room_id
        }
        return RoomMembers(**self.call_api(params=params, json=data)["data"])

    def get_room_member(self, wxid: str) -> RoomMember:
        """获取群成员资料"""
        params = {
            "type": "60"
        }
        data = {
            "wxid": wxid
        }
        response = self.call_api(params=params, json=data)
        response.pop("code")
        response.pop("result")
        return RoomMember(**response)

    def get_room_member_nickname(self, room_id: str, member_id: str) -> RoomMemberNicknameResponse:
        """获取群成员昵称"""
        params = {
            "type": "26"
        }
        data = {
            "chatRoomId": room_id,
            "memberId": member_id
        }
        return RoomMemberNicknameResponse(**self.call_api(params=params, json=data))

    def delete_room_members(self, room_id: str, member_ids: typing.List[str]) -> Response:
        """删除群成员"""
        params = {
            "type": "27"
        }
        data = {
            "chatRoomId": room_id,
            "memberIds": ",".join(member_ids)
        }
        return Response(**self.call_api(params=params, json=data))

    def add_room_members(self, room_id: str, member_ids: typing.List[str]) -> Response:
        """增加群成员"""
        params = {
            "type": "28"
        }
        data = {
            "chatRoomId": room_id,
            "memberIds": ",".join(member_ids)
        }
        return Response(**self.call_api(params=params, json=data))

    def invite_room_members(self, room_id: str, member_ids: str) -> Response:
        """邀请群成员"""
        params = {
            "type": "59"
        }
        data = {
            "chatRoomId": room_id,
            "memberIds": member_ids
        }
        return Response(**self.call_api(params=params, json=data))

    def set_room_self_nickname(self, room_id: str, wxid: str, nickname: str) -> Response:
        """修改账号在指定群的昵称"""
        params = {
            "type": "31"
        }
        data = {
            "chatRoomId": room_id,
            "wxid": wxid,
            "nickName": nickname
        }
        return Response(**self.call_api(params=params, json=data))

    def top_msg(self, room_id: str, wxid: str) -> Response:
        """置顶群消息"""
        params = {
            "type": "51"
        }
        data = {
            "chatRoomId": room_id,
            "wxid": wxid
        }
        return Response(**self.call_api(params=params, json=data))

    def remove_top_msg(self, room_id: str, wxid: str) -> Response:
        """取消置顶群消息"""
        params = {
            "type": "52"
        }
        data = {
            "chatRoomId": room_id,
            "wxid": wxid
        }
        return Response(**self.call_api(params=params, json=data))

    def search_friend(self, keyword: str) -> UserInfo:
        """搜索好友"""
        params = {
            "type": "19"
        }
        data = {
            "keyword": keyword
        }
        return UserInfo(**self.call_api(params=params, json=data)["userInfo"])

    def add_friend(self, wxid: str, msg: str) -> Response:
        """添加好友"""
        params = {
            "type": "20"
        }
        data = {
            "wxid": wxid,
            "msg": msg
        }
        return Response(**self.call_api(params=params, json=data))

    def verify_apply(self, v3: str, v4: str, permission: int) -> Response:
        """验证好友请求"""
        params = {
            "type": "23"
        }
        data = {
            "v3": v3,
            "v4": v4,
            "permission": permission
        }
        return Response(**self.call_api(params=params, json=data))

    def get_db_info(self) -> typing.List[DB]:
        """获取数据库句柄"""
        params = {
            "type": "32"
        }
        return [
            DB(databaseName=item["databaseName"], handle=item["handle"], tables=[
                Table(**sub_item)
                for sub_item in item["tables"]
            ])
            for item in self.call_api(params=params)["data"]
        ]

    def exec_sql(self, db_handle: int, sql: str) -> ExecSQLResponse:
        """查询数据库"""
        params = {
            "type": "34"
        }
        data = {
            "dbHandle": db_handle,
            "sql": sql
        }
        return ExecSQLResponse(**self.call_api(params=params, json=data))

    def decode_image(self, image_path: str, save_path: str) -> Response:
        """解码图片"""
        params = {
            "type": "48"
        }
        data = {
            "imagePath": os.path.abspath(image_path),
            "savePath": os.path.abspath(save_path)
        }
        return Response(**self.call_api(params=params, json=data))

    def ocr(self, image_path: str) -> OCRResponse:
        """识别图片文本内容"""
        params = {
            "type": "49"
        }
        data = {
            "imagePath": os.path.abspath(image_path)
        }
        return OCRResponse(**self.call_api(params=params, json=data))

    def download_attachment(self, msg_id: int) -> Response:
        """下载消息附件"""
        params = {
            "type": "56"
        }
        data = {
            "msgId": msg_id
        }
        return Response(**self.call_api(params=params, json=data))

    def get_voice(self, msg_id: int, voice_dir: str) -> Response:
        """获取语音消息"""
        params = {
            "type": "57"
        }
        data = {
            "msgId": msg_id,
            "voiceDir": os.path.abspath(voice_dir)
        }
        return Response(**self.call_api(params=params, json=data))

    def get_sns_first_page(self) -> Response:
        """获取朋友圈第一页"""
        params = {
            "type": "53"
        }
        return Response(**self.call_api(params=params))

    def get_sns_next_page(self, sns_id: int) -> Response:
        """获取朋友圈下一页"""
        params = {
            "type": "54"
        }
        data = {
            "snsId": sns_id
        }
        return Response(**self.call_api(params=params, json=data))

    def confirm_receipt(self, wxid: str, transcation_id: str, transfer_id: str) -> Response:
        """确认收款"""
        params = {
            "type": "45"
        }
        data = {
            "wxid": wxid,
            "transcationId": transcation_id,
            "transferId": transfer_id
        }
        return Response(**self.call_api(params=params, json=data))

    def refuse_receipt(self, wxid: str, transcation_id: str, transfer_id: str) -> Response:
        """拒绝收款"""
        params = {
            "type": "65"
        }
        data = {
            "wxid": wxid,
            "transcationId": transcation_id,
            "transferId": transfer_id
        }
        return Response(**self.call_api(params=params, json=data))

    def get_qrcode(self) -> QRCodeUrlResponse:
        """获取登录二维码"""
        params = {
            "type": "58"
        }
        return QRCodeUrlResponse(**self.call_api(params=params))

    def logout(self) -> Response:
        """退出登录"""
        params = {
            "type": "44"
        }
        return Response(**self.call_api(params=params))

    @property
    def info(self) -> Account:
        return self.get_self_info()

    def on_event(self, raw_data: bytes) -> None:
        try:
            data = json.loads(raw_data)
            event = Event(**parse_event(data))
            logger.debug(event)
            self.call_hook_func(self.on_before_message, self, event)
            self.event_emitter.emit(str(ALL_MESSAGE), self, event)
            self.event_emitter.emit(str(event.type), self, event)
            self.call_hook_func(self.on_after_message, self, event)
            self.webhook(data)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error(raw_data)

    def handle(
        self,
        events: typing.Union[typing.List[str], str, None] = None,
        once: bool = False
    ) -> typing.Callable[[typing.Callable], None]:
        def wrapper(func):
            listen = self.event_emitter.on if not once else self.event_emitter.once
            if not events:
                listen(str(ALL_MESSAGE), func)
            else:
                for event in events if isinstance(events, list) else [events]:
                    listen(str(event), func)

        return wrapper

    def exit(self) -> None:
        self.call_hook_func(self.on_stop, self)
        self.process.terminate()

    def run(self) -> None:
        try:
            server = socketserver.ThreadingTCPServer((self.server_host, self.server_port), RequestHandler)
            server.bot = self
            logger.info(f"Listening Server at {self.server_host}:{self.server_port}")
            server.serve_forever()
        except (KeyboardInterrupt, SystemExit):
            self.exit()
