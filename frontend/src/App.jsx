import { Suspense, lazy, useEffect, useState } from 'react'
import { Building2, GitCompareArrows, MapPinned, Menu, MoonStar, RotateCcw, SunMedium } from 'lucide-react'
import RankingsPanel from './components/RankingsPanel'
import { fetchHotspots, fetchLocations, fetchRankings } from './api'
import { locationLabel } from './utils'
import './styles/App.css'

const MapView = lazy(() => import('./components/MapView'))
const RightPanel = lazy(() => import('./components/RightPanel'))

const LEFT_PANEL_FALLBACK = 320
const RIGHT_PANEL_FALLBACK = 470

function readCssPxVar(name, fallback) {
  if (typeof document === 'undefined') return fallback
  const rawValue = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  const parsedValue = parseInt(rawValue, 10)
  return Number.isFinite(parsedValue) ? parsedValue : fallback
}

const LEFT_PANEL_DEFAULT = readCssPxVar('--left-panel-width', LEFT_PANEL_FALLBACK)
const RIGHT_PANEL_DEFAULT = readCssPxVar('--right-panel-width', RIGHT_PANEL_FALLBACK)
const CENTER_PANEL_MIN = 620

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [locations, setLocations] = useState({})
  const [rankings, setRankings] = useState([])
  const [hotspots, setHotspots] = useState([])
  const [locationsLoading, setLocationsLoading] = useState(false)
  const [locationsError, setLocationsError] = useState('')
  const [rankingsLoading, setRankingsLoading] = useState(false)
  const [rankingsError, setRankingsError] = useState('')
  const [hotspotsError, setHotspotsError] = useState('')
  const [sortBy, setSortBy] = useState('land_value_score')
  const [activeId, setActiveId] = useState(null)
  const [activeTab, setActiveTab] = useState('details')
  const [compareMode, setCompareMode] = useState(false)
  const [compareIds, setCompareIds] = useState([])
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const leftPanelWidth = LEFT_PANEL_DEFAULT
  const rightPanelWidth = RIGHT_PANEL_DEFAULT

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    let cancelled = false
    setLocationsLoading(true)
    setLocationsError('')

    fetchLocations()
      .then((rows) => {
        if (cancelled) return
        const mappedLocations = {}
        rows.forEach((location) => {
          mappedLocations[location.id] = location
        })
        setLocations(mappedLocations)
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setLocationsError('Location registry is unavailable right now.')
      })
      .finally(() => {
        if (!cancelled) setLocationsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    setRankingsLoading(true)
    setRankingsError('')

    fetchRankings(sortBy, 24)
      .then((rows) => {
        if (!cancelled) setRankings(rows)
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) {
          setRankings([])
          setRankingsError('Market rankings could not be loaded.')
        }
      })
      .finally(() => {
        if (!cancelled) setRankingsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [sortBy])

  useEffect(() => {
    let cancelled = false
    setHotspotsError('')

    fetchHotspots()
      .then((rows) => {
        if (!cancelled) setHotspots(rows)
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setHotspotsError('Hotspot clustering is unavailable.')
      })

    return () => {
      cancelled = true
    }
  }, [])

  const activeLocation = activeId ? locations[activeId] : null
  const locationList = Object.values(locations)
  const locationCount = locationList.length
  const stateCount = new Set(locationList.map((location) => location.state).filter(Boolean)).size
  const hasSelection = Boolean(activeId) || compareIds.length > 0

  function handleSelectLocation(id) {
    if (!id) return

    if (compareMode) {
      handleToggleCompareId(id)
      setActiveTab('compare')
      return
    }

    setActiveId(id)
    setActiveTab('details')
    setIsMobileMenuOpen(false)
  }

  function handleToggleCompareId(id) {
    setCompareIds((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id)
      if (current.length >= 3) return current
      return [...current, id]
    })

    if (!activeId) setActiveId(id)
  }

  function clearContext() {
    setActiveId(null)
    setCompareIds([])
    setCompareMode(false)
    setActiveTab('details')
  }

  function beginResize() {
    // Drag-resize is intentionally disabled to keep fixed full-width rails.
    // If re-enabled, keep center area >= CENTER_PANEL_MIN to avoid text collapse.
    void CENTER_PANEL_MIN
  }

  return (
    <div className={`app theme-${theme}`}>
      <main
        className="app-main"
        style={{
          '--left-panel-width': `${leftPanelWidth}px`,
          '--right-panel-width': `${rightPanelWidth}px`,
        }}
      >
        <section className="app-sidebar">
          <RankingsPanel
            rankings={rankings}
            loading={rankingsLoading}
            error={rankingsError || locationsError}
            sortBy={sortBy}
            onSortChange={setSortBy}
            activeId={activeId}
            compareIds={compareIds}
            compareMode={compareMode}
            onToggleCompareMode={() => setCompareMode((current) => !current)}
            onToggleCompareId={handleToggleCompareId}
            onOpenCompare={() => setActiveTab('compare')}
            onSelect={handleSelectLocation}
            isOpen={isMobileMenuOpen}
            onClose={() => setIsMobileMenuOpen(false)}
          />
        </section>

        <button
          type="button"
          className="panel-resizer left-resizer"
          onPointerDown={beginResize}
          aria-disabled="true"
          aria-label="Market board divider"
          title="Panel resize is locked."
        >
          <span />
        </button>

        <section className="map-shell">
          <div className="map-shell-header">
            <div className="map-shell-copy">
              <p className="eyebrow">Spatial Layer</p>
              <h2 className="display-heading">See where the signal concentrates.</h2>
              <p>Switch the lens, inspect a market, then brief it on the right.</p>
            </div>

            <div className="map-shell-toolbar">
              <div className="map-shell-meta">
                <span><MapPinned size={13} /> {rankings.length || locationCount} tracked</span>
                <span><Building2 size={13} /> {stateCount} states</span>
                <span><GitCompareArrows size={13} /> {compareIds.length} pinned</span>
                {activeLocation ? <span>{locationLabel(activeLocation)}</span> : null}
                {hotspotsError ? <span className="meta-warning">{hotspotsError}</span> : null}
              </div>

              <div className="map-shell-actions">
                <button
                  type="button"
                  className="workspace-action mobile-only"
                  onClick={() => setIsMobileMenuOpen(true)}
                >
                  <Menu size={15} />
                  <span>Markets</span>
                </button>

                {hasSelection ? (
                  <button type="button" className="workspace-action secondary" onClick={clearContext}>
                    <RotateCcw size={15} />
                    <span>Reset</span>
                  </button>
                ) : null}

                <button
                  type="button"
                  className="workspace-action"
                  onClick={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
                  title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                >
                  {theme === 'dark' ? <SunMedium size={16} /> : <MoonStar size={16} />}
                  <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
                </button>
              </div>
            </div>
          </div>

          <div className="map-container">
            <Suspense fallback={<div className="map-loading"><span className="spinner" /></div>}>
              <MapView
                theme={theme}
                locations={locations}
                rankings={rankings}
                hotspots={hotspots}
                sortBy={sortBy}
                activeId={activeId}
                compareMode={compareMode}
                compareIds={compareIds}
                onSelect={handleSelectLocation}
                onToggleCompareMode={() => setCompareMode((current) => !current)}
                onToggleCompareId={handleToggleCompareId}
                onRunCompare={() => setActiveTab('compare')}
              />
            </Suspense>
          </div>
        </section>

        <button
          type="button"
          className="panel-resizer right-resizer"
          onPointerDown={beginResize}
          aria-disabled="true"
          aria-label="Briefing panel divider"
          title="Panel resize is locked."
        >
          <span />
        </button>

        <section className="inspector-shell">
          <Suspense fallback={<div className="side-loading"><span className="spinner" /></div>}>
            <RightPanel
              activeTab={activeTab}
              onTabChange={setActiveTab}
              activeId={activeId}
              compareIds={compareIds}
              locations={locations}
              rankings={rankings}
              hotspots={hotspots}
              onClose={clearContext}
            />
          </Suspense>
        </section>
      </main>

      {(locationsLoading || rankingsLoading) && (
        <div className="global-loading-indicator glass">
          <span className="spinner" />
          <span>Refreshing market intelligence</span>
        </div>
      )}
    </div>
  )
}
