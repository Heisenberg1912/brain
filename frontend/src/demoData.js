const PRICE_HISTORY_DATES = ['2022-01-01', '2023-01-01', '2024-01-01', '2025-01-01', '2026-01-01']

const MARKETS = [
  {
    id: 101,
    name: 'Gurugram Cyber City',
    country_code: 'IN',
    state: 'Haryana',
    city: 'Gurugram',
    locality: 'DLF Cyber City',
    ward: 'DLF Phase 2',
    lat: 28.4945,
    lng: 77.0894,
    zoning_type: 'commercial',
    avg_price_per_sqft: 18500,
    scores: {
      land_value_score: 93,
      development_potential_score: 88,
      future_appreciation_index: 84,
      infra_score: 91,
      price_trend_score: 86,
      zoning_favorability: 92,
      road_access_score: 95,
      metro_access_score: 92,
      economic_access_score: 96,
      strategic_infra_score: 90,
      density_score: 82,
      population_growth_score: 78,
      demand_pressure_score: 88,
      zoning_shift_score: 74,
      annualized_growth_pct: 9.2,
      recent_12m_growth_pct: 7.1,
      climate_exposure_score: 34,
      climate_resilience_score: 66,
      terrain_constraint_score: 12,
      terrain_readiness_score: 88,
      site_risk_score: 24,
      data_confidence_score: 89,
      data_confidence_band: 'high',
      score_calibration_factor: 1.02,
    },
    outlook: {
      predicted_price_1yr: 19950,
      predicted_price_3yr: 22850,
      annual_growth_pct: 7.3,
      confidence: 'high',
      predicted_upside_pct: 7.8,
      signal: 'positive',
    },
    census: {
      year: 2025,
      population: 162000,
      density_per_sqkm: 12400,
      growth_rate_pct: 6.4,
      households: 42000,
    },
    geo: {
      terrain_class: 'flat_urban',
      terrain_slope_pct: 1.8,
      flood_risk_score: 14.2,
      heat_risk_score: 33.8,
      climate_risk_score: 29.4,
    },
    masterplan: {
      zoning_type: 'commercial',
      fsi: 5.2,
      ground_coverage_pct: 42,
      max_height_m: 145,
      setback_front_m: 9,
      setback_side_m: 6,
      version: 'GGM-2026.1',
    },
    planning: {
      id: 401,
      version_tag: 'GGM-2026.1',
      admin_area: 'Gurugram Metropolitan Region',
      market_tier: 'Tier 1',
      validation_status: 'validated',
      floor_plan_constraints: { minimum_frontage_m: 18, podium_parking_required: true },
      zoning_validation_rules: { tod_radius_m: 500, active_frontage_required: true },
      location_intelligence_score: 92,
      massing_inputs: { ideal_floorplate_sqft: 28000 },
      source_summary: 'Transit-oriented commercial zoning with premium leasing comparables.',
    },
    regional_standards: [
      'Rapid Metro TOD guidance',
      'Gurugram fire access standards',
      'Commercial parking and podium norms',
    ],
    price_history: [15400, 16650, 17450, 18100, 18500],
    copy: {
      summary: 'Gurugram remains the cleanest premium office-led land story in the demo set because mobility, pricing depth, and commercial zoning alignment are already in place.',
      keyInsight: 'Acquire selectively near metro-linked office inventory where pricing still trails completed core towers.',
      thesis: 'The corridor combines transit, leasing depth, and institutional occupier demand, creating a premium but still actionable entry point for commercial infill.',
      primary_recommendation: 'Bias acquisition toward metro-adjacent parcels that can support office, hospitality, and premium service retail.',
      recommended_use_case: 'commercial',
      favorability_band: 'prime',
      market_tier: 'Tier 1',
      price_trend_direction: 'up',
      price_momentum_band: 'high',
      demand_profile: 'office_led',
      site_risk_band: 'low',
      zoning_shift_direction: 'stable',
      investment_signal: 'acquire',
      execution_strategy: 'build_now',
      conviction: 'high',
      primary_driver: 'transit anchored office demand',
      verdict: 'Acquire signal with strong conviction as transport access and occupier demand are already proven at scale.',
      strengths: [
        'Rapid Metro adjacency supports premium office and hospitality absorption.',
        'Commercial zoning clarity reduces entitlement friction for vertical development.',
        'Tenant depth keeps leasing benchmarks transparent for institutional underwriting.',
      ],
      risks: [
        'Entry pricing is already premium, leaving less room for execution mistakes.',
        'Office supply additions can temporarily soften rental velocity in specific pockets.',
      ],
      opportunities: [
        'Capture premium mixed retail and food hall frontage under office towers.',
        'Layer branded residences or serviced apartments on adjacent hospitality parcels.',
        'Use asset tokenization for fractional access to stabilized commercial inventory.',
      ],
      opportunity_title: 'Premium office infill',
      opportunity_reason: 'Pricing power and occupier depth make metro-linked commercial parcels the clearest near-term underwriting story.',
      recommendations: [
        { label: 'Prioritize transit plots', action: 'Screen parcels within a five minute walk of Rapid Metro nodes.', priority: 'high' },
        { label: 'Protect yield', action: 'Underwrite rent sensitivity against new Grade A office completions.', priority: 'medium' },
        { label: 'Add hospitality edge', action: 'Mix in serviced stay or premium F&B activation where frontage allows.', priority: 'medium' },
      ],
    },
  },
  {
    id: 103,
    name: 'Whitefield Central',
    country_code: 'IN',
    state: 'Karnataka',
    city: 'Bengaluru',
    locality: 'Whitefield',
    ward: 'Hope Farm',
    lat: 12.9698,
    lng: 77.7499,
    zoning_type: 'mixed_use',
    avg_price_per_sqft: 12850,
    scores: {
      land_value_score: 86,
      development_potential_score: 82,
      future_appreciation_index: 87,
      infra_score: 84,
      price_trend_score: 82,
      zoning_favorability: 87,
      road_access_score: 85,
      metro_access_score: 88,
      economic_access_score: 85,
      strategic_infra_score: 83,
      density_score: 80,
      population_growth_score: 79,
      demand_pressure_score: 84,
      zoning_shift_score: 76,
      annualized_growth_pct: 7.9,
      recent_12m_growth_pct: 6.1,
      climate_exposure_score: 32,
      climate_resilience_score: 64,
      terrain_constraint_score: 14,
      terrain_readiness_score: 85,
      site_risk_score: 28,
      data_confidence_score: 84,
      data_confidence_band: 'medium',
      score_calibration_factor: 1,
    },
    outlook: {
      predicted_price_1yr: 13750,
      predicted_price_3yr: 15850,
      annual_growth_pct: 6.7,
      confidence: 'high',
      predicted_upside_pct: 7,
      signal: 'positive',
    },
    census: {
      year: 2025,
      population: 188000,
      density_per_sqkm: 13600,
      growth_rate_pct: 6.7,
      households: 47000,
    },
    geo: {
      terrain_class: 'urban_plateau',
      terrain_slope_pct: 2.1,
      flood_risk_score: 24.5,
      heat_risk_score: 28.4,
      climate_risk_score: 31.1,
    },
    masterplan: {
      zoning_type: 'mixed_use',
      fsi: 4.2,
      ground_coverage_pct: 44,
      max_height_m: 110,
      setback_front_m: 7,
      setback_side_m: 5,
      version: 'BLR-WF-2026.1',
    },
    planning: {
      id: 403,
      version_tag: 'BLR-WF-2026.1',
      admin_area: 'Bengaluru East',
      market_tier: 'Tier 1',
      validation_status: 'validated',
      floor_plan_constraints: { podium_parking_required: true, frontage_activation_preferred: true },
      zoning_validation_rules: { metro_influence_zone: true, mixed_use_stack_allowed: true },
      location_intelligence_score: 85,
      massing_inputs: { preferred_tower_depth_m: 20 },
      source_summary: 'Balanced tech corridor with better mobility visibility and lower site risk than Bellandur.',
    },
    regional_standards: [
      'Whitefield station influence norms',
      'Mixed-use frontage activation standards',
      'High-rise life safety requirements',
    ],
    price_history: [10850, 11500, 12050, 12550, 12850],
    copy: {
      summary: 'Whitefield offers a steadier Bengaluru growth story with improving transit, lower site risk, and enough pricing momentum to stay attractive for institutional mixed-use product.',
      keyInsight: 'This is the cleaner execution corridor if the goal is balanced upside without Bellandur-level hydrology risk.',
      thesis: 'Whitefield is not the flashiest story, but it combines mobility visibility, tech-driven demand, and relatively manageable development complexity.',
      primary_recommendation: 'Use Whitefield for balanced mixed-use or rental-led product where execution certainty matters as much as upside.',
      recommended_use_case: 'mixed_use',
      favorability_band: 'strong',
      market_tier: 'Tier 1',
      price_trend_direction: 'up',
      price_momentum_band: 'constructive',
      demand_profile: 'steady_tech',
      site_risk_band: 'low',
      zoning_shift_direction: 'stable',
      investment_signal: 'accumulate',
      execution_strategy: 'build_now',
      conviction: 'medium',
      primary_driver: 'improving metro connectivity and family-oriented demand depth',
      verdict: 'Accumulate signal with strong execution visibility for balanced mixed-use and rental product.',
      strengths: [
        'Transit upgrades broaden the catchment without fully pricing out new entrants.',
        'Risk posture is cleaner than more hydrology-sensitive Bengaluru submarkets.',
        'Demand supports residential, retail, and office-lite formats rather than a single product bet.',
      ],
      risks: [
        'The market can feel slower than higher-beta corridors during early leasing phases.',
        'Supply competition remains meaningful in periods of rapid apartment launches.',
      ],
      opportunities: [
        'Package rental housing with neighborhood retail and education-led amenities.',
        'Target family-oriented mixed-use projects near metro access nodes.',
        'Use phased development to protect absorption and preserve pricing discipline.',
      ],
      opportunity_title: 'Balanced mixed-use expansion',
      opportunity_reason: 'Whitefield brings together cleaner risk, improving transit, and broad end-user demand.',
      recommendations: [
        { label: 'Favor phased product', action: 'Stage delivery to match neighborhood absorption instead of overbuilding early.', priority: 'high' },
        { label: 'Lean into family demand', action: 'Program schools, retail, and mobility access into the first phase narrative.', priority: 'medium' },
        { label: 'Use metro proximity', action: 'Price the first wave before the corridor fully captures transit rerating.', priority: 'medium' },
      ],
    },
  },
  {
    id: 104,
    name: 'GIFT City Core',
    country_code: 'IN',
    state: 'Gujarat',
    city: 'Gandhinagar',
    locality: 'GIFT City',
    ward: 'Financial District',
    lat: 23.1642,
    lng: 72.6832,
    zoning_type: 'commercial',
    avg_price_per_sqft: 11150,
    scores: {
      land_value_score: 90,
      development_potential_score: 85,
      future_appreciation_index: 88,
      infra_score: 88,
      price_trend_score: 79,
      zoning_favorability: 94,
      road_access_score: 86,
      metro_access_score: 74,
      economic_access_score: 95,
      strategic_infra_score: 92,
      density_score: 70,
      population_growth_score: 83,
      demand_pressure_score: 81,
      zoning_shift_score: 82,
      annualized_growth_pct: 8.6,
      recent_12m_growth_pct: 6.4,
      climate_exposure_score: 28,
      climate_resilience_score: 72,
      terrain_constraint_score: 9,
      terrain_readiness_score: 91,
      site_risk_score: 18,
      data_confidence_score: 83,
      data_confidence_band: 'medium',
      score_calibration_factor: 0.99,
    },
    outlook: {
      predicted_price_1yr: 12150,
      predicted_price_3yr: 14650,
      annual_growth_pct: 9.5,
      confidence: 'medium',
      predicted_upside_pct: 9,
      signal: 'bullish',
    },
    census: {
      year: 2025,
      population: 62000,
      density_per_sqkm: 7800,
      growth_rate_pct: 8.9,
      households: 18000,
    },
    geo: {
      terrain_class: 'planned_plateau',
      terrain_slope_pct: 1.4,
      flood_risk_score: 10.8,
      heat_risk_score: 32.4,
      climate_risk_score: 27.2,
    },
    masterplan: {
      zoning_type: 'commercial',
      fsi: 5.5,
      ground_coverage_pct: 40,
      max_height_m: 160,
      setback_front_m: 10,
      setback_side_m: 6,
      version: 'GIFT-2026.1',
    },
    planning: {
      id: 404,
      version_tag: 'GIFT-2026.1',
      admin_area: 'Gandhinagar Special Zone',
      market_tier: 'Tier 1',
      validation_status: 'validated',
      floor_plan_constraints: { district_cooling_interface: true, tower_spacing_m: 18 },
      zoning_validation_rules: { finance_core_overlay: true, high_security_frontage: true },
      location_intelligence_score: 90,
      massing_inputs: { preferred_office_floorplate_sqft: 32000 },
      source_summary: 'Policy-backed finance district with strong institutional positioning and rerating potential.',
    },
    regional_standards: [
      'IFSC district design controls',
      'Structured parking and service access code',
      'Commercial tower resilience and cooling standards',
    ],
    price_history: [9050, 9725, 10100, 10700, 11150],
    copy: {
      summary: 'GIFT City offers one of the clearest medium-term rerating stories: policy support, modern infrastructure, and commercial use clarity with room to grow from a lower starting price base.',
      keyInsight: 'State-backed infrastructure and regulatory clarity create a cleaner rerating story than most emerging finance districts.',
      thesis: 'The market has institutional-grade ingredients already in place, while current pricing still leaves room for long-duration upside.',
      primary_recommendation: 'Acquire strategic commercial sites or land-bank select frontage before the district fully matures into a premium national benchmark.',
      recommended_use_case: 'commercial',
      favorability_band: 'prime',
      market_tier: 'Tier 1',
      price_trend_direction: 'up',
      price_momentum_band: 'constructive',
      demand_profile: 'policy_led',
      site_risk_band: 'low',
      zoning_shift_direction: 'up',
      investment_signal: 'acquire',
      execution_strategy: 'land_bank',
      conviction: 'high',
      primary_driver: 'policy backed demand concentration',
      verdict: 'Acquire signal with a land-bank bias as policy and infrastructure tailwinds still have room to flow into land pricing.',
      strengths: [
        'Institutional positioning and regulatory clarity support long-duration underwriting.',
        'Infrastructure is modern and purpose-built for premium commercial product.',
        'Current price base is lower than more mature premium office corridors.',
      ],
      risks: [
        'Absorption still depends on continued policy execution and tenant migration.',
        'Residential and lifestyle depth lags more mature mixed-use districts.',
      ],
      opportunities: [
        'Secure frontage for future office, hospitality, and service ecosystems.',
        'Develop finance-led mixed-use campuses as the district matures.',
        'Tokenize stabilized property to broaden access once the market rerates.',
      ],
      opportunity_title: 'Policy-backed rerating',
      opportunity_reason: 'The combination of regulatory clarity and lower starting prices gives GIFT a compelling medium-term upside setup.',
      recommendations: [
        { label: 'Control the timing', action: 'Favor parcels that can sit patiently through district maturation.', priority: 'high' },
        { label: 'Stay institution-led', action: 'Align product with finance, hospitality, and enterprise services rather than broad mass-market uses.', priority: 'medium' },
        { label: 'Underwrite district build-out', action: 'Treat public realm and tenant migration milestones as primary value drivers.', priority: 'medium' },
      ],
    },
  },
  {
    id: 102,
    name: 'Bellandur',
    country_code: 'IN',
    state: 'Karnataka',
    city: 'Bengaluru',
    locality: 'Outer Ring Road',
    ward: 'Bellandur',
    lat: 12.9279,
    lng: 77.6762,
    zoning_type: 'mixed_use',
    avg_price_per_sqft: 14200,
    scores: {
      land_value_score: 89,
      development_potential_score: 84,
      future_appreciation_index: 90,
      infra_score: 87,
      price_trend_score: 84,
      zoning_favorability: 90,
      road_access_score: 88,
      metro_access_score: 82,
      economic_access_score: 94,
      strategic_infra_score: 86,
      density_score: 89,
      population_growth_score: 84,
      demand_pressure_score: 90,
      zoning_shift_score: 81,
      annualized_growth_pct: 8.8,
      recent_12m_growth_pct: 7.2,
      climate_exposure_score: 46,
      climate_resilience_score: 58,
      terrain_constraint_score: 18,
      terrain_readiness_score: 82,
      site_risk_score: 41,
      data_confidence_score: 85,
      data_confidence_band: 'high',
      score_calibration_factor: 1.01,
    },
    outlook: {
      predicted_price_1yr: 15350,
      predicted_price_3yr: 17600,
      annual_growth_pct: 7.4,
      confidence: 'medium',
      predicted_upside_pct: 8.1,
      signal: 'positive',
    },
    census: {
      year: 2025,
      population: 214000,
      density_per_sqkm: 15800,
      growth_rate_pct: 7.1,
      households: 56000,
    },
    geo: {
      terrain_class: 'lake_influenced_urban',
      terrain_slope_pct: 2.4,
      flood_risk_score: 38,
      heat_risk_score: 29.1,
      climate_risk_score: 36.2,
    },
    masterplan: {
      zoning_type: 'mixed_use',
      fsi: 4.5,
      ground_coverage_pct: 46,
      max_height_m: 120,
      setback_front_m: 7,
      setback_side_m: 5,
      version: 'BLR-ORR-2026.2',
    },
    planning: {
      id: 402,
      version_tag: 'BLR-ORR-2026.2',
      admin_area: 'Bengaluru East',
      market_tier: 'Tier 1',
      validation_status: 'validated',
      floor_plan_constraints: { lake_buffer_m: 75, service_lane_required: true },
      zoning_validation_rules: { active_mixed_use_frontage: true, drainage_clearance_required: true },
      location_intelligence_score: 88,
      massing_inputs: { preferred_basement_levels: 2 },
      source_summary: 'Mixed-use corridor with strong demand but meaningful hydrology and traffic constraints.',
    },
    regional_standards: [
      'ORR mixed-use frontage guidance',
      'Stormwater buffer compliance',
      'Bengaluru high-density parking standards',
    ],
    price_history: [11800, 12550, 13100, 13800, 14200],
    copy: {
      summary: 'Bellandur is the highest-beta Bengaluru story in the demo set: strong employment gravity, mixed-use flexibility, and high rental demand, offset by hydrology management risk.',
      keyInsight: 'The upside remains strong if drainage and mobility upgrades continue to de-risk the corridor.',
      thesis: 'Bellandur can outperform on pricing over the medium term because job density is exceptional, but execution quality matters more here than in cleaner corridors.',
      primary_recommendation: 'Accumulate selectively where flood mitigation, access planning, and tenant catchment are already demonstrable.',
      recommended_use_case: 'mixed_use',
      favorability_band: 'strong',
      market_tier: 'Tier 1',
      price_trend_direction: 'up',
      price_momentum_band: 'high',
      demand_profile: 'tech_and_rental',
      site_risk_band: 'moderate',
      zoning_shift_direction: 'constructive',
      investment_signal: 'accumulate',
      execution_strategy: 'entitle_then_build',
      conviction: 'medium',
      primary_driver: 'employment spillover from outer ring road campuses',
      verdict: 'Accumulate signal with a measured stance: upside is strong, but drainage and access conditions must be actively de-risked.',
      strengths: [
        'Employment density keeps rental absorption and service demand resilient.',
        'Mixed-use zoning supports residential, retail, and office blended product.',
        'Pricing still has room to move if metro connectivity improves realized travel times.',
      ],
      risks: [
        'Lake and drainage constraints can impair approvals and design efficiency.',
        'Traffic friction reduces user experience unless access is carefully planned.',
      ],
      opportunities: [
        'Build premium rental communities tied to major tech campuses.',
        'Pair office or flex workspace with convenience retail and managed living.',
        'Use mobility-linked branding to capture future metro upside before full rerating.',
      ],
      opportunity_title: 'High-beta mixed-use demand',
      opportunity_reason: 'The corridor offers one of the strongest combinations of job density, rental need, and medium-term appreciation potential.',
      recommendations: [
        { label: 'Underwrite drainage', action: 'Favor sites with completed stormwater and lake-buffer compliance.', priority: 'high' },
        { label: 'Design for access', action: 'Treat entry and service planning as a first-order development variable.', priority: 'high' },
        { label: 'Monetize rental demand', action: 'Shape product around premium rental and live-work formats.', priority: 'medium' },
      ],
    },
  },
  {
    id: 105,
    name: 'Hinjawadi Phase 1',
    country_code: 'IN',
    state: 'Maharashtra',
    city: 'Pune',
    locality: 'Hinjawadi',
    ward: 'Phase 1',
    lat: 18.5916,
    lng: 73.7389,
    zoning_type: 'mixed_use',
    avg_price_per_sqft: 9800,
    scores: {
      land_value_score: 83,
      development_potential_score: 81,
      future_appreciation_index: 85,
      infra_score: 79,
      price_trend_score: 81,
      zoning_favorability: 84,
      road_access_score: 82,
      metro_access_score: 71,
      economic_access_score: 86,
      strategic_infra_score: 80,
      density_score: 74,
      population_growth_score: 80,
      demand_pressure_score: 82,
      zoning_shift_score: 73,
      annualized_growth_pct: 7.6,
      recent_12m_growth_pct: 5.8,
      climate_exposure_score: 25,
      climate_resilience_score: 69,
      terrain_constraint_score: 16,
      terrain_readiness_score: 84,
      site_risk_score: 27,
      data_confidence_score: 80,
      data_confidence_band: 'medium',
      score_calibration_factor: 1,
    },
    outlook: {
      predicted_price_1yr: 10550,
      predicted_price_3yr: 12150,
      annual_growth_pct: 7.4,
      confidence: 'medium',
      predicted_upside_pct: 7.7,
      signal: 'positive',
    },
    census: {
      year: 2025,
      population: 141000,
      density_per_sqkm: 9700,
      growth_rate_pct: 7.8,
      households: 36000,
    },
    geo: {
      terrain_class: 'urban_plateau',
      terrain_slope_pct: 2.6,
      flood_risk_score: 18.4,
      heat_risk_score: 27.1,
      climate_risk_score: 26.8,
    },
    masterplan: {
      zoning_type: 'mixed_use',
      fsi: 3.8,
      ground_coverage_pct: 48,
      max_height_m: 92,
      setback_front_m: 6,
      setback_side_m: 4,
      version: 'PUN-HJ-2026.1',
    },
    planning: {
      id: 405,
      version_tag: 'PUN-HJ-2026.1',
      admin_area: 'Pune West',
      market_tier: 'Tier 1',
      validation_status: 'validated',
      floor_plan_constraints: { shuttle_access_required: true, campus_edge_activation: true },
      zoning_validation_rules: { tech_park_interface: true, phased_amenity_rollout: true },
      location_intelligence_score: 82,
      massing_inputs: { preferred_block_depth_m: 24 },
      source_summary: 'Affordable tech corridor with good demand depth and room for professionally managed residential formats.',
    },
    regional_standards: [
      'IT park interface guidelines',
      'Campus edge mobility norms',
      'Mid-rise mixed-use life safety code',
    ],
    price_history: [7950, 8550, 9025, 9500, 9800],
    copy: {
      summary: 'Hinjawadi is a mid-priced tech corridor with strong affordability relative to job growth and room for institutional rental product.',
      keyInsight: 'The story is less about premium pricing today and more about disciplined growth with strong occupier catchment.',
      thesis: 'This corridor works when investors want steady tech-led demand and manageable entry pricing instead of headline-grabbing premium valuations.',
      primary_recommendation: 'Accumulate sites that can support rental housing, neighborhood retail, and flexible live-work product for the tech workforce.',
      recommended_use_case: 'mixed_use',
      favorability_band: 'constructive',
      market_tier: 'Tier 1',
      price_trend_direction: 'up',
      price_momentum_band: 'constructive',
      demand_profile: 'workforce_tech',
      site_risk_band: 'low',
      zoning_shift_direction: 'stable',
      investment_signal: 'accumulate',
      execution_strategy: 'build_now',
      conviction: 'medium',
      primary_driver: 'affordable access to concentrated tech employment',
      verdict: 'Accumulate signal for investors seeking efficient entry pricing and dependable tech-driven demand.',
      strengths: [
        'Pricing remains accessible relative to the strength of nearby tech employment.',
        'The submarket supports professional rental housing and convenience retail.',
        'Risk profile is cleaner than more flood-sensitive high-beta corridors.',
      ],
      risks: [
        'Mass transit depth still trails more mature premium corridors.',
        'User experience depends heavily on project-level amenity and mobility design.',
      ],
      opportunities: [
        'Scale rental housing targeted at the tech workforce and young families.',
        'Build neighborhood mixed-use nodes that serve large campus populations.',
        'Capture appreciation as mobility improvements broaden the catchment.',
      ],
      opportunity_title: 'Affordable tech growth',
      opportunity_reason: 'Hinjawadi combines a healthy job engine with entry pricing that still leaves room for disciplined upside.',
      recommendations: [
        { label: 'Own the rent thesis', action: 'Design product around managed rental, community amenities, and convenience retail.', priority: 'high' },
        { label: 'Keep execution lean', action: 'Favor efficient mid-rise or campus-edge formats over trophy product.', priority: 'medium' },
        { label: 'Track mobility gains', action: 'Treat new transit and road upgrades as catalysts for phase timing.', priority: 'medium' },
      ],
    },
  },
  {
    id: 106,
    name: 'Shamshabad Aero District',
    country_code: 'IN',
    state: 'Telangana',
    city: 'Hyderabad',
    locality: 'Shamshabad',
    ward: 'Airport Zone',
    lat: 17.2403,
    lng: 78.4294,
    zoning_type: 'commercial',
    avg_price_per_sqft: 8900,
    scores: {
      land_value_score: 81,
      development_potential_score: 83,
      future_appreciation_index: 86,
      infra_score: 80,
      price_trend_score: 77,
      zoning_favorability: 85,
      road_access_score: 90,
      metro_access_score: 58,
      economic_access_score: 88,
      strategic_infra_score: 84,
      density_score: 68,
      population_growth_score: 82,
      demand_pressure_score: 79,
      zoning_shift_score: 80,
      annualized_growth_pct: 8,
      recent_12m_growth_pct: 5.6,
      climate_exposure_score: 29,
      climate_resilience_score: 68,
      terrain_constraint_score: 11,
      terrain_readiness_score: 86,
      site_risk_score: 22,
      data_confidence_score: 79,
      data_confidence_band: 'medium',
      score_calibration_factor: 0.98,
    },
    outlook: {
      predicted_price_1yr: 9620,
      predicted_price_3yr: 11350,
      annual_growth_pct: 8.4,
      confidence: 'medium',
      predicted_upside_pct: 8.1,
      signal: 'positive',
    },
    census: {
      year: 2025,
      population: 97000,
      density_per_sqkm: 6900,
      growth_rate_pct: 8.1,
      households: 25000,
    },
    geo: {
      terrain_class: 'airport_plateau',
      terrain_slope_pct: 1.9,
      flood_risk_score: 13.8,
      heat_risk_score: 30.5,
      climate_risk_score: 28.6,
    },
    masterplan: {
      zoning_type: 'commercial',
      fsi: 3.9,
      ground_coverage_pct: 43,
      max_height_m: 100,
      setback_front_m: 8,
      setback_side_m: 5,
      version: 'HYD-AERO-2026.1',
    },
    planning: {
      id: 406,
      version_tag: 'HYD-AERO-2026.1',
      admin_area: 'Hyderabad South',
      market_tier: 'Tier 1',
      validation_status: 'validated',
      floor_plan_constraints: { logistics_access_lane: true, airport_approach_clearance: true },
      zoning_validation_rules: { aviation_influence_zone: true, warehousing_buffer_controls: true },
      location_intelligence_score: 81,
      massing_inputs: { preferred_logistics_clear_height_m: 12 },
      source_summary: 'Airport-led commercial and logistics district with strong accessibility and growing service demand.',
    },
    regional_standards: [
      'Airport influence zone height controls',
      'Logistics interface movement standards',
      'Large-format service commercial guidelines',
    ],
    price_history: [7100, 7600, 8050, 8525, 8900],
    copy: {
      summary: 'Shamshabad is an airport-led growth story with good access, improving commercial depth, and room for rerating from a relatively early price base.',
      keyInsight: 'The best use cases are airport-linked commercial, hospitality, and logistics-support formats rather than generic residential expansion.',
      thesis: 'This corridor benefits from strategic access and expanding airport gravity, making it a compelling selective bet for service and logistics-related development.',
      primary_recommendation: 'Focus on airport-linked service commercial, logistics-support product, and hospitality-led frontage.',
      recommended_use_case: 'commercial',
      favorability_band: 'constructive',
      market_tier: 'Tier 1',
      price_trend_direction: 'up',
      price_momentum_band: 'constructive',
      demand_profile: 'airport_and_logistics',
      site_risk_band: 'low',
      zoning_shift_direction: 'up',
      investment_signal: 'accumulate',
      execution_strategy: 'land_bank',
      conviction: 'medium',
      primary_driver: 'airport adjacency and corridor accessibility',
      verdict: 'Accumulate signal with a land-bank bias as airport-linked demand broadens beyond logistics into services and hospitality.',
      strengths: [
        'Airport adjacency gives the district a clear strategic identity.',
        'Access quality is already ahead of many emerging peripheral corridors.',
        'Entry pricing remains below more mature premium commercial nodes.',
      ],
      risks: [
        'Depth of day-to-day urban life is still developing.',
        'The thesis works best for targeted commercial formats, not every product type.',
      ],
      opportunities: [
        'Build hospitality, airport business services, and logistics-adjacent commercial stock.',
        'Acquire large parcels before the district captures full accessibility rerating.',
        'Use phased development as the airport ecosystem deepens.',
      ],
      opportunity_title: 'Airport-linked commercial optionality',
      opportunity_reason: 'Strategic access and a still-early price base create strong optionality for targeted commercial product.',
      recommendations: [
        { label: 'Stay airport-specific', action: 'Underwrite for hospitality, business services, and logistics-support demand first.', priority: 'high' },
        { label: 'Preserve optionality', action: 'Favor larger sites that can phase into multiple airport-linked uses over time.', priority: 'medium' },
        { label: 'Watch ecosystem depth', action: 'Track non-airport tenant mix to gauge when the district broadens materially.', priority: 'medium' },
      ],
    },
  },
]
const INFRASTRUCTURE = [
  { id: 1001, name: 'Rapid Metro Cyber City', infra_type: 'metro_station', country_code: 'IN', state: 'Haryana', city: 'Gurugram', status: 'operational', lat: 28.4959, lng: 77.0912, tags: ['transit'] },
  { id: 1002, name: 'NH48 Commercial Spine', infra_type: 'highway', country_code: 'IN', state: 'Haryana', city: 'Gurugram', status: 'operational', lat: 28.4888, lng: 77.0825, tags: ['regional_access'] },
  { id: 1003, name: 'Udyog Vihar Enterprise Zone', infra_type: 'economic_zone', country_code: 'IN', state: 'Haryana', city: 'Gurugram', status: 'operational', lat: 28.4971, lng: 77.0784, tags: ['employment'] },
  { id: 1004, name: 'IGI Airport Terminal 3', infra_type: 'airport', country_code: 'IN', state: 'Delhi', city: 'New Delhi', status: 'operational', lat: 28.5562, lng: 77.1, tags: ['air_access'] },
  { id: 1005, name: 'DLF Cyber Greens School', infra_type: 'school', country_code: 'IN', state: 'Haryana', city: 'Gurugram', status: 'operational', lat: 28.5012, lng: 77.0891, tags: ['education'] },
  { id: 1006, name: 'Bellandur Mobility Hub', infra_type: 'metro_station', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'expanding', lat: 12.9267, lng: 77.6707, tags: ['transit'] },
  { id: 1007, name: 'Outer Ring Road Corridor', infra_type: 'highway', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9285, lng: 77.6733, tags: ['road'] },
  { id: 1008, name: 'Sakra World Hospital', infra_type: 'hospital', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9298, lng: 77.6899, tags: ['healthcare'] },
  { id: 1009, name: 'Bellandur International School', infra_type: 'school', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9235, lng: 77.6794, tags: ['education'] },
  { id: 1010, name: 'Kadugodi Metro Station', infra_type: 'metro_station', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9952, lng: 77.7605, tags: ['transit'] },
  { id: 1011, name: 'Whitefield Rail Terminal', infra_type: 'rail', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9965, lng: 77.7614, tags: ['regional_rail'] },
  { id: 1012, name: 'ITPL Economic District', infra_type: 'economic_zone', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9856, lng: 77.7362, tags: ['employment'] },
  { id: 1013, name: 'Narayana Multispeciality Whitefield', infra_type: 'hospital', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.969, lng: 77.7425, tags: ['healthcare'] },
  { id: 1014, name: 'Whitefield Academy', infra_type: 'school', country_code: 'IN', state: 'Karnataka', city: 'Bengaluru', status: 'operational', lat: 12.9725, lng: 77.7461, tags: ['education'] },
  { id: 1015, name: 'GIFT SEZ Core', infra_type: 'economic_zone', country_code: 'IN', state: 'Gujarat', city: 'Gandhinagar', status: 'operational', lat: 23.1647, lng: 72.6849, tags: ['finance'] },
  { id: 1016, name: 'Gandhinagar-Ahmedabad Connector', infra_type: 'highway', country_code: 'IN', state: 'Gujarat', city: 'Gandhinagar', status: 'operational', lat: 23.171, lng: 72.6813, tags: ['road'] },
  { id: 1017, name: 'Ahmedabad International Airport', infra_type: 'airport', country_code: 'IN', state: 'Gujarat', city: 'Ahmedabad', status: 'operational', lat: 23.074, lng: 72.6347, tags: ['air_access'] },
  { id: 1018, name: 'Rajiv Gandhi Infotech Park', infra_type: 'economic_zone', country_code: 'IN', state: 'Maharashtra', city: 'Pune', status: 'operational', lat: 18.5866, lng: 73.7375, tags: ['employment'] },
  { id: 1019, name: 'Hinjawadi Metro Station', infra_type: 'metro_station', country_code: 'IN', state: 'Maharashtra', city: 'Pune', status: 'expanding', lat: 18.5898, lng: 73.732, tags: ['transit'] },
  { id: 1020, name: 'Ruby Hall Clinic Hinjawadi', infra_type: 'hospital', country_code: 'IN', state: 'Maharashtra', city: 'Pune', status: 'operational', lat: 18.5944, lng: 73.7367, tags: ['healthcare'] },
  { id: 1021, name: 'Rajiv Gandhi International Airport', infra_type: 'airport', country_code: 'IN', state: 'Telangana', city: 'Hyderabad', status: 'operational', lat: 17.2403, lng: 78.4294, tags: ['air_access'] },
  { id: 1022, name: 'Aero Business Logistics Park', infra_type: 'economic_zone', country_code: 'IN', state: 'Telangana', city: 'Hyderabad', status: 'operational', lat: 17.2342, lng: 78.4385, tags: ['logistics'] },
  { id: 1023, name: 'ORR Airport Exit Corridor', infra_type: 'highway', country_code: 'IN', state: 'Telangana', city: 'Hyderabad', status: 'operational', lat: 17.2382, lng: 78.4172, tags: ['road'] },
  { id: 1024, name: 'Airport District Medical Center', infra_type: 'hospital', country_code: 'IN', state: 'Telangana', city: 'Hyderabad', status: 'operational', lat: 17.2481, lng: 78.4378, tags: ['healthcare'] },
]

const HOTSPOT_CLUSTERS = [
  {
    cluster_id: 1,
    label: 'premium_core',
    location_ids: [101, 102],
    summary: 'Premium corridors where demand already exists and pricing depth remains durable.',
    dominant_signal: 'pricing_power',
  },
  {
    cluster_id: 2,
    label: 'policy_upside',
    location_ids: [104, 106],
    summary: 'Districts benefitting from strategic infrastructure and policy-backed positioning.',
    dominant_signal: 'institutional_tailwind',
  },
  {
    cluster_id: 3,
    label: 'stable_growth',
    location_ids: [103, 105],
    summary: 'Balanced tech corridors with cleaner risk posture and dependable demand.',
    dominant_signal: 'execution_visibility',
  },
  {
    cluster_id: 4,
    label: 'mixed_use_momentum',
    location_ids: [102, 103, 105],
    summary: 'Mixed-use submarkets with strong rental demand and neighborhood-scale upside.',
    dominant_signal: 'rental_demand',
  },
]

const SUPPORTED_NETWORKS = [
  {
    key: 'polygon',
    label: 'Polygon',
    is_default: true,
    supports_fractional: true,
    supports_plan_nfts: true,
    positioning: 'Low-fee default chain for investor-facing plan assets and property fractions.',
  },
  {
    key: 'base',
    label: 'Base',
    is_default: false,
    supports_fractional: true,
    supports_plan_nfts: true,
    positioning: 'Alternative distribution rail for consumer-friendly fractional products.',
  },
  {
    key: 'ethereum',
    label: 'Ethereum',
    is_default: false,
    supports_fractional: false,
    supports_plan_nfts: true,
    positioning: 'Settlement-grade option for premium registry provenance and institutional signaling.',
  },
]

const STORAGE_PROFILE = {
  backend: 'ipfs',
  provider: 'Lighthouse',
  gateway_base: 'https://gateway.lighthouse.storage/ipfs/',
  uri_scheme: 'ipfs://',
  upload_mode: 'pinned',
}

const CONTRACT_PROFILE = {
  philosophy: 'Keep rights metadata readable, keep issuance cheap, and reserve heavy provenance for premium assets.',
  default_network: 'polygon',
  storage_backend: 'ipfs',
  principles: [
    'Mint rights only after metadata is pinned and auditable.',
    'Separate plan provenance from fractional property economics.',
    'Favor simple investor-readable metadata over protocol complexity.',
  ],
  templates: [
    { key: 'plan_nft', name: 'Architectural Plan NFT', standard: 'ERC-721', asset_type: 'architectural_plan', source_path: 'contracts/PlanRegistry.sol' },
    { key: 'fractional_property', name: 'Fractional Property Token', standard: 'ERC-1155', asset_type: 'tokenized_property', source_path: 'contracts/FractionalPropertyVault.sol' },
    { key: 'exchange_listing', name: 'Secondary Listing Module', standard: 'Module', asset_type: 'exchange_listing', source_path: 'contracts/ListingRouter.sol' },
  ],
}

const ARCHITECTURAL_PLANS = [
  {
    id: 401,
    location_id: 101,
    title: 'Cyber City Podium Tower Pack',
    author_name: 'Studio Meridian',
    current_owner_wallet: '0x8c32a154fc20b7b8f3e8a2f7a2f6402eb6398111',
    version_label: 'v3.2',
    asset_status: 'minted',
    personal_license_allowed: true,
    commercial_license_allowed: true,
    resale_license_allowed: true,
    chain: 'polygon',
    storage_gateway_url: 'https://gateway.lighthouse.storage/ipfs/QmCyberCityPodiumPack',
  },
  {
    id: 402,
    location_id: 104,
    title: 'GIFT Finance Block B',
    author_name: 'Axis Draft Labs',
    current_owner_wallet: '0x17ba3fbe2f6d8d8a06cc11d5d89b904fb2c6ab52',
    version_label: 'v2.4',
    asset_status: 'minted',
    personal_license_allowed: false,
    commercial_license_allowed: true,
    resale_license_allowed: true,
    chain: 'polygon',
    storage_gateway_url: 'https://gateway.lighthouse.storage/ipfs/QmGiftFinanceBlockB',
  },
  {
    id: 403,
    location_id: 102,
    title: 'Bellandur Rental Micro-District',
    author_name: 'Urban Weave',
    current_owner_wallet: '0x3f6d3ea2d1475a8b66a99f7c1a90af3a18db6403',
    version_label: 'v1.9',
    asset_status: 'licensed',
    personal_license_allowed: false,
    commercial_license_allowed: true,
    resale_license_allowed: false,
    chain: 'base',
    storage_gateway_url: 'https://gateway.lighthouse.storage/ipfs/QmBellandurRentalDistrict',
  },
  {
    id: 404,
    location_id: 106,
    title: 'Aero District Logistics Spine',
    author_name: 'Runway Urban',
    current_owner_wallet: '0x62bc0e8fcd7d9486f26015fd8177f1f735c4bc04',
    version_label: 'v2.1',
    asset_status: 'minted',
    personal_license_allowed: true,
    commercial_license_allowed: true,
    resale_license_allowed: true,
    chain: 'polygon',
    storage_gateway_url: 'https://gateway.lighthouse.storage/ipfs/QmAeroDistrictSpine',
  },
]

const TOKENIZED_PROPERTIES = [
  { id: 701, location_id: 101, asset_name: 'Cyber City Income Vault', property_type: 'commercial', status: 'active', valuation_amount: 225000000, currency: 'INR', total_units: 10000, chain: 'polygon', contract_address: '0xd9184fe17c78a7e9878cb3dbf6149da125870701', token_symbol: 'CCIV', token_standard: 'ERC-1155' },
  { id: 702, location_id: 104, asset_name: 'GIFT Core Yield Trust', property_type: 'commercial', status: 'active', valuation_amount: 168000000, currency: 'INR', total_units: 8000, chain: 'polygon', contract_address: '0x7f2d0eb9476bc63b5e710ce57e5fe65a12870702', token_symbol: 'GIFT', token_standard: 'ERC-1155' },
  { id: 703, location_id: 105, asset_name: 'Hinjawadi Rental Commons', property_type: 'mixed_use', status: 'active', valuation_amount: 98000000, currency: 'INR', total_units: 12000, chain: 'base', contract_address: '0x128bcf04a2dadf3bd78a1d807ab2f367a3280703', token_symbol: 'HJRC', token_standard: 'ERC-1155' },
]

const EXCHANGE_LISTINGS = [
  { id: 801, plan_id: 401, seller_wallet: '0xassetdesk001', asking_price: 1850000, currency: 'INR', listing_type: 'primary', status: 'active' },
  { id: 802, plan_id: 402, seller_wallet: '0xassetdesk002', asking_price: 2140000, currency: 'INR', listing_type: 'secondary', status: 'active' },
  { id: 803, plan_id: 404, seller_wallet: '0xassetdesk003', asking_price: 1260000, currency: 'INR', listing_type: 'primary', status: 'active' },
]

function clone(value) {
  if (typeof structuredClone === 'function') return structuredClone(value)
  return JSON.parse(JSON.stringify(value))
}

function round(value, digits = 1) {
  const factor = 10 ** digits
  return Math.round(value * factor) / factor
}

function prettyLabel(value) {
  return String(value ?? '')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase())
}

function getMarket(locationId) {
  return MARKETS.find((market) => market.id === Number(locationId)) || null
}

function average(values) {
  if (!values.length) return 0
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

function overallFavorability(market) {
  return round(
    market.scores.land_value_score * 0.4 +
      market.scores.development_potential_score * 0.25 +
      market.scores.future_appreciation_index * 0.35,
    1,
  )
}

function scoreBand(value) {
  if (value >= 90) return 'prime'
  if (value >= 82) return 'strong'
  if (value >= 74) return 'constructive'
  return 'selective'
}

function toRankingRow(market) {
  return {
    location: market.name,
    location_id: market.id,
    land_value_score: market.scores.land_value_score,
    development_potential_score: market.scores.development_potential_score,
    future_appreciation_index: market.scores.future_appreciation_index,
    zoning_type: market.zoning_type,
  }
}

function toScoreOut(market) {
  return {
    location: market.name,
    location_id: market.id,
    land_value_score: market.scores.land_value_score,
    development_potential_score: market.scores.development_potential_score,
    future_appreciation_index: market.scores.future_appreciation_index,
    components: clone(market.scores),
  }
}

function featureProfile(key, label, averageValue, baselineValue) {
  const delta = round(averageValue - baselineValue, 1)
  return {
    key,
    label,
    average: averageValue,
    delta_from_baseline: delta,
    relative_level: delta > 3 ? 'high' : delta < -3 ? 'low' : 'neutral',
  }
}

function haversineKm(lat1, lng1, lat2, lng2) {
  const toRadians = (value) => (value * Math.PI) / 180
  const earthRadiusKm = 6371
  const deltaLat = toRadians(lat2 - lat1)
  const deltaLng = toRadians(lng2 - lng1)
  const a =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(deltaLng / 2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return earthRadiusKm * c
}

function nearbyInfrastructureFor(locationId, radiusKm = 6) {
  const market = getMarket(locationId)
  if (!market) return []

  return INFRASTRUCTURE
    .map((item) => ({
      ...item,
      distance_km: round(haversineKm(market.lat, market.lng, item.lat, item.lng), 1),
    }))
    .filter((item) => item.distance_km <= radiusKm)
    .sort((left, right) => left.distance_km - right.distance_km)
    .map((item) => ({
      id: item.id,
      name: item.name,
      infra_type: item.infra_type,
      status: item.status,
      lat: item.lat,
      lng: item.lng,
      distance_km: item.distance_km,
    }))
}

function logicOut(market) {
  const weightedScore = overallFavorability(market)

  return {
    weighted_score: weightedScore,
    weighted_band: scoreBand(weightedScore),
    investment_signal: market.copy.investment_signal,
    execution_strategy: market.copy.execution_strategy,
    conviction: market.copy.conviction,
    data_confidence_score: market.scores.data_confidence_score,
    data_confidence_band: market.scores.data_confidence_band,
    primary_driver: market.copy.primary_driver,
    gating_issue: market.copy.risks[0] || null,
    verdict: market.copy.verdict,
    weighted_components: [
      {
        key: 'land_value',
        label: 'Land value',
        value: market.scores.land_value_score,
        weight: 0.4,
        contribution: round(market.scores.land_value_score * 0.4, 1),
      },
      {
        key: 'development_potential',
        label: 'Development potential',
        value: market.scores.development_potential_score,
        weight: 0.25,
        contribution: round(market.scores.development_potential_score * 0.25, 1),
      },
      {
        key: 'future_appreciation',
        label: 'Future appreciation',
        value: market.scores.future_appreciation_index,
        weight: 0.35,
        contribution: round(market.scores.future_appreciation_index * 0.35, 1),
      },
    ],
    rule_hits: [
      {
        code: 'transit_and_access',
        effect: market.scores.metro_access_score >= 80 ? 'positive' : 'neutral',
        detail: `Transit access scores ${market.scores.metro_access_score.toFixed(0)} for this market.`,
      },
      {
        code: 'site_risk',
        effect: market.scores.site_risk_score <= 28 ? 'positive' : 'negative',
        detail: `Site risk score sits at ${market.scores.site_risk_score.toFixed(0)}.`,
      },
    ],
  }
}

function predictionDrivers(market) {
  return [
    {
      key: 'infra',
      label: 'Strategic infrastructure',
      value: market.scores.strategic_infra_score,
      contribution: round(market.scores.strategic_infra_score * 0.22, 1),
      direction: 'positive',
    },
    {
      key: 'demand',
      label: 'Demand pressure',
      value: market.scores.demand_pressure_score,
      contribution: round(market.scores.demand_pressure_score * 0.24, 1),
      direction: 'positive',
    },
    {
      key: 'risk',
      label: 'Site risk',
      value: market.scores.site_risk_score,
      contribution: round(market.scores.site_risk_score * -0.12, 1),
      direction: market.scores.site_risk_score > 35 ? 'negative' : 'neutral',
    },
  ]
}

function coreMetric(score, summary, drivers) {
  return {
    score,
    band: scoreBand(score),
    summary,
    drivers,
  }
}

function locationDetailOut(market) {
  return {
    location: {
      id: market.id,
      name: market.name,
      country_code: market.country_code,
      state: market.state,
      city: market.city,
      locality: market.locality,
      ward: market.ward,
      lat: market.lat,
      lng: market.lng,
      zoning_type: market.zoning_type,
    },
    masterplan: clone(market.masterplan),
    avg_price_per_sqft: market.avg_price_per_sqft,
    price_history: PRICE_HISTORY_DATES.map((recorded_date, index) => ({
      recorded_date,
      price_per_sqft: market.price_history[index],
      property_type: market.copy.recommended_use_case,
    })),
    census: clone(market.census),
    geo_profile: clone(market.geo),
    regional_standards: clone(market.regional_standards),
    nearby_infrastructure: nearbyInfrastructureFor(market.id, 8).map(({ name, infra_type, status, distance_km }) => ({
      name,
      infra_type,
      status,
      distance_km,
    })),
  }
}

function intelligenceOut(market) {
  return {
    location_id: market.id,
    location_name: market.name,
    city: market.city,
    zoning_type: market.zoning_type,
    fsi: market.masterplan.fsi,
    avg_price_per_sqft: market.avg_price_per_sqft,
    land_value_score: market.scores.land_value_score,
    development_potential_score: market.scores.development_potential_score,
    future_appreciation_index: market.scores.future_appreciation_index,
    density_score: market.scores.density_score,
    infra_score: market.scores.infra_score,
    price_trend_score: market.scores.price_trend_score,
    climate_resilience_score: market.scores.climate_resilience_score,
    terrain_readiness_score: market.scores.terrain_readiness_score,
    population: market.census.population,
    growth_rate_pct: market.census.growth_rate_pct,
    terrain_class: market.geo.terrain_class,
    terrain_slope_pct: market.geo.terrain_slope_pct,
    flood_risk_score: market.geo.flood_risk_score,
    heat_risk_score: market.geo.heat_risk_score,
    climate_risk_score: market.geo.climate_risk_score,
    predicted_price_1yr: market.outlook.predicted_price_1yr,
    predicted_price_3yr: market.outlook.predicted_price_3yr,
    prediction_confidence: market.outlook.confidence,
    planning_context_id: market.planning.id,
    planning_context_version: market.planning.version_tag,
    data_confidence_score: market.scores.data_confidence_score,
    data_confidence_band: market.scores.data_confidence_band,
    data_gaps: [],
    regional_standards: clone(market.regional_standards),
    masterplan_version: market.masterplan.version,
    masterplan_dataset_version: market.masterplan.version,
  }
}

function valuationCoreOut(market) {
  const favorability = overallFavorability(market)
  const logic = logicOut(market)

  return {
    location: market.name,
    location_id: market.id,
    summary: market.copy.summary,
    key_insight: market.copy.keyInsight,
    forward_outlook: {
      current_avg_price: market.avg_price_per_sqft,
      predicted_price_1yr: market.outlook.predicted_price_1yr,
      predicted_price_3yr: market.outlook.predicted_price_3yr,
      predicted_upside_pct: market.outlook.predicted_upside_pct,
      annual_growth_pct: market.outlook.annual_growth_pct,
      signal: market.outlook.signal,
      confidence: market.outlook.confidence,
      model_version: 'demo-2026.03',
      summary: `${market.name} carries a ${market.outlook.signal} 12-month outlook with ${market.outlook.predicted_upside_pct.toFixed(1)}% projected upside.`,
      drivers: predictionDrivers(market),
    },
    coverage: {
      confidence_score: market.scores.data_confidence_score,
      confidence_band: market.scores.data_confidence_band,
      source_count: 7,
      freshness_days: 14,
      gaps: [],
    },
    scores: {
      land_value_score: market.scores.land_value_score,
      development_potential_score: market.scores.development_potential_score,
      future_appreciation_index: market.scores.future_appreciation_index,
      overall_favorability_score: favorability,
      strategic_infra_score: market.scores.strategic_infra_score,
      demand_pressure_score: market.scores.demand_pressure_score,
      site_risk_score: market.scores.site_risk_score,
    },
    land_value: coreMetric(
      market.scores.land_value_score,
      'Pricing depth and corridor quality support strong land value realization.',
      [
        { key: 'pricing', label: 'Price trend', value: market.scores.price_trend_score },
        { key: 'access', label: 'Road access', value: market.scores.road_access_score },
      ],
    ),
    development_potential: coreMetric(
      market.scores.development_potential_score,
      'Planning fit and infrastructure readiness support efficient development execution.',
      [
        { key: 'fsi', label: 'FSI readiness', value: market.masterplan.fsi },
        { key: 'infra', label: 'Strategic infra', value: market.scores.strategic_infra_score },
      ],
    ),
    future_appreciation: coreMetric(
      market.scores.future_appreciation_index,
      'Forward pricing and corridor catalysts imply durable medium-term upside.',
      [
        { key: 'upside', label: '1Y upside', value: market.outlook.predicted_upside_pct },
        { key: 'growth', label: 'Annual growth', value: market.outlook.annual_growth_pct },
      ],
    ),
    logic,
    positioning: {
      recommended_use_case: market.copy.recommended_use_case,
      favorability_band: market.copy.favorability_band,
      market_tier: market.copy.market_tier,
      price_trend_direction: market.copy.price_trend_direction,
      price_momentum_band: market.copy.price_momentum_band,
      demand_profile: market.copy.demand_profile,
      site_risk_band: market.copy.site_risk_band,
      zoning_shift_direction: market.copy.zoning_shift_direction,
    },
    strengths: clone(market.copy.strengths),
    risks: clone(market.copy.risks),
    opportunities: clone(market.copy.opportunities),
  }
}

function predictionOut(market) {
  return {
    location_id: market.id,
    location_name: market.name,
    current_avg_price: market.avg_price_per_sqft,
    predicted_price_1yr: market.outlook.predicted_price_1yr,
    predicted_price_3yr: market.outlook.predicted_price_3yr,
    annual_growth_pct: market.outlook.annual_growth_pct,
    confidence: market.outlook.confidence,
    predicted_upside_pct: market.outlook.predicted_upside_pct,
    signal: market.outlook.signal,
    model_version: 'demo-2026.03',
    training_locations: 127,
    r_squared: 0.78,
    drivers: predictionDrivers(market),
    summary: `${market.name} shows ${market.outlook.predicted_upside_pct.toFixed(1)}% projected 1-year upside with ${market.outlook.confidence} confidence.`,
  }
}

function planningContextOut(market) {
  return {
    id: market.planning.id,
    location_id: market.id,
    version_tag: market.planning.version_tag,
    country_code: market.country_code,
    admin_area: market.planning.admin_area,
    market_tier: market.planning.market_tier,
    validation_status: market.planning.validation_status,
    floor_plan_constraints: clone(market.planning.floor_plan_constraints),
    zoning_validation_rules: clone(market.planning.zoning_validation_rules),
    location_intelligence_score: market.planning.location_intelligence_score,
    massing_inputs: clone(market.planning.massing_inputs),
    source_summary: market.planning.source_summary,
  }
}

function hotspotOut(cluster) {
  const rows = cluster.location_ids.map((locationId) => getMarket(locationId)).filter(Boolean)
  const baseline = MARKETS.map((market) => market.scores)
  const avgLandValue = round(average(rows.map((market) => market.scores.land_value_score)), 1)
  const avgDevelopmentPotential = round(average(rows.map((market) => market.scores.development_potential_score)), 1)
  const avgAppreciation = round(average(rows.map((market) => market.scores.future_appreciation_index)), 1)
  const avgInfra = round(average(rows.map((market) => market.scores.infra_score)), 1)
  const avgPriceTrend = round(average(rows.map((market) => market.scores.price_trend_score)), 1)
  const avgPrice = round(average(rows.map((market) => market.avg_price_per_sqft)), 0)
  const hotspotScore = round(avgLandValue * 0.35 + avgDevelopmentPotential * 0.2 + avgAppreciation * 0.45, 1)

  return {
    cluster_id: cluster.cluster_id,
    label: cluster.label,
    summary: cluster.summary,
    cluster_size: rows.length,
    hotspot_score: hotspotScore,
    dominant_signal: cluster.dominant_signal,
    locations: rows.map((market) => ({ location_id: market.id, name: market.name })),
    avg_land_value: avgLandValue,
    avg_development_potential: avgDevelopmentPotential,
    avg_appreciation: avgAppreciation,
    avg_infra_score: avgInfra,
    avg_price_trend: avgPriceTrend,
    avg_price: avgPrice,
    feature_profile: [
      featureProfile('infra_score', 'Infrastructure', avgInfra, average(baseline.map((item) => item.infra_score))),
      featureProfile('price_trend_score', 'Price trend', avgPriceTrend, average(baseline.map((item) => item.price_trend_score))),
      featureProfile('density_score', 'Density', round(average(rows.map((market) => market.scores.density_score)), 1), average(baseline.map((item) => item.density_score))),
    ],
  }
}

function brainModules(market) {
  return [
    { key: 'planning', title: 'Planning layer', summary: `Planning context is current at ${market.planning.version_tag} with ${market.masterplan.fsi} FSI.`, status: 'live', source_system: 'data_bank' },
    { key: 'valuation', title: 'Valuation layer', summary: `Composite favorability is ${overallFavorability(market).toFixed(1)} with ${market.copy.investment_signal} posture.`, status: 'live', source_system: 'valuation' },
    { key: 'forecasting', title: 'Forecasting layer', summary: `${market.outlook.predicted_upside_pct.toFixed(1)}% 1-year upside with ${market.outlook.confidence} confidence.`, status: 'live', source_system: 'valuation_ml' },
    { key: 'asset_rails', title: 'Blockchain rails', summary: 'Plan provenance and tokenized asset hooks are ready for investor packaging.', status: 'ready', source_system: 'blockchain' },
  ]
}

function analysisCards(market) {
  return [
    { label: 'Investment signal', value: prettyLabel(market.copy.investment_signal), tone: market.copy.investment_signal === 'acquire' ? 'strong' : 'watch' },
    { label: '3Y outlook', value: `${round(((market.outlook.predicted_price_3yr / market.avg_price_per_sqft) - 1) * 100, 1)}%`, tone: 'strong' },
    { label: 'Best use case', value: prettyLabel(market.copy.recommended_use_case), tone: 'watch' },
    { label: 'Site risk', value: `${market.scores.site_risk_score.toFixed(0)}/100`, tone: market.scores.site_risk_score > 35 ? 'risk' : 'strong' },
  ]
}

function analysisMarkdown(market) {
  return [
    `## ${market.name} thesis`,
    market.copy.thesis,
    '',
    '### Why the market is working',
    ...market.copy.strengths.map((item) => `- ${item}`),
    '',
    '### What needs watching',
    ...market.copy.risks.map((item) => `- ${item}`),
    '',
    '### Best execution posture',
    `- ${market.copy.primary_recommendation}`,
    `- ${market.copy.opportunity_reason}`,
  ].join('\n')
}

function compareWinner(rows, question = '') {
  const normalizedQuestion = question.toLowerCase()

  if (normalizedQuestion.includes('risk')) {
    return [...rows].sort((left, right) => left.components.site_risk_score - right.components.site_risk_score)[0]
  }

  if (normalizedQuestion.includes('upside') || normalizedQuestion.includes('future') || normalizedQuestion.includes('3 year') || normalizedQuestion.includes('3-year')) {
    return [...rows].sort((left, right) => right.future_appreciation_index - left.future_appreciation_index)[0]
  }

  return [...rows].sort((left, right) => overallFavorability(getMarket(right.location_id)) - overallFavorability(getMarket(left.location_id)))[0]
}

export function getDemoLocations(filters = {}) {
  const activeFilters = Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== '')
  const results = MARKETS.filter((market) => (
    activeFilters.every(([key, value]) => String(market[key] ?? '').toLowerCase().includes(String(value).toLowerCase()))
  ))

  return clone(results)
}

export function getDemoLocationDetail(locationId) {
  const market = getMarket(locationId)
  return market ? clone(locationDetailOut(market)) : null
}

export function getDemoPlanningContext(locationId) {
  const market = getMarket(locationId)
  return market ? clone(planningContextOut(market)) : null
}

export function getDemoInfrastructure() {
  return clone(INFRASTRUCTURE)
}

export function getDemoNearbyInfrastructure(locationId, radiusKm = 6) {
  return clone(nearbyInfrastructureFor(locationId, radiusKm))
}

export function getDemoIntelligence(locationId) {
  const market = getMarket(locationId)
  return market ? clone(intelligenceOut(market)) : null
}

export function getDemoRankings(sortBy = 'land_value_score', top = 20) {
  return clone(
    MARKETS
      .map(toRankingRow)
      .sort((left, right) => (right[sortBy] ?? 0) - (left[sortBy] ?? 0))
      .slice(0, top)
      .map((row, index) => ({ ...row, rank: index + 1 })),
  )
}

export function getDemoScore(locationId) {
  const market = getMarket(locationId)
  return market ? clone(toScoreOut(market)) : null
}

export function getDemoCompare(locationIds = []) {
  return clone(locationIds.map((locationId) => getMarket(locationId)).filter(Boolean).map(toScoreOut))
}

export function getDemoValuationCore(locationId) {
  const market = getMarket(locationId)
  return market ? clone(valuationCoreOut(market)) : null
}

export function getDemoValuationLogic(locationId) {
  const market = getMarket(locationId)
  return market ? clone({ location: market.name, location_id: market.id, logic: logicOut(market) }) : null
}

export function getDemoPrediction(locationId) {
  const market = getMarket(locationId)
  return market ? clone(predictionOut(market)) : null
}

export function getDemoHotspots(nClusters = 4) {
  return clone(HOTSPOT_CLUSTERS.slice(0, nClusters).map(hotspotOut))
}

export function getDemoAIAnalysis(locationId) {
  const market = getMarket(locationId)
  if (!market) return null

  return clone({
    location_id: market.id,
    analysis: analysisMarkdown(market),
    cards: analysisCards(market),
    recommended_questions: [
      `What is the cleanest execution plan for ${market.name}?`,
      `Where is the main risk in ${market.name}?`,
      `How would you phase development in ${market.name}?`,
    ],
  })
}

export function getDemoAIMarketBrief() {
  const leadMarkets = getDemoRankings('land_value_score', 3)

  return clone({
    summary: 'Premium office, selective mixed-use, and policy-backed districts are leading the current presentation set. The strongest stories combine clean access, zoning clarity, and visible occupier demand.',
    national_thesis: 'Investors should separate premium pricing power from policy-upside rerating and from affordable tech-growth corridors rather than treating all urban land as one risk bucket.',
    top_opportunities: leadMarkets.map((row) => {
      const market = getMarket(row.location_id)
      return {
        location_id: market.id,
        location_name: market.name,
        title: market.copy.opportunity_title,
        reason: market.copy.opportunity_reason,
        score: overallFavorability(market),
      }
    }),
    watchouts: [
      'Hydrology and drainage diligence remain critical in high-density Bengaluru corridors.',
      'Policy-led districts need patient timing even when the long-term thesis is strong.',
      'Premium commercial markets reward clean execution but punish overpaying at entry.',
    ],
    prompt_suggestions: [
      'Best risk-adjusted market right now?',
      'Where is mixed-use strongest?',
      'Which corridor has the cleanest 3-year upside?',
    ],
  })
}

export function getDemoAICompare(locationIds = []) {
  const rows = getDemoCompare(locationIds)
  if (rows.length < 2) return null

  const winner = compareWinner(rows)
  const bestUpside = compareWinner(rows, 'upside')
  const lowestRisk = compareWinner(rows, 'risk')

  return clone({
    summary: `${winner.location} is the best rounded story in the selected basket, while ${bestUpside.location} carries the strongest future upside and ${lowestRisk.location} offers the cleanest risk posture.`,
    winner_location_id: winner.location_id,
    winner_location_name: winner.location,
    verdicts: [
      { label: 'Best rounded thesis', value: winner.location, tone: 'strong' },
      { label: 'Top future upside', value: bestUpside.location, tone: 'watch' },
      { label: 'Cleanest risk posture', value: lowestRisk.location, tone: 'strong' },
      { label: 'Basket count', value: `${rows.length} markets`, tone: 'watch' },
    ],
    recommended_questions: [
      `What changes the winner between ${rows[0].location} and ${rows[1].location}?`,
      'Which basket member is best for mixed-use execution?',
      'Where does downside protection look strongest?',
    ],
  })
}

export function getDemoAIBrainProfile(locationId) {
  const market = getMarket(locationId)
  if (!market) return null

  return clone({
    location_id: market.id,
    location_name: market.name,
    systems_covered: ['data_bank', 'valuation', 'valuation_ml', 'blockchain', 'ai'],
    thesis: market.copy.thesis,
    primary_recommendation: market.copy.primary_recommendation,
    modules: brainModules(market),
    recommendations: clone(market.copy.recommendations),
  })
}

export function getDemoAIAnswer(question, { locationId = null, compareIds = [] } = {}) {
  const normalizedQuestion = String(question ?? '').trim().toLowerCase()

  if (compareIds.length >= 2) {
    const rows = getDemoCompare(compareIds)
    const winner = compareWinner(rows, normalizedQuestion)
    const highestUpside = compareWinner(rows, 'upside')
    const lowestRisk = compareWinner(rows, 'risk')

    return clone({
      answer: [
        '## Comparison takeaway',
        `${winner.location} leads for this question.`,
        '',
        `- Best overall posture: ${compareWinner(rows).location}`,
        `- Best future upside: ${highestUpside.location}`,
        `- Cleanest risk posture: ${lowestRisk.location}`,
        '',
        normalizedQuestion.includes('risk')
          ? `The edge comes from ${winner.location} carrying the lowest site-risk burden in the basket while preserving strong demand quality.`
          : normalizedQuestion.includes('upside') || normalizedQuestion.includes('future')
            ? `${winner.location} has the strongest appreciation setup because pricing still has room to rerate alongside its catalyst stack.`
            : `${winner.location} best balances pricing power, execution visibility, and future appreciation within the selected basket.`,
      ].join('\n'),
      context_label: `Compare: ${rows.map((row) => row.location).join(' vs ')}`,
    })
  }

  if (locationId) {
    const market = getMarket(locationId)
    if (!market) return null

    let answer = [
      `## ${market.name}`,
      market.copy.thesis,
      '',
      `- Signal: ${prettyLabel(market.copy.investment_signal)}`,
      `- Best use case: ${prettyLabel(market.copy.recommended_use_case)}`,
      `- 1Y upside: ${market.outlook.predicted_upside_pct.toFixed(1)}%`,
    ]

    if (normalizedQuestion.includes('risk')) {
      answer = [
        `## Risk view for ${market.name}`,
        market.copy.risks[0],
        '',
        ...market.copy.risks.map((item) => `- ${item}`),
        `- Mitigant: ${market.copy.opportunities[0]}`,
      ]
    } else if (normalizedQuestion.includes('use') || normalizedQuestion.includes('fit')) {
      answer = [
        `## Best fit for ${market.name}`,
        market.copy.primary_recommendation,
        '',
        `- Recommended use case: ${prettyLabel(market.copy.recommended_use_case)}`,
        `- Execution strategy: ${prettyLabel(market.copy.execution_strategy)}`,
        `- Why now: ${market.copy.opportunity_reason}`,
      ]
    } else if (normalizedQuestion.includes('upside') || normalizedQuestion.includes('future')) {
      answer = [
        `## Upside view for ${market.name}`,
        `${market.name} shows ${market.outlook.predicted_upside_pct.toFixed(1)}% projected 1-year upside and ${round(((market.outlook.predicted_price_3yr / market.avg_price_per_sqft) - 1) * 100, 1)}% 3-year upside.`,
        '',
        `- Current average price: INR ${market.avg_price_per_sqft.toLocaleString('en-IN')}/sqft`,
        `- Projected 1Y price: INR ${market.outlook.predicted_price_1yr.toLocaleString('en-IN')}/sqft`,
        `- Projected 3Y price: INR ${market.outlook.predicted_price_3yr.toLocaleString('en-IN')}/sqft`,
      ]
    }

    return clone({ answer: answer.join('\n'), context_label: `Market: ${market.name}` })
  }

  const brief = getDemoAIMarketBrief()
  const watchouts = brief.watchouts.slice(0, 2).map((item) => `- ${item}`).join('\n')

  return clone({
    answer: [
      '## National market brief',
      brief.summary,
      '',
      `- Lead market today: ${brief.top_opportunities[0]?.location_name || 'Gurugram Cyber City'}`,
      '- Best policy-upside story: GIFT City Core',
      '- Best affordable tech-growth story: Hinjawadi Phase 1',
      '',
      normalizedQuestion.includes('risk') ? watchouts : brief.national_thesis,
    ].join('\n'),
    context_label: 'National view',
  })
}

export function getDemoPlans(locationId = null) {
  return clone(locationId ? ARCHITECTURAL_PLANS.filter((plan) => plan.location_id === Number(locationId)) : ARCHITECTURAL_PLANS)
}

export function getDemoExchangeListings(filters = {}) {
  const activeFilters = Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== '')
  return clone(
    EXCHANGE_LISTINGS.filter((listing) => (
      activeFilters.every(([key, value]) => String(listing[key] ?? '').toLowerCase() === String(value).toLowerCase())
    )),
  )
}

export function getDemoTokenizedProperties(locationId = null) {
  return clone(locationId ? TOKENIZED_PROPERTIES.filter((property) => property.location_id === Number(locationId)) : TOKENIZED_PROPERTIES)
}

export function getDemoSupportedNetworks() {
  return clone(SUPPORTED_NETWORKS)
}

export function getDemoStorageProfile() {
  return clone(STORAGE_PROFILE)
}

export function getDemoContractProfile() {
  return clone(CONTRACT_PROFILE)
}
