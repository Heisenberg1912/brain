const SCORE_HEX = {
  high: '#18b787',
  medium: '#f59e0b',
  low: '#ef4444',
}

export function scoreHex(value) {
  const numericValue = Number(value) || 0
  if (numericValue >= 75) return SCORE_HEX.high
  if (numericValue >= 45) return SCORE_HEX.medium
  return SCORE_HEX.low
}

export function scoreColor(value) {
  const numericValue = Number(value) || 0
  if (numericValue >= 75) return 'var(--green)'
  if (numericValue >= 45) return 'var(--amber)'
  return 'var(--red)'
}

export function scoreClass(value) {
  const numericValue = Number(value) || 0
  if (numericValue >= 75) return 'high'
  if (numericValue >= 45) return 'mid'
  return 'low'
}

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

export function formatCurrency(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A'

  const {
    currency = 'INR',
    compact = false,
    maximumFractionDigits = 0,
  } = options

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits,
  }).format(Number(value))
}

export function formatNumber(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A'

  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: options.maximumFractionDigits ?? 0,
    notation: options.compact ? 'compact' : 'standard',
  }).format(Number(value))
}

export function formatPercent(value, maximumFractionDigits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A'
  return `${Number(value).toFixed(maximumFractionDigits)}%`
}

export function formatDistance(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A'
  return value < 1 ? `${Math.round(Number(value) * 1000)} m` : `${Number(value).toFixed(1)} km`
}

export function formatLabel(value) {
  if (!value) return 'N/A'
  return String(value)
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

export function locationLabel(locationLike, fallback = 'Unknown location') {
  return locationLike?.name || locationLike?.location || locationLike?.location_name || fallback
}

export function locationSecondaryLabel(locationLike) {
  const parts = [
    locationLike?.locality,
    locationLike?.city,
    locationLike?.state,
  ].filter(Boolean)

  return parts.join(', ')
}

export function compactText(value, fallback = '', maxLength = 120) {
  const text = String(value ?? '')
    .replace(/\s+/g, ' ')
    .trim()

  if (!text) return fallback

  const sentenceMatch = text.match(/^.*?[.!?](?:\s|$)/)
  const firstSentence = sentenceMatch?.[0]?.trim() || text

  if (firstSentence.length <= maxLength) return firstSentence
  return `${firstSentence.slice(0, Math.max(maxLength - 3, 1)).trimEnd()}...`
}

export function truncateMiddle(value, start = 6, end = 4) {
  const text = String(value ?? '').trim()
  if (!text) return 'N/A'
  if (text.length <= start + end + 3) return text
  return `${text.slice(0, start)}...${text.slice(-end)}`
}

const HTML_ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
}

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => HTML_ESCAPE_MAP[char])
}

function formatInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
}

function toList(lines, ordered = false) {
  const tag = ordered ? 'ol' : 'ul'
  const items = lines
    .map((line) => line.replace(ordered ? /^\d+\.\s+/ : /^-\s+/, ''))
    .map((line) => `<li>${formatInlineMarkdown(line)}</li>`)
    .join('')

  return `<${tag}>${items}</${tag}>`
}

export function formatMarkdown(text) {
  if (!text) return ''

  return String(text)
    .trim()
    .split(/\n{2,}/)
    .map((block) => {
      const lines = block
        .split('\n')
        .map((line) => line.trimEnd())
        .filter(Boolean)

      if (lines.length === 0) return ''

      const headingMatch = lines.length === 1 ? lines[0].match(/^(#{1,4})\s+(.+)$/) : null
      if (headingMatch) {
        const level = Math.min(headingMatch[1].length + 1, 5)
        return `<h${level}>${formatInlineMarkdown(headingMatch[2])}</h${level}>`
      }

      if (lines.every((line) => line.startsWith('- '))) {
        return toList(lines, false)
      }

      if (lines.every((line) => /^\d+\.\s+/.test(line))) {
        return toList(lines, true)
      }

      return `<p>${lines.map((line) => formatInlineMarkdown(line)).join('<br>')}</p>`
    })
    .join('')
}

export const INFRA_CONFIG = {
  metro_station: { icon: 'M', color: '#0ea5e9', label: 'Metro Stations' },
  highway: { icon: 'H', color: '#f97316', label: 'Highways' },
  hospital: { icon: '+', color: '#ef4444', label: 'Hospitals' },
  school: { icon: 'S', color: '#8b5cf6', label: 'Schools' },
  economic_zone: { icon: 'E', color: '#14b8a6', label: 'Economic Zones' },
  airport: { icon: 'A', color: '#22c55e', label: 'Airports' },
  rail: { icon: 'R', color: '#eab308', label: 'Rail' },
}

export const ZONING_COLORS = {
  residential: '#f4c95d',
  commercial: '#fb7185',
  industrial: '#60a5fa',
  mixed: '#34d399',
  mixed_use: '#34d399',
  public: '#a78bfa',
  open_space: '#22c55e',
  unclassified: '#94a3b8',
}
