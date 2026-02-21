App({
  globalData: {
    userInfo: null,
    baseUrl: 'https://706e6893.r16.vip.cpolar.cn'
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
