Page({
  data: {},

  onLoad() {
    wx.setNavigationBarTitle({
      title: '首页'
    })
  },

  goToAnalyze() {
    wx.switchTab({
      url: '/pages/analyze/analyze'
    })
  }
})
