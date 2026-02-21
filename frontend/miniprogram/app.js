App({
  globalData: {
    userInfo: null,
    nickName: '',
    baseUrl: 'http://172bc3d4.r28.cpolar.top',
    privacyAgreed: false
  },

  onLaunch() {
    wx.getSystemInfo({
      success: res => {
        this.globalData.systemInfo = res
      }
    })

    this.checkLogin()
  },

  checkLogin() {
    const savedUserInfo = wx.getStorageSync('userInfo')
    const savedNickName = wx.getStorageSync('nickName')

    if (savedUserInfo && savedNickName) {
      this.globalData.userInfo = savedUserInfo
      this.globalData.nickName = savedNickName
      console.log('已登录:', savedNickName)
    }
  },

  saveUserInfo(userInfo) {
    this.globalData.userInfo = userInfo
    this.globalData.nickName = userInfo.nickName || ''
    wx.setStorageSync('userInfo', userInfo)
    wx.setStorageSync('nickName', userInfo.nickName)
    console.log('用户信息已保存:', userInfo)
  }
})
