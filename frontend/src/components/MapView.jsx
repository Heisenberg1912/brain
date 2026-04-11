import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet.heat'
import {
  Activity,
  GitCompareArrows,
  Layers3,
  LocateFixed,
  Maximize2,
  Minimize2,
  Network,
} from 'lucide-react'
import { fetchInfrastructure, fetchNearbyInfra } from '../api'
import {
  formatDistance,
  formatLabel,
  INFRA_CONFIG,
  locationLabel,
  scoreHex,
  ZONING_COLORS,
} from '../utils'
import './MapView.css'

const INDIA_CENTER = [22.5937, 78.9629]
const INDIA_ZOOM = 5

function preferredBasemap(theme) {
  return theme === 'light' ? 'carto-light' : 'carto-dark'
}

function tileConfig(mode) {
  if (mode === 'carto-light') {
    return {
      url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      options: {
        subdomains: 'abcd',
        maxZoom: 20,
      },
    }
  }

  if (mode === 'carto-dark') {
    return {
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      options: {
        subdomains: 'abcd',
        maxZoom: 20,
      },
    }
  }

  return {
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: {
      maxZoom: 19,
    },
  }
}

function createLocationMarker({ score, zoning, active, compared, cityInitial, isPulseOnce, touchSize }) {
  const hasScore = score > 0
  const markerColor = hasScore ? scoreHex(score) : '#6b7280'
  const zoningColor = ZONING_COLORS[zoning] || ZONING_COLORS.unclassified
  const displayText = hasScore ? Math.round(score) : (cityInitial || '·')
  const pulseClass = isPulseOnce ? 'is-pulse-once' : ''
  const touchClass = touchSize ? 'marker-shell--touch' : ''
  const iconW = touchSize ? 48 : 40
  const iconH = touchSize ? 56 : 52
  const anchorX = touchSize ? 24 : 20
  const anchorY = touchSize ? 24 : 20

  return L.divIcon({
    className: 'custom-location-marker',
    iconSize: [iconW, iconH],
    iconAnchor: [anchorX, anchorY],
    html: `
      <div
        class="marker-shell ${touchClass} ${active ? 'is-active' : ''} ${compared ? 'is-compared' : ''} ${hasScore ? 'has-score' : 'no-score'} ${pulseClass}"
        style="--mc:${markerColor}; --ring:${zoningColor};"
      >
        <span class="marker-score">${displayText}</span>
        ${active ? `<span class="marker-zoning-dot" style="background:${zoningColor}"></span>` : ''}
      </div>
    `,
  })
}

function isMapUsable(map) {
  return Boolean(map && map._loaded && map._mapPane && map._container)
}

function parseCoordinate(value) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : null
}

function toLatLng(location) {
  const lat = parseCoordinate(location?.lat)
  const lng = parseCoordinate(location?.lng)

  if (lat === null || lng === null) return null
  return [lat, lng]
}

function hasValidCoords(location) {
  return Boolean(toLatLng(location))
}

export default function MapView({
  theme,
  locations,
  rankings,
  hotspots,
  sortBy,
  activeId,
  compareMode,
  compareIds,
  onSelect,
  onToggleCompareMode,
  onRunCompare,
}) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const tileLayerRef = useRef(null)
  const locationLayerRef = useRef(null)
  const infrastructureLayerRef = useRef(null)
  const heatLayerRef = useRef(null)
  const hasFitBoundsRef = useRef(false)
  const resizeObserverRef = useRef(null)
  const resizeFrameRef = useRef(null)
  const pulseTimeoutRef = useRef(null)

  const [heatmapActive, setHeatmapActive] = useState(false)
  const [pulseId, setPulseId] = useState(null)
  const [infrastructureActive, setInfrastructureActive] = useState(true)
  const [infrastructure, setInfrastructure] = useState([])
  const [infrastructureError, setInfrastructureError] = useState('')
  const [nearbyInfrastructure, setNearbyInfrastructure] = useState([])
  const [basemapMode, setBasemapMode] = useState(() => preferredBasemap(theme))
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [coverageOpen, setCoverageOpen] = useState(false)
  const [isMobileMap, setIsMobileMap] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)')
    const apply = () => {
      setIsMobileMap(mq.matches)
      if (!mq.matches) setCoverageOpen(false)
    }
    apply()
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [])

  const rankingById = useMemo(() => {
    const lookup = {}
    rankings.forEach((row) => {
      lookup[row.location_id] = row
    })
    return lookup
  }, [rankings])

  const activeLocation = activeId ? locations[activeId] : null
  const mappedLocations = useMemo(
    () => Object.values(locations).filter(hasValidCoords),
    [locations],
  )

  const infrastructureCounts = useMemo(() => {
    return infrastructure.reduce((summary, item) => {
      const key = item.infra_type
      summary[key] = (summary[key] || 0) + 1
      return summary
    }, {})
  }, [infrastructure])

  const compareNames = useMemo(
    () => compareIds.map((id) => locationLabel(locations[id], '')).filter(Boolean),
    [compareIds, locations],
  )

  const spotlightHotspots = hotspots.slice(0, 3)
  const activeRanking = activeId ? rankingById[activeId] : null
  const coverageItems = useMemo(() => (
    Object.entries(INFRA_CONFIG)
      .map(([key, config]) => ({
        key,
        label: config.label,
        color: config.color,
        count: infrastructureCounts[key] || 0,
      }))
      .filter((item) => item.count > 0)
      .sort((left, right) => right.count - left.count)
      .slice(0, 4)
  ), [infrastructureCounts])

  const coverageTotal = useMemo(
    () => coverageItems.reduce((sum, item) => sum + item.count, 0),
    [coverageItems],
  )
  const activeScores = activeRanking
    ? [
        { key: 'land', label: 'Land', value: activeRanking.land_value_score },
        { key: 'build', label: 'Build', value: activeRanking.development_potential_score },
        { key: 'future', label: 'Future', value: activeRanking.future_appreciation_index },
      ]
    : []

  useEffect(() => {
    setBasemapMode(preferredBasemap(theme))
  }, [theme])

  useEffect(() => {
    if (!mapRef.current || isMapUsable(mapInstanceRef.current)) return

    const initialTileConfig = tileConfig(basemapMode)

    const map = L.map(mapRef.current, {
      zoomControl: false,
      attributionControl: false,
      minZoom: 4,
      maxZoom: 17,
      scrollWheelZoom: true,
      preferCanvas: true,
    }).setView(INDIA_CENTER, INDIA_ZOOM)

    tileLayerRef.current = L.tileLayer(initialTileConfig.url, initialTileConfig.options).addTo(map)

    locationLayerRef.current = L.layerGroup().addTo(map)
    infrastructureLayerRef.current = L.layerGroup().addTo(map)

    L.control.zoom({ position: 'bottomright' }).addTo(map)

    mapInstanceRef.current = map
    resizeFrameRef.current = requestAnimationFrame(() => {
      if (isMapUsable(map)) {
        map.invalidateSize({ pan: false, debounceMoveend: true })
      }
    })

    return () => {
      if (resizeFrameRef.current) {
        cancelAnimationFrame(resizeFrameRef.current)
        resizeFrameRef.current = null
      }

      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
        resizeObserverRef.current = null
      }

      if (heatLayerRef.current && map.hasLayer(heatLayerRef.current)) {
        map.removeLayer(heatLayerRef.current)
      }

      map.off()
      map.remove()
      mapInstanceRef.current = null
      tileLayerRef.current = null
      locationLayerRef.current = null
      infrastructureLayerRef.current = null
      heatLayerRef.current = null
      hasFitBoundsRef.current = false
    }
  }, [])

  useEffect(() => {
    if (!tileLayerRef.current || !isMapUsable(mapInstanceRef.current)) return

    const currentLayer = tileLayerRef.current
    const nextTileConfig = tileConfig(basemapMode)
    let switched = false

    currentLayer.setUrl(nextTileConfig.url)
    Object.entries(nextTileConfig.options || {}).forEach(([key, value]) => {
      currentLayer.options[key] = value
    })

    const handleTileError = () => {
      if (switched || basemapMode === 'osm') return
      switched = true
      setBasemapMode('osm')
    }

    currentLayer.on('tileerror', handleTileError)

    return () => {
      currentLayer.off('tileerror', handleTileError)
    }
  }, [basemapMode])

  useEffect(() => {
    const map = mapInstanceRef.current
    const container = mapRef.current
    if (!isMapUsable(map) || !container) return

    const invalidate = () => {
      if (resizeFrameRef.current) {
        cancelAnimationFrame(resizeFrameRef.current)
      }

      resizeFrameRef.current = requestAnimationFrame(() => {
        const currentMap = mapInstanceRef.current
        if (isMapUsable(currentMap)) {
          currentMap.invalidateSize({ pan: false, debounceMoveend: true })
        }
      })
    }

    invalidate()

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => invalidate())
      observer.observe(container)
      resizeObserverRef.current = observer
    }

    window.addEventListener('resize', invalidate)

    return () => {
      window.removeEventListener('resize', invalidate)
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect()
        resizeObserverRef.current = null
      }
      if (resizeFrameRef.current) {
        cancelAnimationFrame(resizeFrameRef.current)
        resizeFrameRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    fetchInfrastructure()
      .then((rows) => {
        if (!cancelled) {
          setInfrastructure(rows.filter((item) => item.lat !== null && item.lng !== null))
          setInfrastructureError('')
        }
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setInfrastructureError('Infrastructure overlay is unavailable.')
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!activeId) {
      setNearbyInfrastructure([])
      return
    }

    let cancelled = false

    fetchNearbyInfra(activeId, 6)
      .then((rows) => {
        if (!cancelled) setNearbyInfrastructure(rows)
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setNearbyInfrastructure([])
      })

    return () => {
      cancelled = true
    }
  }, [activeId])

  useEffect(() => () => {
    if (pulseTimeoutRef.current) {
      clearTimeout(pulseTimeoutRef.current)
      pulseTimeoutRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    const layer = locationLayerRef.current
    if (!isMapUsable(map) || !layer) return

    layer.clearLayers()
    const bounds = []

    mappedLocations.forEach((location) => {
      const ranking = rankingById[location.id]
      const score = ranking?.[sortBy] ?? 0
      const hasScore = score > 0
      const latLng = toLatLng(location)
      if (!latLng) return

      const cityInitial = (location.city || location.name || '?')
        .replace(/^(Greater|New|North|South|East|West)\s+/i, '')
        .slice(0, 2)
        .toUpperCase()

      const marker = L.marker(
        latLng,
        {
          icon: createLocationMarker({
            score,
            zoning: location.zoning_type,
            active: location.id === activeId,
            compared: compareIds.includes(location.id),
            cityInitial,
            isPulseOnce: location.id === pulseId,
            touchSize: isMobileMap,
          }),
        },
      )

      marker.on('click', () => {
        onSelect(location.id)
        setPulseId(location.id)
        if (pulseTimeoutRef.current) clearTimeout(pulseTimeoutRef.current)
        pulseTimeoutRef.current = window.setTimeout(() => {
          pulseTimeoutRef.current = null
          setPulseId(null)
        }, 300)
      })
      const scoreLabel = hasScore ? `${Math.round(score)}/100` : 'No score yet'
      marker.bindTooltip(
        `<strong>${locationLabel(location)}</strong><br />${location.city ? `${location.city} · ` : ''}${formatLabel(location.zoning_type || 'unclassified')} zone<br />${formatLabel(sortBy)}: ${scoreLabel}`,
        { direction: 'top', offset: [0, -16] },
      )
      marker.addTo(layer)
      bounds.push(latLng)
    })

    if (!hasFitBoundsRef.current && bounds.length === 1) {
      map.setView(bounds[0], 10, { animate: false })
      hasFitBoundsRef.current = true
    } else if (!hasFitBoundsRef.current && bounds.length > 1) {
      map.fitBounds(bounds, { padding: [36, 36], animate: false, maxZoom: 11 })
      hasFitBoundsRef.current = true
    }
  }, [mappedLocations, rankingById, sortBy, activeId, compareIds, onSelect, pulseId, isMobileMap])

  useEffect(() => {
    const map = mapInstanceRef.current
    const latLng = toLatLng(activeLocation)
    if (!isMapUsable(map) || !latLng) return
    map.flyTo(latLng, 11, { duration: 0.8 })
  }, [activeLocation])

  useEffect(() => {
    const map = mapInstanceRef.current
    const layer = infrastructureLayerRef.current
    if (!isMapUsable(map) || !layer) return

    layer.clearLayers()

    if (!infrastructureActive) return

    infrastructure.forEach((item) => {
      const latLng = toLatLng(item)
      if (!latLng) return

      const config = INFRA_CONFIG[item.infra_type] || {
        icon: 'I',
        color: '#94a3b8',
        label: formatLabel(item.infra_type),
      }

      const marker = L.circleMarker(latLng, {
        radius: 5,
        color: config.color,
        weight: 1,
        fillColor: config.color,
        fillOpacity: 0.88,
      })

      marker.bindTooltip(
        `
          <strong>${item.name}</strong><br />
          ${config.label}<br />
          ${formatLabel(item.status)}
        `,
      )

      marker.addTo(layer)
    })
  }, [infrastructure, infrastructureActive])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!isMapUsable(map)) return

    if (heatLayerRef.current) {
      if (map.hasLayer(heatLayerRef.current)) {
        map.removeLayer(heatLayerRef.current)
      }
      heatLayerRef.current = null
    }

    if (!heatmapActive) return

    const points = rankings
      .map((row) => {
        const location = locations[row.location_id]
        const latLng = toLatLng(location)
        if (!latLng) return null
        return [...latLng, Math.max((row[sortBy] || 0) / 100, 0.2)]
      })
      .filter(Boolean)

    if (points.length === 0) return

    heatLayerRef.current = L.heatLayer(points, {
      radius: 28,
      blur: 22,
      maxZoom: 11,
      gradient: {
        0.15: '#164e63',
        0.4: '#0ea5e9',
        0.65: '#22c55e',
        0.85: '#f59e0b',
        1: '#ef4444',
      },
    }).addTo(map)
  }, [heatmapActive, locations, rankings, sortBy])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!isMapUsable(map)) return

    const frame = requestAnimationFrame(() => {
      const currentMap = mapInstanceRef.current
      if (isMapUsable(currentMap)) {
        currentMap.invalidateSize({ pan: false, debounceMoveend: true })
      }
    })

    return () => cancelAnimationFrame(frame)
  }, [mappedLocations.length, activeId, compareIds.length, infrastructureActive, heatmapActive])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!isMapUsable(map)) return

    const frame = requestAnimationFrame(() => {
      const currentMap = mapInstanceRef.current
      if (isMapUsable(currentMap)) {
        currentMap.invalidateSize({ pan: false, debounceMoveend: true })
      }
    })

    return () => cancelAnimationFrame(frame)
  }, [isFullscreen])

  return (
    <div
      className={`map-view theme-${theme} basemap-${basemapMode}${isFullscreen ? ' map-view--fullscreen' : ''}${isMobileMap ? ' map-view--mobile' : ''}`}
    >
      <div ref={mapRef} className="map-element" />

      <div className="map-left-overlay-stack">
        <div className="map-overlay lens-panel glass">
          <div className="lens-head">
            <div>
              <p className="overlay-label">Active lens</p>
              <h3>{formatLabel(sortBy)}</h3>
            </div>
            <span className="lens-pill">{rankings.length || mappedLocations.length}</span>
          </div>
          <div className="lens-scale" aria-hidden>
            <span className="lens-scale-fill" />
          </div>
          <div className="lens-scale-labels">
            <span>Low</span>
            <span>Mid</span>
            <span>High</span>
          </div>
        </div>

        {!activeLocation ? (
          <div className="map-overlay watchlist-panel glass">
            <p className="overlay-label">Hotspot watchlist</p>
            <h3>Emerging corridors</h3>
            <div className="hotspot-stack">
              {spotlightHotspots.map((hotspot) => (
                <button
                  key={hotspot.cluster_id}
                  className="hotspot-card"
                  onClick={() => {
                    const firstLocation = hotspot.locations?.[0]
                    if (firstLocation?.location_id) onSelect(firstLocation.location_id)
                  }}
                >
                  <div>
                    <strong>{formatLabel(hotspot.label)}</strong>
                    <span>{hotspot.cluster_size} markets</span>
                  </div>
                  <b>{hotspot.hotspot_score.toFixed(0)}</b>
                </button>
              ))}
              {spotlightHotspots.length === 0 ? (
                <p className="overlay-muted">Hotspots will appear here.</p>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>

      <div className="map-overlay-controls glass">
        <button
          className={`control-btn ${infrastructureActive ? 'active' : ''}`}
          onClick={() => setInfrastructureActive((current) => !current)}
          title="Toggle infrastructure"
        >
          <Network size={18} />
          <span>Infra</span>
        </button>
        <button
          className={`control-btn ${heatmapActive ? 'active' : ''}`}
          onClick={() => setHeatmapActive((current) => !current)}
          title="Toggle heatmap"
        >
          <Activity size={18} />
          <span>Heat</span>
        </button>
        <button
          className={`control-btn ${compareMode ? 'active' : ''}`}
          onClick={onToggleCompareMode}
          title="Toggle compare mode"
        >
          <GitCompareArrows size={18} />
          <span>Compare</span>
        </button>
        <button
          className="control-btn"
          onClick={() => {
            const map = mapInstanceRef.current
            if (isMapUsable(map)) {
              map.setView(INDIA_CENTER, INDIA_ZOOM, { animate: false })
            }
          }}
          title="Reset map"
        >
          <LocateFixed size={18} />
          <span>India</span>
        </button>
      </div>

      <div
        className={`map-overlay bottom-left glass map-coverage-panel${isMobileMap && !coverageOpen ? ' map-coverage-panel--collapsed' : ''}`}
      >
        {isMobileMap ? (
          <button
            type="button"
            className="coverage-toggle"
            aria-expanded={coverageOpen}
            onClick={() => setCoverageOpen((open) => !open)}
          >
            <Layers3 size={16} aria-hidden />
            <span>Coverage</span>
            <strong>{coverageTotal}</strong>
          </button>
        ) : (
          <div className="overlay-section-title">
            <Layers3 size={16} />
            <span>Coverage</span>
          </div>
        )}
        {(!isMobileMap || coverageOpen) ? (
          <>
            {infrastructureError ? <p className="overlay-muted">{infrastructureError}</p> : null}
            {coverageItems.length ? (
              <div className="coverage-chip-grid">
                {coverageItems.map((item) => (
                  <div key={item.key} className="coverage-chip">
                    <span className="infra-dot" style={{ backgroundColor: item.color }} />
                    <span>{item.label}</span>
                    <strong>{item.count}</strong>
                  </div>
                ))}
              </div>
            ) : null}
            {!infrastructureError && coverageItems.length === 0 ? (
              <p className="overlay-muted">Infrastructure counts will appear once overlays load.</p>
            ) : null}
          </>
        ) : null}
      </div>

      {activeLocation ? (
        <div className="map-overlay bottom-right glass">
          <p className="overlay-label">Active market</p>
          <h3>{locationLabel(activeLocation)}</h3>
          <p className="overlay-copy">
            {formatLabel(activeLocation.zoning_type)} zone
            {activeLocation.city ? ` • ${activeLocation.city}` : ''}.
          </p>
          {activeScores.length ? (
            <div className="active-score-strip">
              {activeScores.map((item) => (
                <div key={item.key} className="mini-score-chip">
                  <span>{item.label}</span>
                  <strong style={{ color: scoreHex(item.value) }}>{item.value.toFixed(0)}</strong>
                </div>
              ))}
            </div>
          ) : null}
          <div className="catchment-list">
            {nearbyInfrastructure.slice(0, 4).map((item) => (
              <div key={item.id} className="catchment-row">
                <span>{item.name}</span>
                <strong>{formatDistance(item.distance_km)}</strong>
              </div>
            ))}
            {nearbyInfrastructure.length === 0 ? (
              <p className="overlay-muted">No nearby infrastructure was returned for this market.</p>
            ) : null}
          </div>
        </div>
      ) : null}

      {compareIds.length > 0 ? (
        <div className="compare-shelf glass">
          <div className="compare-tags">
            {compareNames.map((name) => (
              <span key={name} className="compare-tag">{name}</span>
            ))}
          </div>
          <button className="run-compare-btn" disabled={compareIds.length < 2} onClick={onRunCompare}>
            Run compare
          </button>
        </div>
      ) : null}

      <button
        type="button"
        className={`map-fullscreen-btn ${isFullscreen ? 'active' : ''}`}
        aria-pressed={isFullscreen}
        aria-label={isFullscreen ? 'Exit fullscreen map' : 'Expand map to full width'}
        title={isFullscreen ? 'Exit fullscreen map' : 'Expand map to full width'}
        onClick={() => setIsFullscreen((current) => !current)}
      >
        {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
      </button>
    </div>
  )
}
