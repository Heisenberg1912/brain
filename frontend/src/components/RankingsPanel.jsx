import { useDeferredValue, useMemo, useState } from 'react'
import {
  ArrowRight,
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

  const filteredRankings = rankings.filter((row) => (
    !deferredSearch || row.location.toLowerCase().includes(deferredSearch)
  ))

  const leadMarket = filteredRankings[0] || rankings[0] || null
  const futureLeader = useMemo(() => {
    if (!rankings.length) return null
    return [...rankings].sort((left, right) => right.future_appreciation_index - left.future_appreciation_index)[0]
  }, [rankings])

  return (
    <aside className={`rankings-panel glass ${isOpen ? 'mobile-open' : ''}`}>
      <div className="rankings-header">
        <div>
          <p className="eyebrow">Market Board</p>
          <h2 className="display-heading">Ranked opportunities</h2>
        </div>
        <button className="close-mobile" onClick={onClose} aria-label="Close market list">
          <X size={18} />
        </button>
      </div>

      <div className="rail-spotlight">
        <article className="spotlight-card">
          <span className="spotlight-label">Lead market</span>
          <strong>{leadMarket?.location || 'Refreshing rankings'}</strong>
          <p>{leadMarket ? `${formatLabel(leadMarket.zoning_type)} zone` : 'Waiting for scores.'}</p>
        </article>

        <article className="spotlight-card compact">
          <span className="spotlight-label">Highest future upside</span>
          <strong>{futureLeader?.location || 'Loading'}</strong>
          <b style={{ color: scoreHex(futureLeader?.future_appreciation_index || 0) }}>
            {futureLeader ? futureLeader.future_appreciation_index.toFixed(0) : '--'}
          </b>
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
            <span>{compareMode ? 'Compare enabled' : 'Compare off'}</span>
          </button>
          <span className="compare-count">{compareIds.length}/3 selected</span>
          <button
            className="compare-open"
            onClick={onOpenCompare}
            disabled={compareIds.length < 2}
          >
            Open compare
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

              return (
                <article
                  key={row.location_id}
                  className={`ranking-card ${isActive ? 'active' : ''}`}
                  onClick={() => onSelect(row.location_id)}
                >
                  <div className="ranking-card-top">
                    <div className="rank-badge">
                      <Trophy size={14} />
                      <span>#{row.rank}</span>
                    </div>
                    <div className="ranking-score" style={{ color: scoreHex(displayScore) }}>
                      {displayScore.toFixed(0)}
                    </div>
                  </div>

                  <div className="ranking-title-group">
                    <h3>{row.location}</h3>
                    <p>{formatLabel(row.zoning_type)} zone</p>
                  </div>

                  <div className="ranking-bars">
                    <div className="bar-row">
                      <span>Land</span>
                      <div className="bar-track">
                        <div className="bar-fill" style={{ width: `${row.land_value_score}%` }} />
                      </div>
                      <strong>{row.land_value_score.toFixed(0)}</strong>
                    </div>
                    <div className="bar-row">
                      <span>Dev</span>
                      <div className="bar-track">
                        <div className="bar-fill alt" style={{ width: `${row.development_potential_score}%` }} />
                      </div>
                      <strong>{row.development_potential_score.toFixed(0)}</strong>
                    </div>
                    <div className="bar-row">
                      <span>Future</span>
                      <div className="bar-track">
                        <div className="bar-fill warm" style={{ width: `${row.future_appreciation_index}%` }} />
                      </div>
                      <strong>{row.future_appreciation_index.toFixed(0)}</strong>
                    </div>
                  </div>

                  <div className="ranking-actions">
                    <button
                      className={`action-chip ${isCompared ? 'selected' : ''}`}
                      disabled={compareDisabled}
                      onClick={(event) => {
                        event.stopPropagation()
                        onToggleCompareId(row.location_id)
                      }}
                    >
                      {isCompared ? 'In basket' : 'Add basket'}
                    </button>
                    <button
                      className="action-chip secondary"
                      onClick={(event) => {
                        event.stopPropagation()
                        onSelect(row.location_id)
                      }}
                    >
                      Open <ArrowRight size={14} />
                    </button>
                  </div>
                </article>
              )
            })}

            {!loading && filteredRankings.length > 0 ? (
              <div className="rail-footer-note">
                <Sparkles size={15} />
                <span>Use compare mode to build a short list.</span>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </aside>
  )
}
