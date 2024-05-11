import typing
from dataclasses import dataclass
from typing import List


@dataclass
class Account:
    """用户"""
    account: str
    city: str
    country: str
    currentDataPath: str
    dataSavePath: str
    dbKey: str
    headImage: str
    mobile: str
    name: str
    province: str
    signature: str
    wxid: str


@dataclass
class UserInfo:
    """搜索用户"""
    V3: str
    account: str
    bigImage: str
    city: str
    nation: str
    nickname: str
    province: str
    sex: str
    signature: str
    smallImage: str
    v3: str


@dataclass
class Contact:
    """联系人"""
    customAccount: str
    delFlag: int
    type: int
    userName: str
    verifyFlag: int
    wxid: str


@dataclass
class Room:
    """群聊"""
    admin: str
    chatRoomId: str
    notice: str
    xml: str


@dataclass
class RoomMembers:
    """群成员"""
    admin: str
    chatRoomId: str
    members: str


@dataclass
class Event:
    """消息事件"""
    content: typing.Optional[typing.Any] = None
    base64Img: typing.Optional[str] = None
    data: typing.Optional[list] = None
    createTime: typing.Optional[int] = None
    displayFullContent: typing.Optional[str] = None
    fromGroup: typing.Optional[str] = None
    fromUser: typing.Optional[str] = None
    isSendByPhone: typing.Optional[int] = None
    isSendMsg: typing.Optional[int] = None
    msgId: typing.Optional[int] = None
    path: typing.Optional[str] = None
    msgSequence: typing.Optional[int] = None
    pid: typing.Optional[int] = None
    sign: typing.Optional[str] = None
    signature: typing.Optional[str] = None
    toUser: typing.Optional[str] = None
    time: typing.Optional[str] = None
    timestamp: typing.Optional[int] = None
    type: typing.Optional[int] = None


@dataclass
class Table:
    """表结构"""
    name: str
    rootpage: str
    sql: str
    tableName: str


@dataclass
class DB:
    """数据库"""
    databaseName: str
    handle: int
    tables: List[Table]


@dataclass
class Response:
    """响应"""
    code: int
    result: str


@dataclass
class CheckLoginResponse(Response):
    """检查登录响应"""
    login_url: str


@dataclass
class RoomMemberNicknameResponse(Response):
    """群成员昵称响应"""
    nickname: str


@dataclass
class ExecSQLResponse(Response):
    """SQL执行响应"""
    data: dict


@dataclass
class OCRResponse(Response):
    """OCR响应"""
    text: str


@dataclass
class NicknameResponse(Response):
    """联系人/群昵称响应"""
    name: str


@dataclass
class QRCodeUrlResponse(Response):
    """登录二维码响应"""
    qrCodeUrl: str


@dataclass
class RoomMember:
    """群成员响应"""
    account: str
    headImage: str
    nickname: str
    v3: str
    wxid: str
