"""短信发送模块 —— 阿里云短信集成。

受 config.ENABLE_SMS 开关控制。
"""

from typing import Optional
from loguru import logger


def _create_client(access_key_id: str, access_key_secret: str):
    """创建阿里云短信客户端。"""
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_dysmsapi20170525.client import Client as SmsClient

    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
    )
    config.endpoint = "dysmsapi.aliyuncs.com"
    return SmsClient(config)


def send_sms(
    phone: str,
    template_code: str,
    params: Optional[dict] = None,
    sign_name: Optional[str] = None,
) -> bool:
    """发送阿里云短信。

    Args:
        phone: 接收手机号。
        template_code: 短信模板编码。
        params: 模板变量字典，如 {"code": "123456"}。
        sign_name: 短信签名（可选，不传则使用配置默认值）。

    Returns:
        发送是否成功。
    """
    from app.core.config import settings

    if not getattr(settings, "ENABLE_SMS", False):
        logger.debug("短信功能已关闭，跳过发送")
        return False

    try:
        from alibabacloud_dysmsapi20170525 import models as sms_models
        import json

        client = _create_client(
            access_key_id=settings.SMS_ACCESS_KEY,
            access_key_secret=settings.SMS_ACCESS_SECRET,
        )

        request = sms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=sign_name or settings.SMS_SIGN_NAME,
            template_code=template_code,
            template_param=json.dumps(params) if params else None,
        )

        response = client.send_sms(request)
        if response.body.code == "OK":
            logger.info(f"短信发送成功: {phone}")
            return True
        else:
            logger.error(f"短信发送失败: {phone} | {response.body.code} | {response.body.message}")
            return False

    except ImportError:
        logger.error("短信 SDK 未安装，请执行: pip install alibabacloud-dysmsapi20170525")
        return False
    except Exception as e:
        logger.error(f"短信发送异常: {phone} | {e}")
        return False
