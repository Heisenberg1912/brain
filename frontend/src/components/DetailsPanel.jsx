import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  BarChart3,
  Building2,
  ChevronDown,
  CloudSun,
  Database,
  Gauge,
  MapPin,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
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
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  RadarController,
  RadialLinearScale,
  Tooltip,
} from 'chart.js'
import { Line, Radar } from 'react-chartjs-2'

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

function getFulfilledValue(result) {
  return result?.status === 'fulfilled' ? result.value : null
}

function ScoreTile({ label, value, tone }) {
  return (
    <div className="score-tile">
      <span className="score-tile-label">{label}</span>
      <strong className={`score-tile-value ${tone}`}>{value}</strong>
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
            {items.map((item) => (
              <li key={item}>{item}</li>
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

  const radarData = useMemo(() => {
    const score = payload.score
    if (!score) return null

    return {
      labels: ['Land Value', 'Dev Potential', 'Future App.', 'Infra', 'Price Trend', 'Density'],
      datasets: [
        {
          label: score.location,
          data: [
            score.land_value_score,
            score.development_potential_score,
            score.future_appreciation_index,
            score.components?.infra_score || 0,
            score.components?.price_trend_score || 0,
            score.components?.density_score || 0,
          ],
          backgroundColor: 'rgba(23, 184, 151, 0.16)',
          borderColor: '#17b897',
          pointBackgroundColor: '#17b897',
          borderWidth: 2,
        },
      ],
    }
  }, [payload.score])

  const radarOptions = {
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
          font: { family: 'Montserrat', size: 11, weight: '600' },
        },
        ticks: { display: false },
      },
    },
    plugins: {
      legend: { display: false },
    },
  }

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

  if (!activeId) {
    return (
      <div className="details-overview">
        <section className="hero-card">
          <p className="eyebrow">National command center</p>
          <h3>Select a market to brief it.</h3>
          <p>Overview, compare, AI, and registry tools stay live in this panel.</p>
        </section>

        <section className="overview-grid">
          <ScoreTile label="Tracked markets" value={formatNumber(rankings.length || Object.keys(locations).length)} />
          <ScoreTile label="Mapped hotspots" value={formatNumber(hotspots.length)} />
          <ScoreTile label="Top score leader" value={overviewLeaders[0]?.location || 'N/A'} />
          <ScoreTile label="Lead cluster" value={overviewHotspots[0] ? formatLabel(overviewHotspots[0].label) : 'N/A'} />
        </section>

        <section className="details-section">
          <div className="section-heading">
            <TrendingUp size={18} />
            <h4>Top ranked markets</h4>
          </div>
          <div className="overview-card-grid">
            {overviewLeaders.map((market) => (
              <article key={market.location_id} className="mini-card">
                <div>
                  <strong>{market.location}</strong>
                  <span>{formatLabel(market.zoning_type)} zone</span>
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
          <div className="overview-card-grid">
            {overviewHotspots.map((hotspot) => (
              <article key={hotspot.cluster_id} className="mini-card">
                <div>
                  <strong>{formatLabel(hotspot.label)}</strong>
                  <span>{hotspot.cluster_size} locations in cluster</span>
                </div>
                <b>{hotspot.hotspot_score.toFixed(0)}</b>
              </article>
            ))}
            {overviewHotspots.length === 0 ? <p className="muted-copy">Hotspot clustering is not available yet.</p> : null}
          </div>
        </section>

        <section className="details-section">
          <div className="section-heading">
            <Database size={18} />
            <h4>Visible product surfaces</h4>
          </div>
          <div className="surface-grid">
            <article className="surface-card">
              <strong>Spatial view</strong>
              <span>Map, heat, infra</span>
            </article>
            <article className="surface-card">
              <strong>Planning + valuation</strong>
              <span>Planning, pricing, risk</span>
            </article>
            <article className="surface-card">
              <strong>AI layer</strong>
              <span>Brief, chat, deep dive</span>
            </article>
            <article className="surface-card">
              <strong>Blockchain layer</strong>
              <span>Plans, listings, assets</span>
            </article>
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

  return (
    <div className="details-container">
      <section className="hero-card detail-hero">
        <div>
          <p className="eyebrow">Location intelligence</p>
          <h3>{selectedName}</h3>
          <div className="hero-meta">
            <span><MapPin size={14} /> {locationMeta || 'Mapped location'}</span>
            <span><Building2 size={14} /> {formatLabel(detail.masterplan?.zoning_type || selectedLocation?.zoning_type)}</span>
            <span><ShieldCheck size={14} /> {formatLabel(core?.positioning?.recommended_use_case || 'market fit pending')}</span>
          </div>
        </div>
        <p className="hero-summary">
          {compactText(core?.key_insight || core?.summary, 'Pricing, planning, infrastructure, and risk in one view.', 110)}
        </p>
      </section>

      <section className="overview-grid">
        <ScoreTile label="Land value" value={score.land_value_score.toFixed(0)} tone="green" />
        <ScoreTile label="Dev potential" value={score.development_potential_score.toFixed(0)} tone="teal" />
        <ScoreTile label="Future app." value={score.future_appreciation_index.toFixed(0)} tone="amber" />
        <ScoreTile
          label="Overall favorability"
          value={core?.scores?.overall_favorability_score ? core.scores.overall_favorability_score.toFixed(1) : 'N/A'}
          tone="ink"
        />
      </section>

      <section className="chart-grid">
        <div className="details-section">
          <div className="section-heading">
            <BarChart3 size={18} />
            <h4>Score profile</h4>
          </div>
          <div className="chart-box">
            {radarData ? <Radar data={radarData} options={radarOptions} /> : <p className="muted-copy">Score radar is unavailable.</p>}
          </div>
        </div>

        <div className="details-section">
          <div className="section-heading">
            <TrendingUp size={18} />
            <h4>Recorded price path</h4>
          </div>
          <div className="chart-box">
            {priceTrendData ? <Line data={priceTrendData} options={lineOptions} /> : <p className="muted-copy">Not enough price history points to chart a trend.</p>}
          </div>
        </div>
      </section>

      <section className="details-grid">
        <article className="details-section">
          <div className="section-heading">
            <Gauge size={18} />
            <h4>Decision engine</h4>
          </div>
          <div className="stats-grid">
            <div className="stat-row">
              <span>Signal</span>
              <strong>{formatLabel(displayedLogic?.investment_signal)}</strong>
            </div>
            <div className="stat-row">
              <span>Execution</span>
              <strong>{formatLabel(displayedLogic?.execution_strategy)}</strong>
            </div>
            <div className="stat-row">
              <span>Conviction</span>
              <strong>{formatLabel(displayedLogic?.conviction)}</strong>
            </div>
            <div className="stat-row">
              <span>Primary driver</span>
              <strong>{formatLabel(displayedLogic?.primary_driver)}</strong>
            </div>
          </div>
          {displayedLogic?.verdict || core?.key_insight ? (
            <p className="section-copy">
              {compactText(displayedLogic?.verdict || core?.key_insight, '', 108)}
            </p>
          ) : null}
        </article>

        <article className="details-section">
          <div className="section-heading">
            <TrendingUp size={18} />
            <h4>Forward outlook</h4>
          </div>
          <div className="stats-grid">
            <div className="stat-row">
              <span>Current avg. / sqft</span>
              <strong>{formatCurrency(prediction?.current_avg_price ?? detail.avg_price_per_sqft)}</strong>
            </div>
            <div className="stat-row">
              <span>1Y projected</span>
              <strong>{formatCurrency(prediction?.predicted_price_1yr ?? intelligence?.predicted_price_1yr)}</strong>
            </div>
            <div className="stat-row">
              <span>3Y projected</span>
              <strong>{formatCurrency(prediction?.predicted_price_3yr ?? intelligence?.predicted_price_3yr)}</strong>
            </div>
            <div className="stat-row">
              <span>Upside</span>
              <strong>{formatPercent(prediction?.predicted_upside_pct)}</strong>
            </div>
            <div className="stat-row">
              <span>Confidence</span>
              <strong>{formatLabel(prediction?.confidence || intelligence?.prediction_confidence)}</strong>
            </div>
          </div>
          {prediction?.summary || core?.forward_outlook?.summary ? (
            <p className="section-copy">
              {compactText(prediction?.summary || core?.forward_outlook?.summary, '', 108)}
            </p>
          ) : null}
        </article>

        <article className="details-section">
          <div className="section-heading">
            <Building2 size={18} />
            <h4>Planning and standards</h4>
          </div>
          <div className="stats-grid">
            <div className="stat-row">
              <span>FSI / FAR</span>
              <strong>{detail.masterplan?.fsi || intelligence?.fsi || 'N/A'}</strong>
            </div>
            <div className="stat-row">
              <span>Max height</span>
              <strong>{detail.masterplan?.max_height_m ? `${detail.masterplan.max_height_m} m` : 'N/A'}</strong>
            </div>
            <div className="stat-row">
              <span>Ground coverage</span>
              <strong>{detail.masterplan?.ground_coverage_pct ? `${detail.masterplan.ground_coverage_pct}%` : 'N/A'}</strong>
            </div>
            <div className="stat-row">
              <span>Planning context</span>
              <strong>{planningContext?.version_tag || intelligence?.planning_context_version || 'N/A'}</strong>
            </div>
            <div className="stat-row">
              <span>Standards linked</span>
              <strong>{formatNumber(detail.regional_standards?.length || 0)}</strong>
            </div>
          </div>
        </article>

        <article className="details-section">
          <div className="section-heading">
            <CloudSun size={18} />
            <h4>Site and climate</h4>
          </div>
          <div className="stats-grid">
            <div className="stat-row">
              <span>Terrain</span>
              <strong>{formatLabel(intelligence?.terrain_class || detail.geo_profile?.terrain_class)}</strong>
            </div>
            <div className="stat-row">
              <span>Slope</span>
              <strong>{intelligence?.terrain_slope_pct ? `${intelligence.terrain_slope_pct}%` : 'N/A'}</strong>
            </div>
            <div className="stat-row">
              <span>Flood risk</span>
              <strong>{formatPercent(intelligence?.flood_risk_score ?? detail.geo_profile?.flood_risk_score)}</strong>
            </div>
            <div className="stat-row">
              <span>Heat risk</span>
              <strong>{formatPercent(intelligence?.heat_risk_score ?? detail.geo_profile?.heat_risk_score)}</strong>
            </div>
            <div className="stat-row">
              <span>Climate risk</span>
              <strong>{formatPercent(intelligence?.climate_risk_score ?? detail.geo_profile?.climate_risk_score)}</strong>
            </div>
          </div>
        </article>

        <article className="details-section">
          <div className="section-heading">
            <Users size={18} />
            <h4>Demand and price context</h4>
          </div>
          <div className="stats-grid">
            <div className="stat-row">
              <span>Population</span>
              <strong>{formatNumber(detail.census?.population)}</strong>
            </div>
            <div className="stat-row">
              <span>Growth rate</span>
              <strong>{formatPercent(detail.census?.growth_rate_pct)}</strong>
            </div>
            <div className="stat-row">
              <span>Density / sqkm</span>
              <strong>{formatNumber(detail.census?.density_per_sqkm)}</strong>
            </div>
            <div className="stat-row">
              <span>Avg. price / sqft</span>
              <strong>{formatCurrency(detail.avg_price_per_sqft)}</strong>
            </div>
            <div className="stat-row">
              <span>Data confidence</span>
              <strong>{formatLabel(intelligence?.data_confidence_band || score.components?.data_confidence_band)}</strong>
            </div>
          </div>
        </article>

        <article className="details-section">
          <div className="section-heading">
            <Zap size={18} />
            <h4>Nearby infrastructure</h4>
          </div>
          <div className="catchment-list large">
            {nearbyInfrastructure.slice(0, 6).map((item) => (
              <div key={`${item.name}-${item.distance_km}`} className="catchment-row">
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
                    {analysis.recommended_questions.slice(0, 3).map((question) => (
                      <span key={question} className="question-chip">{question}</span>
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
