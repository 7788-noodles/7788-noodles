const assert = require('assert')
const billUtils = require('../miniprogram/utils/bill')

function testFormatDateAndMonth() {
  const date = new Date('2026-06-05T08:30:00')

  assert.strictEqual(billUtils.formatDate(date), '2026-06-05')
  assert.strictEqual(billUtils.formatMonth(date), '2026-06')
}

function testNormalizeBillDefaultsToExpense() {
  const bill = billUtils.normalizeBill({
    amount: 25,
    category: '餐饮',
    remark: '午饭'
  })

  assert.strictEqual(bill.type, '支出')
  assert.strictEqual(bill.amount, 25)
  assert.strictEqual(bill.category, '餐饮')
  assert.strictEqual(bill.remark, '午饭')
}

function testNormalizeBillKeepsIncomeType() {
  const bill = billUtils.normalizeBill({
    type: '收入',
    amount: 5000,
    category: '工资',
    remark: '工资到账'
  })

  assert.strictEqual(bill.type, '收入')
  assert.strictEqual(bill.amount, 5000)
}

function testCreateBillAddsStableDateFields() {
  const date = new Date('2026-06-05T08:30:00')
  const bill = billUtils.createBill({
    type: '收入',
    amount: 5000,
    category: '工资',
    remark: '工资到账'
  }, date, 123)

  assert.strictEqual(bill.id, 123)
  assert.strictEqual(bill.type, '收入')
  assert.strictEqual(bill.amount, 5000)
  assert.strictEqual(bill.category, '工资')
  assert.strictEqual(bill.remark, '工资到账')
  assert.strictEqual(bill.date, '2026-06-05')
  assert.strictEqual(bill.month, '2026-06')
  assert.ok(bill.createdAt)
}

function testCreateBillDefaultsMissingTypeToExpense() {
  const date = new Date('2026-06-05T08:30:00')
  const bill = billUtils.createBill({
    amount: 25,
    category: '餐饮',
    remark: '午饭'
  }, date, 456)

  assert.strictEqual(bill.id, 456)
  assert.strictEqual(bill.type, '支出')
  assert.strictEqual(bill.date, '2026-06-05')
  assert.strictEqual(bill.month, '2026-06')
}

function run() {
  testFormatDateAndMonth()
  testNormalizeBillDefaultsToExpense()
  testNormalizeBillKeepsIncomeType()
  testCreateBillAddsStableDateFields()
  testCreateBillDefaultsMissingTypeToExpense()
  console.log('bill tests passed')
}

run()
