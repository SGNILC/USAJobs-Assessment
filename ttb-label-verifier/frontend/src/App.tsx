import { Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ReviewPage from './pages/ReviewPage'
import BatchPage from './pages/BatchPage'

function App() {
  return (
    <div>
      <header className="border-b border-gray-200 px-6 py-4">
        <nav className="mx-auto flex max-w-6xl items-center gap-6 text-lg font-semibold">
          <Link to="/">TTB Label Verifier</Link>
          <Link to="/review">Review</Link>
          <Link to="/batch">Batch</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/batch" element={<BatchPage />} />
      </Routes>
    </div>
  )
}

export default App
