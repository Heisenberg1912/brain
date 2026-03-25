import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  PointElement,
  RadarController,
  RadialLinearScale,
  Tooltip,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'
import { fetchAICompare, fetchCompare } from '../api'
import { scoreColor } from '../utils'
import './CompareView.css'

ChartJS.register(RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

function toNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export default function CompareView({ compareIds, locations, isActive }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [insight, setInsight] = useState(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [insightError, setInsightError] = useState('')
  const radarChartRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    if (compareIds.length < 2) {
      setData(null)
      setLoading(false)
      setLoadError('')
      setInsight(null)
      setInsightError('')
      setInsightLoading(false)
      return () => {
        cancelled = true
      }
    }

    setLoading(true)
    setLoadError('')
    setInsight(null)
    setInsightError('')

    fetchCompare(compareIds)
      .then((response) => {
        if (cancelled) return
        setData(response)
      })
      .catch((error) => {
        console.error(error)
        if (cancelled) return
        setLoadError('Comparison data could not be loaded right now.')
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [compareIds])

  useEffect(() => {
    let cancelled = false

    if (compareIds.length < 2) {
      return () => {
        cancelled = true
      }
    }

    setInsightLoading(true)
    setInsightError('')

    fetchAICompare(compareIds)
      .then((response) => {
        if (!cancelled) {
          setInsight(response)
        }
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) {
          setInsightError('AI compare verdict is unavailable right now.')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setInsightLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [compareIds])

  const chartData = useMemo(() => {
    if (!data?.length) return null

    const colors = ['#6c5ce7', '#00d2a0', '#ffb347']

    return {
      labels: ['Land Value', 'Dev Potential', 'Future Appr.'],
      datasets: data.map((score, index) => ({
        label: score.location || `Location ${index + 1}`,
        data: [
          toNumber(score.land_value_score),
          toNumber(score.development_potential_score),
          toNumber(score.future_appreciation_index),
        ],
        backgroundColor: `${colors[index] ?? '#7c86ff'}22`,
        borderColor: colors[index] ?? '#7c86ff',
        borderWidth: 2,
        pointBackgroundColor: colors[index] ?? '#7c86ff',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1,
        pointRadius: 3,
      })),
    }
  }, [data])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 120,
    plugins: {
      legend: {
        labels: {
          color: '#9b9fbc',
          font: { size: 10, weight: '600' },
          boxWidth: 10,
          boxHeight: 10,
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          color: '#6f728f',
          backdropColor: 'transparent',
          font: { size: 9 },
        },
        grid: { color: '#2a2a3a' },
        angleLines: { color: '#2a2a3a' },
        pointLabels: {
          color: '#9b9fbc',
          font: { size: 10, weight: '600' },
        },
      },
    },
  }), [])

  useEffect(() => {
    if (!isActive) return

    const frameId = requestAnimationFrame(() => {
      radarChartRef.current?.resize()
    })

    return () => cancelAnimationFrame(frameId)
  }, [chartData, compareIds, isActive])

  if (compareIds.length < 2) {
    return <div className="detail-empty">Select 2-3 locations using the Compare button on the map, then click Compare.</div>
  }

  if (loading) {
    return <div className="detail-loading"><span className="spinner" /> Comparing locations...</div>
  }

  if (loadError) {
    return <div className="detail-loading detail-error">{loadError}</div>
  }

  if (!data) return null

  const scoreKeys = [
    { key: 'land_value_score', label: 'Land Val' },
    { key: 'development_potential_score', label: 'Dev Pot' },
    { key: 'future_appreciation_index', label: 'Fut Appr' },
  ]

  return (
    <div className="compare-scroll">
      <div className="detail-section">
        <h3>AI Verdict</h3>
        {insightLoading && <div className="compare-ai-state"><span className="spinner" /> Building comparison brief...</div>}
        {!insightLoading && insightError && <div className="compare-ai-state compare-ai-error">{insightError}</div>}
        {!insightLoading && insight && (
          <div className="compare-ai-shell">
            <div className="compare-ai-summary">{insight.summary}</div>
            <div className="compare-ai-grid">
              {insight.verdicts.map((item) => (
                <div key={`${item.label}-${item.value}`} className={`compare-ai-card tone-${item.tone}`}>
                  <div className="compare-ai-label">{item.label}</div>
                  <div className="compare-ai-value">{item.value}</div>
                </div>
              ))}
            </div>
            {!!insight.recommended_questions?.length && (
              <div className="compare-ai-questions">
                {insight.recommended_questions.map((item) => (
                  <div key={item} className="compare-ai-question">{item}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="detail-section">
        <h3>Score Comparison</h3>
        {chartData && (
          <div className="compare-chart-shell">
            <Radar
              key={`compare-${compareIds.join('-')}`}
              ref={radarChartRef}
              data={chartData}
              options={chartOptions}
            />
          </div>
        )}
      </div>

      <div className="detail-section">
        {scoreKeys.map(({ key, label }) => (
          <div key={key} className="compare-group">
            {data.map((score) => {
              const value = toNumber(score[key])
              const color = scoreColor(value)

              return (
                <div key={`${score.location_id}-${key}`} className="compare-score-row">
                  <span className="cs-label cs-location">{score.location || `Location ${score.location_id}`}</span>
                  <span className="cs-label cs-metric">{label}</span>
                  <div className="cs-bar">
                    <div className="cs-fill" style={{ width: `${Math.max(0, Math.min(value, 100))}%`, background: color }} />
                  </div>
                  <span className="cs-val" style={{ color }}>{value.toFixed(0)}</span>
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
