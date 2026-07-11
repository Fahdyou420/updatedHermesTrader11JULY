import os, json
WRITE_DIR = r'C:\Users\user\Desktop\hermes_claude\mql5_deploy'
os.makedirs(WRITE_DIR, exist_ok=True)

mql = '''#property copyright "Hermes SMC"
#property version "1.00"
#property strict
#property indicator_chart_window

input string AnalysisFile = "Experts\\xau_smc_data.json";
input bool   DeleteOnStart = true;
input int    MaxObjects = 3000;
string PREFIX = "HRSMC_";

void DelPrefixed()
{
   for(int i=ObjectsTotal(0,-1,-1)-1;i>=0;i--)
   {
      string nm = ObjectName(0,i,-1,-1);
      if(StringFind(nm,PREFIX)==0) ObjectDelete(0,nm);
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

void PutRect(string name, datetime t1, double p1, datetime t2, double p2, color clr, bool fill=false, int w=1, int style=0)
{
   if(ObjectFind(0,name)==-1) ObjectCreate(0,name,OBJ_RECTANGLE,0,t1,p1,t2,p2);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,style);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,w);
   ObjectSetInteger(0,name,OBJPROP_FILL,fill);
}

void PutText(string name, datetime t, double p, string txt, color clr, int sz=8)
{
   if(ObjectFind(0,name)==-1) ObjectCreate(0,name,OBJ_TEXT,0,t,p);
   ObjectSetString(0,name,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,sz);
}

void PutLine(string name, datetime t1, double p1, datetime t2, double p2, color clr, int w=1, int style=0)
{
   if(ObjectFind(0,name)==-1) ObjectCreate(0,name,OBJ_TRENDLINE,0,t1,p1,t2,p2);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_STYLE,style);
   ObjectSetInteger(0,name,OBJPROP_WIDTH,w);
}

string GV(string key, string src)
{
   string marker = "\\""+key+"\\"";
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

int OnInit()
{
   if(DeleteOnStart) DelPrefixed();
   string path = TerminalInfoString(TERMINAL_DATA_PATH)+"\\"+AnalysisFile;
   string raw = ReadAll(path);
   if(StringLen(raw)<10)
   {
      Alert("SMC overlay: empty file ", path);
      return INIT_FAILED;
   }
   datetime now = TimeCurrent();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   int drawn = 0;

   color cBullFVG = clrLime; color cBearFVG = clrRed;
   color cBullOB  = clrGreen; color cBearOB  = clrRed;
   color cBullIFVG= clrSpringGreen; color cBearIFVG = clrCrimson;
   color cTLUp = clrDodgerBlue; color cTLDn = clrOrangeRed;

   string tfList[] = {"M15","H4"};
   for(int k=0;k<2;k++)
   {
      string tf = tfList[k];
      int tpos = StringFind(raw, "\\""+tf+"\\"");
      if(tpos<0) continue;
      int ob = StringFind(raw, "{", tpos);
      if(ob<0) continue;
      int d2=0, astart=ob;
      string block="";
      for(int i=ob;i<StringLen(raw);i++)
      {
         ushort c = StringGetCharacter(raw,i);
         if(c=='{') d2++;
         if(c=='}') d2--;
         if(d2==0){ block=StringSubstr(raw,astart,i-astart+1); break; }
      }
      string arrs[] = {"fvgs","order_blocks","trendlines"};
      for(int a=0;a<3;a++)
      {
         string key = arrs[a];
         int kp = StringFind(block, "\\""+key+"\\":");
         if(kp<0) continue;
         int ab = StringFind(block, "[", kp);
         if(ab<0) continue;
         int d3=0,abStart=ab; string arr="";
         for(int j=ab;j<StringLen(block);j++)
         {
            ushort c = StringGetCharacter(block,j);
            if(c=='[') d3++;
            if(c==']') d3--;
            if(d3==0){ arr=StringSubstr(block,abStart,j-abStart+1); break; }
         }
         int si=0, itStart=-1, d4=0;
         for(int ch=0;ch<StringLen(arr);ch++)
         {
            ushort c = StringGetCharacter(arr,ch);
            if(c=='{'){ if(d4==0) itStart=ch; d4++; }
            if(c=='}'){ d4--; if(d4==0 && itStart>=0)
            {
               string it = StringSubstr(arr,itStart,ch-itStart+1);
               string nm = PREFIX+tf+"_"+key+"_"+string(si++);
               if(drawn++>MaxObjects) break;
               if(key=="fvgs")
               {
                  string kind = GV("kind",it);
                  string ttxt = GV("time",it);
                  string bbtxt= GV("bot",it);
                  string tptxt= GV("top",it);
                  datetime t = StringToTime(ttxt);
                  double bot = StringToDouble(bbtxt);
                  double top = StringToDouble(tptxt);
                  bool bull = StringFind(kind,"BULL")!=-1;
                  bool inv  = StringFind(kind,"IFVG")!=-1;
                  color clr = bull?(inv?cBullIFVG:cBullFVG):(inv?cBearIFVG:cBearFVG);
                  bool fill = inv;
                  int w = inv?1:2, s = inv?0:1;
                  PutRect(nm+"R", t, bot, now, top, clr, fill, w, s);
                  string lbl = kind+"\\n"+StringSubstr(bbtxt,0,6)+"-"+StringSubstr(tptxt,0,6);
                  PutText(nm+"L", t, top, lbl, clr, 8);
               }
               else if(key=="order_blocks")
               {
                  string ttxt = GV("time",it);
                  string ty = GV("type",it);
                  string ltxt = GV("low",it);
                  string Ttxt = GV("high",it);
                  datetime t = StringToTime(ttxt);
                  double lo = StringToDouble(ltxt);
                  double hi = StringToDouble(Ttxt);
                  color clr = StringFind(ty,"BUY")!=-1 ? cBullOB : cBearOB;
                  PutRect(nm+"R", t, lo, now, hi, clr, true, 1, 0);
                  PutText(nm+"L", t, hi, "OB", clr, 8);
               }
               else if(key=="trendlines")
               {
                  string ta_txt = GV("a_time",it);
                  string tb_txt = GV("b_time",it);
                  string pa_txt = GV("a_price",it);
                  string pb_txt = GV("b_price",it);
                  string kind = GV("kind",it);
                  datetime ta = StringToTime(ta_txt);
                  datetime tb = StringToTime(tb_txt);
                  double pa = StringToDouble(pa_txt);
                  double pb = StringToDouble(pb_txt);
                  color clr = StringFind(kind,"ascending")!=-1 ? cTLUp : cTLDn;
                  PutLine(nm, ta, pa, tb, pb, clr, 1, 2);
               }
            }}
         }
      }
   }
   Comment(PREFIX+" drawn=",drawn);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason){}
void OnTick(){}
'''

mq_path = os.path.join(WRITE_DIR, 'HRSMC_SMC_Draw.mq5')
with open(mq_path, 'w', encoding='utf-8') as f:
    f.write(mql)

src = r'C:\Users\user\Desktop\hermes_claude\data\rnd\xau_smc_analysis.json'
dst = os.path.join(WRITE_DIR, 'xau_smc_data.json')
with open(src, 'r', encoding='utf-8') as s:
    data = s.read()
with open(dst, 'w', encoding='utf-8') as d:
    d.write(data)
print('DEPLOY_DIR', WRITE_DIR)
print('WROTE', mq_path)
print('JSON', dst)
print('size_mq5=', os.path.getsize(mq_path), 'json=', len(data))
