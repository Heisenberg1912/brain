import { Bot, Boxes, GitCompareArrows, Map, RotateCcw } from 'lucide-react'
import BlockchainPanel from './BlockchainPanel'
import CompareView from './CompareView'
import DetailsPanel from './DetailsPanel'
import AIChat from './AIChat'
import { locationLabel, locationSecondaryLabel } from '../utils'
import './RightPanel.css'

const TABS = [
  { key: 'details', label: 'Overview', icon: Map },
  { key: 'compare', label: 'Compare', icon: GitCompareArrows },
  { key: 'chain', label: 'Blockchain', icon: Boxes },
  { key: 'ai', label: 'AI', icon: Bot },
]

export default function RightPanel({
  activeTab,
  onTabChange,
  activeId,
  compareIds,
  locations,
  rankings,
  hotspots,
  onClose,
  panelMode,
  selectedLocation,
  onSelectLocation,
  sortBy,
}) {
  const isMacro = panelMode === 'macro'
  const isCity = panelMode === 'city'

  const macroSubtitle = 'Pick a market or stay macro.'
  const cityTitle = selectedLocation ? locationLabel(selectedLocation) : 'Market'
  const citySubtitle = selectedLocation ? locationSecondaryLabel(selectedLocation) : ''

  return (
    <aside className={`right-panel glass right-panel--${panelMode}`}>
      <div className="right-panel-header">
        <div className="panel-context">
          <p className="eyebrow">Briefing</p>
          {isMacro ? (
            <>
              <h2 className="display-heading">National Overview</h2>
              <span>{macroSubtitle}</span>
            </>
          ) : (
            <>
              <h2 className="display-heading">{cityTitle}</h2>
              <span>{citySubtitle || 'Market context'}</span>
            </>
          )}
        </div>

        <button className="context-reset" onClick={onClose}>
          <RotateCcw size={16} />
          <span>Reset</span>
        </button>
      </div>

      {isCity ? (
        <div className="tabs">
          {TABS.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.key}
                type="button"
                className={`tab ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => onTabChange(tab.key)}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>
      ) : null}

      <div className="right-panel-content">
        <div key={panelMode} className="right-panel-mode-layer">
          {isMacro ? (
            <DetailsPanel
              activeId={null}
              locations={locations}
              rankings={rankings}
              hotspots={hotspots}
              onSelectLocation={onSelectLocation}
              sortBy={sortBy}
            />
          ) : null}

          {isCity && activeTab === 'details' ? (
            <DetailsPanel
              activeId={activeId}
              locations={locations}
              rankings={rankings}
              hotspots={hotspots}
              onSelectLocation={onSelectLocation}
              sortBy={sortBy}
            />
          ) : null}

          {isCity && activeTab === 'compare' ? (
            compareIds.length >= 2 ? (
              <CompareView
                compareIds={compareIds}
                locations={locations}
              />
            ) : (
              <div className="compare-tab-placeholder">
                <p className="muted-copy">Pin 2+ markets to compare</p>
              </div>
            )
          ) : null}

          {isCity && activeTab === 'chain' ? (
            <BlockchainPanel
              activeId={activeId}
              locations={locations}
            />
          ) : null}

          {isCity && activeTab === 'ai' ? (
            <AIChat
              activeId={activeId}
              compareIds={compareIds}
              locations={locations}
              isActive={activeTab === 'ai'}
            />
          ) : null}
        </div>
      </div>
    </aside>
  )
}
