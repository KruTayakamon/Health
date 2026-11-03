# 🗄️ คลังข้อมูล (Memory / Data Store)

ทุก agent อ่าน/เขียนไฟล์เดียวกัน ต่อท้าย (append) เสมอ ไม่เขียนทับ

| ไฟล์ | รูปแบบ | ตัวอย่าง |
|---|---|---|
| `logs/weight.csv` | `date,kg,note` | `2026-11-04,114.6,หลังชาบูเมื่อวาน` |
| `logs/food.jsonl` | 1 มื้อ/บรรทัด | `{"date":"2026-11-04","time":"12:30","meal":"กลางวัน","items":["ข้าวกะเพราหมูสับไข่ดาว"],"kcal_low":650,"kcal_high":800,"protein_g":32,"fiber_g":3,"confidence":"กลาง","hunger_before":7,"hunger_after":3,"social":false}` |
| `logs/exercise.jsonl` | 1 ครั้ง/บรรทัด | `{"date":"2026-11-04","type":"เวท+เดินลู่","minutes":40,"intensity":"กลาง","est_kcal":230,"note":"สัปดาห์1 แค่ไป"}` |
| `logs/daily.csv` | `date,sleep_h,steps,hunger_1_10,stress_1_5,logged_all,note` | `2026-11-04,6.5,5200,5,3,yes,` |
| `logs/weekly/YYYY-Www.md` | รายงานสัปดาห์ | สร้างโดย progress-analyst หลังรัน `scripts/weekly.py` |
| `data/thai-foods.csv` | ฐานข้อมูลอาหาร | เพิ่มได้เมื่อเจออาหารใหม่ที่กินบ่อย |

## กฎ
- วันที่ใช้ ISO `YYYY-MM-DD` เวลาไทย
- `kcal_low/high` เป็นช่วงเสมอ · `confidence` ∈ {สูง, กลาง, ต่ำ}
- `social: true` สำหรับมื้อบุฟเฟ่ต์/กินกับเพื่อน เพื่อให้ progress-analyst นับวันสังคม
- ก่อนตอบเรื่อง "วันนี้เหลืองบเท่าไหร่" ให้ grep `logs/food.jsonl` ด้วยวันที่วันนี้แล้วรวม kcal (ใช้ค่ากลางของช่วง)
