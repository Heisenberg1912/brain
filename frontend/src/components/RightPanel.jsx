import { Suspense, lazy, useEffect, useState } from 'react'
import './RightPanel.css'

const DetailsPanel = lazy(() => import('./DetailsPanel'))
const CompareView = lazy(() => import('./CompareView'))
const AIChat = lazy(() => import('./AIChat'))

const TABS = [
  { key: 'details', label: 'Details' },
  { key: 'compare', label: 'Compare' },
  { key: 'ai', label: 'AI Query' },
]

export default function RightPanel({ activeTab, onTabChange, activeId, compareIds, locations, rankings }) {
  const [loadedTabs, setLoadedTabs] = useState({ details: true })

  useEffect(() => {
    setLoadedTabs(prev => (
      prev[activeTab]
        ? prev
        : { ...prev, [activeTab]: true }
    ))
  }, [activeTab])

  const tabProps = {
    details: { activeId, rankings, isActive: activeTab === 'details' },
    compare: { compareIds, locations, isActive: activeTab === 'compare' },
    ai: { activeId, compareIds, locations, isActive: activeTab === 'ai' },
  }

  const tabComponents = {
    details: DetailsPanel,
    compare: CompareView,
    ai: AIChat,
  }

  return (
    <aside className="right-panel">
      <div className="tabs">
        {TABS.map(t => (
          <div
            key={t.key}
            className={`tab ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => onTabChange(t.key)}
          >
            {t.label}
          </div>
        ))}
      </div>

      {TABS.map(tab => {
        const TabComponent = tabComponents[tab.key]
        return (
          <div key={tab.key} className={`tab-content ${activeTab === tab.key ? 'active' : ''}`}>
            {loadedTabs[tab.key] && (
              <Suspense fallback={<div className="panel-loading"><span className="spinner" /> Loading panel...</div>}>
                <TabComponent {...tabProps[tab.key]} />
              </Suspense>
            )}
          </div>
        )
      })}
    </aside>
  )
}
