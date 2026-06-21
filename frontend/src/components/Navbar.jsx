import { Link, useLocation } from 'react-router-dom'

/**
 * Top navigation bar — rendered on every page by App.jsx.
 *
 * Displays the app name and two navigation links (Dashboard, Expenses).
 * The link matching the current route gets an "active" CSS class for
 * visual highlighting, determined by comparing location.pathname.
 */
function Navbar() {
  const location = useLocation()

  return (
    <nav className="navbar">
      <span className="navbar-brand">💰 Expense Tracker</span>
      <div className="navbar-links">
        <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
          Dashboard
        </Link>
        <Link to="/expenses" className={location.pathname === '/expenses' ? 'active' : ''}>
          Expenses
        </Link>
      </div>
    </nav>
  )
}

export default Navbar
