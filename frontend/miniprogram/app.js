App({
  globalData: {
    userInfo: null,
    baseUrl: 'http://localhost:8000'
  },

  onLaunch() {
    wx.getSystemInfo({
      success: res => {
        this.globalData.systemInfo = res
      }
    })
  }
})
