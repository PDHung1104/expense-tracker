import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import DashboardPage from './pages/DashboardPage'
import ExpensesPage from './pages/ExpensesPage'

/**
 * Root application component.
 *
 * Renders the Navbar on every page and defines the two main routes:
 *   /          → Dashboard (monthly summary)
 *   /expenses  → Expenses page (full CRUD with filters)
 *
 * When auth is added, this is where the auth gate (checking /api/auth/me
 * on mount and conditionally rendering login vs. app routes) will live.
 */
function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/expenses" element={<ExpensesPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
