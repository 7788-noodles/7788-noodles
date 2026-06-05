const INCOME_TYPE = '收入'
const EXPENSE_TYPE = '支出'
const DEFAULT_CATEGORY = '其他'

function formatDatePart(value) {
  return value < 10 ? '0' + value : String(value)
}

function getCurrentMonth(now) {
  const date = now || new Date()
  return date.getFullYear() + '-' + formatDatePart(date.getMonth() + 1)
}

function getBillMonth(item, now) {
  if (item.month) return item.month
  if (item.date && item.date.length >= 7) return item.date.slice(0, 7)

  if (item.createdAt) {
    const match = String(item.createdAt).match(/(\d{4})[/-](\d{1,2})/)
    if (match) {
      return match[1] + '-' + formatDatePart(Number(match[2]))
    }
  }

  if (item.id) {
    const date = new Date(Number(item.id))
    if (!isNaN(date.getTime())) {
      return date.getFullYear() + '-' + formatDatePart(date.getMonth() + 1)
    }
  }

  return getCurrentMonth(now)
}

function normalizeBill(item, now) {
  return {
    ...item,
    type: item.type || EXPENSE_TYPE,
    month: getBillMonth(item, now)
  }
}

function buildMonthOptions(normalizedBills, currentMonth) {
  return Array.from(new Set([
    currentMonth,
    ...normalizedBills.map(item => item.month)
  ]))
    .filter(Boolean)
    .sort()
    .reverse()
}

function resolveSelectedMonth(monthOptions, selectedMonth, currentMonth) {
  if (!selectedMonth || monthOptions.indexOf(selectedMonth) === -1) {
    return monthOptions.indexOf(currentMonth) !== -1 ? currentMonth : (monthOptions[0] || currentMonth)
  }

  return selectedMonth
}

function buildCategoryStats(categoryMap, totalAmount) {
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

  return categoryStats
}

function calculateStats(bills, selectedMonth) {
  const currentBills = bills.filter(item => item.month === selectedMonth)

  const totalIncome = currentBills.reduce((sum, item) => {
    if (item.type !== INCOME_TYPE) return sum
    return sum + Number(item.amount || 0)
  }, 0)

  const totalExpense = currentBills.reduce((sum, item) => {
    if (item.type === INCOME_TYPE) return sum
    return sum + Number(item.amount || 0)
  }, 0)

  const incomeCategoryMap = {}
  const expenseCategoryMap = {}

  currentBills.forEach(item => {
    const category = item.category || DEFAULT_CATEGORY
    const amount = Number(item.amount || 0)
    const targetMap = item.type === INCOME_TYPE ? incomeCategoryMap : expenseCategoryMap

    if (!targetMap[category]) {
      targetMap[category] = 0
    }

    targetMap[category] += amount
  })

  const incomeCategoryStats = buildCategoryStats(incomeCategoryMap, totalIncome)
  const expenseCategoryStats = buildCategoryStats(expenseCategoryMap, totalExpense)

  return {
    totalAmount: totalExpense.toFixed(2),
    totalIncome: totalIncome.toFixed(2),
    totalExpense: totalExpense.toFixed(2),
    balance: (totalIncome - totalExpense).toFixed(2),
    billCount: currentBills.length,
    categoryStats: expenseCategoryStats,
    incomeCategoryStats,
    expenseCategoryStats,
    currentBills
  }
}

function buildMonthView(rawBills, selectedMonth, now) {
  const currentMonth = getCurrentMonth(now)
  const normalizedBills = rawBills.map(item => normalizeBill(item, now))
  const monthOptions = buildMonthOptions(normalizedBills, currentMonth)
  const resolvedMonth = resolveSelectedMonth(monthOptions, selectedMonth, currentMonth)
  const selectedMonthIndex = monthOptions.indexOf(resolvedMonth)

  return {
    monthOptions,
    selectedMonth: resolvedMonth,
    selectedMonthIndex: selectedMonthIndex >= 0 ? selectedMonthIndex : 0,
    ...calculateStats(normalizedBills, resolvedMonth)
  }
}

module.exports = {
  INCOME_TYPE,
  EXPENSE_TYPE,
  formatDatePart,
  getCurrentMonth,
  getBillMonth,
  normalizeBill,
  buildMonthOptions,
  resolveSelectedMonth,
  buildCategoryStats,
  calculateStats,
  buildMonthView
}
