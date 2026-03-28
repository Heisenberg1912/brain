"""BuiltAttic Brain CLI — the primary interface to the intelligence engine."""
import click

from brain.database import session_context


@click.group()
def cli():
    """BuiltAttic Brain — Real Estate Intelligence Engine"""
    pass


# --- Database commands ---

@cli.group()
def db():
    """Database management commands."""
    pass


@db.command()
def migrate():
    """Run Alembic migrations (upgrade to head)."""
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("Migrations complete.")


@db.command()
def revision():
    """Auto-generate a new Alembic migration."""
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message="auto")
    click.echo("Revision created. Review it in alembic/versions/")


# --- Seed commands ---

@cli.command()
def seed():
    """Load seed data into the database."""
    from brain.data_bank.seed import seed_all
    with session_context() as session:
        try:
            seed_all(session)
            session.commit()
        except Exception as e:
            session.rollback()
            click.echo(f"Error: {e}", err=True)
            raise


# --- Query commands ---

@cli.group()
def query():
    """Query the data bank."""
    pass


@query.command()
def locations():
    """List all locations."""
    from brain.data_bank.service import get_all_locations
    with session_context() as session:
        locs = get_all_locations(session)
        for loc in locs:
            click.echo(f"  [{loc.id}] {loc.name} — {loc.locality}, {loc.ward} ({loc.pin_code})")
        click.echo(f"\nTotal: {len(locs)} locations")


@query.command()
@click.argument("location_id", type=int)
def intelligence(location_id):
    """Show the unified intelligence snapshot for a location."""
    from brain.data_bank.service import build_location_intelligence_record
    with session_context() as session:
        record = build_location_intelligence_record(session, location_id)
        session.commit()
        if not record:
            click.echo("Location not found.")
            return

        click.echo(f"\n{'='*58}")
        click.echo(f"  Intelligence Snapshot: {record['location_name']}")
        click.echo(f"{'='*58}")
        click.echo(f"  Zoning / FSI:      {record['zoning_type']} / {record['fsi']}")
        click.echo(f"  Avg Price:         Rs {record['avg_price_per_sqft']}/sqft")
        click.echo(f"  Scores:            LV={record['land_value_score']} DP={record['development_potential_score']} FA={record['future_appreciation_index']}")
        click.echo(f"  Components:        Density={record['density_score']} Infra={record['infra_score']} Climate={record['climate_resilience_score']} Terrain={record['terrain_readiness_score']}")
        click.echo(f"  Forecast:          1yr={record['predicted_price_1yr']} 3yr={record['predicted_price_3yr']} ({record['prediction_confidence']})")
        click.echo(f"  Risks:             Flood={record['flood_risk_score']} Heat={record['heat_risk_score']} Climate={record['climate_risk_score']}")
        click.echo(f"  Standards:         {', '.join(record['regional_standards']) or 'None'}")
        click.echo(f"  Planning Context:  {record['planning_context_version'] or 'not derived'}")


@query.command()
@click.option("--lat", required=True, type=float, help="Latitude")
@click.option("--lng", required=True, type=float, help="Longitude")
@click.option("--radius", default=5.0, type=float, help="Radius in km")
def nearby(lat, lng, radius):
    """Find locations near a point."""
    from brain.data_bank.service import find_nearby_locations
    with session_context() as session:
        results = find_nearby_locations(session, lat, lng, radius)
        if not results:
            click.echo("No locations found within radius.")
            return
        for r in results:
            loc = r["location"]
            click.echo(f"  [{loc.id}] {loc.name} — {r['distance_km']}km away")
        click.echo(f"\nFound {len(results)} locations within {radius}km")


@query.command()
@click.argument("location_id", type=int)
def summary(location_id):
    """Show full summary for a location."""
    from brain.data_bank.service import get_location_summary
    with session_context() as session:
        s = get_location_summary(session, location_id)
        if not s:
            click.echo("Location not found.")
            return

        loc = s["location"]
        click.echo(f"\n{'='*50}")
        click.echo(f"  {loc.name} ({loc.locality}, {loc.ward})")
        click.echo(f"{'='*50}")

        if s["masterplan"]:
            mp = s["masterplan"]
            click.echo(f"\n  Zoning: {mp.zoning_type} | FSI: {mp.fsi}")
            click.echo(f"  Max Height: {mp.max_height_m}m | Ground Coverage: {mp.ground_coverage_pct}%")
            click.echo(f"  Setbacks: Front={mp.setback_front_m}m, Side={mp.setback_side_m}m")

        if s["avg_price_per_sqft"]:
            click.echo(f"\n  Avg Price: Rs {s['avg_price_per_sqft']}/sqft")

        if s["price_history"]:
            click.echo(f"  Price History ({len(s['price_history'])} records):")
            for p in s["price_history"][:5]:
                click.echo(f"    Rs {p.price_per_sqft}/sqft ({p.property_type}) — {p.recorded_date} [{p.source}]")

        if s["census"]:
            c = s["census"]
            click.echo(f"\n  Population: {c.population:,} | Density: {c.density_per_sqkm}/sqkm")
            click.echo(f"  Growth: {c.growth_rate_pct}% | Households: {c.households:,}")

        if s.get("geo_profile"):
            g = s["geo_profile"]
            click.echo(f"\n  Geo Profile: Terrain={g.terrain_class} | Slope={g.terrain_slope_pct}% | Climate Risk={g.climate_risk_score}")
            click.echo(f"  Flood Risk: {g.flood_risk_score} | Heat Risk: {g.heat_risk_score} | Transit: {g.transit_proximity_km}km")

        if s.get("regional_standards"):
            click.echo(f"\n  Regional Standards:")
            for standard in s["regional_standards"][:5]:
                click.echo(f"    {standard.code}: {standard.title} ({standard.standard_type})")

        if s["nearby_infrastructure"]:
            click.echo(f"\n  Nearby Infrastructure ({len(s['nearby_infrastructure'])} items):")
            for item in s["nearby_infrastructure"][:8]:
                i = item["infrastructure"]
                click.echo(f"    {i.name} ({i.infra_type}, {i.status}) — {item['distance_km']}km")


# --- Scoring commands ---

@cli.command()
@click.option("--location-id", required=True, type=int, help="Location ID to score")
def score(location_id):
    """Score a specific location."""
    from brain.valuation.service import score_location
    with session_context() as session:
        result = score_location(session, location_id)
        session.commit()
        if not result:
            click.echo("Location not found.")
            return

        click.echo(f"\n{'='*50}")
        click.echo(f"  Scores for: {result['location']}")
        click.echo(f"{'='*50}")
        click.echo(f"\n  Land Value Score:          {result['land_value_score']}/100")
        click.echo(f"  Development Potential:     {result['development_potential_score']}/100")
        click.echo(f"  Future Appreciation Index: {result['future_appreciation_index']}/100")

        comp = result.get("components", {})
        click.echo(f"\n  Components:")
        click.echo(f"    Infra Score:          {comp.get('infra_score')}")
        click.echo(f"    Price Trend:          {comp.get('price_trend_score')}")
        click.echo(f"    Zoning Favorability:  {comp.get('zoning_favorability')}")
        click.echo(f"    Density Score:        {comp.get('density_score')}")
        if comp.get("avg_price_per_sqft"):
            click.echo(f"    Avg Price/sqft:       Rs {comp['avg_price_per_sqft']}")


@cli.command()
@click.option("--top", default=10, type=int, help="Number of results")
@click.option("--sort-by", default="land_value_score",
              type=click.Choice(["land_value_score", "development_potential_score", "future_appreciation_index"]))
def rankings(top, sort_by):
    """Show top locations by score."""
    from brain.valuation.service import score_all_locations, get_rankings
    with session_context() as session:
        # Ensure scores exist
        score_all_locations(session)
        results = get_rankings(session, top_n=top, sort_by=sort_by)

        click.echo(f"\n  Top {top} by {sort_by.replace('_', ' ').title()}")
        click.echo(f"  {'='*60}")
        click.echo(f"  {'Rank':<5} {'Location':<20} {'Land Val':>10} {'Dev Pot':>10} {'Future':>10}")
        click.echo(f"  {'-'*60}")
        for r in results:
            click.echo(
                f"  {r['rank']:<5} {r['location']:<20} "
                f"{r['land_value_score']:>10.1f} "
                f"{r['development_potential_score']:>10.1f} "
                f"{r['future_appreciation_index']:>10.1f}"
            )


# --- Ingestion commands ---

@cli.command()
@click.option("--source", default="csv", type=click.Choice(["csv"]), help="Data source type")
@click.option("--path", required=True, type=click.Path(exists=True), help="Path to data directory")
def ingest(source, path):
    """Ingest data from external sources into the data bank."""
    from brain.data_bank.ingestion import ingest_directory
    with session_context() as session:
        try:
            click.echo(f"\nIngesting from: {path} (source: {source})")
            results = ingest_directory(session, path)
            click.echo(f"\n  {'Type':<20} {'Read':>6} {'Stored':>8} {'Skipped':>9} {'Rate':>8}")
            click.echo(f"  {'-'*55}")
            for dtype, result in results.items():
                click.echo(
                    f"  {dtype:<20} {result.records_read:>6} "
                    f"{result.records_stored:>8} {result.records_skipped:>9} "
                    f"{result.success_rate:>7.1f}%"
                )
            click.echo()
        except Exception as e:
            session.rollback()
            click.echo(f"Error: {e}", err=True)
            raise


@cli.command("ingest-web")
@click.option("--manifest", required=True, type=click.Path(exists=True), help="Path to Gemini web enrichment manifest JSON")
def ingest_web(manifest):
    """Fetch web pages, use Gemini to extract structured records, and ingest them."""
    from brain.data_bank.ingestion.gemini_web_ingestor import GeminiWebIngestor

    with session_context() as session:
        try:
            click.echo(f"\nGemini web enrichment from: {manifest}")
            ingestor = GeminiWebIngestor(session)
            results = ingestor.run_manifest(manifest)
            click.echo(f"\n  {'Job':<20} {'Read':>6} {'Stored':>8} {'Skipped':>9} {'Rate':>8}")
            click.echo(f"  {'-'*60}")
            for job_name, result in results.items():
                click.echo(
                    f"  {job_name:<20} {result.records_read:>6} "
                    f"{result.records_stored:>8} {result.records_skipped:>9} "
                    f"{result.success_rate:>7.1f}%"
                )
                if result.errors:
                    click.echo(f"    errors: {len(result.errors)}")
                    for message in result.errors[:3]:
                        click.echo(f"      - {message}")
                    if len(result.errors) > 3:
                        click.echo(f"      - ... {len(result.errors) - 3} more")
            click.echo()
        except Exception as e:
            session.rollback()
            click.echo(f"Error: {e}", err=True)
            raise


# --- ML commands ---

@cli.group()
def ml():
    """Machine learning models for prediction."""
    pass


@ml.command()
def train():
    """Train the price prediction model."""
    from brain.valuation.ml.price_predictor import PricePredictor
    with session_context() as session:
        predictor = PricePredictor()
        result = predictor.train(session)
        if result["status"] == "trained":
            click.echo(f"\n  Model trained successfully")
            click.echo(f"  Locations used: {result['locations']}")
            click.echo(f"  R² score:       {result['r_squared']}\n")
        else:
            click.echo(f"\n  Training failed: {result}\n", err=True)


@ml.command()
@click.argument("location_id", type=int)
def predict(location_id):
    """Predict future prices for a location."""
    from brain.valuation.ml.price_predictor import PricePredictor
    with session_context() as session:
        predictor = PricePredictor()
        pred = predictor.predict(session, location_id)
        if not pred:
            click.echo("Could not generate prediction (not enough data).")
            return
        click.echo(f"\n  {'='*50}")
        click.echo(f"  Price Prediction: {pred.location_name}")
        click.echo(f"  {'='*50}")
        click.echo(f"  Current Avg Price:  Rs {pred.current_avg_price:,.0f}/sqft")
        click.echo(f"  Predicted (1yr):    Rs {pred.predicted_price_1yr:,.0f}/sqft")
        click.echo(f"  Predicted (3yr):    Rs {pred.predicted_price_3yr:,.0f}/sqft")
        click.echo(f"  Annual Growth:      {pred.annual_growth_pct:+.1f}%")
        click.echo(f"  Confidence:         {pred.confidence}\n")


@ml.command()
def hotspots():
    """Detect investment hotspot clusters."""
    from brain.valuation.ml.hotspot_detector import HotspotDetector
    from brain.valuation.service import score_all_locations
    with session_context() as session:
        # Ensure scores exist
        score_all_locations(session)
        detector = HotspotDetector()
        clusters = detector.detect(session)
        if not clusters:
            click.echo("Not enough data for hotspot detection.")
            return
        for h in clusters:
            click.echo(f"\n  Cluster {h.cluster_id}: {h.label.upper()}")
            click.echo(f"  Avg Land Value: {h.avg_land_value:.1f} | Avg Appreciation: {h.avg_appreciation:.1f} | Avg Price: Rs {h.avg_price:,.0f}/sqft")
            click.echo(f"  Locations:")
            for loc in h.locations:
                click.echo(f"    - {loc['name']} (LV={loc['land_value_score']:.1f}, FA={loc['future_appreciation_index']:.1f}, Rs {loc['avg_price']:,.0f})")
        click.echo()


# --- AI commands ---

@cli.command()
@click.argument("question")
def ask(question):
    """Ask a natural language question about real estate data."""
    from brain.ai.service import query as ai_query
    with session_context() as session:
        click.echo("\nThinking...\n")
        answer = ai_query(session, question)
        click.echo(answer)


@cli.command()
@click.option("--location-id", required=True, type=int)
def analyze(location_id):
    """Deep AI analysis of a specific location."""
    from brain.ai.service import analyze_location
    with session_context() as session:
        click.echo("\nAnalyzing...\n")
        answer = analyze_location(session, location_id)
        click.echo(answer)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
def serve(host, port):
    """Start the web UI + API server."""
    import uvicorn
    click.echo(f"\n  BuiltAttic Brain UI: http://{host}:{port}")
    click.echo(f"  API docs:           http://{host}:{port}/docs\n")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    cli()
