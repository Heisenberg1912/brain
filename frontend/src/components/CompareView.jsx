import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  BarChart3,
  GitCompareArrows,
  Sparkles,
  Trophy,
} from 'lucide-react'
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  RadarController,
  RadialLinearScale,
  Tooltip,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'
import { fetchAICompare, fetchCompare } from '../api'
import { compactText, formatLabel, locationLabel, scoreColor } from '../utils'
import './CompareView.css'

ChartJS.register(
  RadarController,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
)

const COLORS = ['#17b897', '#f59e0b', '#3b82f6']

const METRIC_DEFINITIONS = [
  { key: 'land_value_score', label: 'Land Value' },
  { key: 'development_potential_score', label: 'Development Potential' },
  { key: 'future_appreciation_index', label: 'Future Appreciation' },
  { key: 'infra_score', label: 'Infrastructure' },
  { key: 'price_trend_score', label: 'Price Trend' },
  { key: 'density_score', label: 'Density' },
]

function metricValue(row, key) {
  if (key in row) return row[key]
  return row.components?.[key] ?? 0
}

export default function CompareView({ compareIds, locations }) {
  const [comparison, setComparison] = useState([])
  const [aiSummary, setAiSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const compareNames = useMemo(
    () => compareIds.map((id) => locationLabel(locations[id], '')).filter(Boolean),
    [compareIds, locations],
  )

  useEffect(() => {
    if (compareIds.length < 2) {
      setComparison([])
      setAiSummary(null)
      setLoadError('')
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setLoadError('')

    Promise.allSettled([
      fetchCompare(compareIds),
      fetchAICompare(compareIds),
    ])
      .then(([comparisonResult, aiResult]) => {
        if (cancelled) return

        if (comparisonResult.status === 'fulfilled') {
          setComparison(comparisonResult.value)
        } else {
          setComparison([])
          setLoadError('Comparison data could not be loaded.')
        }

        if (aiResult.status === 'fulfilled') {
          setAiSummary(aiResult.value)
        } else {
          setAiSummary(null)
        }
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setLoadError('Comparison data could not be loaded.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [compareIds])

  const chartData = useMemo(() => {
    if (!comparison.length) return null

    return {
      labels: METRIC_DEFINITIONS.map((item) => item.label),
      datasets: comparison.map((row, index) => ({
        label: row.location,
        data: METRIC_DEFINITIONS.map((metric) => metricValue(row, metric.key)),
        backgroundColor: `${COLORS[index]}20`,
        borderColor: COLORS[index],
        pointBackgroundColor: COLORS[index],
        borderWidth: 2,
      })),
    }
  }, [comparison])

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        grid: { color: 'rgba(148, 163, 184, 0.2)' },
        angleLines: { color: 'rgba(148, 163, 184, 0.16)' },
        pointLabels: {
          color: '#94a3b8',
          font: { family: 'Montserrat', size: 10, weight: '600' },
        },
        ticks: { display: false },
      },
    },
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: '#94a3b8',
          font: { family: 'Montserrat', size: 11, weight: '600' },
          usePointStyle: true,
          boxWidth: 8,
        },
      },
    },
  }

  const leaderboard = useMemo(() => {
    if (!comparison.length) return []

    return METRIC_DEFINITIONS.map((metric) => {
      const winner = [...comparison].sort((left, right) => metricValue(right, metric.key) - metricValue(left, metric.key))[0]
      return {
        label: metric.label,
        winner: winner.location,
        value: metricValue(winner, metric.key),
      }
    })
  }, [comparison])

  if (compareIds.length < 2) {
    return (
      <div className="compare-empty">
        <GitCompareArrows size={36} />
        <h3>Build a comparison set</h3>
        <p>Pick 2-3 markets.</p>
        <div className="compare-selected-list">
          {compareIds.map((id) => (
            <span key={id} className="selected-pill">{locationLabel(locations[id], `Market ${id}`)}</span>
          ))}
        </div>
      </div>
    )
  }

  if (loading) return <div className="panel-loading"><span className="spinner" /></div>
  if (loadError) return <div className="panel-error"><AlertTriangle size={22} /><p>{loadError}</p></div>

  return (
    <div className="compare-container">
      <section className="compare-hero">
        <div>
          <p className="eyebrow">Comparison cockpit</p>
          <h3>{compareNames.join(' vs ') || 'Selected markets'}</h3>
          <p>{compactText(aiSummary?.summary, 'Score, momentum, infrastructure, and density side by side.', 100)}</p>
        </div>

        {aiSummary?.winner_location_name ? (
          <div className="winner-card">
            <Trophy size={18} />
            <div>
              <span>AI leader</span>
              <strong>{aiSummary.winner_location_name}</strong>
            </div>
          </div>
        ) : null}
      </section>

      <section className="compare-grid">
        <article className="compare-section">
          <div className="section-heading">
            <BarChart3 size={18} />
            <h4>Score radar</h4>
          </div>
          <div className="compare-chart-box">
            {chartData ? <Radar data={chartData} options={chartOptions} /> : <p className="muted-copy">Chart data is unavailable.</p>}
          </div>
        </article>

        <article className="compare-section ai-verdict">
          <div className="section-heading">
            <Sparkles size={18} />
            <h4>AI verdict</h4>
          </div>
          {aiSummary ? (
            <>
              <p className="section-copy">{compactText(aiSummary.summary, '', 118)}</p>
              <div className="verdict-grid">
                {aiSummary.verdicts?.map((verdict) => (
                  <article key={`${verdict.label}-${verdict.value}`} className={`verdict-card tone-${verdict.tone}`}>
                    <span>{verdict.label}</span>
                    <strong>{verdict.value}</strong>
                  </article>
                ))}
              </div>
              {aiSummary.recommended_questions?.length ? (
                <div className="question-strip">
                  {aiSummary.recommended_questions.slice(0, 3).map((question, index) => (
                    <span key={`${question}-${index}`} className="question-chip">{question}</span>
                  ))}
                </div>
              ) : null}
            </>
          ) : (
            <p className="muted-copy">AI comparison commentary is unavailable, but structured score comparisons still work.</p>
          )}
        </article>
      </section>

      <section className="compare-section">
        <div className="section-heading">
          <Trophy size={18} />
          <h4>Metric leaders</h4>
        </div>
        <div className="leader-grid">
          {leaderboard.map((item) => (
            <article key={item.label} className="leader-card">
              <span>{item.label}</span>
              <strong>{item.winner}</strong>
              <b>{item.value.toFixed(0)}</b>
            </article>
          ))}
        </div>
      </section>

      <section className="compare-table">
        {comparison.map((row) => (
          <article key={row.location_id} className="compare-row-card">
            <header>
              <div>
                <h4>{row.location}</h4>
                <span>{formatLabel(locations[row.location_id]?.zoning_type)}</span>
              </div>
              <b style={{ color: scoreColor(row.land_value_score) }}>{row.land_value_score.toFixed(0)}</b>
            </header>

            <div className="metric-list">
              {METRIC_DEFINITIONS.map((metric) => (
                <div key={metric.key} className="metric-line">
                  <span>{metric.label}</span>
                  <div className="metric-bar">
                    <div className="metric-fill" style={{ width: `${metricValue(row, metric.key)}%` }} />
                  </div>
                  <strong>{metricValue(row, metric.key).toFixed(0)}</strong>
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>
    </div>
  )
}
