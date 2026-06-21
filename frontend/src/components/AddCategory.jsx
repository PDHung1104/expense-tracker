import { useState } from 'react'

/**
 * Inline "add category" form — embedded inside ExpenseForm.
 *
 * Starts as a subtle "+ Add new category" link. Clicking it expands into
 * an inline text input with Add and Cancel buttons. This keeps the user
 * on the expense form without a modal or page navigation.
 *
 * On success, the input clears and collapses back to the link. On error
 * (e.g. duplicate name), the error message is displayed inline.
 */
function AddCategory({ onAdd }) {
  const [name, setName] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')

  const handleAdd = async () => {
    const trimmed = name.trim()
    if (!trimmed) return
    setError('')
    try {
      await onAdd(trimmed)
      setName('')
      setAdding(false)
    } catch (err) {
      setError(err.message)
    }
  }

  if (!adding) {
    return (
      <button type="button" className="btn-link" onClick={() => setAdding(true)}>
        + Add new category
      </button>
    )
  }

  return (
    <div className="add-category-inline">
      <input
        type="text"
        placeholder="Category name"
        value={name}
        onChange={e => { setName(e.target.value); setError('') }}
      />
      <button type="button" className="btn-small" onClick={handleAdd}>Add</button>
      <button type="button" className="btn-small" onClick={() => { setAdding(false); setError('') }}>Cancel</button>
      {error && <span className="error-message">{error}</span>}
    </div>
  )
}

export default AddCategory
