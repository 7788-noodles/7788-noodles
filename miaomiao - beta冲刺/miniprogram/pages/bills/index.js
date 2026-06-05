Page({
  data: {
    bills: []
  },

  onShow() {
    const bills = wx.getStorageSync('bills') || []
    this.setData({
      bills: bills.map(item => ({
        ...item,
        type: item.type || '支出'
      }))
    })
  },
  
  goEdit(e) {
    const { id, type, amount, category, remark } = e.currentTarget.dataset
  
    wx.navigateTo({
      url: `/pages/edit/index?id=${id}&type=${type || '支出'}&amount=${amount}&category=${category}&remark=${remark}`
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
