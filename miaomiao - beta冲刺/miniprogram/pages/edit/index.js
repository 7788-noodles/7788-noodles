Page({
  data: {
    id: '',
    type: '支出',
    amount: '',
    category: '',
    remark: ''
  },

  onLoad(options) {
    this.setData({
      id: options.id || '',
      type: options.type || '支出',
      amount: options.amount || '',
      category: options.category || '',
      remark: options.remark || ''
    })
  },

  onTypeChange(e) {
    this.setData({
      type: e.currentTarget.dataset.type
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
    const { id, type, amount, category, remark } = this.data

    if (!type || !amount || !category || !remark) {
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
          type,
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
