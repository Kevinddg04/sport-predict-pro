import { useState, useEffect } from 'react'
import { getEvaluation } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import './Analytics.css'

const MODEL_COLORS = {
  ensemble: '#00d68f',
  xgboost: '#4f9ef8',
  lightgbm: '#7c3aed',
  random_forest: '#f59e0b',
  poisson: '#ef4444',
}

const METRIC_INFO = {
  accuracy: { label: 'Accuracy', desc: '% predicciones correctas. Baseline ~45%', higher: true },
  log_loss: { label: 'Log Loss', desc: 'Calidad de probabilidades. Menor es mejor', higher: false },
  brier_score: { label: 'Brier Score', desc: 'Error cuadrático de probabilidades. Menor es mejor', higher: false },
  accuracy_lift: { label: 'Mejora vs Baseline', desc: 'Puntos porcentuales sobre predecir siempre local', higher: true },
}

export default function Analytics() {
  const [evaluations, setEvaluations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedMetric, setSelectedMetric] = useState('accuracy')

  useEffect(() => {
    getEvaluation()
      .then((data) => { setEvaluations(data); setLoading(false) })
      .catch((err) => { setError(err.message); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="analytics-page">
      <div className="loading-state">
        <div className="spinner" />
        <p>Cargando métricas de evaluación...</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="analytics-page">
      <div className="error-state card">
        <div className="error-icon">⚠️</div>
        <h3>Modelos no entrenados</h3>
        <p>Ejecuta el pipeline de entrenamiento para ver las métricas:</p>
        <code className="cmd-block">cd backend && python -m ml.trainer</code>
      </div>
    </div>
  )

  const metricData = evaluations.map((e) => ({
    name: e.model_name.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    accuracy: +(e.accuracy * 100).toFixed(2),
    log_loss: +e.log_loss.toFixed(4),
    brier_score: +e.brier_score.toFixed(4),
    accuracy_lift: +(e.accuracy_lift * 100).toFixed(2),
    roi: e.theoretical_roi || 0,
    fill: MODEL_COLORS[e.model_name] || '#4f9ef8',
    n: e.n_samples,
  }))

  const radarData = evaluations.map((e) => ({
    model: e.model_name.replace('_', ' ').toUpperCase(),
    'Accuracy (×100)': +(e.accuracy * 100).toFixed(1),
    'Confianza': +((1 - e.brier_score) * 100).toFixed(1),
    'Log Loss Inv.': +(Math.max(0, 1.5 - e.log_loss) * 100).toFixed(0),
    'Mejora Base.': Math.max(0, +(e.accuracy_lift * 200).toFixed(1)),
  }))

  const metric = METRIC_INFO[selectedMetric]

  return (
    <div className="analytics-page">
      <div className="page-header">
        <h1>📊 Analytics de Modelos</h1>
        <p className="page-subtitle">Comparación de rendimiento de todos los modelos entrenados</p>
      </div>

      {/* Selector de métrica */}
      <div className="metric-selector card">
        <h3>Comparar por métrica</h3>
        <div className="metric-tabs">
          {Object.entries(METRIC_INFO).map(([key, val]) => (
            <button
              key={key}
              className={`metric-tab ${selectedMetric === key ? 'active' : ''}`}
              onClick={() => setSelectedMetric(key)}
            >
              {val.label}
            </button>
          ))}
        </div>
        <p className="metric-desc">ℹ️ {metric.desc}</p>

        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={metricData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
            <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
              labelStyle={{ color: 'var(--text-primary)' }}
            />
            <Bar dataKey={selectedMetric} radius={[6, 6, 0, 0]}>
              {metricData.map((e, i) => <Cell key={i} fill={e.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabla comparativa */}
      <div className="card">
        <h3>Tabla Comparativa Completa</h3>
        <div className="metrics-table-wrapper">
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Modelo</th>
                <th>Accuracy ↑</th>
                <th>vs Baseline ↑</th>
                <th>Log Loss ↓</th>
                <th>Brier Score ↓</th>
                <th>ROI Teórico</th>
                <th>Muestras</th>
              </tr>
            </thead>
            <tbody>
              {metricData
                .sort((a, b) => b.accuracy - a.accuracy)
                .map((m, i) => (
                  <tr key={i} className={m.name.toLowerCase().includes('ensemble') ? 'row-highlight' : ''}>
                    <td>
                      <span className="model-name-cell">
                        <span className="model-dot" style={{ background: m.fill }} />
                        {m.name}
                        {m.name.toLowerCase().includes('ensemble') && (
                          <span className="badge badge-green" style={{ fontSize: '0.65rem' }}>Best</span>
                        )}
                      </span>
                    </td>
                    <td className="metric-val" style={{ color: '#00d68f' }}>{m.accuracy}%</td>
                    <td className="metric-val" style={{ color: m.accuracy_lift > 0 ? '#00d68f' : '#ef4444' }}>
                      {m.accuracy_lift > 0 ? '+' : ''}{m.accuracy_lift}pp
                    </td>
                    <td className="metric-val">{m.log_loss}</td>
                    <td className="metric-val">{m.brier_score}</td>
                    <td className="metric-val" style={{ color: m.roi > 0 ? '#00d68f' : '#ef4444' }}>
                      {m.roi !== 0 ? `${m.roi > 0 ? '+' : ''}${m.roi}%` : 'N/A'}
                    </td>
                    <td className="metric-val">{m.n.toLocaleString()}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Nota metodológica */}
      <div className="card methodology-note">
        <h3>📋 Nota Metodológica</h3>
        <ul>
          <li>Split temporal: 80% train / 20% test (nunca split aleatorio en series de tiempo)</li>
          <li>El baseline predice siempre victoria local (~45% accuracy en fútbol europeo)</li>
          <li>ROI calculado apostando cuando P_modelo {'>'} P_cuota × 1.05 (ventaja del 5%)</li>
          <li>Brier Score promediado sobre las 3 clases (H, D, A) mediante binarización OvR</li>
          <li>Datos: football-data.co.uk — Premier League, La Liga, Bundesliga 2021-2024</li>
        </ul>
      </div>
    </div>
  )
}
