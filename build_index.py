#!/usr/bin/env python3
"""สร้าง index.html (GitHub Pages) จาก ClientPortal.html (เทมเพลต Apps Script)
แปลง 3 จุด: แทน template tag, สลับ google.script.run เป็น fetch, ใส่ API_URL
ใช้ทุกครั้งที่แก้ ClientPortal.html จะได้ไม่ต้องแก้สองที่ให้ตรงกันเอง"""
import re, sys, json

SRC = "/Users/gearsecond/Desktop/apps-script-port/พร้อมวาง/ClientPortal.html"
DST = "index.html"
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
assert "<?!=" not in s and "<?" not in s.replace("<?xml", ""), "ยังมี template tag ค้าง"

old_call = """  google.script.run
    .withSuccessHandler(function(data){ store('client_pin',pin); onData(data); })
    .withFailureHandler(function(e){ pinFail(); })
    .getClientDataByPin(pin);"""
new_call = """  fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=utf-8' },
    body: JSON.stringify({ action: 'clientData', pin: pin }),
  })
  .then(function(r){ return r.json(); })
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
s = s.replace(anchor, "const API_URL = '%s';\n%s" % (API, anchor), 1)

open(DST, "w", encoding="utf-8").write(s)
print("สร้าง index.html แล้ว (%d KB) · แทน companyName %d จุด" % (len(s)//1024, n))
