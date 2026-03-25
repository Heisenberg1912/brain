import { useEffect, useMemo, useRef, useState } from 'react'
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineController,
  LineElement,
  LinearScale,
  PointElement,
  RadarController,
  RadialLinearScale,
  Tooltip,
} from 'chart.js'
import { Bar, Line, Radar } from 'react-chartjs-2'
import { analyzeAI, fetchLocationDetail, fetchScore } from '../api'
import { formatMarkdown, scoreClass, SCORE_WEIGHTS } from '../utils'
import './DetailsPanel.css'

ChartJS.register(
  RadarController,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  CategoryScale,
  LinearScale,
  LineController,
  BarController,
  BarElement,
  Tooltip,
  Legend,
)

const RADAR_LABELS = [
  'Land Value',
  'Dev Potential',
  'Future Appr.',
  'Infra',
  'Price Trend',
  'Zoning',
  'Density',
]

const DISTRIBUTION_BINS = Array.from({ length: 10 }, (_, index) => index * 10)

function toNumber(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function ordinalize(value) {
  const absolute = Math.abs(Math.round(value))
  const lastTwo = absolute % 100

  if (lastTwo >= 11 && lastTwo <= 13) {
    return `${absolute}th`
  }

  switch (absolute % 10) {
    case 1:
      return `${absolute}st`
    case 2:
      return `${absolute}nd`
    case 3:
      return `${absolute}rd`
    default:
      return `${absolute}th`
  }
}

export default function DetailsPanel({ activeId, rankings, isActive }) {
  const [data, setData] = useState(null)
  const [scores, setScores] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const radarChartRef = useRef(null)
  const priceChartRef = useRef(null)
  const distChartRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    if (!activeId) {
      setData(null)
      setScores(null)
      setLoadError('')
      setLoading(false)
      setAnalysis(null)
      return () => {
        cancelled = true
      }
    }

    setLoading(true)
    setLoadError('')
    setData(null)
    setScores(null)
    setAnalysis(null)

    Promise.all([fetchLocationDetail(activeId), fetchScore(activeId)])
      .then(([detail, score]) => {
        if (cancelled) return
        setData(detail)
        setScores(score)
      })
      .catch((error) => {
        console.error(error)
        if (cancelled) return
        setLoadError('Location intelligence could not be loaded right now.')
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [activeId])

  const sortedPrices = useMemo(() => (
    [...(data?.price_history ?? [])]
      .filter((pricePoint) => Number.isFinite(Number(pricePoint.price_per_sqft)))
      .sort((first, second) => first.recorded_date.localeCompare(second.recorded_date))
  ), [data])

  const scoreValues = useMemo(() => {
    if (!scores) return null

    const components = scores.components ?? {}

    return [
      toNumber(scores.land_value_score),
      toNumber(scores.development_potential_score),
      toNumber(scores.future_appreciation_index),
      toNumber(components.infra_score),
      toNumber(components.price_trend_score),
      toNumber(components.zoning_favorability),
      toNumber(components.density_score),
    ]
  }, [scores])

  const radarData = useMemo(() => {
    if (!scoreValues) return null

    return {
      labels: RADAR_LABELS,
      datasets: [{
        data: scoreValues,
        backgroundColor: 'rgba(108, 92, 231, 0.14)',
        borderColor: '#6c5ce7',
        borderWidth: 2,
        pointBackgroundColor: '#6c5ce7',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1,
        pointRadius: 3,
        pointHoverRadius: 4,
      }],
    }
  }, [scoreValues])

  const radarOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 120,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label(context) {
            return `${context.label}: ${Math.round(toNumber(context.parsed.r))}`
          },
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          stepSize: 25,
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

  const priceChartData = useMemo(() => {
    if (sortedPrices.length < 2) return null

    return {
      labels: sortedPrices.map((pricePoint) => (
        new Date(pricePoint.recorded_date).toLocaleDateString('en-US', {
          month: 'short',
          year: '2-digit',
        })
      )),
      datasets: [{
        data: sortedPrices.map((pricePoint) => toNumber(pricePoint.price_per_sqft)),
        borderColor: '#6c5ce7',
        borderWidth: 2,
        fill: true,
        tension: 0.32,
        pointRadius: 2.5,
        pointHoverRadius: 4,
        pointBackgroundColor: '#6c5ce7',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 1,
        backgroundColor(context) {
          const { chart } = context
          const { ctx, chartArea } = chart

          if (!chartArea) {
            return 'rgba(108, 92, 231, 0.18)'
          }

          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
          gradient.addColorStop(0, 'rgba(108, 92, 231, 0.34)')
          gradient.addColorStop(1, 'rgba(108, 92, 231, 0.02)')
          return gradient
        },
      }],
    }
  }, [sortedPrices])

  const priceChartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 120,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label(context) {
            return `Rs ${Math.round(toNumber(context.parsed.y)).toLocaleString()}/sqft`
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#9b9fbc',
          font: { size: 9 },
          maxRotation: 0,
        },
        grid: { display: false },
      },
      y: {
        ticks: {
          color: '#9b9fbc',
          font: { size: 9 },
          callback(value) {
            return `Rs ${Math.round(toNumber(value) / 1000)}k`
          },
        },
        grid: { color: '#2a2a3a' },
      },
    },
  }), [])

  const distributionMeta = useMemo(() => {
    if (!scores || !rankings?.length) return null

    const landValue = toNumber(scores.land_value_score)
    const values = rankings
      .map((item) => Number(item.land_value_score))
      .filter(Number.isFinite)
      .sort((first, second) => first - second)

    if (values.length === 0) return null

    const counts = DISTRIBUTION_BINS.map((binStart, index) => {
      const upperBound = binStart + 10
      return values.filter((value) => (
        index === DISTRIBUTION_BINS.length - 1
          ? value >= binStart && value <= 100
          : value >= binStart && value < upperBound
      )).length
    })

    const currentBin = Math.max(
      0,
      Math.min(
        DISTRIBUTION_BINS.length - 1,
        Math.floor(Math.min(Math.max(landValue, 0), 99.999) / 10),
      ),
    )
    const percentile = Math.round((values.filter((value) => value < landValue).length / values.length) * 100)

    return {
      percentile,
      chartData: {
        labels: DISTRIBUTION_BINS.map((binStart) => `${binStart}-${binStart + 10}`),
        datasets: [{
          data: counts,
          backgroundColor: counts.map((_, index) => (
            index === currentBin ? '#6c5ce7' : 'rgba(255, 255, 255, 0.08)'
          )),
          borderRadius: 999,
          borderSkipped: false,
          barPercentage: 0.84,
          categoryPercentage: 0.96,
          maxBarThickness: 18,
        }],
      },
    }
  }, [rankings, scores])

  const distributionOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 120,
    plugins: {
      legend: { display: false },
      tooltip: {
        displayColors: false,
        callbacks: {
          title(items) {
            return items[0]?.label ? `${items[0].label} score band` : ''
          },
          label(context) {
            const count = Math.round(toNumber(context.parsed.y))
            return `${count} market ${count === 1 ? 'entry' : 'entries'}`
          },
        },
      },
    },
    scales: {
      x: { display: false },
      y: { display: false, beginAtZero: true },
    },
  }), [])

  useEffect(() => {
    if (!isActive) return

    const frameId = requestAnimationFrame(() => {
      radarChartRef.current?.resize()
      priceChartRef.current?.resize()
      distChartRef.current?.resize()
    })

    return () => cancelAnimationFrame(frameId)
  }, [activeId, isActive, priceChartData, radarData, distributionMeta])

  const handleAnalyze = async () => {
    if (!activeId) return
    setAnalyzing(true)

    try {
      const response = await analyzeAI(activeId)
      setAnalysis(response)
    } catch (error) {
      console.error(error)
      setAnalysis({
        analysis: 'Analysis failed. Check the AI service configuration.',
        cards: [],
        recommended_questions: [],
      })
    } finally {
      setAnalyzing(false)
    }
  }

  if (!activeId) {
    return <div className="detail-empty">Select a location from the map or rankings to view detailed intelligence.</div>
  }

  if (loading) {
    return <div className="detail-loading"><span className="spinner" /> Loading location intelligence...</div>
  }

  if (loadError) {
    return <div className="detail-loading detail-error">{loadError}</div>
  }

  if (!data || !scores) return null

  const loc = data.location
  const masterplan = data.masterplan
  const census = data.census
  const infra = data.nearby_infrastructure || []
  const landValue = toNumber(scores.land_value_score)
  const developmentPotential = toNumber(scores.development_potential_score)
  const futureAppreciation = toNumber(scores.future_appreciation_index)

  const tooltipHtml = (weights) => Object.entries(weights).map(([name, value]) => (
    `<div class="tw"><span class="wname">${name}</span><span class="wpct">${Math.round(value * 100)}%</span></div>`
  )).join('')

  const infrastructurePhases = [
    { items: infra.filter((item) => item.status === 'operational'), label: 'Active', cls: 'phase-operational' },
    { items: infra.filter((item) => item.status === 'under_construction'), label: 'Building', cls: 'phase-construction' },
    { items: infra.filter((item) => item.status === 'planned'), label: 'Planned', cls: 'phase-planned' },
  ]

  const pctChange = sortedPrices.length > 1 && toNumber(sortedPrices[0].price_per_sqft) > 0
    ? (((toNumber(sortedPrices[sortedPrices.length - 1].price_per_sqft) - toNumber(sortedPrices[0].price_per_sqft)) / toNumber(sortedPrices[0].price_per_sqft)) * 100).toFixed(1)
    : null

  return (
    <div className="detail-scroll">
      <div className="detail-section">
        <h2 className="detail-name">{loc.name}</h2>
        <div className="detail-subtitle">
          {[loc.locality, loc.city, loc.state, loc.ward ? `${loc.ward} Ward` : null, loc.pin_code].filter(Boolean).join(' · ')}
        </div>
      </div>

      <div className="detail-section">
        <h3>Valuation Intelligence</h3>
        <div className="score-bars">
          {[
            { label: 'Land Value', value: landValue, weights: SCORE_WEIGHTS.land_value, color: 'var(--accent)', glow: 'rgba(108, 92, 231, 0.42)' },
            { label: 'Dev Potential', value: developmentPotential, weights: SCORE_WEIGHTS.development_potential, color: 'var(--green)', glow: 'rgba(0, 210, 160, 0.35)' },
            { label: 'Future Appreciation', value: futureAppreciation, weights: SCORE_WEIGHTS.future_appreciation, color: 'var(--orange)', glow: 'rgba(255, 179, 71, 0.35)' },
          ].map((scoreItem) => (
            <div key={scoreItem.label} className="score-bar-group">
              <div className="sb-label">
                <span>{scoreItem.label}</span>
                <span className={`sb-val ${scoreClass(scoreItem.value)}`}>{scoreItem.value.toFixed(0)}</span>
              </div>
              <div className="sb-track">
                <div
                  className="sb-fill"
                  style={{
                    width: `${Math.max(0, Math.min(scoreItem.value, 100))}%`,
                    backgroundColor: scoreItem.color,
                    boxShadow: `0 0 10px ${scoreItem.glow}`,
                  }}
                />
              </div>
              <div className="score-tooltip" dangerouslySetInnerHTML={{ __html: tooltipHtml(scoreItem.weights) }} />
            </div>
          ))}
        </div>

        {radarData && (
          <div className="detail-chart-shell detail-chart-shell-radar">
            <Radar
              key={`radar-${activeId}`}
              ref={radarChartRef}
              data={radarData}
              options={radarOptions}
            />
          </div>
        )}

        {distributionMeta ? (
          <div className="dist-section">
            <div className="dist-header">
              <span>Market Percentile</span>
              <span className="dist-val">{ordinalize(distributionMeta.percentile)}</span>
            </div>
            <div className="detail-chart-shell detail-chart-shell-distribution">
              <Bar
                key={`distribution-${activeId}-${distributionMeta.percentile}`}
                ref={distChartRef}
                data={distributionMeta.chartData}
                options={distributionOptions}
              />
            </div>
          </div>
        ) : (
          <div className="detail-chart-empty">Not enough market data to plot the local score distribution yet.</div>
        )}
      </div>

      {masterplan && (
        <div className="detail-section">
          <h3>Zoning &amp; FSI</h3>
          <div className="detail-row"><span className="label">Zone Type</span><span className="val cap">{masterplan.zoning_type}</span></div>
          <div className="detail-row"><span className="label">FSI</span><span className="val">{masterplan.fsi}</span></div>
          <div className="detail-row"><span className="label">Max Height</span><span className="val">{masterplan.max_height_m}m</span></div>
          <div className="detail-row"><span className="label">Ground Coverage</span><span className="val">{masterplan.ground_coverage_pct}%</span></div>
          <div className="detail-row"><span className="label">Setbacks</span><span className="val">F:{masterplan.setback_front_m}m S:{masterplan.setback_side_m}m</span></div>
          <div className="detail-row"><span className="label">Source</span><span className="val small">{masterplan.version}</span></div>
        </div>
      )}

      {(data.avg_price_per_sqft || sortedPrices.length > 0) && (
        <div className="detail-section">
          <h3>Pricing</h3>
          {data.avg_price_per_sqft && (
            <div className="detail-row">
              <span className="label">Avg Price/sqft</span>
              <span className="val green">Rs {Math.round(toNumber(data.avg_price_per_sqft)).toLocaleString()}</span>
            </div>
          )}

          {priceChartData ? (
            <div className="price-chart-container">
              {pctChange && (
                <div className={`price-change ${Number(pctChange) >= 0 ? 'up' : 'down'}`}>
                  {Number(pctChange) >= 0 ? '+' : ''}{pctChange}%
                </div>
              )}
              <div className="detail-chart-shell detail-chart-shell-price">
                <Line
                  key={`price-${activeId}-${sortedPrices.length}`}
                  ref={priceChartRef}
                  data={priceChartData}
                  options={priceChartOptions}
                />
              </div>
            </div>
          ) : (
            <div className="detail-chart-empty">More than one pricing snapshot is needed before the trend chart can be drawn.</div>
          )}
        </div>
      )}

      {census && (
        <div className="detail-section">
          <h3>Demographics ({census.year})</h3>
          <div className="detail-row"><span className="label">Population</span><span className="val">{census.population?.toLocaleString()}</span></div>
          <div className="detail-row"><span className="label">Density</span><span className="val">{census.density_per_sqkm?.toLocaleString()}/km²</span></div>
          <div className="detail-row"><span className="label">Growth Rate</span><span className="val">{census.growth_rate_pct}%</span></div>
          <div className="detail-row"><span className="label">Households</span><span className="val">{census.households?.toLocaleString()}</span></div>
        </div>
      )}

      {infra.length > 0 && (
        <div className="detail-section">
          <h3>Nearby Infrastructure ({infra.length})</h3>
          <div className="infra-timeline">
            {infrastructurePhases.map((phase) => (
              <div key={phase.label} className={`infra-phase ${phase.cls}`}>
                <div className="phase-header">{phase.label} <span className="phase-count">{phase.items.length}</span></div>
                <div className="phase-items">
                  {phase.items.length > 0
                    ? phase.items.map((item, index) => (
                      <div key={`${phase.label}-${index}`} className="phase-item">
                        <span className="pi-name">{item.name}</span>
                        <span className="pi-dist">{item.distance_km}km</span>
                      </div>
                    ))
                    : <div className="phase-item empty">None</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="detail-section">
        <button className="analyze-btn" onClick={handleAnalyze} disabled={analyzing}>
          {analyzing ? <><span className="spinner" /> Analyzing...</> : 'Analyze with AI'}
        </button>
        {analysis && (
          <>
            {!!analysis.cards?.length && (
              <div className="analysis-cards">
                {analysis.cards.map((item) => (
                  <div key={`${item.label}-${item.value}`} className={`analysis-card tone-${item.tone || 'neutral'}`}>
                    <div className="analysis-card-label">{item.label}</div>
                    <div className="analysis-card-value">{item.value}</div>
                  </div>
                ))}
              </div>
            )}
            <div className="analysis-result" dangerouslySetInnerHTML={{ __html: formatMarkdown(analysis.analysis) }} />
            {!!analysis.recommended_questions?.length && (
              <div className="analysis-questions">
                {analysis.recommended_questions.map((item) => (
                  <div key={item} className="analysis-question">{item}</div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
