//+------------------------------------------------------------------+
//|                                            RiskModule.mqh         |
//|                       Hermes Risk + Perfect OB Filter            |
//+------------------------------------------------------------------+
#ifndef RiskModule_mqh
#define RiskModule_mqh

#include <Trade/Trade.mqh>

struct TradePlan
{
   string   instruction_id;
   datetime signal_time;
   string   symbol;
   bool     is_buy;
   double   entry_price;
   double   sl;
   double   tp;
   double   lots;
};

// 1% risk rule
double RiskMaxPerTrade(double balance)
{
   return MathMax(0.01, balance * 0.01);
}

// Lot size from pips risk and instrument point value
double CalculateLots(double balance, double sl_pips, double pip_value, double min_lot=0.01, double max_lot=5.0)
{
   if(sl_pips <= 0 || pip_value <= 0) return min_lot;
   double risk_dollars = RiskMaxPerTrade(balance);
   double money_per_pip = pip_value;
   double lots = risk_dollars / (sl_pips * money_per_pip);
   lots = MathMax(min_lot, MathMin(max_lot, lots));
   double step = 0.01;
   lots = MathFloor(lots/step)*step;
   if(lots < min_lot) lots = min_lot;
   return lots;
}

// Perfect OB scoring 0..6
int ScoreOrderBlock(double ob_high, double ob_low, bool bullish,
                   const double fib_618, const double fib_786,
                   bool displacement_clean,
                   bool unmitigated,
                   bool liquidity_sweep_before,
                   bool clean_structure,
                   bool ob_impulse_caused_bos)
{
   int score = 0;
   double mid = (ob_high+ob_low)/2.0;
   if(displacement_clean) score++;
   if(unmitigated) score++;
   if(liquidity_sweep_before) score++;
   if(fib_618 != 0.0 && fib_786 != 0.0 && mid <= MathMax(fib_618,fib_786) && mid >= MathMin(fib_618,fib_786))
      score++;
   if(clean_structure) score++;
   if(ob_impulse_caused_bos) score++;
   return score;
}

// Place limit order at OB wick with filters
void PlaceSniperLimit(CTrade &trade, const TradePlan &plan, int magic)
{
   trade.SetExpertMagicNumber(magic);
   trade.SetDeviationInPoints(10);
   if(plan.is_buy)
   {
      double bid = SymbolInfoDouble(plan.symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(plan.symbol, SYMBOL_ASK);
      double entry = MathMin(plan.entry_price, ask);
      if(!trade.BuyLimit(plan.lots, entry, plan.symbol, plan.sl, plan.tp, "HERMES"))
      {
         Print("[!] BuyLimit failed: ", GetLastError(), " ", trade.ResultRetcodeDescription());
      }
   }
   else
   {
      double bid = SymbolInfoDouble(plan.symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(plan.symbol, SYMBOL_ASK);
      double entry = MathMax(plan.entry_price, bid);
      if(!trade.SellLimit(plan.lots, entry, plan.symbol, plan.sl, plan.tp, "HERMES"))
      {
         Print("[!] SellLimit failed: ", GetLastError(), " ", trade.ResultRetcodeDescription());
      }
   }
}

#endif
