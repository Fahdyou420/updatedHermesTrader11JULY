import { useEffect, useState } from "react";

type Trade = {
  id: string;
  timestamp: string;
  direction: string;
  volume: number;
  entry_price: number;
  close_price: number;
  pnl: number;
};

type StrategyCard = {
  id: string;
  name: string;
  timeframe: string;
  status: string;
  instrument: string;
};

type TradeStats = {
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  net_profit: number;
  expectancy_r: number;
  max_drawdown_percent: number;
  max_dd_pct: number;
  profit_factor: number;
};

type TradeMonitorProps = {
  metrics?: any;
  activeTrades?: Trade[];
  closedTrades?: Trade[];
  balance?: number;
  equity?: number;
  dailyDD?: number;
  weeklyDD?: number;
  onPlaceTrade?: (params: any) => Promise<any>;
  onCloseTrade?: (id: string) => Promise<any>;
};

export default function TradeMonitor({
  metrics,
  activeTrades = [],
  closedTrades = [],
  balance = 0,
  equity = 0,
  dailyDD = 0,
  weeklyDD = 0,
  onPlaceTrade,
  onCloseTrade
}: TradeMonitorProps) {
  const [strategies, setStrategies] = useState<StrategyCard[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [s, st] = await Promise.all([
          fetch("/api/strategies").then((r) => r.json()).catch(() => []),
          fetch("/api/trades/stats").then((r) => r.json()).catch(() => null)
        ]);
        if (cancelled) return;
        setStrategies(Array.isArray(s) ? s : []);
        if (st) setStats(st);
      } catch (e: any) {
        if (!cancelled) setError(e.message || "Failed to load strategies/stats");
      }
    }
    load();
    const id = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const allTrades = [...activeTrades, ...closedTrades];
  const closedList = closedTrades.map((t) => ({
    ...t,
    pnl:
      t.pnl ||
      (t.close_price && t.entry_price
        ? t.direction.toLowerCase().includes("buy")
          ? t.close_price - t.entry_price
          : t.entry_price - t.close_price
        : 0) * t.volume
  }));

  const winRate = stats?.win_rate ?? 0;
  const netPnl = stats?.net_profit ?? closedList.reduce((sum, t) => sum + (t.pnl || 0), 0);
  const expectancy = stats?.expectancy_r ?? 0;
  const profitFactor = stats?.profit_factor ?? 1.0;
  const maxDD = stats?.max_drawdown_percent ?? stats?.max_dd_pct ?? dailyDD;

  return (
    <div className="rounded-2xl border border-white/5 bg-slate-900/40 p-4 shadow-lg shadow-black/20">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-white/80">Trade Desk</h2>
        <span className="text-xs text-white/60">auto-refresh 5s</span>
      </div>

      {error ? (
        <div className="mb-3 rounded-lg border border-red-400/30 bg-red-500/10 p-2 text-xs text-red-200">
          {error}
        </div>
      ) : null}

      <div className="mb-4 grid grid-cols-3 gap-2">
        <Stat label="Win Rate" value={`${(winRate * 100).toFixed(1)}%`} />
        <Stat label="Net PnL" value={netPnl.toFixed(2)} />
        <Stat label="Expectancy" value={expectancy.toFixed(2)} />
        <Stat label="Profit Factor" value={profitFactor.toFixed(2)} />
        <Stat label="Max DD %" value={maxDD.toFixed(2)} />
        <Stat label="Trades" value={`${closedList.length} / ${allTrades.length}`} />
      </div>

      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-wider text-white/60">Strategies</h3>
        <span className="text-[10px] uppercase tracking-wider text-white/40">
          {strategies.length} cards
        </span>
      </div>
      <div className="mb-3 flex max-h-28 flex-wrap gap-1 overflow-y-auto">
        {strategies.length === 0 ? (
          <div className="text-xs text-white/50">No strategy cards yet.</div>
        ) : (
          strategies.map((s, idx) => (
            <div
              key={s.id || s.name || idx}
              className="rounded-lg border border-white/5 bg-slate-900/40 px-2 py-1"
            >
              <div className="text-[11px] font-semibold text-white/80">{s.name}</div>
              <div className="text-[10px] text-white/60">
                {s.timeframe} · {s.instrument} · {s.status}
              </div>
            </div>
          ))
        )}
      </div>

      <div className="flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-wider text-white/60">All Trades</h3>
        <span className="text-[10px] uppercase tracking-wider text-white/40">
          {closedList.length} closed
        </span>
      </div>
      <div className="mt-1 max-h-72 overflow-y-auto">
        <table className="w-full table-auto text-left text-xs">
          <thead>
            <tr className="border-b border-white/5">
              <th className="py-1 pr-2 text-white/60">ID</th>
              <th className="py-1 pr-2 text-white/60">Time</th>
              <th className="py-1 pr-2 text-white/60">Side</th>
              <th className="py-1 pr-2 text-right text-white/60">Entry</th>
              <th className="py-1 pr-2 text-right text-white/60">Close</th>
              <th className="py-1 text-right text-white/60">PnL</th>
            </tr>
          </thead>
          <tbody>
            {allTrades.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-2 text-center text-white/40">
                  No trades.
                </td>
              </tr>
            ) : (
              allTrades.map((t) => {
                const display = closedList.find((c) => c.id === t.id) || t;
                const isWin = (display.pnl || 0) > 0;
                return (
                  <tr key={t.id} className="border-b border-white/5">
                    <td className="py-1 pr-2 text-white/80 font-mono">{t.id}</td>
                    <td className="py-1 pr-2 text-white/60">
                      {t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : "-"}
                    </td>
                    <td className="py-1 pr-2 text-white/80">{t.direction}</td>
                    <td className="py-1 pr-2 text-right text-white/70 font-mono">
                      {t.entry_price.toFixed(2)}
                    </td>
                    <td className="py-1 pr-2 text-right text-white/70 font-mono">
                      {t.close_price.toFixed(2)}
                    </td>
                    <td className={`py-1 text-right font-mono ${isWin ? "text-emerald-300" : "text-red-300"}`}>
                      {(display.pnl || 0).toFixed(2)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/5 bg-slate-900/50 p-2">
      <div className="text-[10px] uppercase tracking-widest text-white/50">{label}</div>
      <div className="text-sm font-semibold text-white/90">{value}</div>
    </div>
  );
}
