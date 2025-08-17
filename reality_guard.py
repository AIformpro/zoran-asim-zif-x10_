
from typing import Dict, Any
import re, json, hashlib, datetime, os
MERKLE_LOG = os.environ.get("ETHICCHAIN_LOG","ethicchain.log")
def _now(): return datetime.datetime.utcnow().isoformat()+"Z"
def _prev():
    if not os.path.exists(MERKLE_LOG): return "0"*64
    last=None
    with open(MERKLE_LOG,"r",encoding="utf-8") as f:
        for line in f:
            if line.strip(): last=json.loads(line)
    return (last or {}).get("merkle","0"*64)
def _merkle(record: Dict[str,Any]) -> str:
    payload=json.dumps({"prev":_prev(),**record},sort_keys=True,ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()
class RealityGuard:
    def __init__(self, threshold: float=0.95): self.threshold=threshold
    def score(self, text:str, ctx:Dict[str,Any])->float:
        sources=ctx.get("sources") or []; digits=len(re.findall(r"\d", text or ""))
        proper=len(re.findall(r"\b[A-Z][a-z]{2,}\b", text or ""))
        has_link=bool(re.search(r"https?://|doi:", text or "", re.I))
        score=1.0
        if (digits>=3 or proper>=4) and not (sources or has_link): score-=0.5
        return max(0.0,min(1.0,score))
    def enforce(self, text:str, ctx:Dict[str,Any])->Dict[str,Any]:
        s=self.score(text,ctx)
        if s>=self.threshold:
            self._log("pass", text, ctx, s); return {"allowed":True,"response":text,"score":s}
        msgs={"fr":"Je ne sais pas / Non vérifié.","en":"I don't know / Not verified.","es":"No lo sé / No verificado."}
        lang=ctx.get("lang","en"); out=msgs.get(lang,msgs["en"])
        self._log("blocked", text, ctx, s, reason="insufficient evidence")
        return {"allowed":False,"response":out,"score":s}
    def _log(self,kind, text, ctx, score, **kw):
        rec={"ts":_now(),"kind":kind,"score":score,"context":ctx,"merkle":""}
        rec.update(kw); rec["merkle"]=_merkle(rec)
        with open(MERKLE_LOG,"a",encoding="utf-8") as f: f.write(json.dumps(rec,ensure_ascii=False)+"\n")
