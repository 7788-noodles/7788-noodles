Page({
  data: {
    id: '',
    amount: '',
    category: '',
    remark: ''
  },

  onLoad(options) {
    this.setData({
      id: options.id || '',
      amount: options.amount || '',
      category: options.category || '',
      remark: options.remark || ''
    })
  },

  onAmountInput(e) {
    this.setData({
      amount: e.detail.value
    })
  },

  onCategoryInput(e) {
    this.setData({
      category: e.detail.value
    })
  },

  onRemarkInput(e) {
    this.setData({
      remark: e.detail.value
    })
  },

  saveEdit() {
    const { id, amount, category, remark } = this.data

    if (!amount || !category || !remark) {
      wx.showToast({
        title: '请把内容填完整',
        icon: 'none'
      })
      return
    }

    const bills = wx.getStorageSync('bills') || []

    const newBills = bills.map(item => {
      if (String(item.id) === String(id)) {
        return {
          ...item,
          amount: Number(amount),
          category,
          remark
        }
      }
      return item
    })

    wx.setStorageSync('bills', newBills)

    wx.showToast({
      title: '修改成功',
      icon: 'success'
    })

    setTimeout(() => {
      wx.navigateBack()
    }, 600)
  }
})