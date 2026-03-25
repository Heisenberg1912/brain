const API = '';

export async function fetchLocations() {
  const res = await fetch(`${API}/api/v1/data/locations`);
  if (!res.ok) throw new Error('Failed to fetch locations');
  return res.json();
}

export async function fetchLocationDetail(id) {
  const res = await fetch(`${API}/api/v1/data/locations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch location detail');
  return res.json();
}

export async function fetchRankings(sortBy = 'land_value_score', top = 20) {
  const res = await fetch(`${API}/api/v1/valuation/rankings?top=${top}&sort_by=${sortBy}`);
  if (!res.ok) throw new Error('Failed to fetch rankings');
  return res.json();
}

export async function fetchScore(locationId) {
  const res = await fetch(`${API}/api/v1/valuation/score/${locationId}`);
  if (!res.ok) throw new Error('Failed to fetch score');
  return res.json();
}

export async function fetchCompare(locationIds) {
  const res = await fetch(`${API}/api/v1/valuation/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ location_ids: locationIds }),
  });
  if (!res.ok) throw new Error('Comparison failed');
  return res.json();
}

export async function fetchInfrastructure() {
  const res = await fetch(`${API}/api/v1/data/infrastructure`);
  if (!res.ok) throw new Error('Failed to fetch infrastructure');
  return res.json();
}

export async function fetchNearbyInfra(locationId, radiusKm = 5) {
  const res = await fetch(`${API}/api/v1/data/locations/${locationId}/nearby-infra?radius_km=${radiusKm}`);
  if (!res.ok) throw new Error('Failed to fetch nearby infrastructure');
  return res.json();
}

export async function askAI(question, { locationId = null, compareIds = [] } = {}) {
  const res = await fetch(`${API}/api/v1/ai/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      location_id: locationId,
      compare_ids: compareIds,
    }),
  });
  if (!res.ok) throw new Error('AI query failed');
  return res.json();
}

export async function analyzeAI(locationId) {
  const res = await fetch(`${API}/api/v1/ai/analyze/${locationId}`);
  if (!res.ok) throw new Error('AI analysis failed');
  return res.json();
}

export async function fetchAIMarketBrief() {
  const res = await fetch(`${API}/api/v1/ai/market-brief`);
  if (!res.ok) throw new Error('AI market brief failed');
  return res.json();
}

export async function fetchAICompare(locationIds) {
  const res = await fetch(`${API}/api/v1/ai/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ location_ids: locationIds }),
  });
  if (!res.ok) throw new Error('AI compare failed');
  return res.json();
}
