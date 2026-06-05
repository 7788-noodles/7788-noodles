const stats = require('../../utils/stats')

Page({
  data: {
    totalAmount: 0,
    totalIncome: 0,
    totalExpense: 0,
    balance: 0,
    billCount: 0,
    categoryStats: [],
    incomeCategoryStats: [],
    expenseCategoryStats: [],
    monthOptions: [],
    selectedMonth: '',
    selectedMonthIndex: 0,
    currentBills: [],
    aiAnalysis: '',
    aiSuggestion: '',
    isAnalyzing: false,
    hasAnalyzed: false
  },

  onShow() {
    const bills = wx.getStorageSync('bills') || []

    this.setData(stats.buildMonthView(bills, this.data.selectedMonth))
  },

  onMonthChange(e) {
    const index = Number(e.detail.value)
    const selectedMonth = this.data.monthOptions[index]

    if (!selectedMonth) return

    const bills = wx.getStorageSync('bills') || []
    const viewData = stats.buildMonthView(bills, selectedMonth)

    this.setData({
      ...viewData,
      aiAnalysis: '',
      aiSuggestion: '',
      hasAnalyzed: false
    })
  },

  testAnalyze() {
    const bills = this.data.currentBills || []

    if (this.data.isAnalyzing) return

    this.setData({
      isAnalyzing: true
    })

    wx.request({
      url: 'http://172.20.10.3:5000/analyze_bills',
      method: 'POST',
      data: {
        month: this.data.selectedMonth,
        bills
      },
      success: (res) => {
        console.log('AI 分析结果：', res.data)

        if (res.data.success) {
          this.setData({
            aiAnalysis: res.data.data.analysis || '',
            aiSuggestion: res.data.data.suggestion || '',
            hasAnalyzed: true
          })

          wx.showToast({
            title: 'AI 分析完成',
            icon: 'success'
          })
        } else {
          wx.showToast({
            title: res.data.message || 'AI 分析失败',
            icon: 'none'
          })
        }
      },
      fail: () => {
        wx.showToast({
          title: 'AI 分析请求失败',
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
