import {
  Building2,
  GitCompareArrows,
  LayoutDashboard,
  MapPinned,
  Menu,
  MoonStar,
  RotateCcw,
  ShieldCheck,
  SunMedium,
} from 'lucide-react'
import { locationLabel, locationSecondaryLabel } from '../utils'
import './Header.css'

export default function Header({
  locationCount,
  stateCount,
  compareCount,
  activeLocation,
  hasSelection,
  theme,
  toggleTheme,
  onResetContext,
  onOpenMenu,
}) {
  const activeLabel = activeLocation ? locationLabel(activeLocation) : 'National overview'
  const secondaryLabel = activeLocation ? locationSecondaryLabel(activeLocation) : 'Investor presentation mode'

  return (
    <header className="header glass">
      <div className="header-brand">
        <button className="menu-trigger" onClick={onOpenMenu} aria-label="Open market list">
          <Menu size={18} />
        </button>

        <div className="brand-mark">
          <LayoutDashboard size={20} />
        </div>

        <div className="brand-copy">
          <span className="brand-title">BuiltAttic Brain</span>
          <span className="brand-subtitle">Investor-grade land intelligence</span>
        </div>
      </div>

      <div className="header-context hide-mobile">
        <div className="context-chip">
          <MapPinned size={15} />
          <div>
            <strong>{activeLabel}</strong>
            <span>{secondaryLabel || 'Select a market to drill in'}</span>
          </div>
        </div>
      </div>

      <div className="header-stats">
        <div className="stat-pill">
          <MapPinned size={14} />
          <span>{locationCount}</span>
          <small>Markets</small>
        </div>
        <div className="stat-pill hide-mobile">
          <Building2 size={14} />
          <span>{stateCount}</span>
          <small>States</small>
        </div>
        <div className="stat-pill">
          <GitCompareArrows size={14} />
          <span>{compareCount}</span>
          <small>Compare</small>
        </div>
      </div>

      <div className="header-actions">
        <div className="presentation-badge hide-mobile">
          <ShieldCheck size={14} />
          <span>Investor View</span>
        </div>

        {hasSelection ? (
          <button className="header-action secondary" onClick={onResetContext}>
            <RotateCcw size={16} />
            <span className="hide-mobile">Reset</span>
          </button>
        ) : null}

        <button
          className="header-action"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? <SunMedium size={17} /> : <MoonStar size={17} />}
          <span className="hide-mobile">{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>
      </div>
    </header>
  )
}
