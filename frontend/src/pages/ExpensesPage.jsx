import { useState, useEffect, useCallback } from 'react'
import { getExpenses, createExpense, updateExpense, deleteExpense, getCategories } from '../api/client'
import ExpenseFilters from '../components/ExpenseFilters'
import ExpenseForm from '../components/ExpenseForm'
import ExpenseList from '../components/ExpenseList'

const defaultFilters = {
  category: '',
  sort_by: 'date',
  order: 'desc',
  date_from: '',
  date_to: '',
}

/**
 * Expenses page — the main CRUD hub for the app.
 *
 * Orchestrates three child components:
 *   ExpenseForm    — add / edit form (dual-mode)
 *   ExpenseFilters — category, sort, and date-range controls
 *   ExpenseList    — table of results with edit/delete actions
 *
 * Filter state lives here at the page level. Changing any filter
 * triggers a fresh API call via the useEffect on `filters`. The
 * editingExpense state lifts the currently-edited row from the
 * table into the form.
 */
function ExpensesPage() {
  const [expenses, setExpenses] = useState([])
  const [categories, setCategories] = useState([])
  const [filters, setFilters] = useState(defaultFilters)
  const [editingExpense, setEditingExpense] = useState(null)
  const [loading, setLoading] = useState(true)

  /** Fetch expenses using current filters. Wrapped in useCallback so the
   *  useEffect dependency is stable (the function identity doesn't change
   *  on every render). */
  const loadExpenses = useCallback(async (f) => {
    try {
      const data = await getExpenses(f)
      setExpenses(data)
    } catch (err) {
      console.error('Failed to load expenses:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  /** Fetch categories for dropdowns. Also wrapped in useCallback for stability. */
  const loadCategories = useCallback(async () => {
    try {
      const data = await getCategories()
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }, [])

  useEffect(() => {
    loadCategories()
  }, [loadCategories])

  // Re-fetch expenses whenever filters change
  useEffect(() => {
    setLoading(true)
    loadExpenses(filters)
  }, [filters, loadExpenses])

  /** Update a single filter key without replacing the entire filters object. */
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  /** Create an expense, refresh categories (in case a new one was added via
   *  AddCategory), and re-fetch the expense list with current filters. */
  const handleAddExpense = async (data) => {
    await createExpense(data)
    await loadCategories()
    loadExpenses(filters)
  }

  /** Update an expense, clear edit mode, refresh data. */
  const handleUpdateExpense = async (id, data) => {
    await updateExpense(id, data)
    setEditingExpense(null)
    await loadCategories()
    loadExpenses(filters)
  }

  /** Delete with a browser confirm dialog, then refresh the list. */
  const handleDeleteExpense = async (id) => {
    if (!window.confirm('Delete this expense?')) return
    await deleteExpense(id)
    loadExpenses(filters)
  }

  return (
    <div className="expenses-page">
      <h1>Expenses</h1>

      <ExpenseForm
        onSubmit={handleAddExpense}
        onUpdate={handleUpdateExpense}
        editingExpense={editingExpense}
        onCancelEdit={() => setEditingExpense(null)}
        categories={categories}
        onCategoryAdded={loadCategories}
      />

      <ExpenseFilters
        filters={filters}
        onChange={handleFilterChange}
        categories={categories}
      />

      {loading ? (
        <p>Loading...</p>
      ) : (
        <ExpenseList
          expenses={expenses}
          onEdit={setEditingExpense}
          onDelete={handleDeleteExpense}
          categories={categories}
        />
      )}
    </div>
  )
}

export default ExpensesPage
