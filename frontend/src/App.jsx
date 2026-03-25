import { Suspense, lazy, useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import RankingsPanel from './components/RankingsPanel'
import { fetchLocations, fetchRankings } from './api'
import './styles/App.css'

const MapView = lazy(() => import('./components/MapView'))
const RightPanel = lazy(() => import('./components/RightPanel'))

export default function App() {
  const [locations, setLocations] = useState({})
  const [rankings, setRankings] = useState([])
  const [rankingsLoading, setRankingsLoading] = useState(false)
  const [rankingsError, setRankingsError] = useState('')
  const [sortBy, setSortBy] = useState('land_value_score')
  const [activeId, setActiveId] = useState(null)
  const [activeTab, setActiveTab] = useState('details')
  const [compareMode, setCompareMode] = useState(false)
  const [compareIds, setCompareIds] = useState([])

  useEffect(() => {
    fetchLocations().then(locs => {
      const map = {}
      locs.forEach(l => { map[l.id] = l })
      setLocations(map)
    }).catch(console.error)
  }, [])

  useEffect(() => {
    setRankingsLoading(true)
    setRankingsError('')
    fetchRankings(sortBy)
      .then(setRankings)
      .catch((error) => {
        console.error(error)
        setRankings([])
        setRankingsError('Rankings could not be loaded right now.')
      })
      .finally(() => setRankingsLoading(false))
  }, [sortBy])

  const handleSelectLocation = useCallback((id) => {
    if (compareMode) {
      setCompareIds(prev => {
        if (prev.includes(id)) return prev.filter(x => x !== id)
        if (prev.length >= 3) return prev
        return [...prev, id]
      })
    } else {
      setActiveId(id)
      setActiveTab('details')
    }
  }, [compareMode])

  const toggleCompare = useCallback(() => {
    setCompareMode(prev => {
      if (prev) setCompareIds([])
      return !prev
    })
  }, [])

  const locationCount = Object.keys(locations).length
  const stateCount = new Set(
    Object.values(locations)
      .map(location => location.state)
      .filter(Boolean),
  ).size

  return (
    <div className="app">
      <Header locationCount={locationCount} stateCount={stateCount} />
      <RankingsPanel
        rankings={rankings}
        loading={rankingsLoading}
        error={rankingsError}
        sortBy={sortBy}
        onSortChange={setSortBy}
        activeId={activeId}
        onSelect={handleSelectLocation}
      />
      <Suspense fallback={<div className="map-loading"><span className="spinner" /> Loading map intelligence...</div>}>
        <MapView
          locations={locations}
          rankings={rankings}
          sortBy={sortBy}
          activeId={activeId}
          onSelect={handleSelectLocation}
          compareMode={compareMode}
          compareIds={compareIds}
          onToggleCompare={toggleCompare}
          onRemoveCompare={(id) => setCompareIds(prev => prev.filter(x => x !== id))}
          onRunCompare={() => setActiveTab('compare')}
        />
      </Suspense>
      <Suspense fallback={<div className="side-loading"><span className="spinner" /> Loading analysis tools...</div>}>
        <RightPanel
          activeTab={activeTab}
          onTabChange={setActiveTab}
          activeId={activeId}
          compareIds={compareIds}
          locations={locations}
          rankings={rankings}
        />
      </Suspense>
    </div>
  )
}
