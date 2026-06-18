import { useState, useEffect } from 'react'
import { Zap, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { predictMatch, getTeams, getLeagues } from '../services/api'
import toast from 'react-hot-toast'
import {
  RadialBarChart, RadialBar, Legend, Tooltip,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Cell
} from 'recharts'
import './Predictions.css'

const LEAGUE_OPTIONS = [
  { code: 'E0',  name: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League' },
  { code: 'SP1', name: '🇪🇸 La Liga' },
  { code: 'D1',  name: '🇩🇪 Bundesliga' },
]

const COLORS = {
  home:  '#00d68f',
  draw:  '#4f9ef8',
  away:  '#ef4444',
}

function ProbBar({ label, value, color }) {
  return (
    <div className="prob-row">
      <span className="prob-label">{label}</span>
      <div className="prob-bar">
        <div
          className="prob-bar-fill"
          style={{ width: `${(value * 100).toFixed(1)}%`, background: color }}
        />
      </div>
      <span className="prob-value" style={{ color }}>{(value * 100).toFixed(1)}%</span>
    </div>
  )
}

function ScoreGrid({ scores }) {
  return (
    <div className="score-grid">
      {scores.slice(0, 6).map((s, i) => (
        <div key={i} className="score-chip">
          <div className="score-result">{s.home_goals} - {s.away_goals}</div>
          <div className="score-prob">{(s.probability * 100).toFixed(1)}%</div>
        </div>
      ))}
    </div>
  )
}

export default function Predictions() {
  const [league, setLeague] = useState('E0')
  const [teams, setTeams] = useState([])
  const [homeTeam, setHomeTeam] = useState('')
  const [awayTeam, setAwayTeam] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    getTeams(league)
      .then((data) => {
        setTeams(data.teams || [])
        setHomeTeam('')
        setAwayTeam('')
        setResult(null)
      })
      .catch(() => toast.error('No se pudieron cargar los equipos'))
  }, [league])

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) return toast.error('Selecciona ambos equipos')
    if (homeTeam === awayTeam) return toast.error('Los equipos deben ser diferentes')

    setLoading(true)
    setResult(null)
    try {
      const data = await predictMatch(homeTeam, awayTeam, league)
      setResult(data)
      toast.success('¡Predicción generada!')
    } catch (err) {
      toast.error(err.message || 'Error al predecir')
    } finally {
      setLoading(false)
    }
  }

  const radialData = result
    ? [
        { name: 'Local', value: +(result.home_win * 100).toFixed(1), fill: COLORS.home },
        { name: 'Empate', value: +(result.draw * 100).toFixed(1), fill: COLORS.draw },
        { name: 'Visitante', value: +(result.away_win * 100).toFixed(1), fill: COLORS.away },
      ]
    : []

  const marketsData = result
    ? [
        { name: 'Over 2.5', value: +(result.over_2_5 * 100).toFixed(1), color: '#f59e0b' },
        { name: 'Under 2.5', value: +(result.under_2_5 * 100).toFixed(1), color: '#7c3aed' },
        { name: 'BTTS', value: +(result.btts * 100).toFixed(1), color: '#00d68f' },
        { name: 'No BTTS', value: +((1 - result.btts) * 100).toFixed(1), color: '#4f9ef8' },
      ]
    : []

  const winner =
    result
      ? result.home_win > result.away_win && result.home_win > result.draw
        ? 'home'
        : result.away_win > result.home_win && result.away_win > result.draw
        ? 'away'
        : 'draw'
      : null

  return (
    <div className="predictions-page">
      <div className="page-header">
        <h1>⚡ Predicciones</h1>
        <p className="page-subtitle">
          Ensemble de modelos ML + Regresión de Poisson para máxima precisión
        </p>
      </div>

      {/* Formulario */}
      <div className="prediction-form card">
        <div className="form-row">
          {/* Liga */}
          <div className="form-group">
            <label>Liga</label>
            <select value={league} onChange={(e) => setLeague(e.target.value)} className="select-input">
              {LEAGUE_OPTIONS.map((l) => (
                <option key={l.code} value={l.code}>{l.name}</option>
              ))}
            </select>
          </div>

          {/* Equipo local */}
          <div className="form-group">
            <label>Equipo Local 🏠</label>
            <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)} className="select-input">
              <option value="">Seleccionar...</option>
              {teams.filter((t) => t !== awayTeam).map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="vs-divider">VS</div>

          {/* Equipo visitante */}
          <div className="form-group">
            <label>Equipo Visitante ✈️</label>
            <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)} className="select-input">
              <option value="">Seleccionar...</option>
              {teams.filter((t) => t !== homeTeam).map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          className="btn btn-primary predict-btn"
          onClick={handlePredict}
          disabled={loading || !homeTeam || !awayTeam}
        >
          {loading ? <><span className="spinner" style={{width:18,height:18}} /> Prediciendo...</>
                   : <><Zap size={18} /> Predecir</>}
        </button>
      </div>

      {/* Resultados */}
      {result && (
        <div className="results-grid animate-fade-up">

          {/* Resumen ganador */}
          <div className={`winner-card card winner-${winner}`}>
            <div className="winner-label">Resultado más probable</div>
            <div className="winner-teams">
              <span className={winner === 'home' ? 'team-highlight' : ''}>{result.home_team}</span>
              <span className="winner-vs">vs</span>
              <span className={winner === 'away' ? 'team-highlight' : ''}>{result.away_team}</span>
            </div>
            <div className="winner-verdict">
              {winner === 'home' && <><TrendingUp size={20} /> Victoria Local</>}
              {winner === 'away' && <><TrendingDown size={20} /> Victoria Visitante</>}
              {winner === 'draw' && <><Minus size={20} /> Empate</>}
            </div>
            <div className="confidence-bar-wrapper">
              <span>Confianza del modelo:</span>
              <strong style={{ color: 'var(--accent-green)' }}>
                {(result.confidence * 100).toFixed(0)}%
              </strong>
            </div>
            <div className="xg-row">
              <span>xG {result.home_team}: <strong style={{color:'var(--accent-green)'}}>{result.expected_home_goals}</strong></span>
              <span>xG {result.away_team}: <strong style={{color:'var(--accent-red)'}}>{result.expected_away_goals}</strong></span>
            </div>
          </div>

          {/* Gráfico radial 1X2 */}
          <div className="card chart-card">
            <h3>Probabilidades 1X2</h3>
            <ResponsiveContainer width="100%" height={220}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="30%" outerRadius="90%" data={radialData}>
                <RadialBar dataKey="value" cornerRadius={4} label={{ position: 'insideStart', fill: '#fff', fontSize: 12 }} />
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }} />
                <Legend iconType="circle" />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="prob-bars">
              <ProbBar label={result.home_team} value={result.home_win} color={COLORS.home} />
              <ProbBar label="Empate"           value={result.draw}     color={COLORS.draw} />
              <ProbBar label={result.away_team} value={result.away_win} color={COLORS.away} />
            </div>
          </div>

          {/* Mercados adicionales */}
          <div className="card chart-card">
            <h3>Mercados Adicionales</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={marketsData} layout="vertical" margin={{ left: 10 }}>
                <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`}
                  tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} width={75} />
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {marketsData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Marcadores más probables */}
          <div className="card scores-card">
            <h3>Marcadores Más Probables</h3>
            <ScoreGrid scores={result.most_likely_scores} />
            <div className="model-info">
              <span className="badge badge-green">Modelo: {result.model}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
