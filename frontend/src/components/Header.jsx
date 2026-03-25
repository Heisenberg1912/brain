import './Header.css'

export default function Header({ locationCount, stateCount }) {
  return (
    <header className="header">
      <div className="logo">
        <div className="logo-icon">B</div>
        <div className="logo-text">Built<span>Attic</span> Brain</div>
      </div>
      <div className="header-stats">
        <span>Locations<span className="val"> {locationCount || '—'}</span></span>
        <span>States<span className="val"> {stateCount || '—'}</span></span>
        <span>Coverage<span className="val"> India</span></span>
      </div>
    </header>
  )
}
