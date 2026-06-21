/**
 * Expense table — renders the list of expenses with edit and delete actions.
 *
 * Each row shows name, category (as a colored tag), amount, date, and notes.
 * Notes are truncated with ellipsis for long text. The Edit button lifts the
 * expense into the parent's editingExpense state; Delete triggers a browser
 * confirm dialog before removing.
 *
 * Empty state: when there are no expenses, renders a friendly message instead
 * of an empty table.
 */
function ExpenseList({ expenses, onEdit, onDelete }) {
  if (expenses.length === 0) {
    return <p className="empty-message">No expenses found. Add one above!</p>
  }

  return (
    <table className="expense-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Category</th>
          <th>Amount</th>
          <th>Date</th>
          <th>Notes</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {expenses.map(e => (
          <tr key={e.id}>
            <td>{e.name}</td>
            <td><span className="category-tag">{e.category}</span></td>
            <td>${e.amount.toFixed(2)}</td>
            <td>{e.date}</td>
            <td className="notes-cell">{e.notes}</td>
            <td className="actions-cell">
              <button className="btn-small" onClick={() => onEdit(e)}>Edit</button>
              <button className="btn-small btn-danger" onClick={() => onDelete(e.id)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default ExpenseList
