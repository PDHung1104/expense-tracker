import { useState, useEffect } from 'react'
import { getExpenses } from '../api/client'

/**
 * Dashboard page — monthly spending overview.
 *
 * Fetches the current month's expenses and computes summary statistics
 * client-side (total spent, expense count, top category by amount).
 * This avoids a dedicated summary API endpoint — the data set for a
 * single user is small enough that computing on the client is fine.
 *
 * The placeholder chart section is where interactive charts (spending
 * over time, category breakdowns) will be added in a future phase.
 */
function DashboardPage() {
  const [summary, setSummary] = useState({ total: 0, count: 0, topCategory: null })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSummary()
  }, [])

  /** Fetch this month's expenses and compute totals client-side. */
  const loadSummary = async () => {
    try {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const dateFrom = `${year}-${month}-01`
      const dateTo = `${year}-${month}-31`

      const expenses = await getExpenses({ date_from: dateFrom, date_to: dateTo })
      const total = expenses.reduce((sum, e) => sum + e.amount, 0)
      const count = expenses.length

      // Top category this month — aggregate by category, pick max
      const byCategory = {}
      expenses.forEach(e => {
        byCategory[e.category] = (byCategory[e.category] || 0) + e.amount
      })
      let topCategory = null
      let topAmount = 0
      Object.entries(byCategory).forEach(([cat, amt]) => {
        if (amt > topAmount) { topCategory = cat; topAmount = amt }
      })

      setSummary({ total, count, topCategory })
    } catch (err) {
      console.error('Failed to load dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <p>Loading dashboard...</p>

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      <div className="summary-cards">
        <div className="card">
          <h3>This Month</h3>
          <p className="big-number">${summary.total.toFixed(2)}</p>
          <p className="sub">{summary.count} expenses</p>
        </div>
        <div className="card">
          <h3>Top Category</h3>
          {summary.topCategory ? (
            <>
              <p className="big-number">{summary.topCategory}</p>
            </>
          ) : (
            <p className="sub">No expenses yet</p>
          )}
        </div>
      </div>
      <div className="placeholder-chart">
        <p>📊 Charts coming soon — more dashboard features will be added here.</p>
      </div>
    </div>
  )
}

export default DashboardPage
