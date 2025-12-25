from pydantic import BaseModel


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str  # 微信授权码
    state: str | None = None  # 可选的状态参数


class DingtalkLoginRequest(BaseModel):
    """钉钉登录请求"""
    code: str  # 钉钉授权码
    state: str | None = None  # 可选的状态参数


class BindAccountRequest(BaseModel):
    """绑定账号请求"""
    account_type: str  # email, wechat, dingtalk
    account_id: str
    account_name: str | None = None
    avatar_url: str | None = None
    extra_data: str | None = None
    # 对于邮箱绑定，需要密码
    password: str | None = None


