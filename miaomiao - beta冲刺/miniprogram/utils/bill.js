const EXPENSE_TYPE = '支出'

function formatDatePart(value) {
  return value < 10 ? '0' + value : String(value)
}

function formatDate(date) {
  const year = date.getFullYear()
  const month = formatDatePart(date.getMonth() + 1)
  const day = formatDatePart(date.getDate())

  return year + '-' + month + '-' + day
}

function formatMonth(date) {
  const year = date.getFullYear()
  const month = formatDatePart(date.getMonth() + 1)

  return year + '-' + month
}

function normalizeBill(item) {
  return {
    ...item,
    type: item.type || EXPENSE_TYPE
  }
}

function createBill(parsed, now, id) {
  const date = now || new Date()

  return normalizeBill({
    id: id || Date.now(),
    ...parsed,
    createdAt: date.toLocaleString(),
    date: formatDate(date),
    month: formatMonth(date)
  })
}

module.exports = {
  EXPENSE_TYPE,
  formatDatePart,
  formatDate,
  formatMonth,
  normalizeBill,
  createBill
}
