import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Zap, Activity, BarChart2, TrendingUp, Database, Shield } from 'lucide-react'
import { healthCheck, getLeagues } from '../services/api'
import './Home.css'

const features = [
  {
    icon: Zap,
    title: 'Predicciones ML',
    desc: 'Ensemble de Poisson + Random Forest + XGBoost + LightGBM para máxima precisión.',
    color: '#00d68f',
    link: '/predictions',
  },
  {
    icon: Activity,
    title: 'Monte Carlo',
    desc: '10,000 simulaciones por partido. Probabilidades calibradas para mercados reales.',
    color: '#4f9ef8',
    link: '/simulation',
  },
  {
    icon: BarChart2,
    title: 'Analytics',
    desc: 'Métricas de evaluación: Accuracy, Log Loss, Brier Score y ROI teórico.',
    color: '#7c3aed',
    link: '/analytics',
  },
  {
    icon: TrendingUp,
    title: 'Forma Reciente',
    desc: 'Analiza los últimos 5 partidos: puntos, goles, rachas local/visitante.',
    color: '#f59e0b',
    link: '/predictions',
  },
  {
    icon: Database,
    title: 'Datos Históricos',
    desc: 'Premier League, La Liga, Bundesliga. Datos desde 2021 sin registro.',
    color: '#00d68f',
    link: '/predictions',
  },
  {
    icon: Shield,
    title: 'Open Source',
    desc: 'FastAPI + React + Docker. Arquitectura profesional lista para portafolio.',
    color: '#4f9ef8',
    link: '/',
  },
]

const stats = [
  { label: 'Partidos analizados', value: '8,000+' },
  { label: 'Ligas cubiertas', value: '3' },
  { label: 'Temporadas', value: '3' },
  { label: 'Simulaciones / partido', value: '10,000' },
]

export default function Home() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [leagues, setLeagues] = useState([])

  useEffect(() => {
    healthCheck()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'))

    getLeagues()
      .then(setLeagues)
      .catch(() => setLeagues([]))
  }, [])

  return (
    <div className="home">
      {/* Hero */}
      <section className="hero animate-fade-up">
        <div className="hero-badge">
          <span className="status-dot" style={{ display: 'inline-block' }} />
          API {apiStatus === 'online' ? '✓ Online' : apiStatus === 'offline' ? '✗ Offline' : '... Conectando'}
        </div>

        <h1 className="hero-title">
          Predicción Deportiva
          <br />
          <span className="gradient-text">con Machine Learning</span>
        </h1>

        <p className="hero-desc">
          Plataforma profesional que combina Poisson, Random Forest, XGBoost y LightGBM
          con simulación Monte Carlo de 10,000 iteraciones para predecir partidos de fútbol.
        </p>

        <div className="hero-actions">
          <Link to="/predictions" className="btn btn-primary">
            <Zap size={18} />
            Hacer Predicción
          </Link>
          <Link to="/simulation" className="btn btn-outline">
            <Activity size={18} />
            Simular Partido
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="stats-grid">
        {stats.map((s, i) => (
          <div key={i} className="stat-card card">
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* Ligas disponibles */}
      {leagues.length > 0 && (
        <section className="leagues-section">
          <h2 className="section-title">Ligas Disponibles</h2>
          <div className="leagues-grid">
            {leagues.map((l) => (
              <div key={l.code} className="league-chip">
                <span className="league-flag">
                  {l.code === 'E0' ? '🏴󠁧󠁢󠁥󠁮󠁧󠁿' : l.code === 'SP1' ? '🇪🇸' : l.code === 'D1' ? '🇩🇪' : '⚽'}
                </span>
                {l.name}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Feature cards */}
      <section>
        <h2 className="section-title">Características</h2>
        <div className="features-grid">
          {features.map(({ icon: Icon, title, desc, color, link }, i) => (
            <Link to={link} key={i} className="feature-card card" style={{ '--accent': color }}>
              <div className="feature-icon" style={{ background: `${color}20`, color }}>
                <Icon size={22} />
              </div>
              <h3 className="feature-title">{title}</h3>
              <p className="feature-desc">{desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section className="tech-section card">
        <h2 className="section-title" style={{ marginBottom: '1rem' }}>Stack Tecnológico</h2>
        <div className="tech-tags">
          {['Python 3.11', 'FastAPI', 'XGBoost', 'LightGBM', 'scikit-learn',
            'Monte Carlo', 'React 18', 'Recharts', 'SQLite', 'Docker', 'GitHub Actions'].map((t) => (
            <span key={t} className="tech-tag">{t}</span>
          ))}
        </div>
      </section>
    </div>
  )
}
