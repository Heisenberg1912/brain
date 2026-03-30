import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  BarChart3,
  Building2,
  ChevronDown,
  CloudSun,
  Gauge,
  MapPin,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react'
import {
  analyzeAI,
  fetchIntelligence,
  fetchLocationDetail,
  fetchPlanningContext,
  fetchPrediction,
  fetchScore,
  fetchValuationCore,
  fetchValuationLogic,
} from '../api'
import {
  compactText,
  formatCurrency,
  formatDistance,
  formatLabel,
  formatMarkdown,
  formatNumber,
  formatPercent,
  locationLabel,
  locationSecondaryLabel,
  scoreColor,
} from '../utils'
import './DetailsPanel.css'

import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
)

const COMPONENT_COLORS = {
  land_value: '#f3a93d',
  development_potential: '#49a5cf',
  future_appreciation: '#26c28c',
}

const FINGERPRINT_METRICS = [
  { key: 'land_value_score', label: 'Land', color: '#f3a93d' },
  { key: 'development_potential_score', label: 'Build', color: '#49a5cf' },
  { key: 'future_appreciation_index', label: 'Future', color: '#26c28c' },
  { key: 'infra_score', label: 'Infra', color: '#f1b96b' },
  { key: 'price_trend_score', label: 'Trend', color: '#8cccf0' },
  { key: 'density_score', label: 'Density', color: '#9a7cf3' },
]

function getFulfilledValue(result) {
  return result?.status === 'fulfilled' ? result.value : null
}

function numericValue(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : 0
}

function toneFromScore(value, inverse = false) {
  const numeric = numericValue(value)

  if (inverse) {
    if (numeric <= 30) return 'good'
    if (numeric <= 55) return 'watch'
    return 'risk'
  }

  if (numeric >= 75) return 'good'
  if (numeric >= 50) return 'watch'
  return 'risk'
}

function describeRuleValue(value) {
  if (value === null || value === undefined || value === '') return 'N/A'
  if (typeof value === 'boolean') return value ? 'Required' : 'Optional'
  if (Array.isArray(value)) return value.map((item) => formatLabel(item)).join(' / ')
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([key, nestedValue]) => `${formatLabel(key)} ${describeRuleValue(nestedValue)}`)
      .join(' / ')
  }
  return String(value)
}

function ruleEntries(record = {}) {
  return Object.entries(record).map(([key, value]) => ({
    key,
    label: formatLabel(key),
    value: describeRuleValue(value),
  }))
}

function standardKey(item, index) {
  if (item && typeof item === 'object') {
    return String(item.id ?? item.code ?? item.title ?? index)
  }
  return `${String(item)}-${index}`
}

function standardLabel(item) {
  if (!item) return 'Standard'
  if (typeof item === 'string') return item
  return item.title || item.code || formatLabel(item.standard_type) || 'Standard'
}

function buildOrbitGradient(components) {
  const totalContribution = components.reduce(
    (total, component) => total + Math.max(numericValue(component.contribution), 0),
    0,
  )

  if (!totalContribution) {
    return 'conic-gradient(rgba(255, 255, 255, 0.1) 0 100%)'
  }

  let cursor = 0
  const segments = components.map((component) => {
    const share = (Math.max(numericValue(component.contribution), 0) / totalContribution) * 100
    const start = cursor
    cursor += share
    const color = COMPONENT_COLORS[component.key] || '#cbd5e1'
    return `${color} ${start}% ${cursor}%`
  })

  return `conic-gradient(${segments.join(', ')})`
}

function ScoreTile({ label, value, tone = 'ink', max = 100, helper = '' }) {
  const numeric = numericValue(value)
  const isNumeric = value !== 'N/A' && value !== ''
  const pct = Math.min(100, Math.max(0, (numeric / max) * 100))

  return (
    <div className="score-tile">
      <span className="score-tile-label">{label}</span>
      <strong className={`score-tile-value ${tone}`}>{value}</strong>
      {helper ? <span className="score-tile-helper">{helper}</span> : null}
      {isNumeric ? (
        <div className="score-tile-bar">
          <div className={`score-tile-fill ${tone}`} style={{ '--pct': `${pct}%` }} />
        </div>
      ) : null}
    </div>
  )
}

function SignalList({ title, items, tone = 'neutral', isOpen, onToggle }) {
  if (!items?.length) return null

  return (
    <article className={`signal-list collapsible ${tone} ${isOpen ? 'is-open' : ''}`}>
      <button
        type="button"
        className="accordion-toggle"
        onClick={onToggle}
        aria-expanded={isOpen}
      >
        <div className="accordion-copy">
          <div className="accordion-title-row">
            <h4>{title}</h4>
            <span className="accordion-count">{items.length}</span>
          </div>
          <p className="accordion-preview">{compactText(items[0], '', 82)}</p>
        </div>
        <ChevronDown size={16} className="accordion-icon" />
      </button>

      {isOpen ? (
        <div className="accordion-body">
          <ul>
            {items.map((item, index) => (
              <li key={`${title}-${index}`}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  )
}

export default function DetailsPanel({ activeId, locations, rankings, hotspots }) {
  const [payload, setPayload] = useState({
    detail: null,
    score: null,
    intelligence: null,
    core: null,
    logic: null,
    prediction: null,
    planningContext: null,
  })
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [analysisError, setAnalysisError] = useState('')
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [expandedPanels, setExpandedPanels] = useState({
    strengths: true,
    risks: false,
    opportunities: false,
    ai: true,
  })

  useEffect(() => {
    if (!activeId) {
      setPayload({
        detail: null,
        score: null,
        intelligence: null,
        core: null,
        logic: null,
        prediction: null,
        planningContext: null,
      })
      setLoadError('')
      setAnalysis(null)
      setAnalysisError('')
      setAnalysisLoading(false)
      setExpandedPanels({
        strengths: true,
        risks: false,
        opportunities: false,
        ai: true,
      })
      return
    }

    let cancelled = false
    setLoading(true)
    setLoadError('')
    setAnalysis(null)
    setAnalysisError('')
    setExpandedPanels({
      strengths: true,
      risks: false,
      opportunities: false,
      ai: true,
    })

    Promise.allSettled([
      fetchLocationDetail(activeId),
      fetchScore(activeId),
      fetchIntelligence(activeId),
      fetchValuationCore(activeId),
      fetchValuationLogic(activeId),
      fetchPrediction(activeId),
      fetchPlanningContext(activeId),
    ])
      .then((results) => {
        if (cancelled) return

        const detail = getFulfilledValue(results[0])
        const score = getFulfilledValue(results[1])

        if (!detail || !score) {
          setLoadError('Core location intelligence could not be loaded for this market.')
          return
        }

        setPayload({
          detail,
          score,
          intelligence: getFulfilledValue(results[2]),
          core: getFulfilledValue(results[3]),
          logic: getFulfilledValue(results[4]),
          prediction: getFulfilledValue(results[5]),
          planningContext: getFulfilledValue(results[6]),
        })
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setLoadError('Core location intelligence could not be loaded for this market.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [activeId])

  const selectedLocation = activeId ? locations[activeId] : null
  const overviewLeaders = rankings.slice(0, 4)
  const overviewHotspots = hotspots.slice(0, 3)
  const stateCount = useMemo(() => (
    new Set(Object.values(locations).map((location) => location.state).filter(Boolean)).size
  ), [locations])

  const priceTrendData = useMemo(() => {
    const history = [...(payload.detail?.price_history || [])]
      .sort((left, right) => new Date(left.recorded_date) - new Date(right.recorded_date))

    if (history.length < 2) return null

    return {
      labels: history.map((entry) => entry.recorded_date),
      datasets: [
        {
          label: 'Price / sqft',
          data: history.map((entry) => entry.price_per_sqft),
          fill: true,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.12)',
          tension: 0.35,
          pointRadius: 3,
        },
      ],
    }
  }, [payload.detail])

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: '#94a3b8', font: { family: 'Montserrat', size: 10 } },
        grid: { color: 'rgba(148, 163, 184, 0.08)' },
      },
      y: {
        ticks: { color: '#94a3b8', font: { family: 'Montserrat', size: 10 } },
        grid: { color: 'rgba(148, 163, 184, 0.08)' },
      },
    },
  }

  function togglePanel(panel) {
    setExpandedPanels((current) => ({
      ...current,
      [panel]: !current[panel],
    }))
  }

  async function runAnalysis() {
    if (!activeId || analysisLoading) return

    setAnalysisLoading(true)
    setAnalysisError('')

    try {
      const result = await analyzeAI(activeId)
      setAnalysis(result)
    } catch (error) {
      console.error(error)
      setAnalysisError('AI deep dive is unavailable for this market right now.')
    } finally {
      setAnalysisLoading(false)
    }
  }

  if (!activeId) {
    return (
      <div className="details-overview stagger-children">
        <section className="hero-card overview-hero">
          <div>
            <p className="eyebrow">National overview</p>
            <h3>Pick a market to decode it.</h3>
          </div>
          <p>Open any market to see how the score is built, how the masterplan is translated, and where the next move sits.</p>
        </section>

        <section className="overview-grid">
          <ScoreTile label="Tracked markets" value={formatNumber(rankings.length || Object.keys(locations).length)} />
          <ScoreTile label="States" value={formatNumber(stateCount)} />
          <ScoreTile label="Hotspot clusters" value={formatNumber(hotspots.length)} />
          <ScoreTile
            label="Lead score"
            value={overviewLeaders[0] ? overviewLeaders[0].land_value_score.toFixed(0) : 'N/A'}
            tone="green"
          />
        </section>

        <section className="details-section">
          <div className="section-heading">
            <TrendingUp size={18} />
            <h4>Top ranked markets</h4>
          </div>
          <div className="leaderboard-list">
            {overviewLeaders.map((market) => (
              <article key={market.location_id} className="leaderboard-row">
                <div className="leaderboard-copy">
                  <strong>{market.location}</strong>
                  <span>{formatLabel(market.zoning_type)} zone</span>
                </div>
                <div className="leaderboard-meter">
                  <span
                    className="leaderboard-fill"
                    style={{ '--pct': `${market.land_value_score}%`, '--tone': scoreColor(market.land_value_score) }}
                  />
                </div>
                <b style={{ color: scoreColor(market.land_value_score) }}>{market.land_value_score.toFixed(0)}</b>
              </article>
            ))}
            {overviewLeaders.length === 0 ? <p className="muted-copy">Rankings are still loading.</p> : null}
          </div>
        </section>

        <section className="details-section">
          <div className="section-heading">
            <Zap size={18} />
            <h4>Hotspot corridors</h4>
          </div>
          <div className="leaderboard-list">
            {overviewHotspots.map((hotspot) => (
              <article key={hotspot.cluster_id} className="leaderboard-row">
                <div className="leaderboard-copy">
                  <strong>{formatLabel(hotspot.label)}</strong>
                  <span>{hotspot.cluster_size} markets in cluster</span>
                </div>
                <div className="leaderboard-meter">
                  <span
                    className="leaderboard-fill"
                    style={{ '--pct': `${hotspot.hotspot_score}%`, '--tone': scoreColor(hotspot.hotspot_score) }}
                  />
                </div>
                <b>{hotspot.hotspot_score.toFixed(0)}</b>
              </article>
            ))}
            {overviewHotspots.length === 0 ? <p className="muted-copy">Hotspot clustering is not available yet.</p> : null}
          </div>
        </section>
      </div>
    )
  }

  if (loading) return <div className="panel-loading"><span className="spinner" /></div>
  if (loadError) return <div className="panel-error"><AlertTriangle size={22} /><p>{loadError}</p></div>

  const { detail, score, intelligence, core, logic, prediction, planningContext } = payload
  if (!detail || !score) return null

  const displayedLogic = logic?.logic || core?.logic
  const selectedName = locationLabel(selectedLocation || detail.location)
  const locationMeta = locationSecondaryLabel(selectedLocation || detail.location)
  const nearbyInfrastructure = detail.nearby_infrastructure || []
  const weightedComponents = displayedLogic?.weighted_components || []
  const weightedScore = numericValue(displayedLogic?.weighted_score ?? core?.scores?.overall_favorability_score)
  const weightedBand = displayedLogic?.weighted_band || core?.positioning?.favorability_band || 'N/A'
  const orbitGradient = buildOrbitGradient(weightedComponents)
  const fingerprintMetrics = FINGERPRINT_METRICS.map((metric) => ({
    ...metric,
    value: numericValue(score.components?.[metric.key] ?? score[metric.key]),
  }))
  const outlookDrivers = prediction?.drivers || core?.forward_outlook?.drivers || []
  const planningRules = [
    ...ruleEntries(planningContext?.floor_plan_constraints),
    ...ruleEntries(planningContext?.zoning_validation_rules),
  ].slice(0, 8)
  const regionalStandards = (detail.regional_standards || []).slice(0, 4)
  const envelopeSummary = [
    detail.masterplan?.fsi ? `FSI ${detail.masterplan.fsi}` : null,
    detail.masterplan?.max_height_m ? `${detail.masterplan.max_height_m}m` : null,
    detail.masterplan?.ground_coverage_pct ? `${detail.masterplan.ground_coverage_pct}% coverage` : null,
  ].filter(Boolean).join(' · ') || 'Envelope pending'
  const setbackSummary = [
    detail.masterplan?.setback_front_m ? `Front ${detail.masterplan.setback_front_m}m` : null,
    detail.masterplan?.setback_side_m ? `Side ${detail.masterplan.setback_side_m}m` : null,
  ].filter(Boolean).join(' · ') || 'Context-based setbacks'
  const masterplanSteps = [
    {
      key: 'zone',
      label: 'Zone',
      value: formatLabel(detail.masterplan?.zoning_type || selectedLocation?.zoning_type),
    },
    {
      key: 'envelope',
      label: 'Envelope',
      value: compactText(envelopeSummary, 'Envelope pending', 52),
    },
    {
      key: 'rules',
      label: 'Rules',
      value: planningRules.length ? `${planningRules.length} local filters applied` : 'No linked rule set',
    },
    {
      key: 'fit',
      label: 'Fit',
      value: formatLabel(core?.positioning?.recommended_use_case || displayedLogic?.execution_strategy),
    },
  ]
  const readinessSignals = [
    { label: 'Location intelligence', value: planningContext?.location_intelligence_score, inverse: false },
    { label: 'Climate resilience', value: intelligence?.climate_resilience_score, inverse: false },
    { label: 'Terrain readiness', value: intelligence?.terrain_readiness_score, inverse: false },
    { label: 'Data confidence', value: intelligence?.data_confidence_score || displayedLogic?.data_confidence_score, inverse: false },
    { label: 'Site risk', value: core?.scores?.site_risk_score, inverse: true },
    { label: 'Flood risk', value: intelligence?.flood_risk_score ?? detail.geo_profile?.flood_risk_score, inverse: true },
  ]
  const marketContext = [
    { label: 'Population', value: formatNumber(detail.census?.population) },
    { label: 'Growth rate', value: formatPercent(detail.census?.growth_rate_pct) },
    { label: 'Density / sqkm', value: formatNumber(detail.census?.density_per_sqkm) },
    { label: 'Avg. price / sqft', value: formatCurrency(detail.avg_price_per_sqft) },
  ]
  const contributionTotal = weightedComponents.reduce(
    (total, component) => total + Math.max(numericValue(component.contribution), 0),
    0,
  )
  const driverMax = Math.max(
    ...outlookDrivers.map((driver) => Math.abs(numericValue(driver.contribution))),
    1,
  )

  return (
    <div className="details-container stagger-children">
      <section className="hero-card detail-hero">
        <div className="hero-main">
          <div>
            <p className="eyebrow">Location intelligence</p>
            <h3>{selectedName}</h3>
            <div className="hero-meta">
              <span><MapPin size={14} /> {locationMeta || 'Mapped location'}</span>
              <span><Building2 size={14} /> {formatLabel(detail.masterplan?.zoning_type || selectedLocation?.zoning_type)}</span>
              <span><ShieldCheck size={14} /> {formatLabel(core?.positioning?.recommended_use_case || 'market fit pending')}</span>
            </div>
          </div>

          <div className="hero-score-pill">
            <span>Weighted score</span>
            <strong>{weightedScore ? weightedScore.toFixed(1) : 'N/A'}</strong>
            <small>{formatLabel(weightedBand)}</small>
          </div>
        </div>

        <p className="hero-summary">
          {compactText(core?.key_insight || core?.summary, 'Pricing, planning, infrastructure, and risk in one view.', 132)}
        </p>
      </section>

      <section className="overview-grid">
        <ScoreTile label="Land value" value={score.land_value_score.toFixed(0)} tone="amber" />
        <ScoreTile label="Dev potential" value={score.development_potential_score.toFixed(0)} tone="teal" />
        <ScoreTile label="Future app." value={score.future_appreciation_index.toFixed(0)} tone="green" />
        <ScoreTile
          label="Overall favorability"
          value={weightedScore ? weightedScore.toFixed(1) : 'N/A'}
          tone="ink"
          helper={formatLabel(weightedBand)}
        />
      </section>

      <section className="visual-grid">
        <article className="details-section">
          <div className="section-heading">
            <Gauge size={18} />
            <h4>Score interpretation</h4>
          </div>

          <div className="score-composer">
            <div className="score-orbit" style={{ '--orbit-fill': orbitGradient }}>
              <div className="score-orbit-center">
                <span>Weighted</span>
                <strong>{weightedScore ? weightedScore.toFixed(1) : 'N/A'}</strong>
                <small>{formatLabel(weightedBand)}</small>
              </div>
            </div>

            <div className="weighted-stack">
              {weightedComponents.map((component) => {
                const color = COMPONENT_COLORS[component.key] || '#cbd5e1'
                const contributionShare = contributionTotal
                  ? (Math.max(numericValue(component.contribution), 0) / contributionTotal) * 100
                  : 0

                return (
                  <div key={component.key} className="weighted-row">
                    <div className="weighted-meta">
                      <div>
                        <strong>{component.label}</strong>
                        <span>{Math.round(numericValue(component.weight) * 100)}% weight</span>
                      </div>
                      <b>{numericValue(component.contribution).toFixed(1)}</b>
                    </div>
                    <div className="weighted-track">
                      <span style={{ '--pct': `${numericValue(component.value)}%`, '--tone': color }} />
                    </div>
                    <div className="weighted-foot">
                      <span>{numericValue(component.value).toFixed(0)} score</span>
                      <span>{contributionShare.toFixed(0)}% of total</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {displayedLogic?.rule_hits?.length ? (
            <div className="rule-hit-grid">
              {displayedLogic.rule_hits.map((rule) => (
                <article key={rule.code} className={`rule-hit-card ${rule.effect}`}>
                  <span>{formatLabel(rule.code)}</span>
                  <strong>{formatLabel(rule.effect)}</strong>
                </article>
              ))}
            </div>
          ) : null}
        </article>

        <article className="details-section">
          <div className="section-heading">
            <BarChart3 size={18} />
            <h4>Market fingerprint</h4>
          </div>

          <div className="fingerprint-chart">
            {fingerprintMetrics.map((metric) => (
              <div key={metric.key} className="fingerprint-column">
                <div className="fingerprint-track">
                  <span style={{ '--pct': `${metric.value}%`, '--tone': metric.color }} />
                </div>
                <strong>{metric.value.toFixed(0)}</strong>
                <span>{metric.label}</span>
              </div>
            ))}
          </div>

          <p className="section-copy">
            {compactText(core?.summary, 'The market fingerprint compares value, build readiness, demand, and price momentum in one scan.', 132)}
          </p>
        </article>
      </section>

      <section className="chart-grid">
        <article className="details-section">
          <div className="section-heading">
            <TrendingUp size={18} />
            <h4>Recorded price path</h4>
          </div>
          <div className="chart-box">
            {priceTrendData ? <Line data={priceTrendData} options={lineOptions} /> : <p className="muted-copy">Not enough price history points to chart a trend.</p>}
          </div>
        </article>

        <article className="details-section">
          <div className="section-heading">
            <TrendingUp size={18} />
            <h4>Forward outlook</h4>
          </div>

          <div className="mini-data-grid">
            <div className="mini-data-card">
              <span>Signal</span>
              <strong>{formatLabel(prediction?.signal || core?.forward_outlook?.signal)}</strong>
            </div>
            <div className="mini-data-card">
              <span>Confidence</span>
              <strong>{formatLabel(prediction?.confidence || core?.forward_outlook?.confidence)}</strong>
            </div>
            <div className="mini-data-card">
              <span>Current</span>
              <strong>{formatCurrency(prediction?.current_avg_price ?? detail.avg_price_per_sqft)}</strong>
            </div>
            <div className="mini-data-card">
              <span>1Y upside</span>
              <strong>{formatPercent(prediction?.predicted_upside_pct ?? core?.forward_outlook?.predicted_upside_pct)}</strong>
            </div>
            <div className="mini-data-card">
              <span>1Y target</span>
              <strong>{formatCurrency(prediction?.predicted_price_1yr ?? core?.forward_outlook?.predicted_price_1yr)}</strong>
            </div>
            <div className="mini-data-card">
              <span>3Y target</span>
              <strong>{formatCurrency(prediction?.predicted_price_3yr ?? core?.forward_outlook?.predicted_price_3yr)}</strong>
            </div>
          </div>

          <div className="driver-stack">
            {outlookDrivers.map((driver) => {
              const barPct = (Math.abs(numericValue(driver.contribution)) / driverMax) * 100
              const tone = driver.direction === 'negative'
                ? 'var(--red)'
                : driver.direction === 'neutral'
                  ? 'var(--amber)'
                  : 'var(--green)'

              return (
                <div key={driver.key} className="driver-row">
                  <div className="driver-head">
                    <span>{driver.label}</span>
                    <strong>{numericValue(driver.value).toFixed(0)}</strong>
                  </div>
                  <div className="driver-track">
                    <span style={{ '--pct': `${barPct}%`, '--tone': tone }} />
                  </div>
                </div>
              )
            })}
          </div>
        </article>
      </section>

      <section className="details-grid">
        <article className="details-section">
          <div className="section-heading">
            <Building2 size={18} />
            <h4>Masterplan interpretation</h4>
          </div>

          <div className="envelope-grid">
            <div className="envelope-tile">
              <span>FSI / FAR</span>
              <strong>{detail.masterplan?.fsi || intelligence?.fsi || 'N/A'}</strong>
            </div>
            <div className="envelope-tile">
              <span>Height</span>
              <strong>{detail.masterplan?.max_height_m ? `${detail.masterplan.max_height_m}m` : 'N/A'}</strong>
            </div>
            <div className="envelope-tile">
              <span>Coverage</span>
              <strong>{detail.masterplan?.ground_coverage_pct ? `${detail.masterplan.ground_coverage_pct}%` : 'N/A'}</strong>
            </div>
            <div className="envelope-tile">
              <span>Version</span>
              <strong>{planningContext?.version_tag || intelligence?.planning_context_version || 'N/A'}</strong>
            </div>
          </div>

          <div className="plan-flow">
            {masterplanSteps.map((step, index) => (
              <article key={step.key} className="plan-step">
                <span className="plan-step-index">0{index + 1}</span>
                <strong>{step.label}</strong>
                <p>{step.value}</p>
              </article>
            ))}
          </div>

          <div className="rule-chip-grid">
            {planningRules.map((rule) => (
              <div key={rule.key} className="rule-chip">
                <span>{rule.label}</span>
                <strong>{rule.value}</strong>
              </div>
            ))}
            {!planningRules.length ? <p className="muted-copy">No planning rule bundle is linked to this market yet.</p> : null}
          </div>

          {regionalStandards.length ? (
            <div className="standards-strip">
              {regionalStandards.map((item, index) => (
                <span key={standardKey(item, index)} className="standard-chip">
                  {standardLabel(item)}
                </span>
              ))}
            </div>
          ) : null}

          <p className="section-copy">
            {compactText(planningContext?.source_summary || setbackSummary, 'Masterplan translation condenses zoning, build envelope, setbacks, and execution fit.', 148)}
          </p>
        </article>

        <article className="details-section">
          <div className="section-heading">
            <CloudSun size={18} />
            <h4>Site + market context</h4>
          </div>

          <div className="compact-stat-grid">
            {readinessSignals.map((signal) => {
              const tone = toneFromScore(signal.value, signal.inverse)

              return (
                <article key={signal.label} className={`metric-card ${tone}`}>
                  <span>{signal.label}</span>
                  <strong>{formatPercent(signal.value, 0)}</strong>
                  <div className="metric-card-bar">
                    <span style={{ '--pct': `${numericValue(signal.value)}%` }} />
                  </div>
                </article>
              )
            })}
          </div>

          <div className="market-mini-grid">
            {marketContext.map((item) => (
              <div key={item.label} className="mini-data-card">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="details-section">
          <div className="section-heading">
            <Zap size={18} />
            <h4>Nearby infrastructure</h4>
          </div>
          <div className="catchment-list large">
            {nearbyInfrastructure.slice(0, 5).map((item, index) => (
              <div key={`${item.name}-${item.distance_km}-${index}`} className="catchment-row">
                <div>
                  <strong>{item.name}</strong>
                  <span>{formatLabel(item.infra_type)} • {formatLabel(item.status)}</span>
                </div>
                <strong>{formatDistance(item.distance_km)}</strong>
              </div>
            ))}
            {nearbyInfrastructure.length === 0 ? <p className="muted-copy">No nearby infrastructure was returned for this location.</p> : null}
          </div>
        </article>
      </section>

      <section className="signal-stack">
        <SignalList
          title="Strengths"
          items={core?.strengths}
          tone="strong"
          isOpen={expandedPanels.strengths}
          onToggle={() => togglePanel('strengths')}
        />
        <SignalList
          title="Risks"
          items={core?.risks}
          tone="risk"
          isOpen={expandedPanels.risks}
          onToggle={() => togglePanel('risks')}
        />
        <SignalList
          title="Opportunities"
          items={core?.opportunities}
          tone="watch"
          isOpen={expandedPanels.opportunities}
          onToggle={() => togglePanel('opportunities')}
        />
      </section>

      <section className="details-section accordion-section">
        <button
          type="button"
          className="accordion-toggle section-toggle"
          onClick={() => togglePanel('ai')}
          aria-expanded={expandedPanels.ai}
        >
          <div className="accordion-copy">
            <div className="section-heading compact">
              <Sparkles size={18} />
              <h4>AI deep dive</h4>
            </div>
            <p className="accordion-preview">
              {analysis
                ? 'AI brief is ready. Open to review the summary and recommended questions.'
                : 'Run a market brief only when you want the expanded AI readout.'}
            </p>
          </div>
          <ChevronDown size={16} className="accordion-icon" />
        </button>

        {expandedPanels.ai ? (
          <div className="accordion-body section-body">
            <button className="ai-analyze-btn" onClick={runAnalysis} disabled={analysisLoading}>
              <Sparkles size={17} />
              <span>{analysisLoading ? 'Generating...' : 'Run AI brief'}</span>
            </button>

            {analysisError ? <p className="panel-inline-error">{analysisError}</p> : null}

            {analysis ? (
              <div className="analysis-shell">
                <div className="analysis-card-grid">
                  {analysis.cards?.map((card) => (
                    <article key={`${card.label}-${card.value}`} className={`insight-card tone-${card.tone}`}>
                      <span>{card.label}</span>
                      <strong>{card.value}</strong>
                    </article>
                  ))}
                </div>

                <div
                  className="analysis-markdown"
                  dangerouslySetInnerHTML={{ __html: formatMarkdown(analysis.analysis) }}
                />

                {analysis.recommended_questions?.length ? (
                  <div className="question-strip">
                    {analysis.recommended_questions.slice(0, 3).map((question, index) => (
                      <span key={`${question}-${index}`} className="question-chip">{question}</span>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>
    </div>
  )
}
