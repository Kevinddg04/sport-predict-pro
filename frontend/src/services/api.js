import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || 'Error desconocido'
    return Promise.reject(new Error(msg))
  }
)

// ── API Methods ──

export const healthCheck = () => api.get('/health')

// Matches
export const getMatches = (params = {}) => api.get('/matches/', { params })
export const getLeagues = () => api.get('/matches/leagues')
export const getSeasons = () => api.get('/matches/seasons')

// Teams
export const getTeams = (league) => api.get('/teams/', { params: { league } })
export const getTeamStats = (teamName, league) =>
  api.get(`/teams/${encodeURIComponent(teamName)}`, { params: { league } })

// Predictions
export const predictMatch = (homeTeam, awayTeam, league = 'E0') =>
  api.post('/predict/', { home_team: homeTeam, away_team: awayTeam, league })

export const getEvaluation = () => api.get('/predict/evaluate')

// Simulations
export const runSimulation = (homeTeam, awayTeam, league = 'E0', nSims = 10000) =>
  api.post('/simulate/', {
    home_team: homeTeam,
    away_team: awayTeam,
    league,
    n_simulations: nSims,
  })

export default api
