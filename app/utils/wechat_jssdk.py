"""微信 JS-SDK 工具"""
import hashlib
import random
import string
import time
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


def generate_nonce_str(length: int = 16) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def get_jsapi_ticket() -> Optional[str]:
    """获取微信 JSAPI ticket"""
    settings = get_settings()
    
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        print(f"⚠️ 微信配置未完整: WECHAT_APP_ID={'已配置' if settings.WECHAT_APP_ID else '未配置'}, "
              f"WECHAT_APP_SECRET={'已配置' if settings.WECHAT_APP_SECRET else '未配置'}")
        return None
    
    # 第一步：获取 access_token
    token_url = "https://api.weixin.qq.com/cgi-bin/token"
    token_params = {
        "grant_type": "client_credential",
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.get(token_url, params=token_params, timeout=10.0)
            token_response.raise_for_status()
            token_data = token_response.json()
            
            # 检查微信 API 返回的错误
            if "errcode" in token_data and token_data.get("errcode") != 0:
                errcode = token_data.get("errcode")
                error_msg = token_data.get("errmsg", "未知错误")
                print(f"⚠️ 获取微信 access_token 失败: token_params={token_params},errcode={errcode}, errmsg={error_msg}")
                
                # 提供更详细的错误说明
                if errcode == 40013:
                    print("   提示: 无效的 AppID，请检查 WECHAT_APP_ID 配置是否正确")
                elif errcode == 40125:
                    print("   提示: 无效的 AppSecret，请检查 WECHAT_APP_SECRET 配置是否正确")
                elif errcode == 50001:
                    print("   提示: 用户未授权，可能的原因：")
                    print("     1. AppID 或 AppSecret 配置错误")
                    print("     2. IP 白名单限制（需要在微信公众平台配置服务器 IP 白名单）")
                    print("     3. 应用类型不支持（某些类型的应用不支持获取 access_token）")
                    print("   请登录微信公众平台检查：")
                    print("     - 开发 -> 基本配置 -> IP 白名单")
                    print("     - 设置 -> 公众号设置 -> 功能设置 -> JS 接口安全域名")
                elif errcode == 61024:
                    print("   提示: IP 白名单限制，请在微信公众平台配置服务器 IP 白名单")
                    print("   路径: 开发 -> 基本配置 -> IP 白名单")
                
                return None
            
            if "access_token" not in token_data:
                print(f"⚠️ 微信 API 响应中缺少 access_token: {token_data}")
                return None
            
            access_token = token_data["access_token"]
            
            # 第二步：获取 jsapi_ticket
            ticket_url = "https://api.weixin.qq.com/cgi-bin/ticket/getticket"
            ticket_params = {
                "type": "jsapi",
                "access_token": access_token,
            }
            
            ticket_response = await client.get(ticket_url, params=ticket_params, timeout=10.0)
            ticket_response.raise_for_status()
            ticket_data = ticket_response.json()
            
            # 检查微信 API 返回的错误
            if ticket_data.get("errcode") != 0:
                error_msg = ticket_data.get("errmsg", "未知错误")
                print(f"⚠️ 获取微信 jsapi_ticket 失败: errcode={ticket_data.get('errcode')}, errmsg={error_msg}")
                return None
            
            ticket = ticket_data.get("ticket")
            if ticket:
                print(f"✓ 成功获取微信 jsapi_ticket")
            return ticket
        except httpx.HTTPStatusError as e:
            print(f"⚠️ HTTP 请求失败: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"⚠️ 获取微信 JSAPI ticket 失败: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def generate_signature(ticket: str, nonce_str: str, timestamp: int, url: str) -> str:
    """生成微信 JS-SDK 签名"""
    # 按照微信文档要求，对参数进行字典序排序并拼接
    string1 = f"jsapi_ticket={ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}"
    # SHA1 加密
    signature = hashlib.sha1(string1.encode('utf-8')).hexdigest()
    return signature


async def get_wechat_jssdk_config(url: str) -> Optional[dict]:
    """获取微信 JS-SDK 配置"""
    settings = get_settings()
    
    if not settings.WECHAT_APP_ID:
        print(f"⚠️ WECHAT_APP_ID 未配置")
        return None
    
    if not settings.WECHAT_APP_SECRET:
        print(f"⚠️ WECHAT_APP_SECRET 未配置")
        return None
    
    print(f"📝 开始获取微信 JS-SDK 配置，URL: {url}")
    
    # 获取 jsapi_ticket
    ticket = await get_jsapi_ticket()
    if not ticket:
        print(f"⚠️ 无法获取 jsapi_ticket，配置获取失败")
        return None
    
    # 生成配置参数
    timestamp = int(time.time())
    nonce_str = generate_nonce_str()
    signature = generate_signature(ticket, nonce_str, timestamp, url)
    
    print(f"✓ 成功生成微信 JS-SDK 配置")
    
    return {
        "appId": settings.WECHAT_APP_ID,
        "timestamp": timestamp,
        "nonceStr": nonce_str,
        "signature": signature,
    }

