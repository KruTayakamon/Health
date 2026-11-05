#!/usr/bin/env python3
"""แปลงข้อมูลจากฐานข้อมูลของแอป "ร่วมทาง" (export ด้วย ArtifactData out_dir) ให้เป็นไฟล์ใน logs/
ใช้: python3 scripts/db_to_logs.py <out_dir>
โดย <out_dir> คือโฟลเดอร์ที่ ArtifactData list ... out_dir=<dir> เขียนไฟล์ <dir>/<collection>/<doc_id>.json ไว้
เขียนทับ logs/weight.csv, logs/food.jsonl, logs/exercise.jsonl, logs/daily.csv, logs/wins.md (ส่วน DB) ให้ตรงกับฐานข้อมูล
"""
import json, os, sys, csv, glob
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src=sys.argv[1] if len(sys.argv)>1 else None
if not src or not os.path.isdir(src): sys.exit("ต้องระบุโฟลเดอร์ export")
def load(col):
    docs=[]
    for f in glob.glob(os.path.join(src,col,"*.json")):
        try:
            d=json.load(open(f,encoding="utf-8"))
            d=d.get("data",d) if isinstance(d,dict) and "data" in d and isinstance(d["data"],dict) else d
            d.setdefault("id",os.path.splitext(os.path.basename(f))[0]); docs.append(d)
        except Exception as e: print("skip",f,e)
    return sorted(docs,key=lambda d:(d.get("date",""),d.get("time",""),d.get("ts","")))
L=lambda *p: os.path.join(ROOT,*p)
w=load("weight")
with open(L("logs/weight.csv"),"w",encoding="utf-8",newline="") as f:
    cw=csv.writer(f); cw.writerow(["date","kg","note"]); [cw.writerow([d.get("date"),d.get("kg"),d.get("note","")]) for d in w]
with open(L("logs/food.jsonl"),"w",encoding="utf-8") as f:
    for d in load("food"):
        f.write(json.dumps({"date":d.get("date"),"time":d.get("time",""),"meal":d.get("meal",""),"items":[i.get("name") if isinstance(i,dict) else i for i in d.get("items",[])] or [d.get("text","")],"text":d.get("text",""),"kcal_low":d.get("kcal_low",0),"kcal_high":d.get("kcal_high",0),"protein_g":d.get("protein_g",0),"fiber_g":d.get("fiber_g",0),"confidence":d.get("confidence","กลาง"),"social":bool(d.get("social"))},ensure_ascii=False)+"\n")
with open(L("logs/exercise.jsonl"),"w",encoding="utf-8") as f:
    for d in load("exercise"):
        f.write(json.dumps({"date":d.get("date"),"time":d.get("time",""),"type":d.get("type",""),"minutes":d.get("minutes",0),"intensity":d.get("intensity",""),"est_kcal":d.get("est_kcal",0),"note":d.get("note","")},ensure_ascii=False)+"\n")
with open(L("logs/daily.csv"),"w",encoding="utf-8",newline="") as f:
    cw=csv.writer(f); cw.writerow(["date","sleep_h","steps","hunger_1_10","stress_1_5","logged_all","note"])
    for d in load("daily"): cw.writerow([d.get("date"),d.get("sleep_h",""),d.get("steps") or "",d.get("hunger",""),d.get("stress",""),"yes" if d.get("logged_all") else "no",d.get("note","")])
wins=load("wins")
with open(L("logs/wins.md"),"w",encoding="utf-8") as f:
    f.write("# สมุดหลักฐาน — ชัยชนะเล็ก ๆ ที่มีคนเห็น\n\n"); [f.write(f"- {d.get('date')} — {d.get('text')}\n") for d in wins]
print(f"weight {len(w)} · food {len(load('food'))} · exercise {len(load('exercise'))} · daily {len(load('daily'))} · wins {len(wins)} → logs/ อัปเดตแล้ว")
