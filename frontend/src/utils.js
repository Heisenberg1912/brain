export function scoreColor(value) {
  if (value >= 70) return 'var(--green)';
  if (value >= 40) return 'var(--orange)';
  return 'var(--red)';
}

export function scoreClass(value) {
  if (value >= 70) return 'high';
  if (value >= 40) return 'mid';
  return 'low';
}

const HTML_ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => HTML_ESCAPE_MAP[char]);
}

function formatInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

export function formatMarkdown(text) {
  if (!text) return '';
  return String(text)
    .trim()
    .split(/\n{2,}/)
    .map((block) => {
      const lines = block
        .split('\n')
        .map((line) => line.trimEnd())
        .filter(Boolean);

      if (lines.length === 0) return '';

      const headingMatch = lines.length === 1
        ? lines[0].match(/^(#{1,3})\s+(.+)$/)
        : null;

      if (headingMatch) {
        const level = Math.min(headingMatch[1].length + 1, 4);
        return `<h${level}>${formatInlineMarkdown(headingMatch[2])}</h${level}>`;
      }

      if (lines.every((line) => line.startsWith('- '))) {
        return `<ul>${lines.map((line) => `<li>${formatInlineMarkdown(line.slice(2))}</li>`).join('')}</ul>`;
      }

      return `<p>${lines.map((line) => formatInlineMarkdown(line)).join('<br>')}</p>`;
    })
    .join('');
}

export const SCORE_WEIGHTS = {
  land_value: { 'Avg Price': 0.30, 'Infra': 0.25, 'Zoning': 0.20, 'Density': 0.15, 'Price Trend': 0.10 },
  development_potential: { 'FSI Headroom': 0.30, 'Zoning Type': 0.25, 'Planned Infra': 0.25, 'Price Growth': 0.20 },
  future_appreciation: { 'Price Trend 5yr': 0.25, 'Infra Pipeline': 0.30, 'Pop. Growth': 0.20, 'Zoning Shift': 0.25 },
};

export const INFRA_CONFIG = {
  metro_station: { icon: 'M', color: '#6c5ce7', label: 'Metro Stations' },
  highway: { icon: 'H', color: '#636e72', label: 'Highways' },
  hospital: { icon: '+', color: '#e17055', label: 'Hospitals' },
  school: { icon: 'S', color: '#fdcb6e', label: 'Schools' },
  economic_zone: { icon: 'E', color: '#00b894', label: 'Tech Parks' },
  airport: { icon: 'A', color: '#0984e3', label: 'Airport' },
};

export const ZONING_COLORS = {
  residential: '#f2d57e',
  commercial: '#ff8a65',
  industrial: '#9b8cff',
  mixed: '#46c5b8',
  public: '#57a9ff',
  open_space: '#73d98d',
  unclassified: '#8d93a6',
}
