import { useEffect, useRef, useState } from 'react'
import { Bot, Boxes, Map, X } from 'lucide-react'
import BlockchainPanel from './BlockchainPanel'
import DetailsPanel from './DetailsPanel'
import AIChat from './AIChat'
import { locationLabel, locationSecondaryLabel } from '../utils'
import './CityModal.css'

const ANIM_MS = 250

const TABS = [
  { key: 'details', label: 'Overview', icon: Map },
  { key: 'chain', label: 'Blockchain', icon: Boxes },
  { key: 'ai', label: 'AI', icon: Bot },
]

export default function CityModal({
  activeTab,
  onTabChange,
  activeId,
  compareIds,
  locations,
  rankings,
  hotspots,
  selectedLocation,
  onSelectLocation,
  sortBy,
  onClose,
}) {
  const [isVisible, setIsVisible] = useState(false)
  const [isExiting, setIsExiting] = useState(false)
  const exitTimerRef = useRef(null)

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => setIsVisible(true))
    })
    return () => cancelAnimationFrame(id)
  }, [])

  useEffect(() => {
    return () => {
      if (exitTimerRef.current) clearTimeout(exitTimerRef.current)
    }
  }, [])

  const isMacro = !selectedLocation
  const cityTitle = isMacro
    ? 'National Overview'
    : (selectedLocation ? locationLabel(selectedLocation) : 'Market')
  const citySubtitle = isMacro
    ? 'Pick a market or stay macro.'
    : (selectedLocation ? locationSecondaryLabel(selectedLocation) : '')

  const resolvedTab = activeTab === 'compare' ? 'details' : activeTab

  function handleDismiss() {
    if (isExiting) return
    setIsExiting(true)
    exitTimerRef.current = window.setTimeout(() => {
      exitTimerRef.current = null
      onClose()
    }, ANIM_MS)
  }

  const rootClass = [
    'city-modal',
    isVisible && !isExiting ? 'city-modal--open' : '',
    isExiting ? 'city-modal--exit' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={rootClass}
      role="dialog"
      aria-modal="true"
      aria-labelledby="city-modal-title"
    >
      <button
        type="button"
        className="city-modal__backdrop"
        aria-label="Close market briefing"
        onClick={handleDismiss}
      />

      <div className={`city-modal__sheet glass${isMacro ? ' city-modal__sheet--macro' : ''}`}>
        <div className="city-modal__handle-wrap" aria-hidden>
          <span className="city-modal__handle-bar" />
        </div>

        <div className="city-modal__header">
          <div className="city-modal__context">
            <p className="eyebrow">Briefing</p>
            <h2 id="city-modal-title" className="display-heading">{cityTitle}</h2>
            <span>{isMacro ? citySubtitle : (citySubtitle || 'Market context')}</span>
          </div>

          <button
            type="button"
            className="city-modal__close"
            onClick={handleDismiss}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {!isMacro ? (
          <div className="city-modal__tabs">
            {TABS.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.key}
                  type="button"
                  className={`city-modal__tab ${resolvedTab === tab.key ? 'active' : ''}`}
                  onClick={() => onTabChange(tab.key)}
                >
                  <Icon size={16} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        ) : null}

        <div className="city-modal__content">
          <div className="city-modal__layer">
            {isMacro ? (
              <DetailsPanel
                activeId={null}
                locations={locations}
                rankings={rankings}
                hotspots={hotspots}
                onSelectLocation={onSelectLocation}
                sortBy={sortBy}
                suppressMacroHero
              />
            ) : null}

            {!isMacro && resolvedTab === 'details' ? (
              <DetailsPanel
                activeId={activeId}
                locations={locations}
                rankings={rankings}
                hotspots={hotspots}
                onSelectLocation={onSelectLocation}
                sortBy={sortBy}
              />
            ) : null}

            {!isMacro && resolvedTab === 'chain' ? (
              <BlockchainPanel
                activeId={activeId}
                locations={locations}
              />
            ) : null}

            {!isMacro && resolvedTab === 'ai' ? (
              <AIChat
                activeId={activeId}
                compareIds={compareIds}
                locations={locations}
                isActive={resolvedTab === 'ai'}
              />
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}
