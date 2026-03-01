const { chooseImage, uploadImage } = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    isLoggedIn: false,
    imagePath: '',
    username: '',
    analyzing: false,
    hasUploadedImage: false,
    result: '',
    parsedResult: null,
    pieChartData: null,
    selectedCategory: '',
    selectedCategoryDetails: ''
  },

  onLoad() {
    wx.setNavigationBarTitle({
      title: '图像分析'
    })

    if (!app.globalData.privacyAgreed) {
      wx.showModal({
        title: '提示',
        content: '请先阅读并同意隐私协议',
        showCancel: false,
        success: () => {
          wx.switchTab({
            url: '/pages/index/index'
          })
        }
      })
      return
    }

    this.checkLoginStatus()
  },

  onShow() {
    if (!app.globalData.privacyAgreed) {
      wx.switchTab({
        url: '/pages/index/index'
      })
      return
    }

    this.checkLoginStatus()

    this.setData({
      analyzing: false
    })
    
    if (this.data.pieChartData) {
      this.drawPieChart()
    }
  },

  checkLoginStatus() {
    const nickName = app.globalData.nickName
    const isLoggedIn = !!nickName && nickName !== '匿名用户'

    this.setData({
      isLoggedIn: isLoggedIn,
      username: nickName || ''
    })

    console.log('分析页登录状态:', isLoggedIn, '昵称:', nickName)
  },

  goToIndex() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  },

  showImagePicker() {
    const that = this
    wx.showActionSheet({
      itemList: ['从相册选择', '拍照'],
      success: res => {
        if (res.tapIndex === 0) {
          that.selectFromAlbum()
        } else {
          that.takePhoto()
        }
      }
    })
  },

  selectFromAlbum() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album'],
      success: res => {
        if (res.tempFilePaths && res.tempFilePaths.length > 0) {
          this.setData({
            imagePath: res.tempFilePaths[0],
            result: '',
            parsedResult: null,
            pieChartData: null,
            selectedCategory: '',
            selectedCategoryDetails: '',
            hasUploadedImage: true,
            analyzing: false
          })
        }
      },
      fail: err => {
        console.error('从相册选择图片失败', err)
        if (err.errMsg && !err.errMsg.includes('cancel')) {
          wx.showToast({
            title: '选择图片失败',
            icon: 'none'
          })
        }
      }
    })
  },

  takePhoto() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['camera'],
      success: res => {
        if (res.tempFilePaths && res.tempFilePaths.length > 0) {
          const tempPath = res.tempFilePaths[0]
          
          this.setData({
            imagePath: tempPath,
            result: '',
            parsedResult: null,
            pieChartData: null,
            selectedCategory: '',
            selectedCategoryDetails: '',
            hasUploadedImage: true,  
            analyzing: false
          })

          wx.saveImageToPhotosAlbum({
            filePath: tempPath,
            success: () => {
              wx.showToast({
                title: '照片已保存到相册',
                icon: 'success',
                duration: 1500
              })
            },
            fail: err => {
              console.error('保存到相册失败:', err)
              if (err.errMsg && err.errMsg.includes('auth')) {
                wx.showModal({
                  title: '需要相册权限',
                  content: '请在设置中开启"添加到相册"权限',
                  showCancel: false
                })
              }
            }
          })
        }
      },
      fail: err => {
        console.error('拍照失败', err)
        if (err.errMsg && !err.errMsg.includes('cancel')) {
          wx.showToast({
            title: '拍照失败',
            icon: 'none'
          })
        }
      }
    })
  },

  chooseImage() {
    this.showImagePicker()
  },

  onUsernameInput(e) {
    this.setData({
      username: e.detail.value
    })
  },

  calculatePieData(pagoda) {
    if (!pagoda) return null

    const l1 = pagoda.L1?.total_value || 0
    const l2 = pagoda.L2?.total_value || 0
    const l3 = pagoda.L3?.total_value || 0
    const l4 = pagoda.L4?.total_value || 0

    const total = l1 + l2 + l3 + l4

    if (total === 0) return null

    const data = [
      { name: '谷薯类', value: l1, color: '#FFD700', angle: 0 },
      { name: '蔬果类', value: l2, color: '#52C41A', angle: 0 },
      { name: '肉蛋类', value: l3, color: '#FF8C00', angle: 0 },
      { name: '奶豆坚果', value: l4, color: '#1890FF', angle: 0 }
    ].filter(item => item.value > 0)

    let currentAngle = 0
    data.forEach(item => {
      item.angle = (item.value / total) * 360
      item.startAngle = currentAngle
      item.endAngle = currentAngle + item.angle
      currentAngle += item.angle
    })

    return {
      data: data,
      total: total
    }
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
        result += `  肉蛋类：${pagoda.L3.total_value || 0}g\n`
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

  getEmojiForCategory(category) {
    const emojiMap = {
      '谷薯类': '🌾',
      '蔬果类': '🥬',
      '肉蛋类': '🍗',
      '奶豆坚果': '🥜'
    }
    return emojiMap[category] || '🍽️'
  },

  drawPieChart() {
    const { pieChartData } = this.data
    if (!pieChartData || !pieChartData.data || pieChartData.data.length === 0) return

    const query = wx.createSelectorQuery()
    query.select('#pieCanvas').fields({
      node: true,
      size: true
    }).exec((res) => {
      if (!res || !res[0]) return

      const canvas = res[0].node
      const ctx = canvas.getContext('2d')
      const dpr = wx.getSystemInfoSync().pixelRatio
      canvas.width = res[0].width * dpr
      canvas.height = res[0].height * dpr
      ctx.scale(dpr, dpr)

      const width = res[0].width
      const height = res[0].height
      const centerX = width / 2
      const centerY = height / 2
      const outerRadius = Math.min(width, height) / 2 - 20
      const innerRadius = outerRadius * 0.6

      let currentAngle = -Math.PI / 2

      pieChartData.data.forEach((item) => {
        const sliceAngle = (item.angle / 360) * 2 * Math.PI

        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.arc(centerX, centerY, outerRadius, currentAngle, currentAngle + sliceAngle)
        ctx.arc(centerX, centerY, innerRadius, currentAngle + sliceAngle, currentAngle, true)
        ctx.closePath()
        
        const gradient = ctx.createLinearGradient(centerX - outerRadius, centerY - outerRadius, centerX + outerRadius, centerY + outerRadius)
        gradient.addColorStop(0, item.color)
        gradient.addColorStop(1, this.lightenColor(item.color, 0.2))
        ctx.fillStyle = gradient
        ctx.fill()
        ctx.shadowColor = 'rgba(0, 0, 0, 0.1)'
        ctx.shadowBlur = 8
        ctx.shadowOffsetX = 2
        ctx.shadowOffsetY = 2

        currentAngle += sliceAngle
      })
    })
  },

  lightenColor(color, amount) {
    const hex = color.replace('#', '')
    const r = parseInt(hex.substring(0, 2), 16)
    const g = parseInt(hex.substring(2, 4), 16)
    const b = parseInt(hex.substring(4, 6), 16)

    const newR = Math.min(255, Math.round(r + (255 - r) * amount))
    const newG = Math.min(255, Math.round(g + (255 - g) * amount))
    const newB = Math.min(255, Math.round(b + (255 - b) * amount))

    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`
  },

  onPieChartClick(e) {
    const { pieChartData } = this.data
    if (!pieChartData || !pieChartData.data || pieChartData.data.length === 0) return

    const query = wx.createSelectorQuery()
    query.select('#pieCanvas').fields({
      node: true,
      size: true,
      rect: true
    }).exec((res) => {
      if (!res || !res[0]) return

      const canvas = res[0].node
      const rect = res[0].rect
      const centerX = rect.width / 2
      const centerY = rect.height / 2
      const outerRadius = Math.min(rect.width, rect.height) / 2 - 20
      const innerRadius = outerRadius * 0.6

      const clickX = e.detail.x - rect.left
      const clickY = e.detail.y - rect.top
      const distance = Math.sqrt(Math.pow(clickX - centerX, 2) + Math.pow(clickY - centerY, 2))

      if (distance >= innerRadius && distance <= outerRadius) {
        let angle = Math.atan2(clickY - centerY, clickX - centerX)
        if (angle < -Math.PI / 2) angle += 2 * Math.PI

        let currentAngle = -Math.PI / 2
        for (let i = 0; i < pieChartData.data.length; i++) {
          const item = pieChartData.data[i]
          const sliceAngle = (item.angle / 360) * 2 * Math.PI
          if (angle >= currentAngle && angle < currentAngle + sliceAngle) {
            this.showCategoryDetails(item.name)
            break
          }
          currentAngle += sliceAngle
        }
      }
    })
  },

  onLegendItemClick(e) {
    const { index } = e.currentTarget.dataset
    const { pieChartData } = this.data
    if (!pieChartData || !pieChartData.data || pieChartData.data.length === 0) return

    const item = pieChartData.data[index]
    this.showCategoryDetails(item.name)
  },

  showCategoryDetails(category) {
    const { parsedResult } = this.data
    if (!parsedResult || !parsedResult.main_ingredients) return

    let details = ''
    const ingredients = parsedResult.main_ingredients

    switch (category) {
      case '谷薯类':
        details = '内含米饭、面条、土豆等'
        break
      case '蔬果类':
        details = '内含' + ingredients.filter(ing => ['蔬菜', '水果', '青菜', '白菜', '萝卜', '番茄', '黄瓜'].some(keyword => ing.includes(keyword))).join('、') + '等'
        break
      case '肉蛋类':
        details = '内含' + ingredients.filter(ing => ['肉', '蛋', '鸡', '鸭', '鱼', '虾', '牛', '羊', '猪'].some(keyword => ing.includes(keyword))).join('、') + '等'
        break
      case '奶豆坚果':
        details = '内含' + ingredients.filter(ing => ['奶', '豆', '坚果', '花生', '杏仁', '核桃'].some(keyword => ing.includes(keyword))).join('、') + '等'
        break
      default:
        details = '暂无详细信息'
    }

    this.setData({
      selectedCategory: category,
      selectedCategoryDetails: details
    })
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
      let pieChartData = null
      
      if (res.status === 'invalid_image') {
        this.setData({
          analyzing: false,
          imagePath: '',
          hasUploadedImage: false,
          result: '',
          parsedResult: null,
          pieChartData: null,
          selectedCategory: '',
          selectedCategoryDetails: ''
        })
        wx.showModal({
          title: '图片无效',
          content: res.message + '\n\n请重新选择图片',
          showCancel: false,
          confirmText: '重新选择',
          success: () => {
            this.showImagePicker() 
          }
        })
        return
      }
      
      try {
        console.log('后端返回数据:', res)
        
        let dataToParse = res
        
        if (typeof dataToParse === 'object' && dataToParse.data !== undefined) {
          dataToParse = dataToParse.data
        }
        
        if (dataToParse === null || dataToParse === undefined) {
          resultText = '分析失败：未返回分析结果'
        } else if (typeof dataToParse === 'string') {
          try {
            parsedResult = JSON.parse(dataToParse)
            resultText = this.formatResult(parsedResult)
            pieChartData = this.calculatePieData(parsedResult?.pagoda_nutrition_vector)
          } catch (parseError) {
            resultText = dataToParse
          }
        } else if (typeof dataToParse === 'object') {
          parsedResult = dataToParse
          resultText = this.formatResult(parsedResult)
          pieChartData = this.calculatePieData(parsedResult?.pagoda_nutrition_vector)
        } else {
          resultText = JSON.stringify(res, null, 2)
        }
      } catch (e) {
        console.error('解析结果失败', e)
        resultText = '解析失败：' + JSON.stringify(e)
      }
      
      this.setData({
        analyzing: false,
        hasUploadedImage: false,
        result: resultText,
        parsedResult: parsedResult,
        pieChartData: pieChartData,
        selectedCategory: '',
        selectedCategoryDetails: ''
      }, () => {
        if (pieChartData) {
          this.drawPieChart()
        }
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
