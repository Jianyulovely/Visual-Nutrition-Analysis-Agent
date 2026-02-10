const { chooseImage, uploadImage } = require('../../utils/api.js')

Page({
  data: {
    imagePath: '',
    username: '',
    analyzing: false,
    result: ''
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
        result: ''
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
      this.setData({
        analyzing: false,
        result: res.data || JSON.stringify(res)
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
