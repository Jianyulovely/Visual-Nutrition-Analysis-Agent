const app = getApp()

Page({
  data: {
    nickName: '',
    isLoggedIn: false,
    privacyAgreed: false
  },

  onLoad() {
    wx.setNavigationBarTitle({
      title: '首页'
    })
  },

  onShow() {
    if (this.data.privacyAgreed) {
      this.checkLoginStatus()
    }
  },

  onPrivacyAgree() {
    console.log("用户同意隐私授权")
    app.globalData.privacyAgreed = true
    this.setData({
      privacyAgreed: true
    })
    this.checkLoginStatus()
  },

  onPrivacyDisagree() {
    console.log("用户拒绝隐私授权")
    wx.showModal({
      title: '提示',
      content: '您需要同意隐私协议才能使用本应用',
      showCancel: false,
      success: () => {
      }
    })
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
    wx.showModal({
      title: '登录提示',
      content: '需要获取您的昵称用于标识分析记录',
      success: modalRes => {
        if (modalRes.confirm) {
          wx.navigateTo({
            url: '/pages/profile/profile'
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
