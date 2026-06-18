import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { BarChart2, Zap, Activity, Home, Menu, X } from 'lucide-react'
import './Navbar.css'

const links = [
  { to: '/',            label: 'Inicio',       icon: Home },
  { to: '/predictions', label: 'Predicciones', icon: Zap },
  { to: '/simulation',  label: 'Monte Carlo',  icon: Activity },
  { to: '/analytics',   label: 'Analytics',    icon: BarChart2 },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Logo */}
        <NavLink to="/" className="navbar-logo">
          <span className="logo-icon">⚽</span>
          <span className="logo-text">
            Sport<span className="logo-accent">Predict</span>
          </span>
          <span className="badge badge-green">Pro</span>
        </NavLink>

        {/* Desktop links */}
        <div className="navbar-links">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>

        {/* API Status */}
        <div className="navbar-status">
          <span className="status-dot" />
          <span className="status-text">API Online</span>
        </div>

        {/* Mobile toggle */}
        <button className="navbar-toggle" onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="navbar-mobile">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-link-mobile ${isActive ? 'nav-link-active' : ''}`
              }
              onClick={() => setOpen(false)}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </div>
      )}
    </nav>
  )
}
