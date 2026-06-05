# 智能记账微信小程序

这是一个微信小程序 + Flask 后端组成的智能记账项目。小程序端负责记账、展示和统计，Flask 后端负责文本解析、语音识别和 AI 分析。

## 主要功能

- 一句话记账：输入自然语言，例如“午饭花了25”“工资到账5000”。
- 语音记账：录音后识别文字，并自动解析账单。
- 收入 / 支出识别：支持区分收入和支出。
- 账单管理：支持查看、编辑、删除账单。
- 按月统计：按月份查看收入、支出、结余和分类统计。
- AI 分析：对当前月份账单生成分析和建议。

## 项目结构

```text
miniprogram/                     小程序前端
  app.js                         小程序入口
  app.json                       页面注册和全局配置
  pages/index/                   首页：文本记账、语音记账、保存账单
  pages/bills/                   账单列表：展示、编辑入口、删除
  pages/edit/                    编辑账单：修改金额、分类、备注、类型
  pages/stats/                   统计页：按月统计、AI 分析
  utils/bill.js                  账单创建和默认字段逻辑
  utils/stats.js                 按月统计和分类统计逻辑

server/                          Flask 后端
  app.py                         后端接口和解析逻辑
  config.py                      API Key 配置
  test_app_logic.py              后端单元测试

tests/                           前端纯逻辑测试
  bill.test.js                   账单保存逻辑测试
  stats.test.js                  统计逻辑测试

cloudfunctions/                  云开发示例函数
project.config.json              微信开发者工具项目配置
```

## 后端接口

Flask 服务默认运行在：

```text
http://172.20.10.3:5000
```

主要接口：

- `POST /parse_bill`：解析一句话账单。
- `POST /speech_to_text`：语音转文字。
- `POST /analyze_bills`：AI 分析账单。
- `GET /test_baidu_token`：测试百度语音 token。

## 启动后端

```powershell
cd C:\Users\14624\Desktop\miaomiao\server
python app.py
```

启动成功后，保持该终端窗口打开，再到微信开发者工具中运行小程序。

如果电脑 IP 发生变化，需要同步修改小程序中的接口地址。

## 运行测试

后端测试：

```powershell
cd C:\Users\14624\Desktop\miaomiao\server
python -m unittest test_app_logic.py
```

前端纯逻辑测试：

```powershell
cd C:\Users\14624\Desktop\miaomiao
node tests\bill.test.js
node tests\stats.test.js
```

## 当前数据存储

账单数据目前保存在小程序本地缓存中：

```js
wx.setStorageSync('bills', bills)
```

每条账单主要字段：

```js
{
  id: 1710000000000,
  type: '收入',
  amount: 5000,
  category: '工资',
  remark: '工资到账5000',
  createdAt: '本地展示时间',
  date: '2026-06-05',
  month: '2026-06'
}
```

## 后续优化方向

- 将账单从本地缓存迁移到云数据库或后端数据库。
- 将接口地址抽成统一配置，避免页面中写死 IP。
- 增加账单列表的按月筛选。
- 增加预算、趋势图、分类图表等统计能力。
- 将 API Key 改为环境变量管理，避免明文写在代码中。
