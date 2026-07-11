import os, json, datetime
TERMINAL = r'C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075'
INDICATORS = os.path.join(TERMINAL, 'MQL5', 'Indicators')
FILES = os.path.join(TERMINAL, 'MQL5', 'Files')
os.makedirs(INDICATORS, exist_ok=True)
os.makedirs(FILES, exist_ok=True)

mql = '''#property copyright "Hermes SMC"
#property version "1.00"
#property strict
#property indicator_chart_window
#property indicator_buffers 0

input string DataFile = "Files\\xau_smc_data.json";
input bool   DeleteOnStart = true;
input int    MaxObjects = 3000;

string PREFIX = "HRSMC2_";

void DelPrefixed()
{
   for(int i=ObjectsTotal(0,-1,-1)-1;i>=0;i--)
   {
      string n = ObjectName(0,i,-1,-1);
      if(StringFind(n,PREFIX)==0) ObjectDelete(0,n);
   }
}

string ReadAll(string path)
{
   int h = FileOpen(path, FILE_READ|FILE_ANSI|FILE_TXT);
   if(h==INVALID_HANDLE) return "";
   string s = FileReadString(h, (int)FileSize(h));
   FileClose(h);
   return s;
}

string GV(string key, string src)
{
   string marker = "\\""+"+key+"\\"";
   int p = StringFind(src, marker);
   if(p<0) return "";
   p = StringFind(src, ":", p+StringLen(marker));
   if(p<0) return "";
   p += 1;
   while(p<StringLen(src) && StringGetCharacter(src,p)==' ') p++;
   if(StringGetCharacter(src,p)=='\"')
   {
      p += 1;
      int e = StringFind(src, "\"", p);
      if(e<0) return "";
      return StringSubstr(src, p, e-p);
   }
   int e = p;
   while(e<StringLen(src) && ((src[e]>='0'&&src[e]<='9')||src[e]=='.'||src[e]=='-')) e++;
   return StringSubstr(src, p, e-p);
}

void PutRect(string n, datetime t1, double p1, datetime t2, double p2, color c, bool fill, int w, int s)
{
   if(ObjectFind(0,n)==-1) ObjectCreate(0,n,OBJ_RECTANGLE,0,t1,p1,t2,p2);
   ObjectSetInteger(0,n,OBJPROP_COLOR,c);
   ObjectSetInteger(0,n,OBJPROP_STYLE,s);
   ObjectSetInteger(0,n,OBJPROP_WIDTH,w);
   ObjectSetInteger(0,n,OBJPROP_FILL,fill);
}

void PutText(string n, datetime t, double p, string txt, color c, int sz)
{
   if(ObjectFind(0,n)==-1) ObjectCreate(0,n,OBJ_TEXT,0,t,p);
   ObjectSetString(0,n,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,n,OBJPROP_COLOR,c);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,sz);
}

void PutLine(string n, datetime t1, double p1, datetime t2, double p2, color c, int w, int s)
{
   if(ObjectFind(0,n)==-1) ObjectCreate(0,n,OBJ_TRENDLINE,0,t1,p1,t2,p2);
   ObjectSetInteger(0,n,OBJPROP_COLOR,c);
   ObjectSetInteger(0,n,OBJPROP_STYLE,s);
   ObjectSetInteger(0,n,OBJPROP_WIDTH,w);
}

int OnInit()
{
   if(DeleteOnStart) DelPrefixed();
   string path = TerminalInfoString(TERMINAL_DATA_PATH)+"\\"+DataFile;
   string raw = ReadAll(path);
   if(StringLen(raw)<10){ Comment("SMC empty"); return INIT_FAILED; }

   datetime now = TimeCurrent();
   int drawn = 0;
   color cBF=clrLime, cRF=clrRed, cBiF=clrSpringGreen, cRiF=clrCrimson;
   color cBO=clrGreen, cRO=clrRed, cTU=clrDodgerBlue, cTD=clrOrangeRed;

   string tfMap[] = {"M15","H4"};
   for(int k=0;k<2;k++)
   {
      string tf = tfMap[k];
      int tpos = StringFind(raw, "\\""+tf+"\\"");
      if(tpos<0) continue;
      int ob = StringFind(raw, "{", tpos);
      if(ob<0) continue;
      int d2=0, startBlock=ob; string block="";
      for(int i=ob;i<StringLen(raw);i++)
      {
         ushort c = StringGetCharacter(raw,i);
         if(c=='{') d2++;
         if(c=='}') d2--;
         if(d2==0){ block = StringSubstr(raw,startBlock,i-startBlock+1); break; }
      }
      string arrs[] = {"fvgs","order_blocks","trendlines","confluences"};
      for(int a=0;a<4;a++)
      {
         string key = arrs[a];
         int kp = StringFind(block, "\\""+key+"\\":");
         if(kp<0) continue;
         int ab = StringFind(block, "[", kp);
         if(ab<0) continue;
         int d3=0, astart=ab; string arr="";
         for(int j=ab;j<StringLen(block);j++)
         {
            ushort c = StringGetCharacter(block,j);
            if(c=='[') d3++;
            if(c==']') d3--;
            if(d3==0){ arr=StringSubstr(block,astart,j-astart+1); break; }
         }
         int si=0, itStart=-1, d4=0;
         for(int ch=0;ch<StringLen(arr);ch++)
         {
            ushort c = StringGetCharacter(arr,ch);
            if(c=='{'){ if(d4==0) itStart=ch; d4++; }
            if(c=='}'){ d4--; if(d4==0 && itStart>=0)
            {
               if(drawn++>MaxObjects) break;
               string it = StringSubstr(arr,itStart,ch-itStart+1);
               string nm = PREFIX+tf+"_"+key+"_"+string(si++);
               if(key=="fvgs")
               {
                  string kind = GV("kind",it);
                  string ttxt = GV("time",it); string btxt=GV("bot",it); string tptxt=GV("top",it);
                  datetime t = StringToTime(ttxt);
                  double bot = StringToDouble(btxt), top = StringToDouble(tptxt);
                  bool bull = StringFind(kind,"BULL")!=-1, inv = StringFind(kind,"iFVG")!=-1;
                  color clr = bull?(inv?cBiF:cBF):(inv?cRiF:cRF);
                  PutRect(nm+"R", t, bot, now, top, clr, inv, inv?1:2, inv?0:1);
                  PutText(nm+"L", t, top, kind+"\\n"+StringSubstr(btxt,0,5)+"-"+StringSubstr(tptxt,0,5), clr, 8);
               }
               else if(key=="order_blocks")
               {
                  string ttxt = GV("time",it); string ty = GV("type",it);
                  string ltxt = GV("low",it); string Ttxt = GV("high",it);
                  datetime t = StringToTime(ttxt);
                  double lo = StringToDouble(ltxt), hi = StringToDouble(Ttxt);
                  color clr = StringFind(ty,"BUY")!=-1 ? cBO : cRO;
                  PutRect(nm+"R", t, lo, now, hi, clr, true, 1, 0);
                  PutText(nm+"L", t, hi, "OB", clr, 8);
               }
               else if(key=="trendlines")
               {
                  string ta_txt = GV("a_time",it), tb_txt = GV("b_time",it);
                  string pa_txt = GV("a_price",it), pb_txt = GV("b_price",it);
                  string kind = GV("kind",it);
                  datetime ta = StringToTime(ta_txt), tb = StringToTime(tb_txt);
                  double pa = StringToDouble(pa_txt), pb = StringToDouble(pb_txt);
                  color clr = StringFind(kind,"ascend")!=-1 ? cTU : cTD;
                  PutLine(nm, ta, pa, tb, pb, clr, 1, 2);
               }
               else if(key=="confluences")
               {
                  string ltxt = GV("low",it), Ttxt = GV("high",it);
                  double lo = StringToDouble(ltxt), hi = StringToDouble(Ttxt);
                  // draw confluence golden band
                  PutRect(nm+"R", iTime(_Symbol,(_Period==PERIOD_M15?PERIOD_H4:PERIOD_M15),0), lo, now, hi, clrGold, true, 1, 0);
                  PutText(nm+"L", iTime(_Symbol,_Period,0), hi, "CONF", clrGold, 9);
               }
            }}
         }
      }
   }
   Comment(PREFIX+" drawn=",drawn, " bias=", GV("bias", raw));
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason){}
void OnTick(){}
'''

mql_path = os.path.join(INDICATORS, 'HRSMC_SMC_Overlay.mq5')
with open(mql_path, 'w', encoding='utf-8') as f: f.write(mql)
print('WROTE', mql_path)

# write terminal-ready JSON into Files folder
src = r'C:\Users\user\Desktop\hermes_claude\data\rnd\xau_smc_analysis.json'
with open(src,'r',encoding='utf-8') as s: data=s.read()
dst_json = os.path.join(FILES, 'xau_smc_data.json')
with open(dst_json,'w',encoding='utf-8') as d: d.write(data)
print('JSON', dst_json, 'bytes=', len(data))
