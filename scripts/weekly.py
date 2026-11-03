#!/usr/bin/env python3
"""สรุปสัปดาห์: ค่าเฉลี่ยน้ำหนัก 7 วัน, คาดการณ์ vs จริง, adherence
ใช้: python3 scripts/weekly.py [YYYY-MM-DD วันสุดท้ายของสัปดาห์]  (ค่าเริ่มต้น = วันนี้)
อ่าน: logs/weight.csv, logs/food.jsonl, logs/exercise.jsonl, logs/daily.csv, profile.yaml
"""
import csv, json, sys, os, re
from datetime import date, timedelta, datetime
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = lambda *p: os.path.join(ROOT, *p)

end = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
this_wk = {end - timedelta(d) for d in range(7)}
prev_wk = {end - timedelta(d) for d in range(7, 14)}

# --- profile (อ่านแบบง่าย ไม่พึ่ง yaml lib) ---
prof = open(L("profile.yaml"), encoding="utf-8").read()
def grab(key, default):
    m = re.search(rf"^\s*{key}:\s*([^\s#]+)", prof, re.M)
    return m.group(1) if m else default
tdee_s = grab("tdee_adaptive_kcal", "null")
if tdee_s == "null":
    lo, hi = map(int, grab("tdee_kcal_estimate", "2300-2450").split("-"))
    tdee = (lo + hi) / 2
else:
    tdee = float(tdee_s)
floor_kcal = int(grab("kcal_floor", "1300"))

# --- weight ---
w = {}
if os.path.exists(L("logs/weight.csv")):
    for r in csv.DictReader(open(L("logs/weight.csv"), encoding="utf-8")):
        try: w[date.fromisoformat(r["date"])] = float(r["kg"])
        except Exception: pass
tw = [w[d] for d in this_wk if d in w]
pw = [w[d] for d in prev_wk if d in w]

# --- food ---
days_kcal, days_prot, social_days, lowconf, meals = {}, {}, set(), 0, 0
if os.path.exists(L("logs/food.jsonl")):
    for line in open(L("logs/food.jsonl"), encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: m = json.loads(line)
        except Exception: continue
        d = date.fromisoformat(m["date"])
        if d not in this_wk: continue
        meals += 1
        k = (m.get("kcal_low", 0) + m.get("kcal_high", 0)) / 2
        days_kcal[d] = days_kcal.get(d, 0) + k
        days_prot[d] = days_prot.get(d, 0) + m.get("protein_g", 0)
        if m.get("social"): social_days.add(d)
        if m.get("confidence") == "ต่ำ": lowconf += 1

# --- exercise ---
gym, ex_min = 0, 0
if os.path.exists(L("logs/exercise.jsonl")):
    for line in open(L("logs/exercise.jsonl"), encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: e = json.loads(line)
        except Exception: continue
        if date.fromisoformat(e["date"]) in this_wk:
            ex_min += e.get("minutes", 0)
            if "เวท" in e.get("type", "") or "ยิม" in e.get("type", ""): gym += 1

# --- daily ---
sleep, logged = [], 0
if os.path.exists(L("logs/daily.csv")):
    for r in csv.DictReader(open(L("logs/daily.csv"), encoding="utf-8")):
        try: d = date.fromisoformat(r["date"])
        except Exception: continue
        if d in this_wk:
            if r.get("sleep_h"): sleep.append(float(r["sleep_h"]))
            if r.get("logged_all", "").lower() in ("yes", "y", "true", "1"): logged += 1

# --- compute ---
iso = end.isocalendar()
print(f"# สรุปสัปดาห์ {iso[0]}-W{iso[1]:02d}  ({min(this_wk)} → {end})\n")
if tw:
    avg = mean(tw)
    print(f"น้ำหนักเฉลี่ย 7 วัน: **{avg:.1f} กก.** (ชั่ง {len(tw)}/7 วัน)")
    if pw:
        delta = avg - mean(pw)
        print(f"เทียบสัปดาห์ก่อน ({mean(pw):.1f}): **{delta:+.2f} กก.**")
    else:
        delta = None
        print("ยังไม่มีข้อมูลสัปดาห์ก่อนให้เทียบ")
else:
    avg, delta = None, None
    print("ยังไม่มีน้ำหนักสัปดาห์นี้")

n_food_days = len(days_kcal)
print()
if n_food_days:
    avg_k = mean(days_kcal.values()); avg_p = mean(days_prot.values())
    deficit = tdee - avg_k
    expected = -deficit * 7 / 7700
    print(f"แคลอรี่เฉลี่ย/วัน: {avg_k:.0f} (บันทึก {n_food_days}/7 วัน, {meals} มื้อ) · โปรตีนเฉลี่ย {avg_p:.0f} ก.")
    print(f"TDEE ที่ใช้: {tdee:.0f} → deficit ≈ {deficit:.0f}/วัน → **คาดว่าควรลด ≈ {expected:+.2f} กก.**")
    if delta is not None:
        ratio = (delta / expected) if expected else 0
        verdict = "✅ ตามเกณฑ์" if delta <= 0 and ratio >= 0.5 else "⚠️ ต่ำกว่าเกณฑ์ → เริ่มวินิจฉัยตามลำดับ"
        print(f"ลดจริง {delta:+.2f} vs คาด {expected:+.2f} → {verdict}")
    low_days = [d for d, k in days_kcal.items() if k < floor_kcal]
    if low_days: print(f"🛡️ มี {len(low_days)} วันที่กินต่ำกว่า {floor_kcal} — ห้ามซ้ำ")
    print(f"วันสังคม/บุฟเฟ่ต์: {len(social_days)} · มื้อความมั่นใจต่ำ: {lowconf}/{meals} ({(lowconf/meals*100 if meals else 0):.0f}%)")
else:
    print("ยังไม่มีบันทึกอาหารสัปดาห์นี้")

print()
print(f"ยิม/เวท: {gym} ครั้ง · ออกกำลังรวม {ex_min} นาที")
print(f"นอนเฉลี่ย: {mean(sleep):.1f} ชม." if sleep else "ไม่มีข้อมูลการนอน")
adh = logged / 7 * 100
print(f"บันทึกครบ (ตามเช็กอิน): {logged}/7 วัน = {adh:.0f}%")

# --- behaviour score (4 สัปดาห์แรก) ---
score = 0
score += 20 if len(tw) >= 5 else 0
score += 20 if adh >= 90 else (10 if adh >= 70 else 0)
score += 20 if gym >= 2 else (10 if gym == 1 else 0)
score += 20 if (n_food_days and len(social_days) <= 2) else 0
score += 20 if n_food_days >= 6 else (10 if n_food_days >= 4 else 0)
print(f"\n**คะแนนพฤติกรรม: {score}/100** → {'สัปดาห์สำเร็จ 🎉' if score >= 80 else 'ยังไม่ถึง 80 — เลือกแก้ 1 ข้อ'}")

# --- diagnosis hints ---
print("\n## คำใบ้สำหรับ progress-analyst")
if adh < 80 or n_food_days < 6: print("1️⃣ บันทึกไม่ครบ → สรุปว่า 'ข้อมูลไม่พอ' ยังไม่ปรับงบ")
elif meals and lowconf / meals > 0.3: print("2️⃣ มื้อความมั่นใจต่ำเกิน 30% → สัปดาห์สอบเทียบ")
elif sleep and mean(sleep) < 6: print("4️⃣ นอนน้อย → แก้การนอนก่อน")
elif len(social_days) > 2: print("5️⃣ วันสังคมเกิน 2 → ปรับกฎบุฟเฟ่ต์ ไม่ลดงบวันปกติ")
else: print("ผ่านข้อ 1,2,4,5 → ตรวจข้อ 3 (น้ำคั่ง/ประจำเดือน/เวทใหม่), 6 (ก้าว), 7 (พอร์ชัน) ด้วยการถาม")
