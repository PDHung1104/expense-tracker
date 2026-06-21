import { useState, useEffect } from 'react'
import { createCategory } from '../api/client'
import AddCategory from './AddCategory'

const emptyForm = { name: '', notes: '', category: '', amount: '', date: '' }

/**
 * Dual-purpose expense form — handles both creating and editing.
 *
 * When editingExpense is null, the form is in "add" mode: fields start
 * empty and submit calls onSubmit (create). When editingExpense is set
 * (user clicked "Edit" in the table), the form pre-fills with that
 * expense's data and submit calls onUpdate (partial update).
 *
 * Includes an inline AddCategory component so users can create a new
 * category without navigating away from this form.
 */
function ExpenseForm({ onSubmit, onUpdate, editingExpense, onCancelEdit, categories, onCategoryAdded }) {
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')

  // Sync form fields when editingExpense changes (entering/exiting edit mode)
  useEffect(() => {
    if (editingExpense) {
      setForm({
        name: editingExpense.name,
        notes: editingExpense.notes,
        category: editingExpense.category,
        amount: String(editingExpense.amount),
        date: editingExpense.date,
      })
    } else {
      setForm(emptyForm)
    }
  }, [editingExpense])

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
    setError('')
  }

  /** Validate required fields, then delegate to the appropriate parent handler
   *  (onSubmit for create, onUpdate for edit). */
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const payload = {
      name: form.name.trim(),
      notes: form.notes.trim(),
      category: form.category,
      amount: parseFloat(form.amount),
      date: form.date,
    }

    if (!payload.name || !payload.category || !payload.amount || !payload.date) {
      setError('Name, category, amount, and date are required.')
      return
    }

    try {
      if (editingExpense) {
        await onUpdate(editingExpense.id, payload)
      } else {
        await onSubmit(payload)
      }
      setForm(emptyForm)
    } catch (err) {
      setError(err.message)
    }
  }

  /** Called by AddCategory when a new category is created. Persists it to the
   *  backend and tells the parent page to refresh its category list so the new
   *  category appears in dropdowns immediately. */
  const handleCategoryAdded = async (name) => {
    await createCategory({ name })
    if (onCategoryAdded) onCategoryAdded()
  }

  const isEditing = !!editingExpense

  return (
    <div className="expense-form-card">
      <h3>{isEditing ? 'Edit Expense' : 'Add Expense'}</h3>
      {error && <p className="error-message">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <input
            name="name"
            placeholder="Name"
            value={form.name}
            onChange={handleChange}
            required
          />
          <input
            name="amount"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="Amount"
            value={form.amount}
            onChange={handleChange}
            required
          />
          <input
            name="date"
            type="date"
            value={form.date}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-row">
          <select name="category" value={form.category} onChange={handleChange} required>
            <option value="">-- Category --</option>
            {categories.map(c => (
              <option key={c.id} value={c.name}>{c.name}</option>
            ))}
          </select>
          <input
            name="notes"
            placeholder="Notes (optional)"
            value={form.notes}
            onChange={handleChange}
          />
        </div>
        <AddCategory onAdd={handleCategoryAdded} />
        <div className="form-actions">
          <button type="submit" className="btn-primary">
            {isEditing ? 'Update' : 'Add'}
          </button>
          {isEditing && (
            <button type="button" className="btn-secondary" onClick={onCancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

export default ExpenseForm
