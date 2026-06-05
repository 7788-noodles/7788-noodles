const assert = require('assert')
const stats = require('../miniprogram/utils/stats')

function testMonthOptionsIncludeCurrentMonth() {
  const view = stats.buildMonthView([], '', new Date('2026-06-05T00:00:00'))

  assert.deepStrictEqual(view.monthOptions, ['2026-06'])
  assert.strictEqual(view.selectedMonth, '2026-06')
  assert.strictEqual(view.billCount, 0)
}

function testBillMonthFallbacks() {
  assert.strictEqual(stats.getBillMonth({ month: '2026-05' }), '2026-05')
  assert.strictEqual(stats.getBillMonth({ date: '2026-04-12' }), '2026-04')
  assert.strictEqual(stats.getBillMonth({ createdAt: '2026/3/8 12:00:00' }), '2026-03')
  assert.strictEqual(
    stats.getBillMonth({ id: new Date('2026-02-01T00:00:00').getTime() }),
    '2026-02'
  )
  assert.strictEqual(stats.getBillMonth({}, new Date('2026-01-01T00:00:00')), '2026-01')
}

function testMonthlyIncomeExpenseStats() {
  const bills = [
    { type: '收入', amount: 5000, category: '工资', month: '2026-06' },
    { type: '收入', amount: 300, category: '兼职', month: '2026-06' },
    { type: '支出', amount: 25, category: '餐饮', month: '2026-06' },
    { type: '支出', amount: 100, category: '购物', month: '2026-06' },
    { type: '支出', amount: 80, category: '餐饮', month: '2026-05' }
  ]

  const result = stats.calculateStats(bills, '2026-06')

  assert.strictEqual(result.totalIncome, '5300.00')
  assert.strictEqual(result.totalExpense, '125.00')
  assert.strictEqual(result.balance, '5175.00')
  assert.strictEqual(result.billCount, 4)
  assert.strictEqual(result.incomeCategoryStats.length, 2)
  assert.strictEqual(result.expenseCategoryStats.length, 2)
  assert.strictEqual(result.expenseCategoryStats[0].category, '购物')
  assert.strictEqual(result.expenseCategoryStats[0].amount, '100.00')
}

function testOldBillsDefaultToExpense() {
  const bills = [
    { amount: 50, category: '餐饮', month: '2026-06' },
    { type: '收入', amount: 100, category: '红包', month: '2026-06' }
  ].map(item => stats.normalizeBill(item, new Date('2026-06-05T00:00:00')))

  const result = stats.calculateStats(bills, '2026-06')

  assert.strictEqual(result.totalIncome, '100.00')
  assert.strictEqual(result.totalExpense, '50.00')
  assert.strictEqual(result.balance, '50.00')
  assert.strictEqual(result.expenseCategoryStats[0].category, '餐饮')
}

function run() {
  testMonthOptionsIncludeCurrentMonth()
  testBillMonthFallbacks()
  testMonthlyIncomeExpenseStats()
  testOldBillsDefaultToExpense()
  console.log('stats tests passed')
}

run()
