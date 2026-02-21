const app = getApp()
const defaultAvatarUrl = 'https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0'

Page({
  data: {
    avatarUrl: defaultAvatarUrl,
    nickName: ''
  },

  onLoad() {
    wx.setNavigationBarTitle({
      title: '完善个人信息'
    })
  },

  onChooseAvatar(e) {
    const { avatarUrl } = e.detail
    this.setData({
      avatarUrl
    })
  },

  onNickNameInput(e) {
    this.setData({
      nickName: e.detail.value
    })
  },

  onSubmit() {
    const { nickName, avatarUrl } = this.data

    if (!nickName || nickName.trim() === '') {
      wx.showToast({
        title: '请输入昵称',
        icon: 'none'
      })
      return
    }

    const userInfo = {
      nickName: nickName,
      avatarUrl: avatarUrl
    }

    app.globalData.userInfo = userInfo
    app.globalData.nickName = nickName

    wx.setStorageSync('userInfo', userInfo)
    wx.setStorageSync('nickName', nickName)

    wx.showToast({
      title: '登录成功',
      icon: 'success',
      duration: 1500
    })

    setTimeout(() => {
      wx.navigateBack()
    }, 1500)
  }
})
