import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Predictions from './pages/Predictions'
import Simulation from './pages/Simulation'
import Analytics from './pages/Analytics'
import './App.css'

export default function App() {
  return (
    <div className="app-wrapper">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/"            element={<Home />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/simulation"  element={<Simulation />} />
          <Route path="/analytics"   element={<Analytics />} />
        </Routes>
      </main>
    </div>
  )
}
