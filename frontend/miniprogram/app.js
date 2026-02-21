App({
  globalData: {
    userInfo: null,
    nickName: '',
    baseUrl: 'https://706e6893.r16.vip.cpolar.cn'
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

  doLogin(callback) {
    const that = this
    
    wx.getUserProfile({
      desc: '用于获取用户昵称',
      success: res => {
        console.log('登录成功:', res.userInfo)
        that.globalData.userInfo = res.userInfo
        that.globalData.nickName = res.userInfo.nickName || '微信用户'
        wx.setStorageSync('userInfo', res.userInfo)
        wx.setStorageSync('nickName', res.userInfo.nickName)
        
        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        })
        
        if (callback) callback(res.userInfo)
      },
      fail: err => {
        console.error('登录失败:', err)
        wx.showToast({
          title: '登录失败',
          icon: 'none'
        })
      }
    })
  }
})
