/**
 * Filter and sort controls for the expenses list.
 *
 * Renders a horizontal bar with:
 *   - Category dropdown (with "All" option)
 *   - Sort-by dropdown (date / amount / category)
 *   - Sort-order toggle button (↑ Asc / ↓ Desc)
 *   - Date range inputs (from / to)
 *
 * This component is "controlled" — all state lives in the parent
 * (ExpensesPage). Every change calls onChange(key, value) which
 * updates a single filter key without replacing the whole object,
 * so the other filters are preserved.
 */
function ExpenseFilters({ filters, onChange, categories }) {
  return (
    <div className="filters-bar">
      <select
        value={filters.category}
        onChange={e => onChange('category', e.target.value)}
      >
        <option value="">All Categories</option>
        {categories.map(c => (
          <option key={c.id} value={c.name}>{c.name}</option>
        ))}
      </select>

      <select
        value={filters.sort_by}
        onChange={e => onChange('sort_by', e.target.value)}
      >
        <option value="date">Sort by Date</option>
        <option value="amount">Sort by Amount</option>
        <option value="category">Sort by Category</option>
      </select>

      <button
        className="btn-small"
        onClick={() => onChange('order', filters.order === 'asc' ? 'desc' : 'asc')}
        title="Toggle sort order"
      >
        {filters.order === 'asc' ? '↑ Asc' : '↓ Desc'}
      </button>

      <input
        type="date"
        placeholder="From"
        value={filters.date_from}
        onChange={e => onChange('date_from', e.target.value)}
      />
      <input
        type="date"
        placeholder="To"
        value={filters.date_to}
        onChange={e => onChange('date_to', e.target.value)}
      />
    </div>
  )
}

export default ExpenseFilters
