const { chooseImage, uploadImage } = require('../../utils/api.js')

Page({
  data: {
    imagePath: '',
    username: '',
    analyzing: false,
    result: '',
    parsedResult: null
  },

  onLoad() {
    wx.setNavigationBarTitle({
      title: '图像分析'
    })
  },

  onShow() {
    this.setData({
      analyzing: false
    })
  },

  chooseImage() {
    chooseImage(1).then(res => {
      this.setData({
        imagePath: res[0],
        result: '',
        parsedResult: null
      })
    }).catch(err => {
      console.error('选择图片失败', err)
    })
  },

  onUsernameInput(e) {
    this.setData({
      username: e.detail.value
    })
  },

  formatResult(data) {
    if (!data) return '无数据'
    
    let result = ''
    
    if (data.dish_name) {
      result += `菜品名称：${data.dish_name}\n\n`
    }
    
    if (data.main_ingredients && data.main_ingredients.length > 0) {
      result += `主要食材：${data.main_ingredients.join('、')}\n\n`
    }
    
    if (data.description) {
      result += `描述：${data.description}\n\n`
    }
    
    if (data.pagoda_nutrition_vector) {
      const pagoda = data.pagoda_nutrition_vector
      result += '营养金字塔：\n'
      
      if (pagoda.L1) {
        result += `  谷薯类：${pagoda.L1.total_value || 0}g\n`
      }
      if (pagoda.L2) {
        result += `  蔬果类：${pagoda.L2.total_value || 0}g\n`
      }
      if (pagoda.L3) {
        result += `  动物性食物：${pagoda.L3.total_value || 0}g\n`
      }
      if (pagoda.L4) {
        result += `  奶豆坚果类：${pagoda.L4.total_value || 0}g\n`
      }
      if (pagoda.L5) {
        result += `  油：${pagoda.L5.oil || 0}g\n`
        result += `  盐：${pagoda.L5.salt || 0}g\n`
      }
      result += '\n'
    }
    
    if (data.feature_tags && data.feature_tags.length > 0) {
      result += `标签：${data.feature_tags.join('、')}\n`
    }
    
    return result || JSON.stringify(data, null, 2)
  },

  analyzeImage() {
    const { imagePath, username } = this.data

    if (!imagePath) {
      wx.showToast({
        title: '请先上传图片',
        icon: 'none'
      })
      return
    }

    if (!username) {
      wx.showToast({
        title: '请输入用户名',
        icon: 'none'
      })
      return
    }

    this.setData({
      analyzing: true
    })

    uploadImage(imagePath, { username }).then(res => {
      let resultText = ''
      let parsedResult = null
      
      try {
        console.log('后端返回数据:', res)
        
        let dataToParse = res
        
        if (typeof dataToParse === 'object' && dataToParse.data) {
          dataToParse = dataToParse.data
        }
        
        if (typeof dataToParse === 'string') {
          try {
            parsedResult = JSON.parse(dataToParse)
            resultText = this.formatResult(parsedResult)
          } catch (parseError) {
            resultText = dataToParse
          }
        } else if (typeof dataToParse === 'object') {
          parsedResult = dataToParse
          resultText = this.formatResult(parsedResult)
        } else {
          resultText = JSON.stringify(res, null, 2)
        }
      } catch (e) {
        console.error('解析结果失败', e)
        resultText = typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)
      }
      
      this.setData({
        analyzing: false,
        result: resultText,
        parsedResult: parsedResult
      })
      wx.showToast({
        title: '分析完成',
        icon: 'success'
      })
    }).catch(err => {
      this.setData({
        analyzing: false
      })
      console.error('分析失败', err)
    })
  }
})
