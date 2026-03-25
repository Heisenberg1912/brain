import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import L from 'leaflet'
import 'leaflet.heat'
import { fetchInfrastructure, fetchNearbyInfra } from '../api'
import { INFRA_CONFIG, ZONING_COLORS } from '../utils'
import './MapView.css'

const CATCHMENT_RADIUS_KM = 5
const CATCHMENT_RADIUS_M = CATCHMENT_RADIUS_KM * 1000
const INDIA_CENTER = [22.5937, 78.9629]
const INDIA_ZOOM = 5

function withAlpha(hex, alpha) {
  const normalized = hex.replace('#', '')
  const expanded = normalized.length === 3
    ? normalized.split('').map(char => char + char).join('')
    : normalized
  const value = Number.parseInt(expanded, 16)
  const r = (value >> 16) & 255
  const g = (value >> 8) & 255
  const b = value & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function getZoneRadius(score = 50) {
  return 260 + Math.round(score * 9)
}

function getZoneFillOpacity(score = 50, isActive = false) {
  return Math.min(0.28, (isActive ? 0.18 : 0.10) + score / 900)
}

function createMarkerIcon(color, score, isActive, zoom) {
  const size = Math.max(18, Math.min(38, zoom * 2.15))
  const displayScore = zoom >= 14 || isActive
  const bubbleSize = isActive ? size + 8 : size
  const frameSize = bubbleSize + 22

  return L.divIcon({
    className: '',
    iconSize: [frameSize, frameSize],
    iconAnchor: [frameSize / 2, frameSize / 2],
    html: `<div class="map-marker ${isActive ? 'active' : ''}" style="width:${frameSize}px;height:${frameSize}px">
      <div class="marker-glow" style="background:${withAlpha(color, isActive ? 0.28 : 0.18)}"></div>
      <div class="ring" style="border-color:${withAlpha(color, 0.7)}"></div>
      <div class="score-bubble" style="width:${bubbleSize}px;height:${bubbleSize}px;background:linear-gradient(180deg, ${withAlpha(color, 0.96)}, ${withAlpha(color, 0.72)});border-color:${withAlpha(color, isActive ? 0.82 : 0.56)};box-shadow:0 12px 28px ${withAlpha(color, isActive ? 0.28 : 0.16)}">
        ${displayScore ? `<span class="score-text">${Math.round(score)}</span>` : '<span class="score-dot"></span>'}
      </div>
    </div>`,
  })
}

export default function MapView({
  locations, rankings, sortBy, activeId, onSelect,
  compareMode, compareIds, onToggleCompare, onRemoveCompare, onRunCompare,
}) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})
  const catchmentRef = useRef(null)
  const catchmentInfraRef = useRef(null) // layer group for infra within catchment
  const connectionLinesRef = useRef(null) // lines from location to infra
  const heatLayerRef = useRef(null)
  const infraLayersRef = useRef({})
  const zoningLayerRef = useRef(null)
  const initialBoundsAppliedRef = useRef(false)

  // Cache infrastructure data so we don't re-fetch
  const infraCacheRef = useRef(null)
  // Cache nearby infra per location
  const nearbyCacheRef = useRef({})

  const [heatmapActive, setHeatmapActive] = useState(false)
  const [zoningActive, setZoningActive] = useState(true)
  const [infraPanelOpen, setInfraPanelOpen] = useState(false)
  const [infraData, setInfraData] = useState([])
  const [infraVisible, setInfraVisible] = useState({})
  const [zoom, setZoom] = useState(12)
  const [catchmentStats, setCatchmentStats] = useState(null)

  const rankingById = useMemo(
    () => Object.fromEntries(rankings.map(r => [r.location_id, r])),
    [rankings],
  )

  // Init map
  useEffect(() => {
    if (mapInstanceRef.current) return
    const map = L.map(mapRef.current, { zoomControl: false, fadeAnimation: true }).setView(INDIA_CENTER, INDIA_ZOOM)
    map.createPane('zoningPane')
    map.getPane('zoningPane').style.zIndex = '320'
    L.control.zoom({ position: 'topright' }).addTo(map)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OSM &copy; CARTO',
      maxZoom: 19,
    }).addTo(map)

    map.on('zoomend', () => setZoom(map.getZoom()))
    mapInstanceRef.current = map
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || activeId || initialBoundsAppliedRef.current) return

    const points = Object.values(locations)
      .filter(loc => loc.lat != null && loc.lng != null)
      .map(loc => [loc.lat, loc.lng])

    if (points.length === 0) {
      map.setView(INDIA_CENTER, INDIA_ZOOM)
      initialBoundsAppliedRef.current = true
      return
    }

    if (points.length === 1) {
      map.setView(points[0], 11)
      initialBoundsAppliedRef.current = true
      return
    }

    map.fitBounds(points, { padding: [36, 36], maxZoom: 6 })
    initialBoundsAppliedRef.current = true
  }, [locations, activeId])

  // Add/update location markers
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    Object.values(locations).forEach(loc => {
      if (loc.lat == null || loc.lng == null) return
      if (markersRef.current[loc.id]) return

      const marker = L.marker([loc.lat, loc.lng], {
        icon: createMarkerIcon('#6c5ce7', 0, false, map.getZoom()),
      }).addTo(map)
      marker.on('click', () => onSelect(loc.id))
      marker.bindTooltip(loc.name, { direction: 'top', offset: [0, -20], className: 'custom-tooltip' })
      markersRef.current[loc.id] = marker
    })
  }, [locations, onSelect])

  // Zoning Layer (Simulated Master Plan)
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !locations) return

    if (zoningLayerRef.current) {
      map.removeLayer(zoningLayerRef.current)
    }

    if (zoningActive) {
      const layer = L.layerGroup()

      Object.values(locations).forEach(loc => {
        if (loc.lat == null || loc.lng == null) return

        const ranking = rankingById[loc.id]
        const score = ranking?.[sortBy] ?? 50
        const color = ZONING_COLORS[loc.zoning_type] || ZONING_COLORS.residential
        const isActive = loc.id === activeId

        L.circle([loc.lat, loc.lng], {
          pane: 'zoningPane',
          radius: getZoneRadius(score),
          color: withAlpha(color, isActive ? 0.82 : 0.48),
          weight: isActive ? 2 : 1,
          opacity: isActive ? 0.95 : 0.55,
          fillColor: color,
          fillOpacity: getZoneFillOpacity(score, isActive),
          className: `zone-halo${isActive ? ' active' : ''}`,
        }).addTo(layer)
          .bindTooltip(`${loc.name} · ${(loc.zoning_type || 'unclassified').replace('_', ' ')} · ${Math.round(score)}`, { sticky: true, className: 'custom-tooltip' })
          .on('click', () => onSelect(loc.id))
      })

      zoningLayerRef.current = layer
      layer.addTo(map)
    }
  }, [locations, rankingById, sortBy, zoningActive, onSelect, activeId])

  // Update marker styles from rankings and zoom
  useEffect(() => {
    rankings.forEach(r => {
      const marker = markersRef.current[r.location_id]
      if (!marker) return
      const score = r[sortBy]
      const color = score >= 70 ? '#00d2a0' : score >= 40 ? '#ffb347' : '#ff6b6b'
      const isActive = r.location_id === activeId

      // If zoning is active, we make markers smaller so they don't block the "plan"
      const effectiveZoom = zoningActive ? zoom - 1 : zoom
      marker.setIcon(createMarkerIcon(color, score, isActive, effectiveZoom))
      marker.setZIndexOffset(isActive ? 1000 : 0)
      marker.setOpacity(heatmapActive ? 0 : 1)
    })
  }, [rankings, sortBy, activeId, zoom, zoningActive, heatmapActive])

  // Update heatmap automatically
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    const showHeat = heatmapActive || (zoom <= 11 && !zoningActive)

    if (showHeat) {
      if (heatLayerRef.current) map.removeLayer(heatLayerRef.current)
      const points = rankings.map(r => {
        const loc = locations[r.location_id]
        if (!loc) return null
        return [loc.lat, loc.lng, (r[sortBy] || 50) / 100]
      }).filter(Boolean)

      heatLayerRef.current = L.heatLayer(points, {
        radius: zoom <= 11 ? 25 : 35,
        blur: zoom <= 11 ? 15 : 20,
        maxZoom: 17,
        gradient: { 0.2: '#ff6b6b', 0.5: '#ffb347', 0.8: '#00d2a0', 1: '#00ffcc' },
      }).addTo(map)
    } else {
      if (heatLayerRef.current) {
        map.removeLayer(heatLayerRef.current)
        heatLayerRef.current = null
      }
    }
  }, [rankings, locations, sortBy, heatmapActive, zoom, zoningActive])

  // Catchment: Pan to active location + show real infrastructure within radius
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !activeId) return
    const loc = locations[activeId]
    if (loc?.lat == null || loc?.lng == null) return

    map.flyTo([loc.lat, loc.lng], Math.max(map.getZoom(), 14), { duration: 1.2 })

    // Clear old catchment layers
    if (catchmentRef.current) map.removeLayer(catchmentRef.current)
    if (catchmentInfraRef.current) map.removeLayer(catchmentInfraRef.current)
    if (connectionLinesRef.current) map.removeLayer(connectionLinesRef.current)

    // Draw catchment circle
    catchmentRef.current = L.circle([loc.lat, loc.lng], {
      radius: CATCHMENT_RADIUS_M,
      color: '#6c5ce7',
      fillColor: '#6c5ce7',
      fillOpacity: 0.06,
      weight: 2,
      dashArray: '8,6',
    }).addTo(map)

    // Fetch nearby infra and show on map
    const cached = nearbyCacheRef.current[activeId]
    if (cached) {
      renderCatchmentInfra(map, loc, cached)
    } else {
      fetchNearbyInfra(activeId, CATCHMENT_RADIUS_KM)
        .then(data => {
          nearbyCacheRef.current[activeId] = data
          renderCatchmentInfra(map, loc, data)
        })
        .catch(console.error)
    }
  }, [activeId, locations])

  // Render infrastructure pins + connection lines inside catchment
  function renderCatchmentInfra(map, loc, infraList) {
    if (catchmentInfraRef.current) map.removeLayer(catchmentInfraRef.current)
    if (connectionLinesRef.current) map.removeLayer(connectionLinesRef.current)

    const infraGroup = L.layerGroup()
    const linesGroup = L.layerGroup()

    // Aggregate stats by type
    const stats = {}

    infraList.forEach(item => {
      if (item.lat == null || item.lng == null) return
      const cfg = INFRA_CONFIG[item.infra_type] || { icon: '?', color: '#888', label: item.infra_type }

      // Count by type
      if (!stats[item.infra_type]) stats[item.infra_type] = { count: 0, nearest: item.distance_km, label: cfg.label, color: cfg.color }
      stats[item.infra_type].count++
      stats[item.infra_type].nearest = Math.min(stats[item.infra_type].nearest, item.distance_km)

      // Infrastructure marker
      const icon = L.divIcon({
        className: '',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
        html: `<div class="infra-marker catchment-infra" style="width:20px;height:20px;background:${cfg.color};border:1px solid ${cfg.color}88;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:700;color:#fff">${cfg.icon}</div>`,
      })
      L.marker([item.lat, item.lng], { icon })
        .addTo(infraGroup)
        .bindPopup(`<strong>${item.name}</strong><br><span style="opacity:0.7">${cfg.label} &middot; ${item.distance_km} km &middot; ${(item.status || '').replace('_', ' ')}</span>`)

      // Connection line (faded, dashed)
      const lineOpacity = Math.max(0.08, 0.4 - (item.distance_km / CATCHMENT_RADIUS_KM) * 0.35)
      L.polyline([[loc.lat, loc.lng], [item.lat, item.lng]], {
        color: cfg.color,
        weight: 1.5,
        opacity: lineOpacity,
        dashArray: '4,4',
      }).addTo(linesGroup)
    })

    catchmentInfraRef.current = infraGroup
    connectionLinesRef.current = linesGroup
    linesGroup.addTo(map)
    infraGroup.addTo(map)

    setCatchmentStats(stats)
  }

  // Clear catchment stats when no active location
  useEffect(() => {
    if (!activeId) setCatchmentStats(null)
  }, [activeId])

  const toggleHeatmap = useCallback(() => setHeatmapActive(prev => !prev), [])
  const toggleZoning = useCallback(() => setZoningActive(prev => !prev), [])

  const toggleInfraPanel = useCallback(async () => {
    setInfraPanelOpen(prev => !prev)
    if (!infraCacheRef.current) {
      try {
        const d = await fetchInfrastructure()
        infraCacheRef.current = d
        setInfraData(d)
      } catch (e) { console.error(e) }
    }
  }, [])

  const toggleInfraType = useCallback((type) => {
    const map = mapInstanceRef.current
    if (!map) return
    setInfraVisible(prev => {
      const next = { ...prev, [type]: !prev[type] }
      if (next[type]) {
        const layer = L.layerGroup()
        const cfg = INFRA_CONFIG[type] || { icon: '?', color: '#888' }
        infraData.filter(i => i.infra_type === type).forEach(i => {
          if (i.lat == null || i.lng == null) return
          const icon = L.divIcon({
            className: '',
            iconSize: [22, 22],
            iconAnchor: [11, 11],
            html: `<div class="infra-marker" style="width:22px;height:22px;background:${cfg.color};border:1px solid ${cfg.color};border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;color:#fff">${cfg.icon}</div>`,
          })
          L.marker([i.lat, i.lng], { icon }).addTo(layer)
            .bindPopup(`<strong>${i.name}</strong><br><span style="color:var(--text-dim)">${i.infra_type} &middot; ${(i.status || '').replace('_', ' ')}</span>`)
        })
        infraLayersRef.current[type] = layer
        layer.addTo(map)
      } else {
        if (infraLayersRef.current[type]) { map.removeLayer(infraLayersRef.current[type]); delete infraLayersRef.current[type] }
      }
      return next
    })
  }, [infraData])

  // Compute score breakdown for the catchment stats badge
  const catchmentSummary = useMemo(() => {
    if (!catchmentStats) return null
    const total = Object.values(catchmentStats).reduce((sum, s) => sum + s.count, 0)
    return { total, byType: catchmentStats }
  }, [catchmentStats])

  return (
    <main className="map-container">
      <div ref={mapRef} id="map" />

      <div className="map-controls">
        <button className={`map-ctrl-btn ${zoningActive ? 'active' : ''}`} onClick={toggleZoning}>
          Zoning Map
        </button>
        <button className={`map-ctrl-btn ${heatmapActive ? 'active' : ''}`} onClick={toggleHeatmap}>
          Heatmap
        </button>
        <button className={`map-ctrl-btn ${infraPanelOpen ? 'active' : ''}`} onClick={toggleInfraPanel}>
          Infrastructure
        </button>
        <button className={`map-ctrl-btn ${compareMode ? 'active' : ''}`} onClick={onToggleCompare}>
          Compare
        </button>
      </div>

      {infraPanelOpen && (
        <div className="infra-layer-panel visible">
          <div className="il-title">Infrastructure Layers</div>
          {Object.entries(INFRA_CONFIG).map(([type, cfg]) => (
            <div key={type} className={`infra-toggle ${infraVisible[type] ? 'on' : ''}`} onClick={() => toggleInfraType(type)}>
              <div className="it-icon" style={infraVisible[type] ? { background: 'var(--accent)', borderColor: 'var(--accent)', color: '#fff' } : {}}>{cfg.icon}</div>
              {cfg.label}
            </div>
          ))}
        </div>
      )}

      {/* Catchment Stats Panel — shows when a location is selected */}
      {catchmentSummary && activeId && (
        <div className="catchment-panel">
          <div className="catchment-title">
            Catchment ({CATCHMENT_RADIUS_KM} km)
            <span className="catchment-total">{catchmentSummary.total} infra</span>
          </div>
          <div className="catchment-grid">
            {Object.entries(catchmentSummary.byType).map(([type, data]) => (
              <div key={type} className="catchment-row">
                <span className="catchment-dot" style={{ background: data.color }} />
                <span className="catchment-label">{data.label}</span>
                <span className="catchment-count">{data.count}</span>
                <span className="catchment-dist">{data.nearest.toFixed(1)} km</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {compareMode && (
        <div className="compare-bar visible">
          <span>Compare:</span>
          <div className="compare-chips">
            {compareIds.map(id => (
              <div key={id} className="compare-chip">{locations[id]?.name || id}
                <span className="remove-chip" onClick={() => onRemoveCompare(id)}>&times;</span>
              </div>
            ))}
          </div>
          {compareIds.length >= 2 && <button className="compare-go-btn" onClick={onRunCompare}>Compare</button>}
        </div>
      )}

      <div className="map-legend">
        <div className="legend-title">Zoning & Value</div>
        {zoningActive && (
          <div className="legend-section">
            <div className="legend-item"><div className="legend-dot square" style={{ background: ZONING_COLORS.residential }} /> Resid.</div>
            <div className="legend-item"><div className="legend-dot square" style={{ background: ZONING_COLORS.commercial }} /> Comm.</div>
            <div className="legend-item"><div className="legend-dot square" style={{ background: ZONING_COLORS.mixed }} /> Mixed</div>
            <div className="legend-item"><div className="legend-dot square" style={{ background: ZONING_COLORS.industrial }} /> Indust.</div>
          </div>
        )}
        <div className="legend-divider" />
        <div className="legend-section">
          <div className="legend-item"><div className="legend-dot" style={{ background: '#00d2a0' }} /> High</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#ffb347' }} /> Mid</div>
          <div className="legend-item"><div className="legend-dot" style={{ background: '#ff6b6b' }} /> Low</div>
        </div>
      </div>
    </main>
  )
}
