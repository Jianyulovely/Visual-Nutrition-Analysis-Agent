const app = getApp()

Page({
  data: {
    nickName: '',
    isLoggedIn: false
  },

  onLoad() {
    wx.setNavigationBarTitle({
      title: '首页'
    })

    this.checkLoginStatus()
  },

  onShow() {
    this.checkLoginStatus()
  },

  checkLoginStatus() {
    const nickName = app.globalData.nickName
    const isLoggedIn = !!nickName && nickName !== '匿名用户'

    this.setData({
      nickName: nickName,
      isLoggedIn: isLoggedIn
    })

    console.log('登录状态:', isLoggedIn, '昵称:', nickName)
  },

  handleLogin() {
    const that = this
    
    wx.showModal({
      title: '登录提示',
      content: '需要获取您的昵称用于标识分析记录',
      success: modalRes => {
        if (modalRes.confirm) {
          app.doLogin((userInfo) => {
            that.checkLoginStatus()
          })
        }
      }
    })
  },

  goToAnalyze() {
    wx.switchTab({
      url: '/pages/analyze/analyze'
    })
  }
})
