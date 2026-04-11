import { useEffect, useRef } from 'react'

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

function focusableElements(root) {
  return Array.from(root.querySelectorAll(FOCUSABLE_SELECTOR))
}

export function useDialogFocusTrap(dialogRef, onDismiss) {
  const onDismissRef = useRef(onDismiss)
  onDismissRef.current = onDismiss

  useEffect(() => {
    const root = dialogRef.current
    if (!root) return undefined

    const previous = document.activeElement

    const focusInitial = () => {
      const close = root.querySelector('.city-modal__close, .compare-modal__close')
      if (close && typeof close.focus === 'function') {
        close.focus()
        return
      }
      const list = focusableElements(root)
      list[0]?.focus()
    }

    const focusTimer = window.setTimeout(focusInitial, 0)

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onDismissRef.current()
        return
      }

      if (event.key !== 'Tab') return

      const list = focusableElements(root)
      if (list.length === 0) return

      const first = list[0]
      const last = list[list.length - 1]
      const active = document.activeElement

      if (event.shiftKey) {
        if (active === first) {
          event.preventDefault()
          last.focus()
        }
      } else if (active === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown, true)

    return () => {
      window.clearTimeout(focusTimer)
      document.removeEventListener('keydown', handleKeyDown, true)
      if (previous && typeof previous.focus === 'function' && document.contains(previous)) {
        previous.focus()
      }
    }
  }, [dialogRef])
}
