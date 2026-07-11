//+------------------------------------------------------------------+
//|                                         TradeJournal.mqh         |
//|                        Appends trade and equity events to disk  |
//+------------------------------------------------------------------+
#ifndef TradeJournal_mqh
#define TradeJournal_mqh

void EnsureJournalDir()
{
   string dir = TerminalInfoString(TERMINAL_DATA_PATH) + "/MQL5/Files/hermes_journal";
   FolderCreate(dir);
}

string GetJournalPath()
{
   EnsureJournalDir();
   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now,dt);
   string day = StringFormat("%04d-%02d-%02d",dt.year,dt.mon,dt.day);
   return TerminalInfoString(TERMINAL_DATA_PATH)+"/MQL5/Files/hermes_journal/trades_"+day+".csv";
}

void AppendJournalRow(string row)
{
   int h = FileOpen(GetJournalPath(),FILE_CSV|FILE_READ|FILE_WRITE|FILE_ANSI);
   if(h==INVALID_HANDLE)
   {
      h = FileOpen(GetJournalPath(),FILE_CSV|FILE_WRITE|FILE_ANSI);
      if(h==INVALID_HANDLE){Print("[!] Journal file open error: ",GetLastError());return;}
      FileWrite(h,"time,zone,ticket,side,open,sl,tp,close,profit,result");
   }
   FileSeek(h,0,SEEK_END);
   FileWrite(h,row);
   FileClose(h);
}

void LogTradeOpen(string ticket, string side, double entry, double sl, double tp)
{
   AppendJournalRow(StringFormat("%s,%s,%s,%s,%.5f,%.5f,%.5f,0,0,PENDING",TimeToString(TimeCurrent()),g_instrument, ticket, side, entry, sl, tp));
}

void LogTradeClose(string ticket, double exit_price, double profit)
{
   AppendJournalRow(StringFormat("%s,%s,%s,?,0,0,0,%.5f,%.2f,%s",TimeToString(TimeCurrent()),g_instrument, ticket, exit_price, profit, profit>0?"WIN":"LOSS"));
}

#endif
