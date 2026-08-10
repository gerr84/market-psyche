# Who builds data centers while tokens commoditize? (2026-08-10)

## The apparent contradiction
Tokens at fixed quality fell ~300x since 2023 (commodity). Yet ~$1.2T / ~100 GW
of DC capacity is being committed (CBRE/JLL; capacity ->200 GW by 2030).
Why build if the product is commoditizing?

## Resolution: the DC bet is NOT on token price
1. VOLUME. arXiv 2511.23455 projects a post-2027 demand explosion. If price
   falls 5x/yr but volume grows 10x/yr, total spend rises. DCs are built for
   megawatts x utilization (throughput), not token price.
2. SOVEREIGNTY (biggest non-price driver). NTT DATA: 95% of orgs say sovereign/
   private AI important. Sovereign infra 15-30% more expensive than hyperscaler
   -- paid BECAUSE regulated data can't use the cheap commodity API. This matches
   our self-host model: own capacity only for sovereignty/latency, never for price.
3. HYPERSCALERS, not random privatecos, are the volume. AWS/MSFT/Google/Meta/
   Oracle build their own. Private enterprises mostly colocate/rent (our SMB finding).
4. OVERSEAS = sovereign + hyperscaler JVs. MEA $100B+ (G42 200MW UAE, Saudi,
   Pure/SEGRO 48MW Paris pre-let to hyperscaler). SEA (Malaysia/Thailand/NZ) =
   AWS/Google. Not private SMBs.

## Are companies stopping? Partial, and NOT because of commoditization
- JPMorgan: ~60% of 2027-planned capacity hasn't broken ground; ~7% cancelled.
- Sightline: 30-50% of US 2026 AI DCs delayed/cancelled -> but bottleneck is
  POWER + COMMUNITY CONSENT, not "tokens are cheap" (Forbes: $130B stalled).
- SemiAnalysis rebuttal: the 30-50% is delays/permits, not true cancellations;
  clickbait inflated Bloomberg's milder framing.

## Synthesis
They SEE the commoditization math (our cost models show it). They build anyway
because: hyperscalers ARE the commodity suppliers (capture volume); sovereigns
are legally excluded from the commodity market (must own). Random privatecos
largely DON'T build -- they rent/colocate, exactly as the SMB analysis predicted.
The "utility" framing is half-right: tokens are a commodity; the DC build is a
hedge on volume + sovereignty, not a bet against the price decline.

## Monitor
research/news_watcher/ (alpha-news-watcher skill) -- sources_datacenter.yaml +
watcher_datacenter.py. Run on cron (09:00/20:00 ET) to track WHO builds, WHERE,
and any cancellation signals. Initial run: feeds partially blocked (Reuters/
Bloomberg RSS throttling); pipeline functional, dedupe + digest written.
