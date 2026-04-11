import { Suspense, lazy, useEffect, useState } from 'react'
import { GitCompareArrows, Menu, MoonStar, RotateCcw, SunMedium } from 'lucide-react'
import RankingsPanel from './components/RankingsPanel'
import CityModal from './components/CityModal'
import CompareModal from './components/CompareModal'
import TopNav from './components/TopNav'
import { fetchHotspots, fetchLocations, fetchRankings } from './api'
import { locationLabel } from './utils'
import './styles/App.css'

const MapView = lazy(() => import('./components/MapView'))

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
  const [marketSearch, setMarketSearch] = useState('')
  const [briefingModalOpen, setBriefingModalOpen] = useState(false)
  const [compareModalOpen, setCompareModalOpen] = useState(false)

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

  useEffect(() => {
    if (compareIds.length < 2) setCompareModalOpen(false)
  }, [compareIds.length])

  const selectedLocation = activeId && locations[activeId] ? locations[activeId] : null

  const locationList = Object.values(locations)
  const locationCount = locationList.length
  const stateCount = new Set(locationList.map((location) => location.state).filter(Boolean)).size
  const trackedCount = rankings.length || locationCount
  const clusterCount = hotspots.length
  const hasSelection = Boolean(activeId) || compareIds.length > 0

  function handleSelectLocation(id) {
    if (!id) return

    if (compareMode) {
      handleToggleCompareId(id)
      setCompareModalOpen(true)
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
  }

  function clearContext() {
    setActiveId(null)
    setCompareIds([])
    setCompareMode(false)
    setActiveTab('details')
    setCompareModalOpen(false)
  }

  function dismissCityModal() {
    setBriefingModalOpen(false)
    setActiveId(null)
    setActiveTab('details')
  }

  function resetWorkspace() {
    setBriefingModalOpen(false)
    clearContext()
  }

  function openMarketsBriefing() {
    if (briefingModalOpen && !selectedLocation) {
      return
    }
    setBriefingModalOpen(true)
    if (selectedLocation || compareIds.length > 0 || compareMode) {
      clearContext()
    }
  }

  return (
    <div className={`app theme-${theme}${isMobileMenuOpen ? ' app--rankings-open' : ''}`}>
      <main className="app-main">
        <section className="app-sidebar">
          <RankingsPanel
            rankings={rankings}
            loading={rankingsLoading}
            error={rankingsError || locationsError}
            searchQuery={marketSearch}
            sortBy={sortBy}
            activeId={activeId}
            compareIds={compareIds}
            compareMode={compareMode}
            onToggleCompareMode={() => setCompareMode((current) => !current)}
            onToggleCompareId={handleToggleCompareId}
            compareModalOpen={compareModalOpen}
            onOpenCompare={() => setCompareModalOpen(true)}
            onSelect={handleSelectLocation}
            isOpen={isMobileMenuOpen}
            onClose={() => setIsMobileMenuOpen(false)}
          />
        </section>

        <section className="map-shell">
          <TopNav
            searchQuery={marketSearch}
            onSearchChange={setMarketSearch}
            sortBy={sortBy}
            onSortChange={setSortBy}
            trackedCount={trackedCount}
            stateCount={stateCount}
            clusterCount={clusterCount}
            onMarketsBriefing={openMarketsBriefing}
          />

          <div className="map-shell-header">
            <div className="map-shell-copy">
              <p className="eyebrow">Spatial Layer</p>
              <h2 className="display-heading">See where the signal concentrates.</h2>
              <p>Switch the lens, inspect a market, then brief it on the right.</p>
            </div>

            <div className="map-shell-toolbar">
              <div className="map-shell-meta">
                <span><GitCompareArrows size={13} /> {compareIds.length} pinned</span>
                {selectedLocation ? <span>{locationLabel(selectedLocation)}</span> : null}
                {hotspotsError ? <span className="meta-warning">{hotspotsError}</span> : null}
              </div>

              <div className="map-shell-actions">
                {hasSelection ? (
                  <button type="button" className="workspace-action secondary" onClick={resetWorkspace}>
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

          <div className={`map-container${selectedLocation ? ' map-container--city' : ''}`}>
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
                onRunCompare={() => setCompareModalOpen(true)}
              />
            </Suspense>
          </div>
        </section>
      </main>

      {/* Briefing modal: macro (TopNav GO / Markets Overview) or city selection; X/backdrop dismiss clears selection only (pins preserved). Use Reset for full clear. */}
      {(briefingModalOpen || selectedLocation) ? (
        <CityModal
          activeTab={activeTab}
          onTabChange={setActiveTab}
          activeId={activeId}
          compareIds={compareIds}
          locations={locations}
          rankings={rankings}
          hotspots={hotspots}
          selectedLocation={selectedLocation}
          onSelectLocation={handleSelectLocation}
          sortBy={sortBy}
          onClose={dismissCityModal}
        />
      ) : null}

      {compareModalOpen && compareIds.length >= 2 ? (
        <CompareModal
          compareIds={compareIds}
          locations={locations}
          onClose={() => setCompareModalOpen(false)}
        />
      ) : null}

      {(locationsLoading || rankingsLoading) && (
        <div className="global-loading-indicator glass">
          <span className="spinner" />
          <span>Refreshing market intelligence</span>
        </div>
      )}

      <button
        type="button"
        className="rankings-fab"
        aria-label="Open market rankings"
        onClick={() => setIsMobileMenuOpen(true)}
      >
        <Menu size={20} aria-hidden />
      </button>
    </div>
  )
}
