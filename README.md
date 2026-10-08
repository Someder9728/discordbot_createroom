# Discord Voice Channel Bulk Creator

บอท Python สร้างห้องเสียง **ถาวร** ด้วย Slash commands `/create` และ `/createfile` ห้องไม่หายเมื่อสมาชิกออกหรือปิดบอท ไม่มีคำสั่งลบอัตโนมัติ ใช้งานผ่านบัญชี Bot เท่านั้น

## 1. สิ่งที่ต้องเตรียม

- Python **3.11 ขึ้นไป** (แนะนำ 3.12) และอินเทอร์เน็ต
- เซิร์ฟเวอร์ Discord ที่คุณมีสิทธิ์เชิญบอทและจัดการช่อง
- โปรเจกต์ที่แตก ZIP แล้ว โดยไฟล์ `bot.py` อยู่ในโฟลเดอร์ `discord-voice-creator`
- ผู้สั่งต้องมี Manage Channels ระดับเซิร์ฟเวอร์ และในช่องที่สั่ง/Category ปลายทางด้วย

## 2. ติดตั้ง Python และเตรียม Windows

ดาวน์โหลด Python จาก https://www.python.org/downloads/windows/ ติดตั้งและเลือก Add Python to PATH หากมีตัวเลือก จากนั้นเปิด PowerShell ใหม่ ตรวจเวอร์ชันด้วย `py --version` หากคำสั่งไม่พบให้ตรวจการติดตั้งหรือใช้ `python` แทน `py`

เปิด PowerShell ในโฟลเดอร์โปรเจกต์ (หรือเปลี่ยนเส้นทางด้านล่างเป็นตำแหน่งจริง):

```powershell
cd "C:\path\to\discord-voice-creator"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

หากใช้เวอร์ชันอื่นที่รองรับ เปลี่ยน `-3.12` ตามเวอร์ชันที่ติดตั้ง คำสั่งนี้เรียก Python ใน venv โดยตรง จึงไม่ต้อง activate และไม่ต้องเปลี่ยน Execution Policy

## 3. สร้าง Application และ Bot ใหม่

1. เปิด [Discord Developer Portal](https://discord.com/developers/applications) และเข้าสู่ระบบ
2. เลือก New Application ตั้งชื่อ เช่น Voice Creator แล้วเปิด Application นั้น
3. ไปหน้า Bot หากยังไม่มี Bot ให้ใช้ตัวเลือกเพิ่ม Bot (หน้าตา Portal อาจเปลี่ยน)
4. กด Reset Token/สร้าง Token แล้วคัดลอก **Bot Token** เก็บไว้ใน `.env` ตามหัวข้อ 5 ไม่ใช่ Application ID หรือ Client Secret
5. บอทนี้ไม่ต้องเปิด Privileged Gateway Intents: Message Content, Server Members หรือ Presence; ใช้ Slash commands และ default intents
6. หากใช้เฉพาะส่วนตัว สามารถปิด Public Bot ตามความเหมาะสม และไม่ต้องเปิด Requires OAuth2 Code Grant สำหรับการเชิญแบบนี้

Token คือรหัสเข้าถึงบอท อย่าส่งในแชต ภาพหน้าจอ Git หรือ ZIP หากหลุดให้ Reset Token ทันทีแล้วแก้ `.env`

## 4. Scopes, Permissions และเชิญเข้าเซิร์ฟเวอร์

1. ไป OAuth2 → URL Generator เลือก scopes `bot` และ `applications.commands` หาก Portal มีตัวเลือก Installation ให้ใช้ Guild Install
2. ใน Bot Permissions เลือก **Manage Channels** และ **View Channels** ไม่ต้องให้ Administrator, Connect หรือ Speak เพราะบอทไม่ได้เข้าห้องเสียง
3. เปิด URL ที่ได้ เลือกเซิร์ฟเวอร์ แล้ว Authorize ด้วยบัญชีที่มีสิทธิ์ติดตั้งแอป/Manage Server
4. ตรวจ Server Settings → Roles ว่าบอทมีสิทธิ์ตามที่เลือก และตรวจ Channel/Category permission overrides ว่าไม่ได้ปฏิเสธ View Channels หรือ Manage Channels ของบอท
5. ผู้ใช้ต้องมี Use Application Commands ในช่องที่ใช้ รวมถึง Manage Channels การเปิดสิทธิ์คำสั่งให้ทุกคนใน Integrations ไม่ได้ข้ามการตรวจสิทธิ์ในโค้ด

การตอบเป็น ephemeral มองเห็นเฉพาะผู้สั่ง บอทไม่ส่งข้อความปกติในช่องจึงไม่ต้องให้ Send Messages สำหรับงานนี้

## 5. สร้าง `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

ใส่ Token จริงแทนข้อความตัวอย่าง แล้วบันทึกเป็นชื่อ `.env` ไม่ใช่ `.env.txt`:

```dotenv
DISCORD_TOKEN=ใส่_TOKEN_จริงบนเครื่องคุณ
TEST_GUILD_ID=
```

โค้ดอ่าน Token จาก `.env` ข้าง `bot.py` เท่านั้น ไม่อ่าน Token จาก environment ของเครื่อง ไม่มี Token ในโค้ดหรือไฟล์ตัวอย่าง `.gitignore` กัน `.env` แต่ไม่กันการส่งไฟล์ด้วยมือ

แนะนำช่วงทดลอง: Discord → User Settings → Advanced → Developer Mode แล้วคลิกขวาชื่อเซิร์ฟเวอร์ → Copy Server ID ใส่ใน `TEST_GUILD_ID` เพื่อ sync คำสั่งเฉพาะเซิร์ฟเวอร์ทดลองอย่างรวดเร็ว หากเว้นว่างจะ sync แบบ global และอาจต้องรอ Discord กระจายคำสั่ง เปิดบอทใหม่หลังแก้ค่านี้

หากเคย sync แบบ test แล้วเปลี่ยนเป็น global คำสั่งเฉพาะเซิร์ฟเวอร์เดิมอาจยังอยู่ ควรใช้โหมดเดิมต่อ หรือให้ผู้ดูแลล้าง guild command registrations ก่อนย้ายโหมดเพื่อไม่ให้มีคำสั่งซ้ำ

## 6. รันและทดลองบน Windows

```powershell
.\.venv\Scripts\python.exe bot.py
```

รอ log `Synced 2 commands` และ `Connected as ...` เปิดบอทเพียงหนึ่ง process ต่อ Token กด Ctrl+C เพื่อหยุด Windows ต้องเปิดและไม่ sleep จึงทำงานต่อเนื่องได้

ทดลองในช่องข้อความของเซิร์ฟเวอร์:

1. พิมพ์ `/create` แล้วเลือกช่องกรอก `amount:3` และ `name:Room` → ได้ Room 1, Room 2, Room 3
2. สั่ง `/create amount:2 name:Room` อีกครั้ง → ได้ Room 4 และ Room 5
3. ทดลอง `category` โดยเลือก Category ที่มีอยู่ เช่น Voice Rooms
4. พิมพ์ `/createfile` เลือกช่อง `file` แล้วอัปโหลด `channels.example.txt` → ได้ 3 ห้อง; ข้ามบรรทัดว่าง

ค่าตัวอย่างด้านบนอธิบายช่องกรอกของ Discord ไม่ใช่คำสั่ง shell หากต้องการ Room 1–100 ให้ใช้ `/create amount:100 name:Room` โดยไม่ใส่ Category และเซิร์ฟเวอร์ต้องมีพื้นที่พอ

## 7. พฤติกรรมและข้อจำกัด

- `name` คือ prefix: โค้ดต่อช่องว่างและเลขให้ ค้นเลขสูงสุดจาก **Voice Channels ทั้งเซิร์ฟเวอร์** ไม่แยก Category ไม่รวม Stage Channels และไม่สนตัวพิมพ์ใหญ่เล็ก เช่น Room 100 แล้วครั้งต่อไปเริ่ม 101 ไม่เติมช่องเลขที่ถูกลบ และไม่มีฐานข้อมูล ถ้าลบเลขสูงสุดอาจใช้เลขนั้นใหม่
- `/createfile` อ่าน UTF-8 หรือ UTF-8-SIG (UTF-8 with BOM), 1 บรรทัดต่อชื่อ ตัดช่องว่างหัวท้าย ข้ามบรรทัดว่าง ไม่เติมเลข ชื่อซ้ำในไฟล์/กับห้องเดิมจะสร้างซ้ำตามไฟล์ จึงไม่ควรสั่งไฟล์เดิมซ้ำโดยไม่ตรวจห้อง
- ชื่อสุดท้ายต้องยาว 1–100 ตัวอักษร ไม่มี control characters ตรวจทุกชื่อก่อนเริ่มสร้าง หากชื่อใดผิดจะไม่เริ่มงาน
- safety max **100 ห้องต่อคำสั่ง**, ไฟล์ไม่เกิน **64 KiB** เป็นนโยบายของโปรเจกต์ ไม่ใช่ Discord rate limit
- Category คือกลุ่มช่องที่ต้องสร้างเองใน Discord ก่อน เลือก category เพื่อจัดห้องใต้กลุ่มนั้น ห้องใหม่ใช้ permission overwrites ของ Category ตามพฤติกรรม discord.py; ไม่ระบุจะสร้างนอก Category ใช้สิทธิ์ระดับเซิร์ฟเวอร์ ตรวจ View Channel/Connect ของสมาชิกก่อนให้ใช้งานจริง โดยเฉพาะ Category ส่วนตัว
- Discord จำกัด **50 ช่องต่อ Category** รวมทั้งข้อความและเสียง หากต้องการ 100 ห้องใต้ Category ให้แบ่งเป็นสอง Category ที่มีพื้นที่ และสั่งครั้งละไม่เกินพื้นที่ที่เหลือ
- ตรวจเพดาน **500 guild channels** รวม Category แต่ไม่รวม threads ก่อนสร้าง และ Discord เป็นผู้ตัดสินสุดท้ายหากมีการเปลี่ยนข้อจำกัดหรือมีคนสร้างช่องระหว่างทำงาน โค้ดหยุดเมื่อ API ปฏิเสธ
- สร้างทีละห้องแบบ sequential ให้ discord.py จัดการ rate limits ไม่เร่งด้วย concurrent requests ไม่ retry create เองเมื่อผลไม่ชัดเจน
- รับงานสร้างได้หนึ่งงานต่อเซิร์ฟเวอร์ภายใน process นี้ ผู้ดูแล/บอทอื่นยังอาจสร้างห้องพร้อมกันได้ จึงไม่รับประกันไม่มีชื่อซ้ำจากระบบภายนอก
- อัปเดต progress ประมาณทุก 5 วินาทีเมื่อการสร้างห้องคืนผล ระหว่างรอ rate limit อาจไม่มีความคืบหน้า งานตั้งเวลาสูงสุดประมาณ 12 นาทีเพื่อเผื่ออายุ interaction token หากหมดเวลาจะหยุดส่ง create เพิ่ม ห้องล่าสุดอาจสร้างแล้วแม้ client หมดเวลารอ
- สรุปสำเร็จ, ล้มเหลว/ไม่ยืนยัน, ยังไม่ได้ทำ ไม่มี rollback ห้องถาวรที่สร้างแล้ว ผู้ดูแลต้องตรวจและลบเองหากต้องการ ไม่มีระบบ resume หลัง restart และ logs ไม่เก็บ Token หรือชื่อไฟล์/เนื้อหาไฟล์

## 8. Deploy บน Ubuntu VPS แบบ systemd

ตัวอย่างสำหรับ Ubuntu 24.04 LTS ที่มี systemd และ Python 3.12: SSH เข้า VPS ด้วยบัญชีที่ใช้ sudo ได้ ไม่ต้องเปิด inbound port ให้บอท; ต้องออกอินเทอร์เน็ต HTTPS/WebSocket และ DNS ได้

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip unzip
python3 --version
sudo useradd --system --create-home --home-dir /opt/discord-voice-creator --shell /usr/sbin/nologin discordbot
```

หากมี user นี้อยู่แล้ว ไม่ต้องสร้างซ้ำ ส่ง ZIP จากเครื่อง Windows ไป VPS (เปลี่ยนชื่อผู้ใช้/host):

```powershell
scp .\discord-voice-creator.zip youruser@YOUR_VPS_IP:/tmp/
```

ZIP มีโฟลเดอร์ `discord-voice-creator/` อยู่ภายใน บน VPS ติดตั้งดังนี้:

```bash
unzip /tmp/discord-voice-creator.zip -d /tmp/voice-creator-upload
sudo cp -a /tmp/voice-creator-upload/discord-voice-creator/. /opt/discord-voice-creator/
sudo chown -R discordbot:discordbot /opt/discord-voice-creator
sudo -u discordbot python3 -m venv /opt/discord-voice-creator/.venv
sudo -u discordbot /opt/discord-voice-creator/.venv/bin/python -m pip install --upgrade pip
sudo -u discordbot /opt/discord-voice-creator/.venv/bin/python -m pip install -r /opt/discord-voice-creator/requirements.txt
sudo -u discordbot cp /opt/discord-voice-creator/.env.example /opt/discord-voice-creator/.env
sudo chmod 600 /opt/discord-voice-creator/.env
sudo nano /opt/discord-voice-creator/.env
```

ใส่ Token และ TEST_GUILD_ID ตามหัวข้อ 5 ใช้ editor เพื่อไม่ให้ Token เข้า shell history `.env` ต้องเป็นเจ้าของ `discordbot` และสิทธิ์ 600 อย่าสั่ง cat หรือส่งไฟล์นี้ให้คนอื่น บอทใช้ไฟล์ `.env` โดยตรง จึง **ไม่ต้องตั้ง EnvironmentFile** ใน systemd

คัดลอก service ตัวอย่างที่ให้มาแล้วสั่ง:

```bash
sudo cp /opt/discord-voice-creator/deploy/discord-voice-creator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now discord-voice-creator
sudo systemctl status discord-voice-creator --no-pager
sudo journalctl -u discord-voice-creator -n 50 --no-pager
sudo journalctl -u discord-voice-creator -f
```

กด Ctrl+C ออกจากการดู logs ไม่ได้หยุด service สำหรับแก้ `.env` หรืออัปเดตโค้ด:

```bash
sudo systemctl restart discord-voice-creator
sudo systemctl status discord-voice-creator --no-pager
```

หยุดด้วย `sudo systemctl stop discord-voice-creator` และยกเลิกเริ่มตอนเปิดเครื่องด้วย `sudo systemctl disable discord-voice-creator` หลังไฟล์ service เปลี่ยนต้อง `daemon-reload` ก่อน restart หากเริ่มผิดซ้ำจน systemd จำกัด ให้แก้สาเหตุแล้ว `sudo systemctl reset-failed discord-voice-creator` และ start ใหม่ ห้ามรัน `python bot.py` พร้อม service

VPS ต้องเปิดต่อเนื่องและเชื่อมต่อ Discord ได้ systemd เริ่มตอน boot และ restart เมื่อ process ล้ม แต่ไม่รับประกัน uptime ของผู้ให้บริการหรือ Discord เมื่อ restart ระหว่างงาน ห้องที่สำเร็จแล้วคงอยู่ และงานที่เหลือไม่ทำต่อเอง

## 9. แก้ปัญหา

| อาการ | สิ่งที่ตรวจ |
|---|---|
| ไม่พบ DISCORD_TOKEN | `.env` อยู่ข้าง bot.py, ชื่อไม่ลงท้าย .txt, แก้ placeholder แล้ว |
| Token ไม่ถูกต้อง | ใช้ Bot Token ล่าสุดจากหน้า Bot แล้ว restart |
| ไม่เห็น Slash commands | รอ sync, ตรวจ scopes/Use Application Commands/Integrations, TEST_GUILD_ID ถูกเซิร์ฟเวอร์, รีโหลด Discord |
| Missing Access / Missing Permissions | บอทอยู่ในเซิร์ฟเวอร์และ View Channels/Manage Channels ไม่ถูก overrides ปฏิเสธ |
| Category พื้นที่ไม่พอ | นับรวมช่องข้อความและเสียง แบ่งงานไป Category อื่น |
| Progress ค้าง | อาจรอ rate limit ดู logs อย่าสั่งซ้ำหรือ restart เพื่อเร่ง |
| ไฟล์อ่านไม่ได้ | บันทึกเป็น UTF-8 ใน Notepad ไม่ใช่ ANSI/UTF-16 และแนบ .txt |
| service ไม่เริ่ม | ตรวจ paths, venv, เจ้าของ/สิทธิ์ .env และ journalctl |
| งานหยุดกลางทาง | ตรวจห้องจริงและสรุปก่อนสั่งใหม่ ไฟล์อาจสร้างชื่อซ้ำ เลขต่อเริ่มจากห้องที่ยังอยู่ |

## 10. ตรวจโค้ดและแหล่งอ้างอิง

```powershell
.\.venv\Scripts\python.exe -m py_compile bot.py
.\.venv\Scripts\python.exe -c "import bot; print([c.name for c in bot.bot.tree.get_commands()])"
```

การ import ไม่ login และไม่ต้องมี Token การทดสอบออนไลน์ต้องใช้ Token ของคุณและเซิร์ฟเวอร์ทดลองก่อนสร้างชุดใหญ่

ตรวจข้อมูลเอกสารเมื่อ 8 ตุลาคม 2026:

- [Discord Channel Resource: ความยาวชื่อและ Category 50 ช่อง](https://docs.discord.com/developers/resources/channel)
- [Discord Error Codes: 30013 maximum guild channels (500)](https://docs.discord.com/developers/topics/opcodes-and-status-codes)
- [Discord OAuth2: bot และ applications.commands](https://docs.discord.com/developers/topics/oauth2)
- [Discord Rate Limits](https://docs.discord.com/developers/topics/rate-limits)
- [discord.py API](https://discordpy.readthedocs.io/en/stable/api.html)
- [discord.py Interactions](https://discordpy.readthedocs.io/en/stable/interactions/api.html)

ข้อจำกัดอาจเปลี่ยนได้ อย่าเพิ่มค่าคงที่ใน bot.py โดยไม่ตรวจเอกสารและทดสอบ API ก่อน
#   d i s c o r d b o t _ c r e a t e r o o m  
 