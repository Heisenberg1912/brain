import {
  getDemoAIAnalysis,
  getDemoAIAnswer,
  getDemoAIBrainProfile,
  getDemoAICompare,
  getDemoAIMarketBrief,
  getDemoCompare,
  getDemoContractProfile,
  getDemoExchangeListings,
  getDemoHotspots,
  getDemoInfrastructure,
  getDemoIntelligence,
  getDemoLocationDetail,
  getDemoLocations,
  getDemoNearbyInfrastructure,
  getDemoPlanningContext,
  getDemoPlans,
  getDemoPrediction,
  getDemoRankings,
  getDemoScore,
  getDemoStorageProfile,
  getDemoSupportedNetworks,
  getDemoTokenizedProperties,
  getDemoValuationCore,
  getDemoValuationLogic,
} from './demoData'

const API = ''

function buildQuery(params = {}) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    query.set(key, String(value))
  })

  const serialized = query.toString()
  return serialized ? `?${serialized}` : ''
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`

    try {
      const errorPayload = await response.json()
      if (typeof errorPayload?.detail === 'string' && errorPayload.detail.trim()) {
        detail = errorPayload.detail
      }
    } catch {
      // Fall back to the generic message when the body is not JSON.
    }

    throw new Error(detail)
  }

  return response.json()
}

async function withDemoFallback(requestFactory, fallbackFactory) {
  try {
    return await requestFactory()
  } catch {
    return fallbackFactory()
  }
}

export function fetchLocations(filters = {}) {
  return withDemoFallback(
    () => requestJson(`/api/v1/data/locations${buildQuery(filters)}`),
    () => getDemoLocations(filters),
  )
}

export function fetchLocationDetail(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/data/locations/${locationId}`),
    () => getDemoLocationDetail(locationId),
  )
}

export function fetchPlanningContext(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/data/locations/${locationId}/planning-context`),
    () => getDemoPlanningContext(locationId),
  )
}

export function fetchInfrastructure() {
  return withDemoFallback(
    () => requestJson('/api/v1/data/infrastructure'),
    () => getDemoInfrastructure(),
  )
}

export function fetchNearbyInfra(locationId, radiusKm = 5) {
  return withDemoFallback(
    () => requestJson(`/api/v1/data/locations/${locationId}/nearby-infra${buildQuery({ radius_km: radiusKm })}`),
    () => getDemoNearbyInfrastructure(locationId, radiusKm),
  )
}

export function fetchIntelligence(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/data/locations/${locationId}/intelligence`),
    () => getDemoIntelligence(locationId),
  )
}

export function fetchRankings(sortBy = 'land_value_score', top = 20) {
  return withDemoFallback(
    () => requestJson(`/api/v1/valuation/rankings${buildQuery({ top, sort_by: sortBy })}`),
    () => getDemoRankings(sortBy, top),
  )
}

export function fetchScore(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/valuation/score/${locationId}`),
    () => getDemoScore(locationId),
  )
}

export function fetchCompare(locationIds) {
  return withDemoFallback(
    () => requestJson('/api/v1/valuation/compare', {
      method: 'POST',
      body: JSON.stringify({ location_ids: locationIds }),
    }),
    () => getDemoCompare(locationIds),
  )
}

export function fetchValuationCore(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/valuation/core/${locationId}`),
    () => getDemoValuationCore(locationId),
  )
}

export function fetchValuationLogic(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/valuation/logic/${locationId}`),
    () => getDemoValuationLogic(locationId),
  )
}

export function fetchPrediction(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/valuation/predict/${locationId}`),
    () => getDemoPrediction(locationId),
  )
}

export function fetchHotspots(nClusters = 4) {
  return withDemoFallback(
    () => requestJson(`/api/v1/valuation/hotspots${buildQuery({ n_clusters: nClusters })}`),
    () => getDemoHotspots(nClusters),
  )
}

export function askAI(question, { locationId = null, compareIds = [] } = {}) {
  return withDemoFallback(
    () => requestJson('/api/v1/ai/query', {
      method: 'POST',
      body: JSON.stringify({
        question,
        location_id: locationId,
        compare_ids: compareIds,
      }),
    }),
    () => getDemoAIAnswer(question, { locationId, compareIds }),
  )
}

export function analyzeAI(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/ai/analyze/${locationId}`),
    () => getDemoAIAnalysis(locationId),
  )
}

export function fetchAIMarketBrief() {
  return withDemoFallback(
    () => requestJson('/api/v1/ai/market-brief'),
    () => getDemoAIMarketBrief(),
  )
}

export function fetchAICompare(locationIds) {
  return withDemoFallback(
    () => requestJson('/api/v1/ai/compare', {
      method: 'POST',
      body: JSON.stringify({ location_ids: locationIds }),
    }),
    () => getDemoAICompare(locationIds),
  )
}

export function fetchAIBrainProfile(locationId) {
  return withDemoFallback(
    () => requestJson(`/api/v1/ai/brain/${locationId}`),
    () => getDemoAIBrainProfile(locationId),
  )
}

export function fetchPlans(locationId = null) {
  return withDemoFallback(
    () => requestJson(`/api/v1/chain/plans${buildQuery({ location_id: locationId })}`),
    () => getDemoPlans(locationId),
  )
}

export function fetchPlanLicenses(planId) {
  return requestJson(`/api/v1/chain/plans/${planId}/licenses`)
}

export function fetchExchangeListings(filters = {}) {
  return withDemoFallback(
    () => requestJson(`/api/v1/chain/exchange/listings${buildQuery(filters)}`),
    () => getDemoExchangeListings(filters),
  )
}

export function fetchTokenizedProperties(locationId = null) {
  return withDemoFallback(
    () => requestJson(`/api/v1/chain/properties${buildQuery({ location_id: locationId })}`),
    () => getDemoTokenizedProperties(locationId),
  )
}

export function fetchSupportedNetworks() {
  return withDemoFallback(
    () => requestJson('/api/v1/chain/networks'),
    () => getDemoSupportedNetworks(),
  )
}

export function fetchStorageProfile() {
  return withDemoFallback(
    () => requestJson('/api/v1/chain/storage/profile'),
    () => getDemoStorageProfile(),
  )
}

export function fetchContractProfile() {
  return withDemoFallback(
    () => requestJson('/api/v1/chain/contracts/profile'),
    () => getDemoContractProfile(),
  )
}

export function mintPlan(planId, payload) {
  return requestJson(`/api/v1/chain/plans/${planId}/mint`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
