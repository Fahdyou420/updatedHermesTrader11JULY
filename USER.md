# User Profile

Dialectic profile of risk tolerance, instrument/session preferences, and intervention patterns. Dated entries only; never overwrite existing bullets.

<!-- 2026-07-07T00:00:00Z — initial bootstrap -->

## Signals Observed

<!-- 2026-07-07T10:47:44.448867+00:00 — memory-department sync cycle 1 -->
- observed_preference: In-depth per-trade journaling with timestamps and #Test_OPS required; 0-trade and fabricated results rejected. Kanban + cron required over delegate_task for survivability across restarts. No explicit risk-tolerance override observed yet; intervention pattern is process-integrity enforcement, not parameter changes.
- risk_tolerance_signals: daily_trailing_dd_limit=4%, max_trailing_dd_limit=8%, account_size=100000, leverage=1:100, spread_assumption=50-60, reject_empty_metrics=true
- instrument_session_signals: primary_instrument=XAUUSD, secondary=BTCUSD, active_timeframes=[D1,H4,M15], chart_session_channels=[M1,M5]
- intervention_patterns: 2026-07-07 demanded exact raw evidence instead of summaries; demanded pinned skills and durable kanban/cron wiring; demanded end-to-end manual verification. Same run also showed repeated watch on XAUUSD D1/H4/M15 with gold_breakout, and rejection sensitivity to empty/zero-metric artifacts.

<!-- 2026-07-07T18:05:00Z — memory-department sync cycle 4 -->
- observed_preference: strong preference for zero-tolerance discrepancy handling: raw JSON > reliability log > card markdown for strategy status authority. gold_breakout last session was left unresolved hypothesis despite zero-trade artifact; inferred desired action is status normalization or documented blocker, not silent reuse.
- risk_tolerance_signals: prior limits loaded; no change this cycle. Live account shows managed risk; reliability cycle 11-13 shows history PnL swings from -2138.01 to -1019.68 USD over 30 days depending on artifact version, confirming sensitivity to stale evidence.
- instrument_session_signals: XAUUSD remains primary execution focus with D1/H4/M15 evidence confirmation; BTCUSD remains evidence-only in active cards (smc_ob_entry_M15/H4 and smc_fvg_fill_H4 cite BTCUSD while execution stack is XAUUSD), suggesting instrument/card alignment audit still needed.
- intervention_patterns: reliability/backtest mismatches must be rechecked from raw file paths again before escalation; stale snapshots in deep reviews continue to surface; nightly_scan cron broken since Jul 3 with exit=2 apostrophe quoting issue remains unfixed.
- tags: user, profile, 2026-07-07

<!-- 2026-07-07T19:00:00Z — memory-department sync cycle 5 -->
- observed_preference: system must cross-check cached execution state against live endpoints before declaring silent/idle status; empty kanban plus stale execution state files do not equal no-activity evidence.
- risk_tolerance_signals: promotion gate appears strict: WR >=45%, PF >=1.15, maxDD <=4% from approved artifacts; user enforces do_not_trade/watch_only until all three pass.
- intervention_patterns: recurring pattern is stale/deep-review snapshot being disputed by live probe; any analyst-style report should be tagged with capture timestamp and every balance/equity/position statement should cite the exact endpoint/run time rather than prose summaries.
- tags: user, profile, 2026-07-07

<!-- 2026-07-07T22:33:00Z — memory-department sync cycle 6 -->
- observed_preference: live account state must be independently probed this run before being quoted; when native endpoints return HTTP=000/connection refused, all balance/equity/history statements must carry no_evidence or stale-cache-only tags with exact archive run time instead of live prose.
- risk_tolerance_signals: promotion gate remains strict: WR >=45%, PF >=1.15, maxDD <=4%; additional signal from native 30-day history shows max drawdown around 6890.25 from ~98980 baseline, confirming intolerance for large directional losses in the same algorithmic regime.
- instrument_session_signals: XAUUSD remains primary research focus; current native endpoint state is service_unreachable this run, so all XAUUSD lifecycle claims should be treated as cache-only unless refreshed after service recovery.
- intervention_patterns: recurring mode is stale/deep-review snapshot being disputed by a live probe failure cycle; forward-validation and reporting outputs must not advance capital decisions without fresh live endpoint confirmation or explicit no_evidence annotation.
- tags: user, profile, 2026-07-07

<!-- 2026-07-08T00:00:00Z — memory-department sync cycle 7 -->
- observed_preference: when service reachability has been proven, stale cached summaries in 05_RND analyst notes are treated as dispute-worthy rather than provisional truth; author and reliability cycles must not anchor live-looking summaries unless rerun from current endpoint.
- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. Additional intolerance for repeated stale evidence: drawn cache-to-live mismatch becomes a repair action, not a tolerance limit.
- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 observed live footprint; BTCUSD secondary evidence-only. `gold_breakout` remains research candidate, not live promotion, despite strong profit-factor baselines.
- intervention_patterns: reliability and analyst outputs that cite missing/cached metrics are being disputed explicitly; filing ANALYST notes with live-reachability proof does not exempt them from metric-level cache detection.
- tags: user, profile, 2026-07-08

<!-- 2026-07-08T12:50:00Z — memory-department sync cycle 8 -->
- observed_preference: when raw artifacts and card text disagree, card text is treated as UX wording only; the disputed/UNVERIFIED flag is expected to persist until the card wording is reconciled with the artifact, not after service recovery alone. Unfixed cron errors like nightly_scan exit=2/"today's" apostrophe failure across multiple cycles are tolerated without explicit manual restart; not every reliability fault triggers immediate intervention.
- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. Native reachable-cycle compute shows a stable 26-pair-trade sample with sum PnL -929.77 USD and paired-sequence drawdown 6832.05 USD, reinforcing intolerance for sustained negative expectancy and confirming live promotion should remain blocked.
- instrument_session_signals: XAUUSD primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. gold_breakout remains research candidate only despite on-disk zero-trade artifact; no promotion observed unless nonzero backtest or documented data-path blocker is supplied.
- intervention_patterns: reliability cycle 20 reached status=ok but did not clear disputed flags because underlying artifact/card mismatches remained; connectivity oscillation 7779 HTTP=000/EXIT=7 in cycles 25–26 after stable cycles 20–24 was logged but not escalated for repair. Pattern observed: service recovery alone is treated as necessary, not sufficient, for dispute resolution; artifact/card reconciliation is the actual resolution gate.
- tags: user, profile, 2026-07-08

<!-- 2026-07-08T12:55:00Z — memory-department sync cycle 9 -->
||- risk_tolerance_signals: live demo account shows balance decline from 98980.32 to 97539.62 in recent 30-day native history window; paired-sequence drawdown rose from 6832.05 USD to 9318.12 USD in consecutive live probes. User tolerates algorithmic drawdown expansion without abort signal, but strict promotion gate remains against strategies with negative expectancy or unresolved metric disputes.
||- instrument_session_signals: XAUUSD remains primary execution focus on D1/H4/M15; BTCUSD remains evidence-only. gold_breakout remains research candidate; no promotion observed despite on-disk artifacts.
||- intervention_patterns: reliability oscillation on native MT5 port 7779 and unresolved nightly_scan cron (invalid choice: "today's") persisted >24h without manual repair; evidence-drift disputes in analyst docs are treated as expected monitor output rather than escalation triggers.
||- tags: user, profile, 2026-07-08

<!-- 2026-07-08T15:06:00Z — memory-department sync cycle 10 -->
||- observed_preference: recurring reliability and review disputes are dominated by active strategy card instrument drift versus raw artifact metadata; expects instrument-field reconciliation to be a hard precondition for any promotion review or dispute resolution, not an afterthought.
||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. Additional intolerance for cross-instrument mislabeling because it poisons promotion audit trails.
||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 observed live footprint; BTCUSD evidence-only. Current active docs show instrument drift across strategy family (gold_breakout=XAUUSD, smc_* cards=BTCUSD) — owner expects this to be reconciled, not tolerated.
||- intervention_patterns: live endpoint outages do not clear disputed/UNVERIFIED flags; only documented artifact reconciliation or explicit rerun with correct instrument scope resolves disputes. Stale cron jobs like nightly_scan remain unresolved across multiple days without manual escalation.
||- tags: user, profile, 2026-07-09

<!-- 2026-07-08T15:06:00Z — memory-department sync cycle 11 -->
||- observed_preference: reliability cycle34 produced HIGH findings listing gold_breakout zero-trade artifact risk, active card instrument mismatch, history pairing contamination, kanban stale pids/manifest, and broken nightly_scan cron, yet no user-visible intervention occurred. Pattern indicates user treats reliability reports as expected monitor output and leaves repair actions to future explicit work items rather than immediate manual escalation.
||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. cycle34 explicit recommendation delete/regenerate gold_breakout.json remains pending; user accepts discovery-driven repair sequencing.
||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. instrument-drift across gold_breakout vs smc_* cards remains unresolved without approval.
||- intervention_patterns: high-severity reliability findings do not trigger immediate user repair; repair sequencing is discovery-driven and tickets are expected to be filed, not executed at time of finding.
||- tags: user, profile, 2026-07-09

<!-- 2026-07-09T00:00:00Z — memory-department sync cycle 13 -->
|||- observed_preference: board activation does not equal successful execution; kanban `launched` tasks with live PIDs must be independently verified against live process health and log completion evidence before claims are accepted. Unresolved reliability findings persist across multiple cycles without manual escalation; discovery-driven repair sequencing is expected.
|||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%.
|||- instrument_session_signals: XAUUSD remains primary execution focus. Current run shows MT5 bridge returning no data and yfinance GC=F fallback being used for M15 bars; live MT5 pathway remains unstable in observed activity.
|||- intervention_patterns: unresolved reliability findings continue across cycles without explicit manual repair; subagent failures are logged but do not escalate to immediate environment fix or kanban PID reset.
|||- tags: user, profile, 2026-07-09

<!-- 2026-07-09T14:05:00Z — memory-department sync cycle 14 -->
|||- observed_preference: recurring kanban subagent launch generations repeat the identical numpy/pandas cp311-vs-Python 3.13 preflight failure without user-visible repair escalation; user treats reliability findings as expected monitor output and does not manually clear stale PIDs/manifests or escalate broken subagent environments between cycles.
|||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. Current active strategies remain non-promotable; gold_breakout hypothesis pending nonzero artifact or documented data-path blocker.
|||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. Native MT5 API reachability oscillates across cycles; when unreachable, all live history/account/positions claims must be tagged no_evidence.
|||- intervention_patterns: relibility findings are filed but not converted into immediate repair actions; user favors discovery-driven sequencing with kanban tickets over manual intervention. Broken cron jobs like nightly_scan and subagent environment failures persist across multiple days without explicit escalation.
|||- tags: user, profile, 2026-07-09

<!-- 2026-07-10T00:00:00Z — memory-department sync cycle 15 -->
||- observed_preference: new journaled/local FVG-style artifacts on disk have not been mapped into active strategy cards; existing active definitions continue to show instrument drift (%smc_* cards=BTCUSD vs local evidence on XAUUSD). Pattern indicates user is not manually reconciling card-to-artifact metadata between cycles.
||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. Current resolved posture remains do_not_trade_live/watch_only because no artifact set clears all three gates and earlier reliability disputes remain open.
||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. Persistent active-card instrument drift remains unreconciled across `02_STRATEGIES/active/`.
||- intervention_patterns: unresolved reliability findings still persist across cycles without explicit manual repair or kanban-clear action; stalled cron jobs and subagent import failures are tolerated as expected monitor output rather than escalation triggers.
||- tags: user, profile, 2026-07-10

<!-- 2026-07-10T12:00:00Z — memory-department sync cycle 16 -->
||- observed_preference: new kanban subagent generations are launched while prior-cycle identical infrastructure blockers remain unresolved; tolerance implies discovery-driven sequencing rather than immediate environment repair, but launch recurrence without root-cause closure does not advance reliability state.
||- risk_tolerance_signals: unchanged. No live promotion is accepted while native API is unreachable and zero-trade/hypothesis artifacts continue to outnumber passing strategies.
||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. Unreconciled active-card instrument drift persists.
||- intervention_patterns: cycle16 shows blocked native API + recurring subagent import failure coexisting with fresh kanban launches; neutral intervention posture retained — repair sequencing via kanban tickets rather than immediate manual escalation.
||- tags: user, profile, 2026-07-10

<!-- 2026-07-10T18:00:00Z — memory-department sync cycle 17 -->
||- observed_preference: instrument/card reconciliation is expected but has still not been executed after multiple memory entries; orphaned nonzero artifacts on disk are not being promoted or rejected because mapping work is pending. Discovery-driven repair continues, with no manual escalation to fix drift or stale kanban PIDs.
||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. gold_breakout remains hypothesis; smc_* cards remain rejected/hypothesis; live promotion remains blocked by unreachable native API and insufficient verifying artifacts.
||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. Unreconciled active-card instrument drift remains across `02_STRATEGIES/active/` despite repeated cycles.
||- intervention_patterns: unresolved reliability findings and orphaned artifacts persist without explicit manual repair; new kanban launches continue despite unreachable native service and recurring subagent env blockers; pattern is discovery-driven sequencing with filing preferred over immediate escalation.
||- tags: user, profile, 2026-07-10

<!-- 2026-07-10T20:00:00Z — memory-department sync cycle 18 -->
||- observed_preference: kanban in_progress PID updates with new task labels do not constitute progress when the underlying infrastructure blockers remain open; user expects root-cause closure before treating new launches as advancement.
||- risk_tolerance_signals: promotion gate unchanged: WR ≥45%, PF ≥1.15, maxDD ≤4%. Oscillating native API reachability and disputed cached summaries continue to block live promotion.
||- instrument_session_signals: XAUUSD remains primary execution focus; D1/H4/M15 active; BTCUSD evidence-only. Active-card instrument drift persists as an unresolved precondition.
||- intervention_patterns: reliability findings continue to be filed without immediate environment repair; kanban recurrence with identical blocker profiles shows discovery-driven sequencing persists over manual escalation.
||- tags: user, profile, 2026-07-10

<!-- 2026-07-10T20:15:00Z — memory-department sync cycle 19 -->
- observed_preference: new kanban subagent launches are accepted without root-cause closure of prior-cycle blockers; cycle19 records this as expected monitor output, not as resolution. No change to general intervention pattern.
- risk_tolerance_signals: unchanged. Promotion gate remains WR >=45%, PF >=1.15, maxDD <=4%. Live promotion posture remains do_not_trade/watch_only while unresolved disputed artifacts and unstable native service state persist.
- instrument_session_signals: XAUUSD remains primary execution focus on D1/H4/M15; BTCUSD evidence-only. Active-card instrument drift remains unresolved.
- intervention_patterns: discovery-driven repair sequencing and kanban ticket filing continue; no manual escalation observed within this cycle.
- tags: user, profile, 2026-07-10

<!-- 2026-07-10T21:00:00Z — memory-department sync cycle 20 -->
- observed_preference: kanban in_progress PID relaunches without root-cause closure are treated as monitor output, not progress; prior-cycle blockers were never closed yet execution resumed with new PIDs, and user has not manually corrected the stale-kanban pattern. Rule: unresolved infrastructure or environment blockers invalidate new launch evidence until incident_log records closure.
- risk_tolerance_signals: unchanged. Promotion gate remains WR ≥45%, PF ≥1.15, maxDD ≤4%.
- instrument_session_signals: unchanged. XAUUSD primary on D1/H4/M15; BTCUSD evidence-only; active-card instrument drift remains unresolved.
- intervention_patterns: discovery-driven sequencing with kanban ticket filing continues; no manual escalation observed within this cycle.
- tags: user, profile, 2026-07-10

<!-- 2026-07-10T23:59:00Z — memory-department sync cycle 21 -->
- observed_preference: Cypher-28 cached live-history summaries reused across research markdown must not be treated as authoritative when offline-stamped and contradicted by live endpoint; promotion/gating must require fresh derivation from current native probe or explicitly marked cache-only provenance.
- risk_tolerance_signals: unchanged. Promotion gate remains WR ≥45%, PF ≥1.15, maxDD ≤4%. Gold-specific alternative: D1 native claim 87 trades / WR 81.61% / PF 12.91 exists in research pack, but remains blocked by gold_breakout card hypoth status mismatch and live-endpoint contradictions; no relaxed threshold was observed.
- instrument_session_signals: XAUUSD remains primary execution focus on D1/H4/M15; BTCUSD evidence-only. active-card instrument drift persists in 02_STRATEGIES/active without user-driven reconciliation intervention.
- intervention_patterns: same discovery-driven posture continues; no manual escalation for stale kanban PIDs, oscillating native API, or conflicting history caches—repair sequencing remains delegated to kanban/incident-log rather than immediate manual action.
|||- tags: user, profile, 2026-07-10

<!-- 2026-07-11T11:50:00Z — memory-department sync cycle 23 -->
||||- no_new_learning: no risk-tolerance, instrument/session preference, or intervention-pattern changes observed relative to prior cycles; XAUUSD primary execution on D1/H4/M15, BTCUSD evidence-only, promotion gate WR≥45% / PF≥1.15 / maxDD≤4%, discovery-driven repair posture retained, kanban stale-PID pattern persists without manual escalation.
||||- tags: user, profile, 2026-07-11, no-new-learning

<!-- 2026-07-11T21:02:00Z — memory-department sync cycle 27 -->
||- no_new_learning: no risk-tolerance, instrument/session preference, or intervention-pattern changes observed relative to prior cycles; XAUUSD primary execution on D1/H4/M15, BTCUSD evidence-only, promotion gate WR≥45% / PF≥1.15 / maxDD≤4%, discovery-driven repair posture retained, kanban-launched subagent generations with unresolved root causes treated as monitor output not progress, and cycle44/cycle46 math-integrity findings reinforce that cached aggregate backtest metrics must be recomputed from raw ticket evidence before reuse.
||- risk_tolerance_signals: unchanged.
||- instrument_session_signals: unchanged.
||- intervention_patterns: unchanged.
||- tags: user, profile, 2026-07-11, no-new-learning

<!-- 2026-07-11T11:45Z — memory-department sync cycle 24 -->
||- no_new_learning: no risk-tolerance, instrument/session preference, or intervention-pattern changes observed relative to prior cycles; XAUUSD primary execution on D1/H4/M15, BTCUSD evidence-only, promotion gate WR≥45% / PF≥1.15 / maxDD≤4%, discovery-driven repair posture retained, kanban-launched subagent generations with unresolved root causes treated as monitor output not progress.
||- risk_tolerance_signals: unchanged.
||- instrument_session_signals: unchanged.
||- intervention_patterns: unchanged.
||- tags: user, profile, 2026-07-11, no-new-learning

<!-- 2026-07-11T19:00:00Z — memory-department sync cycle 26 -->
||- no_new_learning: no risk-tolerance, instrument/session preference, or intervention-pattern changes observed relative to prior cycles; XAUUSD primary execution on D1/H4/M15, BTCUSD evidence-only, promotion gate WR≥45% / PF≥1.15 / maxDD≤4%, discovery-driven repair posture retained, kanban-launched subagent generations with unresolved root causes treated as monitor output not progress, and cycle37/cycle38 corrections of mistaken dispute clearance reinforce that verification-rule conditional gates take precedence over metric matching alone.
||- risk_tolerance_signals: unchanged.
||- instrument_session_signals: unchanged.
||- intervention_patterns: unchanged.
||- tags: user, profile, 2026-07-11, no-new-learning

<!-- 2026-07-12T01:04:00Z — memory-department sync cycle 29 -->
||- no_new_learning: no risk-tolerance, instrument/session preference, or intervention-pattern changes observed relative to prior cycles; XAUUSD primary execution focus on D1/H4/M15, BTCUSD evidence-only, promotion gate WR≥45% / PF≥1.15 / maxDD≤4%, discovery-driven repair posture retained. New escalation surface: the MT5 execution environment has now been confirmed full-stack unreachable across 6 ports (7779/5559/5560/5561/5562/5563) in consecutive cycles 48 and 50 since at least 2026-07-12T00:24Z, execution subagents launched in kanban generation PIDs 9856/20148/1420 have zero matching live processes and zero deliverables beyond 2026-07-07 manifests, and the identified Python 3.13 / NumPy 2.4.3 environment blocker from incident_log cycle39 remains unclosed. These reliability findings are being filed but have not triggered manual escalation or kanban-state cleanup.
||- risk_tolerance_signals: unchanged. Promotion gate WR ≥45%, PF ≥1.15, maxDD ≤4% remains strict; no live entry permitted while environment is down and all active strategies carry disputed or failed metric status.
||- instrument_session_signals: unchanged. XAUUSD primary execution focus on D1/H4/M15; BTCUSD evidence-only. gold_breakout remains research candidate; no promotion observed.
||- intervention_patterns: unchanged. Discovery-driven repair sequencing via kanban/incident-log filing persists; repeated full-stack reliability findings and environment-blocker escalations have not produced manual intervention or kanban state cleanup within this observation window. Pattern is tolerating multi-cycle open blocker set as expected monitor output.
||- tags: user, profile, 2026-07-12, no-new-learning, full-stack-outage, kanban-stale-state, python-env-blocker
