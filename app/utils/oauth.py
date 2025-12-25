"""第三方登录OAuth工具"""
import json
from typing import Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


async def get_wechat_user_info(code: str) -> dict:
    """通过微信授权码获取用户信息"""
    settings = get_settings()
    
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="微信登录未配置"
        )
    
    # 第一步：通过code获取access_token
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    token_params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(token_url, params=token_params)
        token_data = token_response.json()
        
        if "errcode" in token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"微信授权失败: {token_data.get('errmsg', '未知错误')}"
            )
        
        access_token = token_data.get("access_token")
        openid = token_data.get("openid")
        
        if not access_token or not openid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="获取微信access_token失败"
            )
        
        # 第二步：通过access_token获取用户信息
        user_info_url = "https://api.weixin.qq.com/sns/userinfo"
        user_info_params = {
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN"
        }
        
        user_info_response = await client.get(user_info_url, params=user_info_params)
        user_info = user_info_response.json()
        
        if "errcode" in user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取微信用户信息失败: {user_info.get('errmsg', '未知错误')}"
            )
        
        return {
            "openid": openid,
            "nickname": user_info.get("nickname", ""),
            "headimgurl": user_info.get("headimgurl", ""),
            "unionid": user_info.get("unionid"),  # 可选，需要微信开放平台
            "extra_data": json.dumps({
                "province": user_info.get("province"),
                "city": user_info.get("city"),
                "country": user_info.get("country"),
                "sex": user_info.get("sex"),
            })
        }


async def get_dingtalk_user_info(code: str) -> dict:
    """通过钉钉授权码获取用户信息"""
    settings = get_settings()
    
    if not settings.DINGTALK_APP_KEY or not settings.DINGTALK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="钉钉登录未配置"
        )
    
    # 第一步：通过code获取access_token
    token_url = "https://oapi.dingtalk.com/sns/gettoken"
    token_params = {
        "appid": settings.DINGTALK_APP_KEY,
        "appsecret": settings.DINGTALK_APP_SECRET
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(token_url, params=token_params)
        token_data = token_response.json()
        
        if token_data.get("errcode") != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取钉钉access_token失败: {token_data.get('errmsg', '未知错误')}"
            )
        
        access_token = token_data.get("access_token")
        
        # 第二步：通过临时授权码获取用户信息
        user_info_url = "https://oapi.dingtalk.com/sns/getuserinfo_bycode"
        user_info_data = {
            "tmp_auth_code": code
        }
        user_info_headers = {
            "x-acs-dingtalk-access-token": access_token
        }
        
        user_info_response = await client.post(
            user_info_url,
            json=user_info_data,
            headers=user_info_headers
        )
        user_info = user_info_response.json()
        
        if user_info.get("errcode") != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"获取钉钉用户信息失败: {user_info.get('errmsg', '未知错误')}"
            )
        
        user_info_data = user_info.get("user_info", {})
        return {
            "openid": user_info_data.get("openid", ""),
            "nickname": user_info_data.get("nick", ""),
            "unionid": user_info_data.get("unionid", ""),
            "avatar_url": user_info_data.get("avatar_url", ""),
            "extra_data": json.dumps({
                "main_org_name": user_info_data.get("main_org_name"),
            })
        }



