/**
 * 统一的错误处理工具函数
 * 用于从后端错误响应中提取错误信息
 */
export function extractErrorMessage(error) {
  // 默认错误消息
  let message = '操作失败'
  
  if (!error) {
    return message
  }
  
  // 详细的错误日志（开发环境）
  if (import.meta.env.DEV) {
    console.error('错误详情:', {
      error,
      errorType: typeof error,
      response: error.response,
      responseData: error.response?.data,
      responseDataType: typeof error.response?.data,
      responseStatus: error.response?.status,
      request: error.request,
      message: error.message
    })
  }
  
  // 优先从 error.response.data 获取错误信息
  // FastAPI 通常返回 {detail: "错误信息"} 或 {detail: [{msg: "错误信息"}]} 格式
  if (error.response?.data) {
    const data = error.response.data
    
    // 处理不同的数据结构
    if (typeof data === 'string') {
      message = data
    } else if (data && typeof data === 'object') {
      if (data.detail) {
        // 如果 detail 是数组（Pydantic 验证错误）
        if (Array.isArray(data.detail)) {
          // 提取第一个错误信息
          const firstError = data.detail[0]
          if (firstError && firstError.msg) {
            // 移除 "Value error, " 前缀（如果存在）
            message = firstError.msg.replace(/^Value error, /, '')
          } else if (firstError && typeof firstError === 'string') {
            message = firstError
          } else {
            message = JSON.stringify(firstError)
          }
        } else {
          // detail 是字符串
          message = String(data.detail)
        }
      } else if (data.message) {
        message = String(data.message)
      } else {
        // 尝试提取其他可能的错误字段
        const errorKeys = Object.keys(data)
        if (errorKeys.length > 0) {
          message = JSON.stringify(data)
        }
      }
    } else {
      message = String(data)
    }
  } else if (error.response) {
    // 如果有响应但没有 data
    message = `操作失败: ${error.response.status} ${error.response.statusText || ''}`
  } else if (error.request) {
    // 请求已发送但没有收到响应
    message = '网络错误，请检查网络连接'
  } else {
    // 其他错误
    message = error.message || '操作失败'
  }
  
  return message
}

