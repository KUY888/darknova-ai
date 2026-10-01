const $ = s => document.querySelector(s);
const msgs = $('#msgs'), chat = $('#chat'), box = $('#msg'), sendBtn = $('#send'), sel = $('#mode');
const M = {
  code: {h: 'ให้ช่วยเขียนโค้ดอะไรดี?', p: 'ขอให้เขียน แก้ หรืออธิบายโค้ด...',
    c: ['เขียนฟังก์ชัน Python อ่านไฟล์ CSV', 'อธิบายโค้ดที่ฉันจะวางให้', 'แปลง JavaScript เป็น TypeScript']},
  plan: {h: 'อยากทำโปรเจกต์อะไร?', p: 'บอกเป้าหมาย แล้วจะวางแผนให้...',
    c: ['วางแผนทำเว็บขายของออนไลน์', 'วางแผนทำแอปจดบันทึก', 'วางแผนทำ REST API ด้วย Flask']},
  debug: {h: 'เจอ Error อะไร?', p: 'วาง Error หรือ Traceback ที่นี่...',
    c: ['แก้ ModuleNotFoundError ใน Python', 'ทำไม fetch ถึงขึ้น CORS error', 'วาง Traceback ให้ช่วยหาสาเหตุ']},
};
let mode = 'code', busy = false, timer = null, hist = [];
try { hist = JSON.parse(sessionStorage.getItem('dn_hist') || '[]'); } catch {}

function render(md) {
  if (window.marked && window.DOMPurify) return DOMPurify.sanitize(marked.parse(md));
  const d = document.createElement('div'); d.textContent = md; return d.innerHTML.replace(/\n/g, '<br>');
}
async function copy(t, b, label) {
  try { await navigator.clipboard.writeText(t); b.textContent = 'คัดลอกแล้ว'; } catch { b.textContent = 'ไม่สำเร็จ'; }
  setTimeout(() => b.textContent = label, 1500);
}
function enhance(el) {
  el.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (window.hljs && code) hljs.highlightElement(code);
    const lang = ((code && code.className.match(/language-(\w+)/)) || [])[1] || 'code';
    const text = (code || pre).innerText;
    const w = document.createElement('div'), h = document.createElement('div'), s = document.createElement('span'), b = document.createElement('button');
    w.className = 'cb'; h.className = 'cb-h'; s.textContent = lang; b.textContent = 'Copy';
    b.onclick = () => copy(text, b, 'Copy');
    h.append(s, b); pre.replaceWith(w); w.append(h, pre);
  });
}
function add(role, text, cls = '') {
  msgs.querySelector('.hero')?.remove();
  const d = document.createElement('div'); d.className = 'm ' + (role === 'user' ? 'u' : 'a') + ' ' + cls;
  if (cls === 'thinking') d.innerHTML = '<span class="dots"><i></i><i></i><i></i></span>';
  else if (role === 'ai' && !cls) {
    d.innerHTML = render(text); enhance(d);
    const a = document.createElement('button'); a.className = 'act'; a.textContent = 'คัดลอก';
    a.onclick = () => copy(text, a, 'คัดลอก'); d.appendChild(a);
  } else d.textContent = text;
  msgs.appendChild(d); chat.scrollTop = chat.scrollHeight; return d;
}
function hero() {
  msgs.innerHTML = '';
  const d = document.createElement('div'); d.className = 'hero';
  d.innerHTML = '<div class="mark">✦</div>';
  const h = document.createElement('h2'); h.textContent = M[mode].h; d.appendChild(h);
  M[mode].c.forEach(t => {
    const b = document.createElement('button'); b.className = 'chip'; b.textContent = t;
    b.onclick = () => { box.value = t; grow(); box.focus(); }; d.appendChild(b);
  });
  msgs.appendChild(d);
}
function setMode(m) {
  mode = m; sel.value = m; box.placeholder = M[m].p;
  document.querySelectorAll('.mode').forEach(x => x.classList.toggle('on', x.dataset.mode === m));
  if (msgs.querySelector('.hero')) hero();
}
function grow() { box.style.height = 'auto'; box.style.height = Math.min(box.scrollHeight, 200) + 'px'; }
function lock(sec) {
  clearInterval(timer);
  let left = sec;
  const tick = () => {
    const off = left > 0;
    box.disabled = sendBtn.disabled = off;
    box.placeholder = off ? `ส่งข้อความไม่ได้ชั่วคราว (${left} วินาที)` : M[mode].p;
    if (!off) clearInterval(timer);
    left--;
  };
  tick(); timer = setInterval(tick, 1000);
}
async function call(url, body, label) {
  if (busy) return; busy = true;
  const th = add('ai', '', 'thinking');
  try {
    const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const j = await r.json(); th.remove();
    if (j.login) { showLogin(); busy = false; return; }
    if (!r.ok) {
      add('ai', j.error || 'เกิดข้อผิดพลาด', j.warning || j.restricted ? 'warn' : 'err');
      if (j.restricted) lock(j.retry_after);
    } else if (url.endsWith('scan')) add('ai', j.reply, 'scan');
    else {
      add('ai', j.reply);
      hist.push({role: 'user', content: label}, {role: 'assistant', content: j.reply});
      sessionStorage.setItem('dn_hist', JSON.stringify(hist.slice(-40)));
    }
  } catch { th.remove(); add('ai', 'เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ ตรวจสอบว่า main.py ยังรันอยู่', 'err'); }
  busy = false;
}
function send() {
  const t = box.value.trim(); if (!t || busy || box.disabled) return;
  box.value = ''; grow(); add('user', t);
  call('/api/chat', {mode, message: t, history: hist.slice(-20)}, t);
}
function drawer(open) { $('#drawer').classList.toggle('open', open); $('#scrim').classList.toggle('on', open); }
function newChat() { hist = []; sessionStorage.removeItem('dn_hist'); hero(); drawer(false); }

sendBtn.onclick = send;
box.oninput = grow;
box.onkeydown = e => {  // Enter ส่งเฉพาะบนเดสก์ท็อป บนมือถือขึ้นบรรทัดใหม่
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && matchMedia('(pointer:fine)').matches) { e.preventDefault(); send(); }
};
sel.onchange = () => setMode(sel.value);
document.querySelectorAll('.mode').forEach(b => b.onclick = () => { setMode(b.dataset.mode); drawer(false); });
$('#menu').onclick = () => drawer(true);
$('#scrim').onclick = () => drawer(false);
$('#clear').onclick = $('#new').onclick = newChat;
$('#scan').onclick = () => {
  drawer(false);
  const p = prompt('พาธโฟลเดอร์โปรเจกต์ (เช่น ~/darknova-ai)'); if (!p) return;
  add('user', 'Scan: ' + p); call('/api/scan', {path: p}, p);
};
hist.length ? hist.forEach(m => add(m.role === 'user' ? 'user' : 'ai', m.content)) : hero();
setMode(mode);

function showLogin() { $('#login').hidden = false; $('#pw').focus(); }
async function doLogin() {
  try {
    const r = await fetch('/api/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({password: $('#pw').value})});
    const j = await r.json();
    if (r.ok) { $('#login').hidden = true; $('#pw').value = ''; $('#lerr').textContent = ''; }
    else $('#lerr').textContent = j.error || 'เข้าสู่ระบบไม่สำเร็จ';
  } catch { $('#lerr').textContent = 'เชื่อมต่อเซิร์ฟเวอร์ไม่ได้'; }
}
$('#go').onclick = doLogin;
$('#pw').onkeydown = e => { if (e.key === 'Enter') doLogin(); };
$('#logout').onclick = async () => { await fetch('/api/logout', {method: 'POST'}); newChat(); showLogin(); };
fetch('/api/status').then(r => r.json()).then(s => {
  $('#scan').hidden = !s.scan; $('#logout').hidden = !s.auth_required;
  if (s.auth_required && !s.authed) showLogin();
}).catch(() => {});
