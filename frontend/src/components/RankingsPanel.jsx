import { useDeferredValue, useMemo, useState } from 'react'
import {
  GitCompareArrows,
  Search,
  SlidersHorizontal,
  Sparkles,
  Trophy,
  X,
} from 'lucide-react'
import { formatLabel, scoreHex } from '../utils'
import './RankingsPanel.css'

const SORT_OPTIONS = [
  { value: 'land_value_score', label: 'Land Value' },
  { value: 'development_potential_score', label: 'Development Potential' },
  { value: 'future_appreciation_index', label: 'Future Appreciation' },
]

const CARD_METRICS = [
  { key: 'land_value_score', label: 'Land' },
  { key: 'development_potential_score', label: 'Build' },
  { key: 'future_appreciation_index', label: 'Future' },
]

function averageScore(rows, key) {
  if (!rows.length) return 0
  return rows.reduce((total, row) => total + (Number(row[key]) || 0), 0) / rows.length
}

export default function RankingsPanel({
  rankings,
  loading,
  error,
  sortBy,
  onSortChange,
  activeId,
  compareIds,
  compareMode,
  onToggleCompareMode,
  onToggleCompareId,
  onOpenCompare,
  onSelect,
  isOpen,
  onClose,
}) {
  const [search, setSearch] = useState('')
  const deferredSearch = useDeferredValue(search.trim().toLowerCase())

  const filteredRankings = useMemo(() => (
    rankings.filter((row) => (
      !deferredSearch || row.location.toLowerCase().includes(deferredSearch)
    ))
  ), [deferredSearch, rankings])

  const leadMarket = filteredRankings[0] || rankings[0] || null
  const futureLeader = useMemo(() => {
    if (!rankings.length) return null
    return [...rankings].sort((left, right) => right.future_appreciation_index - left.future_appreciation_index)[0]
  }, [rankings])

  const activeLens = SORT_OPTIONS.find((option) => option.value === sortBy) || SORT_OPTIONS[0]
  const visibleAverage = useMemo(
    () => averageScore(filteredRankings, sortBy),
    [filteredRankings, sortBy],
  )

  return (
    <aside className={`rankings-panel glass ${isOpen ? 'mobile-open' : ''}`}>
      <div className="rankings-header">
        <div>
          <p className="eyebrow">Market Board</p>
          <h2 className="display-heading">Signals by market</h2>
        </div>
        <button className="close-mobile" onClick={onClose} aria-label="Close market list">
          <X size={18} />
        </button>
      </div>

      <div className="rail-summary">
        <article className="summary-card">
          <span className="summary-label">Lead market</span>
          <strong>{leadMarket?.location || 'Refreshing'}</strong>
          <p>{leadMarket ? `${formatLabel(leadMarket.zoning_type)} zone` : 'Waiting for rankings.'}</p>
        </article>

        <article className="summary-card">
          <span className="summary-label">Future leader</span>
          <strong>{futureLeader?.future_appreciation_index?.toFixed(0) || '--'}</strong>
          <p>{futureLeader?.location || 'Loading market'}</p>
        </article>

        <article className="summary-card compact">
          <span className="summary-label">Visible set</span>
          <strong>{filteredRankings.length || 0}</strong>
          <p>{filteredRankings.length ? `${activeLens.label} avg ${visibleAverage.toFixed(0)}` : 'No markets in view'}</p>
        </article>
      </div>

      <div className="rankings-toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search city, corridor, or locality"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>

        <div className="compare-banner">
          <button
            className={`compare-toggle ${compareMode ? 'active' : ''}`}
            onClick={onToggleCompareMode}
          >
            <GitCompareArrows size={16} />
            <span>{compareMode ? 'Pinning on' : 'Pin markets'}</span>
          </button>
          <span className="compare-count">{compareIds.length}/3 pinned</span>
          <button
            className="compare-open"
            onClick={onOpenCompare}
            disabled={compareIds.length < 2}
          >
            Compare
          </button>
        </div>
      </div>

      <div className="sort-strip">
        <div className="sort-label">
          <SlidersHorizontal size={15} />
          <span>Score lens</span>
        </div>
        <div className="sort-pills">
          {SORT_OPTIONS.map((option) => (
            <button
              key={option.value}
              className={`sort-pill ${sortBy === option.value ? 'active' : ''}`}
              onClick={() => onSortChange(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rankings-list">
        {loading ? (
          <div className="panel-state"><span className="spinner" /></div>
        ) : null}

        {!loading && error ? (
          <div className="panel-state error">{error}</div>
        ) : null}

        {!loading && !error && filteredRankings.length === 0 ? (
          <div className="panel-state">{search ? 'No markets match that search.' : 'No rankings available.'}</div>
        ) : null}

        {!loading && !error && filteredRankings.length > 0 ? (
          <div className="scroll-container">
            {filteredRankings.map((row) => {
              const isActive = row.location_id === activeId
              const isCompared = compareIds.includes(row.location_id)
              const displayScore = Number(row[sortBy]) || 0
              const compareDisabled = !isCompared && compareIds.length >= 3
              const cardMetrics = CARD_METRICS.map((metric) => ({
                ...metric,
                value: Number(row[metric.key]) || 0,
              }))

              return (
                <article
                  key={row.location_id}
                  className={`ranking-card ${isActive ? 'active' : ''}`}
                  onClick={() => onSelect(row.location_id)}
                >
                  <div className="ranking-card-head">
                    <div className="ranking-title-wrap">
                      <div className="rank-badge">
                        <Trophy size={13} />
                        <span>#{row.rank}</span>
                      </div>

                      <div className="ranking-title-group">
                        <h3>{row.location}</h3>
                        <p>{formatLabel(row.zoning_type)} zone</p>
                      </div>
                    </div>

                    <div className="ranking-card-actions">
                      <button
                        className={`pin-chip ${isCompared ? 'selected' : ''}`}
                        disabled={compareDisabled}
                        onClick={(event) => {
                          event.stopPropagation()
                          onToggleCompareId(row.location_id)
                        }}
                      >
                        {isCompared ? 'Pinned' : compareMode ? 'Pick' : 'Pin'}
                      </button>

                      <div className="ranking-score-block">
                        <span>{activeLens.label}</span>
                        <strong style={{ color: scoreHex(displayScore) }}>{displayScore.toFixed(0)}</strong>
                      </div>
                    </div>
                  </div>

                  <div className="ranking-fingerprint" aria-hidden>
                    {cardMetrics.map((metric) => (
                      <div
                        key={metric.key}
                        className={`fingerprint-lane ${sortBy === metric.key ? 'active' : ''}`}
                      >
                        <span
                          className="fingerprint-fill"
                          style={{ '--pct': `${metric.value}%`, '--tone': scoreHex(metric.value) }}
                        />
                      </div>
                    ))}
                  </div>

                  <div className="fingerprint-labels">
                    {cardMetrics.map((metric) => (
                      <div
                        key={metric.key}
                        className={`fingerprint-stat ${sortBy === metric.key ? 'active' : ''}`}
                      >
                        <span>{metric.label}</span>
                        <strong>{metric.value.toFixed(0)}</strong>
                      </div>
                    ))}
                  </div>
                </article>
              )
            })}

            <div className="rail-footer-note">
              <Sparkles size={15} />
              <span>Click a row to open its score and masterplan interpretation.</span>
            </div>
          </div>
        ) : null}
      </div>
    </aside>
  )
}
