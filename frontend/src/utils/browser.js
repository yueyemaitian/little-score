/**
 * 浏览器环境检测工具
 */

/**
 * 检测是否在微信浏览器中
 */
export function isWeChatBrowser() {
  const ua = navigator.userAgent.toLowerCase()
  return /micromessenger/.test(ua)
}

/**
 * 检测是否在钉钉浏览器中
 */
export function isDingTalkBrowser() {
  const ua = navigator.userAgent.toLowerCase()
  return /dingtalk/.test(ua)
}

/**
 * 获取当前浏览器环境类型
 * @returns {'wechat' | 'dingtalk' | 'other'}
 */
export function getBrowserType() {
  if (isWeChatBrowser()) {
    return 'wechat'
  }
  if (isDingTalkBrowser()) {
    return 'dingtalk'
  }
  return 'other'
}

/**
 * 获取推荐的登录方式
 * @returns {Array<'wechat' | 'dingtalk' | 'email'>}
 */
export function getRecommendedLoginMethods() {
  const browserType = getBrowserType()
  const methods = []
  
  if (browserType === 'wechat') {
    methods.push('wechat')
  } else if (browserType === 'dingtalk') {
    methods.push('dingtalk')
  }
  
  // 邮箱登录始终可用
  methods.push('email')
  
  return methods
}



