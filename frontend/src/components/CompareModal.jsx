import { useEffect, useMemo, useRef, useState } from 'react'
import { X } from 'lucide-react'
import CompareView from './CompareView'
import { useDialogFocusTrap } from '../hooks/useDialogFocusTrap'
import { locationLabel } from '../utils'
import './CompareModal.css'

const ANIM_MS = 250

export default function CompareModal({ compareIds, locations, onClose }) {
  const [isVisible, setIsVisible] = useState(false)
  const [isExiting, setIsExiting] = useState(false)
  const exitTimerRef = useRef(null)
  const dialogRef = useRef(null)

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

  const compareNames = useMemo(
    () => compareIds.map((id) => locationLabel(locations[id], '')).filter(Boolean),
    [compareIds, locations],
  )

  const title = `Comparing ${compareIds.length} markets`
  const subtitle = compareNames.join(' vs ') || 'Selected markets'

  function handleDismiss() {
    if (isExiting) return
    setIsExiting(true)
    exitTimerRef.current = window.setTimeout(() => {
      exitTimerRef.current = null
      onClose()
    }, ANIM_MS)
  }

  useDialogFocusTrap(dialogRef, handleDismiss)

  const rootClass = [
    'compare-modal',
    isVisible && !isExiting ? 'compare-modal--open' : '',
    isExiting ? 'compare-modal--exit' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      ref={dialogRef}
      className={rootClass}
      role="dialog"
      aria-modal="true"
      aria-labelledby="compare-modal-title"
    >
      <button
        type="button"
        className="compare-modal__backdrop"
        aria-label="Close comparison"
        onClick={handleDismiss}
      />

      <div className="compare-modal__sheet glass">
        <div className="compare-modal__header">
          <div className="compare-modal__context">
            <p className="eyebrow">Compare</p>
            <h2 id="compare-modal-title" className="display-heading">{title}</h2>
            <span>{subtitle}</span>
          </div>

          <button
            type="button"
            className="compare-modal__close"
            onClick={handleDismiss}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="compare-modal__content">
          <CompareView
            compareIds={compareIds}
            locations={locations}
            hideHeroHeading
          />
        </div>
      </div>
    </div>
  )
}
