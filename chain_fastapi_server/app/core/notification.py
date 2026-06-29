"""通知模块 —— 微信模板消息后端。

提供可扩展的通知接口（Protocol）和微信公众号模板消息实现。
受 config.ENABLE_WECHAT_NOTIFY 开关控制。
"""

import json
from typing import Optional, Protocol, runtime_checkable

import requests
from loguru import logger


@runtime_checkable
class NotificationBackend(Protocol):
    """通知后端协议，所有通知后端需实现 send 方法。"""

    def send(self, title: str, content: str, **kwargs) -> bool:
        """发送通知。成功返回 True，失败返回 False。"""
        ...


class WeChatBackend:
    """微信公众号模板消息通知后端。"""

    def __init__(self, app_id: str, app_secret: str, template_id: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.template_id = template_id
        self._access_token: Optional[str] = None

    def get_access_token(self) -> Optional[str]:
        """获取微信 access_token。"""
        url = (
            f"https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        )
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "access_token" in data:
                    self._access_token = data["access_token"]
                    return self._access_token
                logger.error(f"获取 access_token 失败: {data}")
            else:
                logger.error(f"获取 access_token HTTP 错误: {resp.status_code}")
        except Exception as e:
            logger.error(f"获取 access_token 异常: {e}")
        return None

    def send(self, title: str, content: str, touser: str = "", **kwargs) -> bool:
        """发送微信模板消息。

        Args:
            title: 消息标题（填入 thing 字段）。
            content: 消息内容（填入 character_string 字段）。
            touser: 接收者 openid，为空时需在 kwargs 中传入 openid_list。

        Returns:
            发送是否成功。
        """
        from app.core.config import settings

        if not getattr(settings, "ENABLE_WECHAT_NOTIFY", False):
            return False

        openid_list = kwargs.get("openid_list", [])
        if touser:
            openid_list = [touser]
        if not openid_list:
            logger.warning("微信通知：未指定接收者 openid")
            return False

        access_token = self.get_access_token()
        if not access_token:
            return False

        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

        # 注意：thing1/character_string2 是模板字段名，需与微信公众号后台配置一致
        data = {
            "thing1": {"value": title[:20]},
            "character_string2": {"value": content[:200]},
        }

        success_count = 0
        for openid in openid_list:
            payload = {
                "touser": openid,
                "template_id": self.template_id,
                "data": data,
            }
            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200 and resp.json().get("errcode") == 0:
                    success_count += 1
                else:
                    logger.error(f"微信发送失败: {resp.text}")
            except Exception as e:
                logger.error(f"微信发送异常: {e}")

        return success_count == len(openid_list)


def send_template_message(
    title: str,
    content: str,
    openid_list: Optional[list[str]] = None,
    template_id: Optional[str] = None,
) -> dict:
    """便捷函数：发送微信模板消息。

    使用全局配置的 WeChatBackend 实例。

    Args:
        title: 消息标题。
        content: 消息内容。
        openid_list: 接收者 openid 列表。
        template_id: 模板 ID（可选，不传则使用默认配置）。

    Returns:
        {"errcode": ..., "errmsg": ...}
    """
    from app.core.config import settings

    if not getattr(settings, "ENABLE_WECHAT_NOTIFY", False):
        return {"errcode": 0, "errmsg": "微信通知已关闭"}

    backend = WeChatBackend(
        app_id=settings.WECHAT_APP_ID,
        app_secret=settings.WECHAT_APP_SECRET,
        template_id=template_id or settings.WECHAT_TEMPLATE_ID,
    )

    ok = backend.send(title=title, content=content, openid_list=openid_list or [])
    if ok:
        return {"errcode": 200, "errmsg": f"发送成功: {len(openid_list or [])} 条"}
    return {"errcode": 10000, "errmsg": "发送失败"}
