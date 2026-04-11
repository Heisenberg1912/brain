import { useEffect, useRef, useState } from 'react'
import { Building2, Info, MapPinned, Radar, Search } from 'lucide-react'
import './TopNav.css'

const LENS_OPTIONS = [
  { value: 'land_value_score', label: 'Land Value' },
  { value: 'development_potential_score', label: 'Develop' },
  { value: 'future_appreciation_index', label: 'Future' },
]

export default function TopNav({
  searchQuery,
  onSearchChange,
  sortBy,
  onSortChange,
  trackedCount,
  stateCount,
  clusterCount,
  onMarketsBriefing,
}) {
  const [statsOpen, setStatsOpen] = useState(false)
  const statsWrapRef = useRef(null)

  useEffect(() => {
    if (!statsOpen) return
    function handlePointerDown(event) {
      if (statsWrapRef.current && !statsWrapRef.current.contains(event.target)) {
        setStatsOpen(false)
      }
    }
    function handleKey(event) {
      if (event.key === 'Escape') setStatsOpen(false)
    }
    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleKey)
    }
  }, [statsOpen])

  const statsBadges = (
    <>
      <span className="top-nav__badge">
        <MapPinned size={13} aria-hidden />
        {trackedCount} tracked
      </span>
      <span className="top-nav__badge">
        <Building2 size={13} aria-hidden />
        {stateCount} states
      </span>
      <span className="top-nav__badge">
        <Radar size={13} aria-hidden />
        {clusterCount} clusters
      </span>
    </>
  )

  return (
    <nav className="top-nav" aria-label="Workspace">
      <label className="top-nav__search">
        <Search size={16} aria-hidden />
        <input
          type="search"
          aria-label="Search city, corridor, or locality"
          placeholder="Search city, corridor, or locality"
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
          autoComplete="off"
        />
      </label>

      <div className="top-nav__lens-row">
        <div className="top-nav__lens" role="group" aria-label="Score lens">
          {LENS_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`top-nav__pill ${sortBy === option.value ? 'active' : ''}`}
              onClick={() => onSortChange(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        <div className="top-nav__end">
          <div className="top-nav__stats top-nav__stats--desktop" aria-label="Coverage">
            {statsBadges}
          </div>

          <div className="top-nav__stats-mobile" ref={statsWrapRef}>
            <button
              type="button"
              className={`top-nav__stats-toggle ${statsOpen ? 'active' : ''}`}
              aria-expanded={statsOpen}
              aria-controls="top-nav-stats-popover"
              aria-label="Coverage stats"
              onClick={() => setStatsOpen((open) => !open)}
            >
              <Info size={18} aria-hidden />
            </button>
            {statsOpen ? (
              <div
                id="top-nav-stats-popover"
                className="top-nav__stats-dropdown glass"
                role="region"
                aria-label="Coverage"
              >
                <div className="top-nav__stats top-nav__stats--stacked">
                  {statsBadges}
                </div>
              </div>
            ) : null}
          </div>

          <button
            type="button"
            className="top-nav__markets-overview"
            onClick={() => onMarketsBriefing?.()}
          >
            Markets Overview
          </button>
        </div>
      </div>
    </nav>
  )
}
