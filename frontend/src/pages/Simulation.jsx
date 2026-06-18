import { useState, useEffect } from 'react'
import { Activity, Play } from 'lucide-react'
import { runSimulation, getTeams } from '../services/api'
import toast from 'react-hot-toast'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, Legend
} from 'recharts'
import './Simulation.css'

const LEAGUE_OPTIONS = [
  { code: 'E0', name: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League' },
  { code: 'SP1', name: '🇪🇸 La Liga' },
  { code: 'D1', name: '🇩🇪 Bundesliga' },
]

const SIM_OPTIONS = [1000, 5000, 10000, 50000]

const CUSTOM_LABEL = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.05) return null
  const RADIAN = Math.PI / 180
  const r = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + r * Math.cos(-midAngle * RADIAN)
  const y = cy + r * Math.sin(-midAngle * RADIAN)
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={13} fontWeight={700}>
      {(percent * 100).toFixed(1)}%
    </text>
  )
}

export default function Simulation() {
  const [league, setLeague] = useState('E0')
  const [teams, setTeams] = useState([])
  const [homeTeam, setHomeTeam] = useState('')
  const [awayTeam, setAwayTeam] = useState('')
  const [nSims, setNSims] = useState(10000)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    getTeams(league).then((d) => { setTeams(d.teams || []); setHomeTeam(''); setAwayTeam(''); setResult(null) })
  }, [league])

  const handleSimulate = async () => {
    if (!homeTeam || !awayTeam) return toast.error('Selecciona ambos equipos')
    if (homeTeam === awayTeam) return toast.error('Los equipos deben ser diferentes')
    setLoading(true)
    setResult(null)
    try {
      const data = await runSimulation(homeTeam, awayTeam, league, nSims)
      setResult(data)
      toast.success(`¡${nSims.toLocaleString()} simulaciones completadas!`)
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const pieData = result
    ? [
        { name: `${result.home_team} gana`, value: +(result.home_win_pct * 100).toFixed(1), fill: '#00d68f' },
        { name: 'Empate',                   value: +(result.draw_pct * 100).toFixed(1),     fill: '#4f9ef8' },
        { name: `${result.away_team} gana`, value: +(result.away_win_pct * 100).toFixed(1), fill: '#ef4444' },
      ]
    : []

  const marketsBar = result
    ? [
        { name: 'O+0.5', value: +(result.over_0_5_pct * 100).toFixed(1) },
        { name: 'O+1.5', value: +(result.over_1_5_pct * 100).toFixed(1) },
        { name: 'O+2.5', value: +(result.over_2_5_pct * 100).toFixed(1) },
        { name: 'O+3.5', value: +(result.over_3_5_pct * 100).toFixed(1) },
        { name: 'O+4.5', value: +(result.over_4_5_pct * 100).toFixed(1) },
        { name: 'BTTS',  value: +(result.btts_pct * 100).toFixed(1) },
      ]
    : []

  // Top 15 scores para el heatmap
  const topScores = result
    ? result.most_likely_scores.slice(0, 12)
    : []

  return (
    <div className="sim-page">
      <div className="page-header">
        <h1>🎲 Simulación Monte Carlo</h1>
        <p className="page-subtitle">
          Simula miles de partidos y obtén distribuciones de probabilidad precisas
        </p>
      </div>

      {/* Formulario */}
      <div className="sim-form card">
        <div className="form-row-sim">
          <div className="form-group">
            <label>Liga</label>
            <select value={league} onChange={(e) => setLeague(e.target.value)} className="select-input">
              {LEAGUE_OPTIONS.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Local 🏠</label>
            <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)} className="select-input">
              <option value="">Seleccionar...</option>
              {teams.filter((t) => t !== awayTeam).map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="vs-text">VS</div>
          <div className="form-group">
            <label>Visitante ✈️</label>
            <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)} className="select-input">
              <option value="">Seleccionar...</option>
              {teams.filter((t) => t !== homeTeam).map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Simulaciones</label>
            <select value={nSims} onChange={(e) => setNSims(+e.target.value)} className="select-input">
              {SIM_OPTIONS.map((n) => <option key={n} value={n}>{n.toLocaleString()}</option>)}
            </select>
          </div>
        </div>

        <button className="btn btn-primary sim-btn" onClick={handleSimulate} disabled={loading || !homeTeam || !awayTeam}>
          {loading
            ? <><span className="spinner" style={{ width: 18, height: 18 }} /> Simulando...</>
            : <><Play size={18} /> Simular {nSims.toLocaleString()} partidos</>}
        </button>
      </div>

      {/* Resultados */}
      {result && (
        <div className="sim-results animate-fade-up">
          {/* Estadísticas clave */}
          <div className="sim-stats-grid">
            {[
              { label: 'Victoria Local', value: `${(result.home_win_pct * 100).toFixed(1)}%`, color: '#00d68f', icon: '🏠' },
              { label: 'Empate',          value: `${(result.draw_pct * 100).toFixed(1)}%`,     color: '#4f9ef8', icon: '🤝' },
              { label: 'Victoria Visit.', value: `${(result.away_win_pct * 100).toFixed(1)}%`, color: '#ef4444', icon: '✈️' },
              { label: 'Over 2.5',        value: `${(result.over_2_5_pct * 100).toFixed(1)}%`, color: '#f59e0b', icon: '⚽' },
              { label: 'BTTS',            value: `${(result.btts_pct * 100).toFixed(1)}%`,     color: '#7c3aed', icon: '🎯' },
              { label: 'Goles prom.',     value: `${(result.avg_home_goals + result.avg_away_goals).toFixed(2)}`, color: '#00d68f', icon: '📊' },
            ].map((s, i) => (
              <div key={i} className="sim-stat card">
                <div className="sim-stat-icon">{s.icon}</div>
                <div className="sim-stat-value" style={{ color: s.color }}>{s.value}</div>
                <div className="sim-stat-label">{s.label}</div>
              </div>
            ))}
          </div>

          <div className="sim-charts-grid">
            {/* Pie chart 1X2 */}
            <div className="card">
              <h3>Distribución 1X2 ({result.n_simulations.toLocaleString()} simulaciones)</h3>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={100} labelLine={false} label={CUSTOM_LABEL}>
                    {pieData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Bar chart mercados */}
            <div className="card">
              <h3>Mercados de Goles</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={marketsBar} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {marketsBar.map((e, i) => (
                      <Cell key={i} fill={`hsl(${160 - i * 20}, 80%, 55%)`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Marcadores top */}
          <div className="card">
            <h3>Top Marcadores Simulados</h3>
            <div className="scores-heatmap">
              {topScores.map((s, i) => {
                const pct = s.probability * 100
                const intensity = Math.min(pct / 15, 1)
                return (
                  <div
                    key={i}
                    className="heatmap-cell"
                    style={{ background: `rgba(0, 214, 143, ${0.1 + intensity * 0.5})`, borderColor: `rgba(0, 214, 143, ${intensity * 0.6})` }}
                  >
                    <div className="heatmap-score">{s.home_goals}–{s.away_goals}</div>
                    <div className="heatmap-prob">{pct.toFixed(2)}%</div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
