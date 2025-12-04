import api from './index'

export const enumsApi = {
  getEnums() {
    return api.get('/enums/enums')
  }
}

