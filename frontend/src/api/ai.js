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
   * 识别音频文件并返回解析结果（用于微信浏览器等不支持 Web Speech API 的环境）
   * @param {File|Blob} audioFile - 音频文件
   * @returns {Promise} - 返回解析结果
   */
  recognizeAudio(audioFile) {
    const formData = new FormData()
    formData.append('audio', audioFile, 'audio.webm')
    return api.post('/ai/recognize-audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取可用选项（项目列表、兑换选项等）
   * @returns {Promise} - 返回可用选项
   */
  getAvailableOptions() {
    return api.get('/ai/available-options')
  }
}

