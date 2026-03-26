import { useEffect, useMemo, useRef, useState } from 'react'
import { Bot, Send, Sparkles, TrendingUp } from 'lucide-react'
import { askAI, fetchAIBrainProfile, fetchAIMarketBrief } from '../api'
import { compactText, formatLabel, formatMarkdown, locationLabel } from '../utils'
import './AIChat.css'

const DEFAULT_SUGGESTIONS = [
  'Best risk-adjusted market right now?',
  'Where is mixed-use strongest?',
  'Compare upside and risk.',
]

export default function AIChat({ activeId, compareIds, locations, isActive }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [brief, setBrief] = useState(null)
  const [briefError, setBriefError] = useState('')
  const [brainProfile, setBrainProfile] = useState(null)
  const [brainError, setBrainError] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    setMessages([])
  }, [activeId, compareIds.join('|')])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (!isActive) return

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
        if (!cancelled) setBriefError('AI market brief is unavailable right now.')
      })

    return () => {
      cancelled = true
    }
  }, [isActive])

  useEffect(() => {
    if (!isActive || !activeId || compareIds.length >= 2) {
      setBrainProfile(null)
      setBrainError('')
      return
    }

    let cancelled = false

    fetchAIBrainProfile(activeId)
      .then((response) => {
        if (!cancelled) {
          setBrainProfile(response)
          setBrainError('')
        }
      })
      .catch((error) => {
        console.error(error)
        if (!cancelled) setBrainError('Location AI profile could not be loaded.')
      })

    return () => {
      cancelled = true
    }
  }, [activeId, compareIds.length, isActive])

  const activeLocation = activeId ? locations[activeId] : null
  const compareNames = useMemo(
    () => compareIds.map((id) => locationLabel(locations[id], '')).filter(Boolean),
    [compareIds, locations],
  )

  const contextLabel = useMemo(() => {
    if (compareNames.length >= 2) return `Compare: ${compareNames.join(' vs ')}`
    if (activeLocation) return `Market: ${locationLabel(activeLocation)}`
    return 'National view'
  }, [activeLocation, compareNames])

  const suggestions = useMemo(() => {
    if (compareNames.length >= 2) {
      return [
        `Better 3-year upside: ${compareNames.join(' or ')}?`,
        `Key risk difference: ${compareNames[0]} vs ${compareNames[1]}`,
        'Better fit for mixed-use?',
      ]
    }

    if (activeLocation) {
      return [
        `Thesis for ${locationLabel(activeLocation)}`,
        `Key risk in ${locationLabel(activeLocation)}`,
        `Best use case for ${locationLabel(activeLocation)}`,
      ]
    }

    return brief?.prompt_suggestions?.length ? brief.prompt_suggestions : DEFAULT_SUGGESTIONS
  }, [activeLocation, brief, compareNames])

  async function send(question) {
    const normalizedQuestion = question || input.trim()
    if (!normalizedQuestion || loading) return

    setInput('')
    setMessages((current) => [...current, { role: 'user', text: normalizedQuestion }])
    setLoading(true)

    try {
      const response = await askAI(normalizedQuestion, {
        locationId: activeId,
        compareIds,
      })

      setMessages((current) => [
        ...current,
        {
          role: 'bot',
          text: response.answer,
          contextLabel: response.context_label,
        },
      ])
    } catch (error) {
      console.error(error)
      setMessages((current) => [
        ...current,
        {
          role: 'bot',
          text: error.message || 'AI query failed.',
          error: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-chat">
      <div className="ai-header">
        <Sparkles size={16} className="sparkle-icon" />
        <span className="context-text">{contextLabel}</span>
      </div>

      <div className="ai-scroll-area">
        {messages.length === 0 ? (
          <div className="ai-empty-state">
            {brainProfile ? (
              <section className="ai-card emphasis">
                <div className="ai-card-header">
                  <Bot size={18} />
                  <h4>{brainProfile.location_name}</h4>
                </div>
                <p>{compactText(brainProfile.thesis, 'No thesis returned.', 110)}</p>
                <div className="brain-module-grid">
                  {brainProfile.modules?.slice(0, 3).map((module) => (
                    <article key={module.key} className={`brain-module-card status-${module.status}`}>
                      <div>
                        <strong>{module.title}</strong>
                        <span>{formatLabel(module.status)} • {module.source_system}</span>
                      </div>
                    </article>
                  ))}
                </div>
                {brainProfile.recommendations?.length ? (
                  <div className="recommendation-strip">
                    {brainProfile.recommendations.map((item) => (
                      <article key={item.label} className={`recommendation-card priority-${item.priority}`}>
                        <strong>{item.label}</strong>
                        <span>{item.action}</span>
                      </article>
                    ))}
                  </div>
                ) : null}
              </section>
            ) : null}

            {brief ? (
              <section className="ai-card">
                <div className="ai-card-header">
                  <TrendingUp size={18} />
                  <h4>Market brief</h4>
                </div>
                <p>{compactText(brief.summary, 'National summary unavailable.', 110)}</p>
                {brief.top_opportunities?.length ? (
                  <div className="opportunity-list">
                    {brief.top_opportunities.slice(0, 2).map((item) => (
                      <article key={`${item.location_name}-${item.title}`} className="opportunity-card">
                        <strong>{item.location_name}</strong>
                        <span>{compactText(item.reason, item.title, 64)}</span>
                      </article>
                    ))}
                  </div>
                ) : null}
              </section>
            ) : null}

            {brainError ? <p className="panel-inline-error">{brainError}</p> : null}
            {briefError ? <p className="panel-inline-error">{briefError}</p> : null}

            <div className="suggestions-grid">
              {suggestions.map((suggestion) => (
                <button key={suggestion} className="suggestion-pill" onClick={() => send(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`message-row ${message.role}`}>
            <div className={`message-bubble ${message.error ? 'error' : ''}`}>
              {message.role === 'bot' ? <div className="bot-avatar"><Sparkles size={12} /></div> : null}
              <div
                className="message-content"
                dangerouslySetInnerHTML={{ __html: formatMarkdown(message.text) }}
              />
              {message.contextLabel ? <span className="message-context">{message.contextLabel}</span> : null}
            </div>
          </div>
        ))}

        {loading ? (
          <div className="message-row bot">
            <div className="message-bubble loading">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </div>

      <div className="ai-input-container">
        <div className="input-wrapper">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') send()
            }}
            placeholder="Ask about this market or basket"
          />
          <button className="send-button" onClick={() => send()} disabled={loading || !input.trim()}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}
