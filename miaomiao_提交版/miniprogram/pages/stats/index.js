Page({
  data: {
    totalAmount: 0,
    billCount: 0,
    categoryStats: [],
    aiAnalysis: '',
    aiSuggestion: '',
    isAnalyzing: false,
    hasAnalyzed: false
  },

  onShow() {
    const bills = wx.getStorageSync('bills') || []

    const totalAmount = bills.reduce((sum, item) => {
      return sum + Number(item.amount || 0)
    }, 0)

    const categoryMap = {}

    bills.forEach(item => {
      const category = item.category || '其他'
      const amount = Number(item.amount || 0)

      if (!categoryMap[category]) {
        categoryMap[category] = 0
      }

      categoryMap[category] += amount
    })

    const categoryStats = Object.keys(categoryMap)
  .map(category => {
    const rawAmount = categoryMap[category]
    const percent = totalAmount > 0 ? (rawAmount / totalAmount) * 100 : 0

    return {
      category,
      amount: rawAmount.toFixed(2),
      rawAmount,
      percent: percent.toFixed(1),
      percentWidth: 'width: ' + percent.toFixed(1) + '%'
    }
  })
  .sort((a, b) => b.rawAmount - a.rawAmount)

categoryStats.forEach(item => {
  delete item.rawAmount
})

    this.setData({
      totalAmount: totalAmount.toFixed(2),
      billCount: bills.length,
      categoryStats
    })
  },
  testAnalyze() {
    const bills = wx.getStorageSync('bills') || []
  
    if (this.data.isAnalyzing) return
  
    this.setData({
      isAnalyzing: true
    })
  
    wx.request({
      url: 'http://172.20.10.3:5000/analyze_bills',
      method: 'POST',
      data: {
        bills: bills
      },
      success: (res) => {
        console.log('分析接口返回：', res.data)
  
        if (res.data.success) {
          this.setData({
            aiAnalysis: res.data.data.analysis || '',
            aiSuggestion: res.data.data.suggestion || '',
            hasAnalyzed: true
          })
  
          wx.showToast({
            title: '分析生成成功',
            icon: 'success'
          })
        } else {
          wx.showToast({
            title: res.data.message || '分析失败',
            icon: 'none'
          })
        }
      },
      fail: () => {
        wx.showToast({
          title: '请求分析接口失败',
          icon: 'none'
        })
      },
      complete: () => {
        this.setData({
          isAnalyzing: false
        })
      }
    })
  }
})