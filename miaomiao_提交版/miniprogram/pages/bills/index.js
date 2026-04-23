Page({
  data: {
    bills: []
  },

  onShow() {
    const bills = wx.getStorageSync('bills') || []
    this.setData({
      bills
    })
  },
  
  goEdit(e) {
    const { id, amount, category, remark } = e.currentTarget.dataset
  
    wx.navigateTo({
      url: `/pages/edit/index?id=${id}&amount=${amount}&category=${category}&remark=${remark}`
    })
  },

  deleteBill(e) {
    const id = e.currentTarget.dataset.id
    const bills = this.data.bills || []

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条账单吗？',
      success: (res) => {
        if (res.confirm) {
          const newBills = bills.filter(item => item.id !== id)

          wx.setStorageSync('bills', newBills)
          this.setData({
            bills: newBills
          })

          wx.showToast({
            title: '删除成功',
            icon: 'success'
          })
        }
      }
    })
  }
})