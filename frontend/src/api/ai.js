import api from './index'

export const aiApi = {
  /**
   * 解析语音指令
   * @param {string} text - 语音转文字后的内容
   * @returns {Promise} - 返回解析结果
   */
  parseVoiceCommand(text) {
    return api.post('/ai/parse-voice-command', { text })
  },

  /**
   * 获取可用选项（项目列表、兑换选项等）
   * @returns {Promise} - 返回可用选项
   */
  getAvailableOptions() {
    return api.get('/ai/available-options')
  }
}

