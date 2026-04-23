Page({
  data: {
    text: '',
    parsed: null,
    audioPath: '',
    recognizedText: '',
    recentBills: []
  },

  onTextInput(e) {
    this.setData({
      text: e.detail.value
    })
  },

  onShow() {
    const bills = wx.getStorageSync('bills') || []
  
    this.setData({
      recentBills: bills.slice(0, 3)
    })
  },

  goParse() {
    const text = this.data.text.trim()

    if (!text) {
      wx.showToast({
        title: '先输入一句话',
        icon: 'none'
      })
      return
    }

    wx.request({
      url: 'http://172.20.10.3:5000/parse_bill',
      method: 'POST',
      data: {
        text: text
      },
      success: (res) => {
        const result = res.data

        if (result.success) {
          this.setData({
            parsed: result.data
          })
        } else {
          wx.showToast({
            title: result.message || '解析失败',
            icon: 'none'
          })
        }
      },
      fail: () => {
        wx.showToast({
          title: '请求后端失败',
          icon: 'none'
        })
      }
    })
  },

  startRecord() {
    const recorderManager = wx.getRecorderManager()

    recorderManager.start({
      duration: 60000,
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 96000,
      format: 'mp3'
    })

    wx.showToast({
      title: '开始录音',
      icon: 'none'
    })
  },

  stopRecord() {
    const recorderManager = wx.getRecorderManager()

    recorderManager.stop()

    recorderManager.onStop((res) => {
      console.log('录音文件路径:', res.tempFilePath)

      this.setData({
        audioPath: res.tempFilePath
      })

      wx.showToast({
        title: '录音完成',
        icon: 'success'
      })
    })
  },

  recognizeAudio() {
    const audioPath = this.data.audioPath

    if (!audioPath) {
      wx.showToast({
        title: '请先录音',
        icon: 'none'
      })
      return
    }

    wx.uploadFile({
      url: 'http://172.20.10.3:5000/speech_to_text',
      filePath: audioPath,
      name: 'file',
      success: (res) => {
        const result = JSON.parse(res.data)

        if (result.success) {
          const text = (result.text || '').trim()

          this.setData({
            text: text,
            recognizedText: text
          })

          wx.request({
            url: 'http://172.20.10.3:5000/parse_bill',
            method: 'POST',
            data: {
              text: text
            },
            success: (parseRes) => {
              const parseResult = parseRes.data

              if (parseResult.success) {
                this.setData({
                  parsed: parseResult.data
                })

                wx.showToast({
                  title: '识别并解析成功',
                  icon: 'success'
                })
              } else {
                wx.showToast({
                  title: parseResult.message || '解析失败',
                  icon: 'none'
                })
              }
            },
            fail: () => {
              wx.showToast({
                title: '解析请求失败',
                icon: 'none'
              })
            }
          })
        } else {
          wx.showToast({
            title: result.message || '识别失败',
            icon: 'none'
          })
        }
      },
      fail: () => {
        wx.showToast({
          title: '上传失败',
          icon: 'none'
        })
      }
    })
  },

  saveBill() {
    const parsed = this.data.parsed
    if (!parsed) return

    const bills = wx.getStorageSync('bills') || []

    bills.unshift({
      id: Date.now(),
      ...parsed,
      createdAt: new Date().toLocaleString()
    })

    wx.setStorageSync('bills', bills)

    wx.setStorageSync('bills', bills)

wx.showToast({
  title: '保存成功',
  icon: 'success'
})

this.setData({
  text: '',
  parsed: null,
  audioPath: '',
  recognizedText: '',
  recentBills: bills.slice(0, 3)
})
  },

  goBills() {
    wx.navigateTo({
      url: '/pages/bills/index'
    })
  },

  goStats() {
    wx.navigateTo({
      url: '/pages/stats/index'
    })
  }
})