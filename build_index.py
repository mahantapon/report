#!/usr/bin/env python3
"""สร้าง index.html (GitHub Pages) จาก ClientPortal.html (เทมเพลต Apps Script)
แปลง 3 จุด: แทน template tag, สลับ google.script.run เป็น fetch, ใส่ API_URL
ใช้ทุกครั้งที่แก้ ClientPortal.html จะได้ไม่ต้องแก้สองที่ให้ตรงกันเอง"""
import re, sys, json

SRC = "/Users/gearsecond/Desktop/apps-script-port/พร้อมวาง/ClientPortal.html"
DST = "index.html"
# ตัวพักข้อมูลบนเซิร์ฟเวอร์ของบริษัท — ลดเวลารอของลูกค้าจาก 2-8 วินาที เหลือ ~0.3 วินาที
CACHE = "https://assistant.bestbest.work/rcache/"
# Apps Script ตัวจริง — ใช้เป็นทางถอยเมื่อตัวพักล่ม (ช้าแต่ยังใช้งานได้ ไม่ทำให้ลูกค้าเปิดเว็บไม่ได้)
API = ("https://script.google.com/macros/s/"
       "AKfycbxo5iY4E9CazLb2sEkbR9XS4mkEUdoPAfYCsLAtR2IcqCMuEuQJGiab-ShKvSHfeVhC/exec")
COMPANY = "บริษัท เรืองอนันต์ คอร์ปอเรชั่น จำกัด"

# โลโก้ base64 ดึงจาก index.html เดิม (ฝังอยู่จุดเดียวที่ #logoGate)
old = open(DST, encoding="utf-8").read()
m = re.search(r'<img id="logoGate" src="(data:image/png;base64,[^"]+)"', old)
assert m, "หาโลโก้ base64 ใน index.html เดิมไม่เจอ"
LOGO = m.group(1)

s = open(SRC, encoding="utf-8").read()
s = s.replace("<?!= logoDataUri ?>", LOGO)
n = s.count("<?!= companyName ?>")
s = s.replace("<?!= companyName ?>", COMPANY)
# DOC_API: หน้า static ยิงตรงเข้า Apps Script (ไม่ผ่านตัวพัก — ไฟล์เอกสารห้ามแคช)
doc_old = "const DOC_API = '<?!= webAppUrl ?>';"
assert s.count(doc_old) == 1, "หา DOC_API scriptlet ไม่เจอ"
s = s.replace(doc_old, "const DOC_API = '%s';" % API, 1)

assert "<?!=" not in s and "<?" not in s.replace("<?xml", ""), "ยังมี template tag ค้าง"

old_call = """  google.script.run
    .withSuccessHandler(function(data){ store('client_pin',pin); onData(data); })
    .withFailureHandler(function(e){ pinFail(); })
    .getClientDataByPin(pin);"""
new_call = """  apiPost({ action: 'clientData', pin: pin })
  .then(function(data){
    if (data && data.error) throw new Error(data.error);
    store('client_pin', pin);
    onData(data);
  })
  .catch(function(e){
    pinFail(/PIN/.test(String(e && e.message))
      ? 'รหัสไม่ถูกต้อง กรุณาตรวจสอบและลองใหม่อีกครั้ง'
      : 'เชื่อมต่อระบบไม่ได้ กรุณาลองใหม่อีกครั้ง');
  });"""
assert s.count(old_call) == 1, "หา google.script.run ไม่เจอ"
s = s.replace(old_call, new_call, 1)


anchor = "let DATA = null, cur = '', lbList = [], lbIdx = 0;"
assert s.count(anchor) == 1
HELPER = """const API_CACHE = '%s';
const API_URL   = '%s';
// ยิงไปที่ตัวพักข้อมูลก่อน ถ้าติดต่อไม่ได้หรือตอบไม่ปกติ ค่อยถอยไปยิง Apps Script ตรง ๆ
// ⚠️ ทางถอยนี้สำคัญ — เซิร์ฟเวอร์ตัวพักล่มต้องไม่ทำให้ลูกค้าเปิดเว็บไม่ได้ แค่ช้าลงเท่านั้น
function apiPost(body){
  const opt = { method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'},
                body: JSON.stringify(body) };
  return fetch(API_CACHE, opt)
    .then(function(r){ if(!r.ok) throw new Error('cache '+r.status); return r.json(); })
    .catch(function(){ return fetch(API_URL, opt).then(function(r){ return r.json(); }); });
}
""" % (CACHE, API)
s = s.replace(anchor, HELPER + anchor, 1)

# ── สร้าง 2 เวอร์ชันจากเทมเพลตเดียว ──
#   index.html      = เว็บจริง ซ่อนแท็บ "รายละเอียดงวดงาน" (หลังบ้านยังไม่นิ่ง) เหลือ ภาพรวม/รายวัน/รายสัปดาห์
#   demo/index.html = เดโม โชว์ครบทุกแท็บ (report.ruanganan.com/demo) ไว้ทดลองก่อนยกขึ้นเว็บจริง
import os
assert s.count("/*__HIDE_TABS__*/") == 1, "หา placeholder HIDE_TABS ไม่เจอ"

prod = s.replace("/*__HIDE_TABS__*/", "'f'")   # เว็บจริง: ซ่อนงวดงาน
open(DST, "w", encoding="utf-8").write(prod)

demo = s.replace("/*__HIDE_TABS__*/", "")      # เดโม: โชว์ครบ
os.makedirs("demo", exist_ok=True)
open("demo/index.html", "w", encoding="utf-8").write(demo)

print("สร้าง index.html (เว็บจริง ซ่อนงวดงาน) + demo/index.html (โชว์ครบ) · %d KB · companyName %d จุด" % (len(prod)//1024, n))
