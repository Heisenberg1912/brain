import { useState } from 'react'
import { scoreColor, ZONING_COLORS } from '../utils'
import './RankingsPanel.css'

export default function RankingsPanel({ rankings, loading, error, sortBy, onSortChange, activeId, onSelect }) {
  const [search, setSearch] = useState('')

  const filtered = rankings.filter(r =>
    (r.location || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <aside className="left-panel">
      <div className="panel-header">
        <span className="panel-title">Rankings</span>
        <select
          className="sort-select"
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
        >
          <option value="land_value_score">Land Value</option>
          <option value="development_potential_score">Dev Potential</option>
          <option value="future_appreciation_index">Future Appreciation</option>
        </select>
      </div>
      
      <div className="search-container">
        <input 
          type="text" 
          placeholder="Filter locations..." 
          className="rankings-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && <span className="clear-search" onClick={() => setSearch('')}>&times;</span>}
      </div>

      <div className="rankings-list">
        {loading && <div className="panel-state">Loading rankings...</div>}
        {!loading && error && <div className="panel-state error">{error}</div>}
        {!loading && !error && filtered.length === 0 && (
          <div className="panel-state">
            {search ? 'No locations match this filter.' : 'No ranked locations available yet.'}
          </div>
        )}

        {!loading && !error && filtered.map(r => {
          const mainScore = r[sortBy]
          const color = scoreColor(mainScore)
          const zoningColor = ZONING_COLORS[r.zoning_type] || ZONING_COLORS.residential
          
          return (
            <div
              key={r.location_id}
              className={`ranking-card ${r.location_id === activeId ? 'active' : ''}`}
              onClick={() => onSelect(r.location_id)}
            >
              <div className="ranking-top">
                <span className="ranking-rank">#{r.rank}</span>
                <div className="ranking-name-box">
                  <span className="ranking-name">{r.location}</span>
                  <div className="zoning-tag" style={{ background: zoningColor }}>
                    {r.zoning_type}
                  </div>
                </div>
                <span
                  className="ranking-badge"
                  style={{ color, background: color.replace(')', ', 0.1)').replace('var(', 'rgba(').replace('--green', '0,210,160').replace('--orange', '255,179,71').replace('--red', '255,107,107') }}
                >
                  {mainScore.toFixed(0)}
                </span>
              </div>
              <div className="ranking-scores">
                <div className="mini-score">
                  <span className="l">LV</span>
                  <span className="v">{r.land_value_score.toFixed(0)}</span>
                </div>
                <div className="mini-score">
                  <span className="l">DP</span>
                  <span className="v">{r.development_potential_score.toFixed(0)}</span>
                </div>
                <div className="mini-score">
                  <span className="l">FA</span>
                  <span className="v">{r.future_appreciation_index.toFixed(0)}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
