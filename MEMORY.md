# Memory

Append-only institutional memory for the Hermes trading stack. All entries are dated and attributed.

<!-- 2026-07-07T00:00:00Z — initial bootstrap -->

<!-- 2026-07-07T10:47:44.448867+00:00 — memory-department sync cycle 1 -->
- lesson: On 2026-07-07, candidate-intake finished for gold_breakout, smc_fvg_fill_H4, smc_ob_entry_H4, smc_ob_entry_M15. gold_breakout data-availability-check INCONCLUSIVE because data/market_data/XAUUSD_D1*.json is missing. smc_fvg_fill_H4 trace shows 193 trades, win_rate=0.4456, expectancy_r=0.1565, max_drawdown_pct=16.61, status=rejected. gold_breakout strategy card remained hypothesis while raw artifact exists with 0 trades; reliability marked it UNVERIFIED - disputed. Rule: candidate-intake must verify card status aligns with artifact presence before run-backtest.
- source_departments: [candidate-intake, data-availability-check, reliability-check]
- tags: memory, lesson, 2026-07-07

<!-- 2026-07-07T11:29:00Z — memory-department sync cycle 2 -->
- lesson: On 2026-07-07, reliability found gold_breakout in hypothesis while data/rnd/results/gold_breakout.json artifact exists with total_trades=0, indicating a hypothesis/artifacts mismatch that must not be treated as verified. Parallel raw trace local_smc_fvg_fill_M15_trace.json produced 193 trades with win_rate=0.4456, expectancy_r=0.1565, max_drawdown_pct=16.61, profit_factor=1.29 and failed win_rate/expectancy/max_dd gates; artifact notes attribute failure to missing killzone filter and wider OB-based SL. Rule: candidate-intake must check for real non-zero metrics and gate results, not just artifact file presence, before any promotion.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, 2026-07-07

<!-- 2026-07-07T13:15:00Z — memory-department sync cycle 3 -->
- lesson: Cross-department reconciliation shows card-claim text drifting from raw artifacts in two ways: gold_breakout.md claims "No backtest results this session" while data/rnd/results/gold_breakout.json exists with total_trades=0 and expected zero metrics; smc_fvg_fill_H4.md tags instrument=BTCUSD while raw artifact desk2_smc_fvg_fill_H4_1783288880537064000.json contains symbol=XAUUSD. Cycle4 incident log initially misclassified card as UNVERIFIED disputed because of claim mismatch, then later runs confirmed artifact values matched cited metrics. Rule: raw artifact is canonical; card text, tags, and claim fields must be reconciled before analysis because evidence drift turns rejected/hypothesis cards into false disputed findings.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, canonical-artifacts, evidence-drift, reconciliation, 2026-07-07

<!-- 2026-07-07T18:05:00Z — memory-department sync cycle 4 -->
- lesson: Reliability cycle 4-8 repeatedly observed that gold_breakout remained labeled `hypothesis` while data/rnd/results/gold_breakout.json existed as a zero-trade backtest artifact; card text claiming "No backtest results this session" should be treated as UX wording only and raw JSON as canonical evidence. Rule: for strategy status changes, authority priority is raw Artifact JSON > reliability incident_log > active card markdown; zero-trade artifacts are real evidence and must trigger `backtested_rejected` wording or documented data-path blocker, not unresolved hypothesis.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, gold_breakout, canonical-artifacts, 2026-07-07

<!-- 2026-07-07T22:33:00Z — memory-department sync cycle 6 -->
- lesson: Reliability cycle 17 found all native MT5 endpoints on 7779 unreachable with HTTP=000/connection refused, yet prior cached deep-review numbers were still being treated as live quotes in 05_RND notes. In the same run, direct JSON artifacts remained canonical for non-live evidence, and correlation-based live claims should be treated as no_evidence until refreshed. Rule: if the service is unreachable this run, all live history/account/positions claims are cache-only and must be annotated with archive run time or no_evidence, not reused as current state.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, service-state, cache-only, no-evidence, 2026-07-07

<!-- 2026-07-08T00:00:00Z — memory-department sync cycle 7 -->
- lesson: After 2026-07-08 deep-research review, 05_RND/2026-07-08_scan_deep_research.md cites files that do not exist on disk: data/rnd/xau_native_strategy_pack.json, data/rnd/xau_native_backtest_matrix_m15_d1.json, data/rnd/xau_strategy_backtest_metrics.json. This is a recurrence of evidence drift, but worse: incident_log cycle20 already proved native endpoints are reachable with fresh live evidence, yet analyst note still relies on cached deep-review 30d summaries that were contested/corrected in the same run. Rule: service-state is not enough — every cited metric must be independently rerun against live current evidence if freshness is claimed; otherwise tag claim as cache-only with exact archive run timestamp.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, evidence-drift, stale-cache, 2026-07-08

<!-- 2026-07-08T12:50:00Z — memory-department sync cycle 8 -->
- lesson: Across cycles 22–26, gold_breakout remained tagged `hypothesis` despite a zero-trade raw artifact `data/rnd/results/gold_breakout.json` on disk; the card text is UX wording, not canonical status. In the same span, native MT5 service toggled from reachable to flat EXIT=7/connection refused and back in consecutive cycles without explanatory repair. Rule: for status arbitration use raw artifact metrics first, service reachability second; repeated connectivity oscillation should be logged as a distinct reliability blocker, not treated as transient noise that clears disputed flags.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, gold_breakout, service-oscillation, canonical-artifacts, 2026-07-08

<!-- 2026-07-08T12:55:00Z — memory-department sync cycle 9 -->
- lesson: Reliability cycles 29–30 found that the native /history endpoint returns mutable underlying datasets across consecutive live probes: 52 deals -> 56 deals within the same 30-day window, causing paired-trade recomputes to shift from -929.77 USD to -6256.69 USD and then +3079.96 USD in the following run. Exact numeric summaries cached in analyst notes or prior reliability cycles cannot be reused unless rerun from the current payload. Rule: whenever native endpoints are reachable, all cited exact history/account metrics must be recomputed from the fresh endpoint response in the same cycle; cached exact values are no_evidence/reuse-disputed by default.
- source_departments: [reliability, backtester, execution]
- tags: memory, lesson, native-history-mutation, cache-dispute, live-recompute-required, 2026-07-08

<!-- 2026-07-08T15:06:00Z — memory-department sync cycle 10 -->
|- lesson: Reliability cycle34 found active strategy cards instrument-drifted against raw artifacts: smc_fvg_fill_H4, smc_ob_entry_M15, smc_ob_entry_H4 markdown fields instrument=BTCUSD while local skills_subagent_* and desk2 artifacts point to XAUUSD. This turns real backtested_rejected outcomes into metadata-disputed findings and prevents safe promotion reviews. Rule: before any promotion/dispute arbitration, enforce exact reconciliation of active card frontmatter `instrument` against raw artifact `symbol` or path metadata; mismatches must be fixed or segregated before accepting claims as disputed/promotion-ready.
|- source_departments: [reliability, backtester, execution]
|- tags: memory, lesson, 2026-07-08, instrument-mismatch, canonical-artifacts

<!-- 2026-07-08T15:06:00Z — memory-department sync cycle 11 -->
|- lesson: Cycle34 confirmed that exact native /history recomputes diverge by pairing methodology even on the same raw payload: cycle30/cycle33 ticket-level pairing returned +3079.96 USD / 14.29% WR / MDD=2114.00 USD while cycle34 position_id aggregation returned -2416.69 USD / 50% WR / MDD=-6885 USD. Rule: once service state or pairing methodology changes, every previously cited exact history/account metric is automatically no_evidence/reuse-disputed until rerun from the current payload in the same cycle.
|- source_departments: [reliability, backtester, execution]
|- tags: memory, lesson, 2026-07-08, native-history-pairing, cache-dispute

<!-- 2026-07-08T22:10:00Z — cron market-study 2026-07-08 London sync -->
|- lesson: On 2026-07-08 London session, verified cached SMC scan from 14:16 UTC showed BEARISH structure with swing high 4131.51 and swing low 4050.00; subsequent live_feed analysis through 11:20 UTC confirmed bearish CHoCH at 11:15 M15 close, impulsive drop from 4131.51 through 4121/4116 equal lows to 4080.64 SSL sweep. Key structural artifacts: unfilled bearish FVG 4116.33-4125.09, unfilled premium FVG 4132-4154, bullish OB 4078.55-4087.07 formed during SSL sweep recovery, bearish OB 4132.63-4133.76 unmitigated. Rule: for cron-driven studies, use cached SMC scan geometry as anchor and live_feed.jsonl for freshness gating; when >20 M15 bars stale, downgrade claims to no_evidence.
|- source_departments: [market-study-cron, execution]
|- tags: memory, lesson, 2026-07-08, xauusd, smc-structure, choch, ssl-sweep, fvg

<!-- 2026-07-09T09:30:00Z — memory-department sync cycle 13 -->
||- lesson: On 2026-07-09, kanban board shows 3 in_progress subagent tasks tagged `launched` with PIDs (2952, 2096, 17920), but raw logs for all three show fatal `ImportError: Unable to import required dependency numpy` / pandas chain failure before any analysis ran. Outcome manifests in `data/run/outcomes/` remain in `ready` state with no completion evidence. Reliability already logged this exact failure mode in three incident_log entries on the same date tied to numpy/pandas import failure under Python 3.13. Rule: board state `launched` + PID count is necessary but NOT sufficient evidence of successful execution; reliability must verify live process health and successful numpy/pandas import under the exact runtime version before accepting any backtest/job deliverable as completed. Do not reset stale kanban PIDs or clear `in_progress` flags based solely on manifest status.
||- source_departments: [execution, backtester, reliability]
||- tags: memory, lesson, 2026-07-09, kanban, subagent, numpy, cpython-mismatch, venv

<!-- 2026-07-09T14:05:00Z — memory-department sync cycle 14 -->
||- lesson: On 2026-07-09, execution department launched a new kanban generation of 3 subagent tasks with PIDs 2952, 2096, 17920; this repeats the exact numpy/pandas cp311-vs-Python3.13 preflight failure already logged in prior cycles with different PIDs. Outcome manifests remain ready state without completion markers, and reliability has not yet added a cycle-specific incident_log entry for these new PIDs. Rule: recurring env preflight failure across kanban generations is a structural blocker, not a transient issue; every new launch generation must be treated as disputed until clean logs with successful imports are produced. Do not clear in_progress or disputes based on manifest readiness alone.
||- source_departments: [execution, backtester, reliability]
||- tags: memory, lesson, 2026-07-09, kanban, subagent, numpy, cpython-mismatch, venv, recurring-blocker

<!-- 2026-07-10T00:00:00Z — memory-department sync cycle 15 -->
|- lesson: On 2026-07-10, new journaled/local FVG-style artifacts appear on disk, but no active strategy card maps them as promotion-ready; prior reliability disputes for trading-stats/history pairing and subagent env blockers are still open. Rule: new small or journaled artifacts are monitor-only evidence until sample size is sufficient, metadata reconciles to an active card, and earlier history/dispute findings are resolved; they do not alone unlock a promotion gate.
|- source_departments: [backtester, execution, reliability]
|- tags: memory, lesson, 2026-07-10, artifact-mapping, sample-size, unresolved-disputes

<!-- 2026-07-10T12:00:00Z — memory-department sync cycle 16 -->
|- lesson: On 2026-07-10, kanban shows 3 new in_progress subagent tasks (PIDs 2952, 2096, 17920) launched while incident_log flags native MT5 API on 7779 unreachable (`000FAIL`) and prior-cycle identical subagent generations failed on `ImportError: Unable to import required dependency numpy` under cp311 vs Python 3.13. Repeating the launch pattern under the same unresolved infrastructure blocker treats recurrence as progress. Rule: before launching a new kanban subagent generation, verify the basic runtime import path under the deployed Python version and confirm native service reachability; if either blocker is unresolved, do not launch until the prior cycle's root cause is closed and annotated in incident_log.
|- source_departments: [execution, backtester, reliability]
|- tags: memory, lesson, 2026-07-10, native-api-unreachable, subagent-launch-blocker, cp311-cpython13, kanban-recurrence

<!-- 2026-07-10T18:00:00Z — memory-department sync cycle 17 -->
|- lesson: On 2026-07-10, new raw artifact `data/rnd/results/skills_subagent_order_block_m15.json` exists with 2186 trades, win_rate=27.08%, profit_factor=0.6162, net_profit=-9997.5, and trade prices around 1224-1240 consistent with historical XAUUSD; however active card `smc_ob_entry_M15.md` still cites instrument=BTCUSD with stale Desk 2 metrics (52 trades, 15.38% WR). This means a new nonzero artifact is orphaned and the active card's metrics are unreconciled. Rule: whenever an on-disk raw artifact filename/scope matches an active strategy card, the card must be reconciled to the artifact or the artifact explicitly marked orphan; orphaned nonzero artifacts do not count as promotion evidence until mapped, and worn card metrics must not be reused while newer raw files are ignored.
|- source_departments: [backtester, execution, reliability]
|- tags: memory, lesson, 2026-07-10, orphaned-artifact, evidence-drift, canonical-artifacts, smc_ob_entry_M15

<!-- 2026-07-10T20:00:00Z — memory-department sync cycle 18 -->
|- lesson: On 2026-07-10 evening cycle, kanban showed 3 new in_progress subagent tasks with PIDs 19116/10316/12112, but task definitions repeat prior execution/backtest/pattern studies already blocked by oscillating native API reachability and recurring Python 3.13 import failures; new PIDs are necessary but not sufficient evidence of progress. In the same run, `data/rnd/results/skills_subagent_order_block_m15.json` appeared with 2186 trades, WR 27.08%, PF 0.6162, net -9997.5, yet active card `smc_ob_entry_M15.md` still cites instrument=BTCUSD and stale 52-trade metrics. Rule: before treating kanban in_progress as live progress, verify root-cause closure for native reachability and Python env blockers in incident_log; orphaned nonzero artifacts remain monitor-only until active cards are reconciled.
|- source_departments: [execution, backtester, reliability]
|- tags: memory, lesson, 2026-07-10, orphaned-artifact, instrument-drift, kanban-pid, subagent-blocker

<!-- 2026-07-10T20:15:00Z — memory-department sync cycle 19 -->
- lesson: On 2026-07-10 latest kanban state, 3 new execution subagent tasks are `launched` with PIDs 19116/10316/12112, but incident_log already records identical unresolved blockers: native :7779 reachability oscillates across cycles, cached 30-day live-history summaries are stale/disputed, prior subagent generations failed on `ImportError`/numpy-pandas under Python 3.13, and orphaned artifacts remain unreconciled to active cards. Rule: new kanban PID counts alone are not evidence of progress when the same root causes are still open; cycle19 marks this launch set as `launched - disputed` until incident_log closes the native/reachability and env blockers and a completed deliverable appears on disk.
- source_departments: [execution, backtester, reliability]
- tags: memory, lesson, 2026-07-10, kanban-recurrence, disputed-launch, native-oscillation, env-blocker

<!-- 2026-07-10T21:00:00Z — memory-department sync cycle 20 -->
- lesson: On 20206-07-10 latest kanban state, execution again lists 3 in_progress subagent tasks (PIDs 17928/9440/6504) after kanban replaced prior generation, but this cron run's direct OS process check returned NO_SUCH_PROCESSES for all three. Prior cycle's Finding 18 was never closed in incident_log, and the new PIDs are repeating the exact same unresolved blockers: oscillating native :7779 reachability, offline-stamped cached live-history summaries still reused in research notes, and recurring Python 3.13 numpy/pandas import failures in subagent logs. Rule: do not accept kanban in_progress as evidence of execution progress when the root-cause blocker set from the prior generation remains open; each new PID generation without incident_log closure is `UNVERIFIED - disputed` until a clean run emits verified deliverables.
- source_departments: [execution, backtester, reliability]
- tags: memory, lesson, 2026-07-10, kanban-pid, subagent-launch, disputed-blocker, no-live-process, evidence-gap

<!-- 2026-07-10T23:59:00Z — memory-department sync cycle 21 -->
- lesson: On 2026-07-10 Cycle25, cache inconsistency within the same history artifact family became blocking evidence for promotion: offline-stamped `xau_backtest_update_latest.json` and `xau_native_strategy_pack.json` report 28 paired trades / `net_pnl=-2416.69` / WR 50.00%, while `native_history_30d_xauusd.json` shows 33 tickets forming 16 closed pairs / `pnl=-2228.88` / WR 68.75%, and the live `/history?days=30&instrument=XAUUSD` endpoint returned 52 deals with sum pnl `-1997.58`. None of these three raw sources agree. Rule: if cached history artifacts disagree with each other and with the current live endpoint, promote gating from all of them is blocked; require one authoritative derivation trace with explicit pairing methodology and source provenance before accepting any exact history/account metric for promotion decisions.
- source_departments: [backtester, execution, reliability]
|- tags: memory, lesson, 2026-07-10, cache-consistency, history-pairing, promotion-gate, provenance

<!-- 2026-07-11T09:00:00Z — memory-department sync cycle 22 -->
||- lesson: Cycle-28 confirmed kanban-launched subagent generations repeating identical unresolved blockers is structural evidence of failure, not progress: 3 execution subagents reported in_progress with PIDs 17928/9440/6504, but no live processes or `data/run/outcomes/` deliverables date beyond 2026-07-07 and prior-cycle identical blockers (native :7779 oscillating reachability, Python 3.13 numpy/pandas import failures, cached live-history reuse) were never closed in incident_log. Rule: mark every new kanban subagent generation `launched - disputed` until incident_log records closure of root causes and verified deliverables appear on disk; PID count alone is not execution progress.
||- source_departments: [reliability, execution, backtester]
||- tags: memory, lesson, 2026-07-11, kanban-recurrence, subagent-launch-blocker, live-process-verification, disputed-progress

<!-- 2026-07-11T11:50:00Z — memory-department sync cycle 23 -->
||- lesson: Cycles 28–32 reconfirmed the same kanban subagent dispute (3 in_progress tasks with PIDs 17928/9440/6504, zero live processes, zero deliverables beyond 2026-07-07 manifests) without any kanban state cleanup; `/api/native/smc_analysis?instrument=XAUUSD&timeframe=M15&n=200` returned HTTP 404 in cycle32 as well, and incident_log keeps restating the expectation as `no_evidence` rather than escalating to an open owner action. Rule: stale kanban in_progress entries that remain disputed for 4+ consecutive cycles without root-cause closure or cleaned manifests become noise that pollutes every subsequent cycle's inputs; endpoints with sustained 404/no_evidence across multiple cycles must be reclassified from monitoring nuance to an explicit infrastructure blocker with owner action, otherwise live SMC forward-validation remains permanently unavailable.
||- source_departments: [reliability, execution, backtester]
||- tags: memory, lesson, 2026-07-11, kanban-stale-state, infrastructure-blocker, smc-analysis-404, disputed-progress

<!-- 2026-07-11T11:45Z — memory-department sync cycle 24 -->
|- lesson: Incident_log cycle36 shows kanban recurrence with new execution subagent PIDs 9756/13804/17564 tagged launched/in_progress while prior generation's root-cause set remains open in incident_log (native :7779 oscillating, nightly_scan argparse broken, incomplete deliverables), and no matching live OS processes were found; history endpoint mutation also recurred — cycles22-24 saw 52 deals/26 paired trades/sum=-929.77 USD while cycle36 live `/api/native/history?days=30&instrument=XAUUSD` returned 8 tickets representing 4 closed positions and live recompute net PnL -3415.00 USD / 0% WR. Rule: new kanban PID generation without incident_log root-cause closure must be marked `launched - disputed`; every cited exact history/account/position metric must be recomputed from the current live endpoint response in the same cycle because the underlying dataset mutated across consecutive probes.
|- source_departments: [reliability, execution, backtester]
|- tags: memory, lesson, 2026-07-11, kanban-recurrence, history-mutation, disputed-launch, no-live-process

<!-- 2026-07-11T10:10:00Z — memory-department sync cycle 25 -->
||- lesson: Incident_log cycle38 overruled an incorrect dispute clearance from cycle36 for `smc_fvg_fill_H4`: cycle36 had ruled 'confirmed' because cited metrics matched the raw artifact, but verification-rules.md mandates `status=hypothesis + nonzero valid metrics => always-dispute`. Cycle38 reinstated the dispute and corrected the prior clearance. Rule: metric matching is necessary but NOT sufficient for clearing a reliability dispute; verification-rule conditional gates (status tags, sample-size minimums, instrument reconciliation) must be evaluated first, and any incorrect clearance must be overruled in subsequent cycles to prevent false 'confirmed' states from entering promotion audits.
||- source_departments: [reliability, backtester, execution]
||- tags: memory, lesson, 2026-07-11, verification-rules, dispute-clearance, procedure-over-metrics

<!-- 2026-07-11T19:00:00Z — memory-department sync cycle 26 -->
||- lesson: Cycle 39 identified the exact subagent crash root cause: all three execution subagent logs terminate with `ModuleNotFoundError: No module named 'numpy._core._multiarray_umath'` because NumPy 2.4.3's compiled extension exists as `_multiarray_umath.cp311-win_amd64.pyd` while active runtime is Python 3.13. Despite this precise identification in incident_log, cycle 43 kanban still shows 3 new in_progress tasks with PIDs 9856/20148/1420 while `ps` confirms no matching live processes and `data/run/outcomes/` contains zero deliverables beyond 2026-07-07 manifests; kanban `detail=running` also contradicts manifest `status=ready`. Rule: an incident_log root-cause finding with exact module/path mismatch is necessary but NOT sufficient to stop recurrence; execution must validate the import path under the deployed Python version and confirm live processes exist before treating new kanban generations as progress. Three-way state inconsistency (kanban detail vs manifest status vs process table) is itself a reliability finding and must trigger state cleanup, not just dispute tagging.
||- source_departments: [reliability, execution, backtester]
||- tags: memory, lesson, 2026-07-11, python-numpy-mismatch, kanban-recurrence, state-contradiction, subagent-blocker

<!-- 2026-07-11T21:02:00Z — memory-department sync cycle 27 -->
||- lesson: Cycle 44 found silent aggregate math drift inside `data/rnd/xau_native_strategy_pack_backtest_2026-07-11.json`: the embedded `pairs` array (P&Ls -756.0, -683.5, -796.0, -1179.5) sums to exactly -3415.00 USD with average -853.75 USD, but the JSON header claims `net_pnl_usd=-3425.04` and `average_loss_usd=-856.26`. The same cycle also found a source-level contradiction: `gold_breakout_d1_2020_plus` is cited as 87 trades / 81.61% WR / PF 12.91 in one strategy-pack artifact but 66 trades / 53.03% WR / PF 2.04 in another. Both are mathematical and cross-source contradictions within the strategy-pack JSON family that were being reused as canonical evidence. Rule: whenever a backtest JSON artifact contains both raw ticket/position paylists and precomputed aggregate headers, independently recompute all aggregates from the raw list before citing them; treat JSON files from the same strategy family as single-source-of-truth only when exact cross-file agreement is confirmed, otherwise mark them `cache-disputed` and trace to the producing endpoint.
||- source_departments: [reliability, backtester, execution]
||- tags: memory, lesson, 2026-07-11, math-integrity, aggregate-drift, strategy-pack, cache-disputed

<!-- 2026-07-12T00:00:00Z — memory-department sync cycle 28 -->
||- lesson: On 2026-07-12, kanban state.json shows 3 execution subagents in_progress with PIDs 9856/20148/1420 tagged `running`, but direct OS process inspection confirms no matching processes exist, and subagent logs for the current generation terminate with ModuleNotFoundError: No module named 'numpy._core._multiarray_umath' because NumPy 2.4.3's compiled extension is built for CPython 3.11 while the active runtime is Python 3.13. Cycle39 had already identified this exact module/path mismatch, yet cycle48/cycle50 kanban reused the same PIDs and implied completion via manifest status=ready while delivering zero files. Rule: identifying the exact Python/NumPy environment mismatch in incident_log is necessary but NOT sufficient to prevent kanban launch recurrence; before treating any new kanban generation as progress, execution must verify the import path under the deployed Python version and confirm live processes exist. Kanban entries where manifest status disagrees with process table are direct reliability contradictions and require state cleanup, not just dispute tagging.
||- source_departments: [reliability, execution, backtester]
||- tags: memory, lesson, 2026-07-12, python-numpy-mismatch, kanban-stale-state, cross-artifact-contradiction

<!-- 2026-07-12T01:04:00Z — memory-department sync cycle 29 -->
||- lesson: Cycles 48 and 50 (2026-07-12T00:24Z and 2026-07-12T01:04Z) both document the MT5 execution environment in a confirmed stable full-stack outage: all six ports (7779, 5559, 5560, 5561, 5562, 5563) return HTTP=000/connection refused simultaneously. This is no longer intermittent connectivity oscillation — it is stable full-stack unavailability persisting across multiple consecutive cycles with zero recovery. The same kanban generation (PIDs 9856/20148/1420, launched 2026-07-11T11:46Z) remains tagged `in_progress` with `detail=running` despite zero live processes and zero deliverables beyond dated stubs, and the identified Python 3.13 / NumPy 2.4.3 compiled-extension mismatch in incident_log cycle39 has not been remediated. Rule: when service reachability transitions from intermittent oscillation to stable full-stack outage and the identified root cause remains uncleared for >12 hours, the execution department is in confirmed unrecoverable state, not transient degradation. Every new kanban launch generation under the same unclosed blocker set must be treated as `launched - disputed`; no-deliverable kanban entries older than one cycle require automatic state cleanup, not perpetual dispute tagging.
||- source_departments: [reliability, execution, backtester]
||- tags: memory, lesson, 2026-07-12, full-stack-outage, execution-unrecoverable, kanban-state-cleanup-required, no-live-service

<!-- 2026-07-11T21:02:00Z — memory-department sync cycle 27 -->
|- lesson: Cycle 44 found silent aggregate math drift inside `data/rnd/xau_native_strategy_pack_backtest_2026-07-11.json`: the embedded `pairs` array (P&Ls -756.0, -683.5, -796.0, -1179.5) sums to exactly -3415.00 USD with average -853.75 USD, but the JSON header claims `net_pnl_usd=-3425.04` and `average_loss_usd=-856.26`. The same cycle also found a source-level contradiction: `gold_breakout_d1_2020_plus` is cited as 87 trades / 81.61% WR / PF 12.91 in one strategy-pack artifact but 66 trades / 53.03% WR / PF 2.04 in another. Both are mathematical and cross-source contradictions within the strategy-pack JSON family that were being reused as canonical evidence. Rule: whenever a backtest JSON artifact contains both raw ticket/position paylists and precomputed aggregate headers, independently recompute all aggregates from the raw list before citing them; treat JSON files from the same strategy family as single-source-of-truth only when exact cross-file agreement is confirmed, otherwise mark them `cache-disputed` and trace to the producing endpoint.
|- source_departments: [reliability, backtester, execution]
|- tags: memory, lesson, 2026-07-11, math-integrity, aggregate-drift, strategy-pack, cache-disputed

<!-- 2026-07-12T00:00:00Z — memory-department sync cycle 28 -->
|- lesson: On 2026-07-12, kanban state.json shows 3 execution subagents in_progress with PIDs 9856/20148/1420 tagged `running`, but direct OS process inspection confirms no matching processes exist, and subagent logs for the current generation terminate with ModuleNotFoundError: No module named 'numpy._core._multiarray_umath' because NumPy 2.4.3's compiled extension is built for CPython 3.11 while the active runtime is Python 3.13. Cycle39 had already identified this exact module/path mismatch, yet cycle48/cycle50 kanban reused the same PIDs and implied completion via manifest status=ready while delivering zero files. Rule: identifying the exact Python/NumPy environment mismatch in incident_log is necessary but NOT sufficient to prevent kanban launch recurrence; before treating any new kanban generation as progress, execution must verify the import path under the deployed Python version and confirm live processes exist. Kanban entries where manifest status disagrees with process table are direct reliability contradictions and require state cleanup, not just dispute tagging.
|- source_departments: [reliability, execution, backtester]
|- tags: memory, lesson, 2026-07-12, python-numpy-mismatch, kanban-stale-state, cross-artifact-contradiction
