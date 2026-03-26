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
}) {
  const activeLocation = activeId ? locations[activeId] : null
  const compareNames = compareIds.map((id) => locationLabel(locations[id], '')).filter(Boolean)

  const contextTitle = compareIds.length >= 2
    ? `Comparing ${compareIds.length} markets`
    : activeLocation
      ? locationLabel(activeLocation)
      : 'National overview'

  const contextSubtitle = compareIds.length >= 2
    ? compareNames.join(' vs ') || 'Selected comparison set'
    : activeLocation
      ? locationSecondaryLabel(activeLocation)
      : 'Pick a market or stay macro.'

  return (
    <aside className="right-panel glass">
      <div className="right-panel-header">
        <div className="panel-context">
          <p className="eyebrow">Briefing</p>
          <h2 className="display-heading">{contextTitle}</h2>
          <span>{contextSubtitle || 'Market context'}</span>
        </div>

        <button className="context-reset" onClick={onClose}>
          <RotateCcw size={16} />
          <span>Reset</span>
        </button>
      </div>

      <div className="tabs">
        {TABS.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              className={`tab ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => onTabChange(tab.key)}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      <div className="right-panel-content">
        {activeTab === 'details' ? (
          <DetailsPanel
            activeId={activeId}
            locations={locations}
            rankings={rankings}
            hotspots={hotspots}
          />
        ) : null}

        {activeTab === 'compare' ? (
          <CompareView
            compareIds={compareIds}
            locations={locations}
          />
        ) : null}

        {activeTab === 'chain' ? (
          <BlockchainPanel
            activeId={activeId}
            locations={locations}
          />
        ) : null}

        {activeTab === 'ai' ? (
          <AIChat
            activeId={activeId}
            compareIds={compareIds}
            locations={locations}
            isActive={activeTab === 'ai'}
          />
        ) : null}
      </div>
    </aside>
  )
}
