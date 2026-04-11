import { useEffect, useMemo, useState } from 'react'
import {
  Boxes,
  ExternalLink,
  FileText,
  Globe,
  Layers3,
  Network,
  Shield,
  Store,
} from 'lucide-react'
import {
  fetchContractProfile,
  fetchExchangeListings,
  fetchPlans,
  fetchStorageProfile,
  fetchSupportedNetworks,
  fetchTokenizedProperties,
} from '../api'
import { compactText, formatCurrency, formatLabel, formatNumber, locationLabel, truncateMiddle } from '../utils'
import './BlockchainPanel.css'

export default function BlockchainPanel({ activeId, locations }) {
  const [plans, setPlans] = useState([])
  const [properties, setProperties] = useState([])
  const [networks, setNetworks] = useState([])
  const [storageProfile, setStorageProfile] = useState(null)
  const [contractProfile, setContractProfile] = useState(null)
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    Promise.allSettled([
      fetchPlans(activeId),
      fetchTokenizedProperties(activeId),
      fetchSupportedNetworks(),
      fetchStorageProfile(),
      fetchContractProfile(),
      fetchExchangeListings({ status: 'active' }),
    ])
      .then(([plansResult, propertiesResult, networksResult, storageResult, contractResult, listingsResult]) => {
        if (cancelled) return

        const nextPlans = plansResult.status === 'fulfilled' ? plansResult.value : []
        const nextListings = listingsResult.status === 'fulfilled' ? listingsResult.value : []

        setPlans(nextPlans)
        setProperties(propertiesResult.status === 'fulfilled' ? propertiesResult.value : [])
        setNetworks(networksResult.status === 'fulfilled' ? networksResult.value : [])
        setStorageProfile(storageResult.status === 'fulfilled' ? storageResult.value : null)
        setContractProfile(contractResult.status === 'fulfilled' ? contractResult.value : null)
        setListings(nextListings)

        if (plansResult.status === 'rejected' && propertiesResult.status === 'rejected') {
          setError('Blockchain registry data could not be loaded.')
        }
      })
      .catch((fetchError) => {
        console.error(fetchError)
        if (!cancelled) setError('Blockchain registry data could not be loaded.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [activeId])

  const selectedLocationName = activeId ? locationLabel(locations[activeId]) : 'National registry overview'
  const locationPlanIds = useMemo(() => new Set(plans.map((plan) => plan.id)), [plans])
  const visibleListings = useMemo(() => {
    if (!activeId) return listings
    return listings.filter((listing) => locationPlanIds.has(listing.plan_id))
  }, [activeId, listings, locationPlanIds])

  if (loading) return <div className="panel-loading"><span className="spinner" /></div>
  if (error) return <div className="panel-error"><p>{error}</p></div>

  return (
    <div className="blockchain-panel">
      <section className="chain-hero">
        <div>
          <p className="eyebrow">Registry and asset rails</p>
          <h3>{selectedLocationName}</h3>
          <p>Plans, listings, networks, and tokenized assets in one view.</p>
        </div>
        <div className="chain-hero-stats">
          <div className="hero-stat">
            <span>Plans</span>
            <strong>{formatNumber(plans.length)}</strong>
          </div>
          <div className="hero-stat">
            <span>Properties</span>
            <strong>{formatNumber(properties.length)}</strong>
          </div>
          <div className="hero-stat">
            <span>Listings</span>
            <strong>{formatNumber(visibleListings.length)}</strong>
          </div>
        </div>
      </section>

      <section className="bp-section">
        <div className="bp-header">
          <Globe size={18} />
          <h4>Network posture</h4>
        </div>
        <div className="bp-grid">
          <article className="bp-card compact">
            <span>Storage</span>
            <strong>{formatLabel(storageProfile?.backend)}</strong>
            <small>{storageProfile?.gateway_base ? 'Gateway connected' : 'Gateway unavailable'}</small>
          </article>
          <article className="bp-card compact">
            <span>Default network</span>
            <strong>{contractProfile?.default_network || 'N/A'}</strong>
            <small>{String(contractProfile?.philosophy ?? '').trim() || 'Contract profile unavailable'}</small>
          </article>
          <article className="bp-card compact">
            <span>Supported chains</span>
            <strong>{formatNumber(networks.length)}</strong>
            <small>{networks.filter((item) => item.supports_fractional).length} fractional-ready</small>
          </article>
        </div>
      </section>

      <section className="bp-section">
        <div className="bp-header">
          <Network size={18} />
          <h4>Supported networks</h4>
        </div>
        <div className="bp-grid">
          {networks.map((network) => (
            <article key={network.key} className={`bp-card compact ${network.is_default ? 'highlight' : ''}`}>
              <span>{network.label}</span>
              <strong>{network.key}</strong>
              <small>{String(network.positioning ?? '').trim()}</small>
            </article>
          ))}
          {networks.length === 0 ? <p className="empty-msg">No network metadata returned.</p> : null}
        </div>
      </section>

      <section className="bp-section">
        <div className="bp-header">
          <Layers3 size={18} />
          <h4>Contract templates</h4>
        </div>
        <div className="bp-list">
          {contractProfile?.templates?.map((template) => (
            <article key={template.key} className="bp-card">
              <div className="bp-card-top">
                <strong>{template.name}</strong>
                <span className="bp-badge">{template.standard}</span>
              </div>
              <p>{formatLabel(template.asset_type)}</p>
              <small>Template ready</small>
            </article>
          ))}
          {!contractProfile?.templates?.length ? <p className="empty-msg">No contract templates available.</p> : null}
        </div>
      </section>

      <section className="bp-section">
        <div className="bp-header">
          <FileText size={18} />
          <h4>Architectural plans</h4>
        </div>
        <div className="bp-list">
          {plans.map((plan) => (
            <article key={plan.id} className="bp-card">
              <div className="bp-card-top">
                <strong>{plan.title}</strong>
                <span className={`bp-badge status-${plan.asset_status}`}>{formatLabel(plan.asset_status)}</span>
              </div>
              <p>{compactText(`${plan.author_name} • ${plan.version_label}`, '', 46)}</p>
              <div className="bp-meta-row">
                <span>{plan.chain || 'Not minted'}</span>
                <span>{truncateMiddle(plan.current_owner_wallet)}</span>
              </div>
              <div className="bp-icon-row">
                {plan.personal_license_allowed ? <span><Shield size={13} /> Personal</span> : null}
                {plan.commercial_license_allowed ? <span><Shield size={13} /> Commercial</span> : null}
                {plan.resale_license_allowed ? <span><Shield size={13} /> Resale</span> : null}
              </div>
              {plan.storage_gateway_url ? (
                <a className="bp-link" href={plan.storage_gateway_url} target="_blank" rel="noreferrer">
                  <ExternalLink size={14} />
                  Open storage
                </a>
              ) : null}
            </article>
          ))}
          {plans.length === 0 ? <p className="empty-msg">No plans are registered for this scope yet.</p> : null}
        </div>
      </section>

      <section className="bp-section">
        <div className="bp-header">
          <Store size={18} />
          <h4>Active exchange listings</h4>
        </div>
        <div className="bp-list">
          {visibleListings.map((listing) => (
            <article key={listing.id} className="bp-card">
              <div className="bp-card-top">
                <strong>Plan #{listing.plan_id}</strong>
                <span className="bp-badge">{formatLabel(listing.listing_type)}</span>
              </div>
              <p>{formatCurrency(listing.asking_price, { currency: listing.currency || 'USD' })}</p>
              <div className="bp-meta-row">
                <span>{truncateMiddle(listing.seller_wallet)}</span>
                <span>{formatLabel(listing.status)}</span>
              </div>
            </article>
          ))}
          {visibleListings.length === 0 ? <p className="empty-msg">No active listings were returned for this scope.</p> : null}
        </div>
      </section>

      <section className="bp-section">
        <div className="bp-header">
          <Boxes size={18} />
          <h4>Tokenized properties</h4>
        </div>
        <div className="bp-list">
          {properties.map((property) => (
            <article key={property.id} className="bp-card">
              <div className="bp-card-top">
                <strong>{property.asset_name}</strong>
                <span className="bp-badge">{property.token_symbol || property.token_standard || 'Asset token'}</span>
              </div>
              <p>{formatLabel(property.property_type)} • {formatLabel(property.status)}</p>
              <div className="bp-meta-row">
                <span>{formatCurrency(property.valuation_amount, { currency: property.currency || 'USD' })}</span>
                <span>{formatNumber(property.total_units)} units</span>
              </div>
              <div className="bp-meta-row">
                <span>{property.chain || 'N/A'}</span>
                <span>{property.contract_address ? truncateMiddle(property.contract_address) : 'Contract pending'}</span>
              </div>
            </article>
          ))}
          {properties.length === 0 ? <p className="empty-msg">No tokenized properties were returned for this scope.</p> : null}
        </div>
      </section>
    </div>
  )
}
