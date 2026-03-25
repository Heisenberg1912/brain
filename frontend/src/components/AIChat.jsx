import { useEffect, useMemo, useRef, useState } from 'react'
import { askAI, fetchAIMarketBrief } from '../api'
import { escapeHtml, formatMarkdown } from '../utils'
import './AIChat.css'

const SUGGESTIONS = [
  'Which Indian market has the strongest future appreciation?',
  'Compare Hyderabad vs Pune growth corridors',
  'Best mixed-use opportunities across India?',
  'Where should I build commercial next?',
]

export default function AIChat({ activeId, compareIds, locations, isActive }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [brief, setBrief] = useState(null)
  const [briefError, setBriefError] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!isActive || brief) return

    let cancelled = false

    fetchAIMarketBrief()
      .then((response) => {
        if (!cancelled) {
          setBrief(response)
          setBriefError('')
        }
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) {
          setBriefError('AI market pulse is unavailable right now.')
        }
      })

    return () => {
      cancelled = true
    }
  }, [brief, isActive])

  const activeLocation = activeId ? locations?.[activeId] : null
  const compareNames = useMemo(() => (
    (compareIds || []).map((id) => locations?.[id]?.name).filter(Boolean)
  ), [compareIds, locations])

  const contextLabel = useMemo(() => {
    if (compareNames.length >= 2) {
      return compareNames.join(' vs ')
    }
    if (activeLocation) {
      return [activeLocation.name, activeLocation.city, activeLocation.state].filter(Boolean).join(' · ')
    }
    return brief?.national_thesis || 'India market context'
  }, [activeLocation, brief, compareNames])

  const suggestions = useMemo(() => {
    if (compareNames.length >= 2) {
      return [
        `Which of ${compareNames.join(' and ')} has the better 3-year upside?`,
        `What is the key risk difference between ${compareNames[0]} and ${compareNames[1]}?`,
        `Which one is better for commercial development?`,
      ]
    }

    if (activeLocation) {
      return [
        `Should I buy in ${activeLocation.name}?`,
        `What are the biggest risks in ${activeLocation.name}?`,
        `What is the best use case for ${activeLocation.name}?`,
      ]
    }

    return brief?.prompt_suggestions?.length ? brief.prompt_suggestions : SUGGESTIONS
  }, [activeLocation, brief, compareNames])

  const send = async (question) => {
    const q = question || input.trim()
    if (!q || loading) return
    setInput('')

    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)

    try {
      const res = await askAI(q, {
        locationId: activeId,
        compareIds,
      })
      setMessages(prev => [...prev, { role: 'bot', text: res.answer, contextLabel: res.context_label }])
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: 'Failed to get response. Check API connection.', error: true }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-container">
      <div className="ai-context-bar">
        <span className="ai-context-label">Brain Context</span>
        <span className="ai-context-value">{contextLabel}</span>
      </div>

      {messages.length === 0 && brief && (
        <div className="ai-brief">
          <div className="ai-brief-head">
            <div>
              <div className="ai-brief-title">Market Pulse</div>
              <div className="ai-brief-thesis">{brief.national_thesis}</div>
            </div>
          </div>
          <p className="ai-brief-summary">{brief.summary}</p>

          {!!brief.top_opportunities?.length && (
            <div className="ai-brief-grid">
              {brief.top_opportunities.slice(0, 4).map((item) => (
                <button
                  key={`${item.location_id}-${item.location_name}-${item.title}`}
                  className="ai-brief-card"
                  onClick={() => send(`Give me a deep read on ${item.location_name}.`)}
                >
                  <div className="ai-brief-card-top">
                    <span className="ai-brief-location">{item.location_name}</span>
                    {typeof item.score === 'number' && <span className="ai-brief-score">{Math.round(item.score)}</span>}
                  </div>
                  <div className="ai-brief-card-title">{item.title}</div>
                  <div className="ai-brief-card-reason">{item.reason}</div>
                </button>
              ))}
            </div>
          )}

          {!!brief.watchouts?.length && (
            <div className="ai-watchouts">
              {brief.watchouts.slice(0, 2).map((item) => (
                <div key={item} className="ai-watchout">{item}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {messages.length === 0 && briefError && (
        <div className="ai-brief ai-brief-error">{briefError}</div>
      )}

      {messages.length === 0 && (
        <div className="ai-suggestions">
          {suggestions.map(s => (
            <div key={s} className="ai-chip" onClick={() => send(s)}>{s}</div>
          ))}
        </div>
      )}

      <div className="ai-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`ai-message ${msg.role}`}>
            {msg.role === 'bot' && msg.contextLabel && (
              <div className="ai-inline-context">{msg.contextLabel}</div>
            )}
            <div
              className={`bubble ${msg.error ? 'error' : ''}`}
              dangerouslySetInnerHTML={{ __html: msg.role === 'bot' ? formatMarkdown(msg.text) : escapeHtml(msg.text) }}
            />
          </div>
        ))}
        {loading && (
          <div className="ai-message bot">
            <div className="bubble"><span className="spinner" /> Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="ai-input-row">
        <input
          className="ai-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask BuiltAttic Brain about this market..."
        />
        <button className="ai-send" onClick={() => send()} disabled={loading || !input.trim()}>
          Ask
        </button>
      </div>
    </div>
  )
}
