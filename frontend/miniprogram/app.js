App({
  globalData: {
    userInfo: null,
    baseUrl: 'http://localhost:8000'
  },

  // 小程序启动时触发
  onLaunch() {
    wx.getSystemInfo({  //获取手机型号
      success: res => {
        this.globalData.systemInfo = res
      }
    })
  }
})
