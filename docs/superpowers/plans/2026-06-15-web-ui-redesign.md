# Web UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the IrrigaTOP Flask web UI to the approved "Botanical Calm" design with a light/dark theme toggle, without changing any backend behavior or the no-reload AJAX control flow.

**Architecture:** Two files change — `web/templates/index.html` (new markup, webfonts, theme init/toggle script, and the existing control behavior re-wired to the new markup via jQuery) and `web/static/styles.css` (themed CSS variables + the restyle). No backend/`app.py` change. All controls keep their endpoints (`/`, `/status`, `/health`, `/intensity`, `/pump`) and form field names (`action`, `slider`, `pump_id`). Theme is a `data-theme` attribute on `<html>` driving CSS-variable overrides, defaulting to `prefers-color-scheme` and persisted in `localStorage`.

**Tech Stack:** Flask/Jinja template, jQuery 3.6 (kept), vanilla CSS custom properties, Google Fonts (Fraunces + Hanken Grotesk) with system fallbacks. Verification via Docker (web image + `eclipse-mosquitto`) and headless Chromium (`zenika/alpine-chrome`).

**Testing note:** No JS unit-test framework exists in this repo and this is a static restyle, so verification is (a) **contract regression** against a live broker and (b) **visual render** checks in both themes — not TDD unit tests.

**Reference:** Approved prototype at `docs/superpowers/specs/assets/web-ui-redesign-prototype.html`; preview image at `docs/superpowers/specs/assets/web-ui-redesign-preview.png`; spec at `docs/superpowers/specs/2026-06-15-web-ui-redesign-design.md`.

**Hard constraints (must not break):**
- No page reloads / no navigation — every control stays AJAX.
- Endpoints and field names (`action`, `slider`, `pump_id`) unchanged.
- Same controls, Portuguese copy, "IrrigaTOP" name, 5s status/health polling.

---

### Task 1: Replace the stylesheet with the themed "Botanical Calm" CSS

**Files:**
- Modify (full replace): `web/static/styles.css`

- [ ] **Step 1: Overwrite `web/static/styles.css` with the exact contents below**

```css
:root {
  --paper: #efece3;
  --card: #f8f6f0;
  --ink: #1c2a22;
  --ink-dim: #6d7a70;
  --line: rgba(28, 42, 34, 0.10);
  --green: #2e7d52;
  --green-bright: #46a86e;
  --clay: #bb6240;
  --btn-on-bg: #2e7d52;
  --btn-on-text: #f4f7f2;
  --glow: rgba(70, 168, 110, 0.16);
  --grain-opacity: 0.5;
  --grain-blend: multiply;
  --thumb: var(--paper);

  --radius-sm: 13px;
  --serif: 'Fraunces', Georgia, serif;
  --sans: 'Hanken Grotesk', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

[data-theme="dark"] {
  --paper: #0f1613;
  --card: #18211c;
  --ink: #e9ece4;
  --ink-dim: #8e9b90;
  --line: rgba(255, 255, 255, 0.11);
  --green: #4fae74;
  --green-bright: #62c489;
  --clay: #cd7d57;
  --btn-on-bg: #2f8457;
  --btn-on-text: #f4f7f2;
  --glow: rgba(70, 168, 110, 0.20);
  --grain-opacity: 0.5;
  --grain-blend: screen;
  --thumb: #cfe6d8;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
  background: radial-gradient(120% 70% at 50% -10%, var(--glow), transparent 55%), var(--paper);
  position: relative;
  transition: background .35s, color .35s;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: var(--grain-opacity);
  mix-blend-mode: var(--grain-blend);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
}

.shell { position: relative; z-index: 1; max-width: 430px; margin: 0 auto; padding: 26px 22px 48px; }

header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px; }
.brand { display: flex; align-items: center; gap: 10px; }
.leaf { width: 26px; height: 26px; color: var(--green); }
.wordmark { font-family: var(--serif); font-weight: 500; font-size: 25px; letter-spacing: -0.4px; }
.wordmark i { font-style: italic; color: var(--green); }

.head-right { display: flex; align-items: center; gap: 10px; }
.chip {
  display: inline-flex; align-items: center; gap: 7px;
  font-size: 12px; font-weight: 600; color: var(--green);
  background: color-mix(in srgb, var(--green) 12%, transparent);
  padding: 6px 11px; border-radius: 999px;
}
.chip .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green-bright); box-shadow: 0 0 0 3px color-mix(in srgb, var(--green) 20%, transparent); }
.chip.offline { color: var(--ink-dim); background: var(--line); }
.chip.offline .dot { background: var(--ink-dim); box-shadow: none; }

.theme-btn {
  appearance: none; cursor: pointer; width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid var(--line); background: var(--card); color: var(--ink);
  display: grid; place-items: center; transition: .2s;
}
.theme-btn svg { width: 17px; height: 17px; }
.theme-btn .moon { display: none; }
[data-theme="dark"] .theme-btn .moon { display: block; }
[data-theme="dark"] .theme-btn .sun { display: none; }

.eyebrow { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: var(--ink-dim); font-weight: 600; margin: 0 0 12px 2px; }

.toggle {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0;
  border: 1px solid var(--line); border-radius: 999px; padding: 4px;
  background: var(--card); margin-bottom: 28px;
}
.toggle button {
  appearance: none; border: none; background: transparent; cursor: pointer;
  font-family: var(--sans); font-size: 14px; font-weight: 600; color: var(--ink-dim);
  padding: 12px; border-radius: 999px; transition: .2s;
}
.toggle button.active { background: var(--ink); color: var(--paper); }

.status { margin-bottom: 30px; }
.status-line { font-family: var(--serif); font-weight: 400; font-size: 30px; letter-spacing: -0.5px; line-height: 1.15; }
.status-line b { font-weight: 600; color: var(--green); font-style: italic; }
.status[data-state="off"] .status-line b { color: var(--clay); }
.status-sub { margin-top: 8px; font-size: 13px; color: var(--ink-dim); display: flex; align-items: center; gap: 7px; }
.status-sub .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green-bright); }
.status[data-state="off"] .status-sub .dot { background: var(--ink-dim); }

.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; margin-bottom: 34px; }
.actions .pulse { grid-column: 1 / -1; }
.act {
  appearance: none; cursor: pointer; font-family: var(--sans);
  border: 1px solid var(--line); background: var(--card); color: var(--ink);
  border-radius: var(--radius-sm); padding: 17px; font-size: 15px; font-weight: 600; letter-spacing: .3px;
  transition: .18s;
}
.act:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }
.act .k { display: block; font-size: 11px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; opacity: .55; margin-bottom: 3px; }
.act.on.active { background: var(--btn-on-bg); border-color: var(--btn-on-bg); color: var(--btn-on-text); }
.act.on.active .k { opacity: .7; }
.act.off.active { background: var(--clay); border-color: var(--clay); color: #fbf3ee; }
.pulse { color: var(--ink-dim); }

.intensity { border-top: 1px solid var(--line); padding-top: 26px; }
.intensity-top { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 18px; }
.intensity-label { font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: var(--ink-dim); font-weight: 600; padding-bottom: 14px; }
.reading { font-family: var(--serif); font-weight: 400; line-height: 0.85; letter-spacing: -2px; }
.reading .num { font-size: 74px; }
.reading .pct { font-size: 26px; color: var(--green); margin-left: 2px; }

.slider-wrap { display: flex; align-items: center; gap: 16px; }
input[type="range"] {
  flex: 1; -webkit-appearance: none; height: 4px; border-radius: 2px;
  background: linear-gradient(to right, var(--green) 0 0%, var(--line) 0% 100%);
  outline: none;
}
input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; width: 26px; height: 26px; border-radius: 50%;
  background: var(--thumb); border: 2px solid var(--green); cursor: pointer;
  box-shadow: 0 2px 8px rgba(46, 125, 82, 0.30);
}
input[type="range"]::-moz-range-thumb {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--thumb); border: 2px solid var(--green); cursor: pointer;
}
.num-box {
  width: 58px; padding: 9px 0; text-align: center; font-family: var(--sans);
  font-size: 15px; font-weight: 700; color: var(--ink);
  background: transparent; border: 1px solid var(--line); border-radius: 10px;
}

.toast {
  position: fixed; bottom: 26px; left: 50%; transform: translateX(-50%) translateY(120px); z-index: 2;
  background: var(--ink); color: var(--paper);
  font-size: 13px; font-weight: 600; padding: 12px 20px; border-radius: 999px;
  display: inline-flex; align-items: center; gap: 9px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  opacity: 0; transition: opacity .3s ease, transform .3s ease;
}
.toast::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--green-bright); }
.toast.error::before { background: var(--clay); }
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
```

- [ ] **Step 2: Commit**

```bash
git add web/static/styles.css
git commit -m "feat(web): Botanical Calm themed stylesheet with light/dark"
```

---

### Task 2: Rewrite the template markup, fonts, theme toggle, and re-wire control JS

**Files:**
- Modify (full replace): `web/templates/index.html`

Notes for the engineer:
- Action buttons are `type="button"` with `data-action` (NOT form submits) — this guarantees no navigation/reload.
- The status text comes from polling `/status`; map device payloads `ON`/`OFF`/`PULSE` to Portuguese display words. Unknown/`No status available` falls back to the raw text.
- The slider fill is painted via inline `background` using CSS vars so it stays theme-aware.
- The theme init script lives in `<head>` (before body) to avoid a flash of the wrong theme; it also honors a `?theme=` query param purely so the verification step can screenshot each theme.

- [ ] **Step 1: Overwrite `web/templates/index.html` with the exact contents below**

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IrrigaTOP</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,ital,wght@9..144,0,400;9..144,0,500;9..144,0,600;9..144,1,500;9..144,1,600&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
  <script>
    (function () {
      try {
        var params = new URLSearchParams(location.search);
        var saved = params.get('theme') || localStorage.getItem('irrigatop-theme');
        var theme = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', theme);
      } catch (e) {
        document.documentElement.setAttribute('data-theme', 'light');
      }
    })();
  </script>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"
          integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4="
          crossorigin="anonymous"></script>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand">
        <svg class="leaf" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 20A7 7 0 0 1 4 13c0-5 4-9 16-9 0 8-5 13-9 14z"/>
          <path d="M5 19c4-3 7-5 9-9"/>
        </svg>
        <span class="wordmark">Irriga<i>TOP</i></span>
      </div>
      <div class="head-right">
        <button class="theme-btn" id="themeBtn" type="button" aria-label="Alternar tema">
          <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        </button>
        <span class="chip offline" id="conn-chip"><span class="dot"></span><span id="conn-text">—</span></span>
      </div>
    </header>

    <p class="eyebrow">Bomba ativa</p>
    <div class="toggle" id="pump-toggle">
      <button type="button" class="active" data-value="1">Bomba 1</button>
      <button type="button" data-value="2">Bomba 2</button>
    </div>

    <div class="status" id="status" data-state="">
      <div class="status-line">A bomba está <b id="status-word">—</b></div>
      <div class="status-sub"><span class="dot"></span><span id="status-sub">Bomba 1</span></div>
    </div>

    <div class="actions">
      <button class="act on" type="button" data-action="ON"><span class="k">Ligar</span>ON</button>
      <button class="act off" type="button" data-action="OFF"><span class="k">Desligar</span>OFF</button>
      <button class="act pulse" type="button" data-action="PULSE"><span class="k">Pulso 2s</span>PULSE</button>
    </div>

    <div class="intensity">
      <div class="intensity-top">
        <span class="intensity-label">Intensidade</span>
        <span class="reading"><span class="num" id="intensity-num">0</span><span class="pct">%</span></span>
      </div>
      <div class="slider-wrap">
        <input type="range" id="range" min="0" max="100" value="0">
        <input class="num-box" type="number" id="rangenumber" min="0" max="100" value="0">
      </div>
    </div>
  </div>

  <div id="notification" class="toast"></div>

  <script>
    // Theme toggle (vanilla; init already ran in <head>)
    document.getElementById('themeBtn').addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('irrigatop-theme', next); } catch (e) {}
    });
  </script>

  <script>
    $(function () {
      var $notification = $('#notification');
      function showNotification(message, type) {
        type = type || 'error';
        $notification.text(message).removeClass('error success').addClass(type).addClass('show');
        setTimeout(function () { $notification.removeClass('show'); }, 3000);
      }

      var STATE_WORDS = { ON: 'ligada', OFF: 'desligada', PULSE: 'em pulso' };
      var STATE_CLASS = { ON: 'on', OFF: 'off', PULSE: 'pulse' };

      function renderStatus(raw) {
        var key = (raw || '').toUpperCase();
        $('#status-word').text(STATE_WORDS[key] || raw || '—');
        var state = STATE_CLASS[key] || '';
        $('#status').attr('data-state', state);
        $('.act').removeClass('active');
        if (state === 'on') { $('.act.on').addClass('active'); }
        else if (state === 'off') { $('.act.off').addClass('active'); }
        var pumpLabel = $('#pump-toggle button.active').text();
        $('#status-sub').text((state === 'on' ? 'Regando agora · ' : 'Em espera · ') + pumpLabel);
      }

      function updateStatus() {
        $.getJSON('/status')
          .done(function (data) {
            if (data.success) { renderStatus(data.status); }
            else { showNotification(data.message); }
          })
          .fail(function () { showNotification('Falha ao obter o status da bomba'); });

        $.getJSON('/health')
          .done(function (data) {
            var online = data.status === 'online';
            $('#conn-chip').removeClass('online offline').addClass(online ? 'online' : 'offline');
            $('#conn-text').text(online ? 'Online' : 'Offline');
          })
          .fail(function () {
            $('#conn-chip').removeClass('online').addClass('offline');
            $('#conn-text').text('Offline');
          });
      }
      setInterval(updateStatus, 5000);
      updateStatus();

      // Action buttons (ON / OFF / PULSE)
      $('.act').on('click', function () {
        var action = $(this).data('action');
        $.ajax({
          url: '/', type: 'POST', data: { action: action },
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
          success: function (response) {
            if (response.success) { showNotification(response.message, 'success'); updateStatus(); }
            else { showNotification(response.message); }
          },
          error: function () { showNotification('Falha ao enviar o comando para a bomba'); }
        });
      });

      // Intensity slider + number
      var $slider = $('#range'), $num = $('#rangenumber'), $reading = $('#intensity-num');
      var debounceTimeout;
      function debounce(fn, delay) { clearTimeout(debounceTimeout); debounceTimeout = setTimeout(fn, delay); }
      function paintSlider(value) {
        var min = parseInt($slider.attr('min'), 10), max = parseInt($slider.attr('max'), 10);
        var pct = ((value - min) / (max - min)) * 100;
        $slider.css('background', 'linear-gradient(to right, var(--green) 0 ' + pct + '%, var(--line) ' + pct + '% 100%)');
      }
      function sendIntensity(value) {
        $.post('/intensity', { slider: value })
          .done(function (response) {
            if (response.success) { showNotification(response.message, 'success'); }
            else { showNotification(response.message); }
          })
          .fail(function () { showNotification('Falha ao atualizar a intensidade'); });
      }
      $slider.on('input change', function () {
        var value = $(this).val();
        $num.val(value); $reading.text(value); paintSlider(value);
        debounce(function () { sendIntensity(value); }, 300);
      });
      $num.on('change', function () {
        var value = parseInt($(this).val(), 10);
        if (isNaN(value)) { value = 0; }
        value = Math.max(0, Math.min(100, value));
        $(this).val(value); $slider.val(value); $reading.text(value); paintSlider(value);
        sendIntensity(value);
      });
      paintSlider($slider.val());

      // Pump selector (segmented toggle)
      $('#pump-toggle button').on('click', function () {
        $('#pump-toggle button').removeClass('active');
        $(this).addClass('active');
        var pumpId = $(this).data('value');
        $.post('/pump', { pump_id: pumpId })
          .done(function (response) {
            if (response.success) { showNotification(response.message, 'success'); }
            else { showNotification(response.message); }
          })
          .fail(function () { showNotification('Falha ao selecionar a bomba'); });
      });
    });
  </script>
</body>
</html>
```

- [ ] **Step 2: Sanity-check the template renders (no Jinja/syntax error)**

Run:
```bash
cd web && python -c "from jinja2 import Environment, FileSystemLoader; Environment(loader=FileSystemLoader('templates')).get_template('index.html'); print('template parses OK')"
```
Expected: `template parses OK`

- [ ] **Step 3: Commit**

```bash
git add web/templates/index.html
git commit -m "feat(web): Botanical Calm template + theme toggle, behavior preserved"
```

---

### Task 3: Contract regression — verify endpoints and field names survive

**Files:** none (verification only). Reuses the Docker harness pattern from the robustness sweep.

- [ ] **Step 1: Build the web image**

Run:
```bash
cd /1.git-repos/irrigatop/web && docker build -q -t irrigatop-web .
```
Expected: prints an image sha, no error.

- [ ] **Step 2: Start a throwaway broker + app on a shared network**

Run:
```bash
cd /tmp && docker rm -f irw-app irw-mqtt >/dev/null 2>&1
docker network create irw-net 2>/dev/null || true
printf 'listener 1883 0.0.0.0\nallow_anonymous true\n' > /tmp/irw-mqtt.conf
docker run -d --name irw-mqtt --network irw-net -v /tmp/irw-mqtt.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto:2-openssl >/dev/null
sleep 3
docker run -d --name irw-app --network irw-net \
  -e MQTT_BROKER=irw-mqtt -e MQTT_PORT=1883 -e MQTT_TOPIC=irrigation \
  -e MQTT_USERNAME=x -e MQTT_PASSWORD=x \
  -e BASIC_AUTH_USERNAME=u -e BASIC_AUTH_PASSWORD=p \
  -v /tmp/irw-data:/app/instance irrigatop-web
sleep 28
docker ps --filter name=irw-app --format '{{.Status}}'
docker logs irw-app 2>&1 | grep -iE "MQTT connected successfully|Subscribed to topics" | tail -2
```
Expected: `irw-app` shows `Up ...`, plus lines showing `MQTT connected successfully` and `Subscribed to topics: irrigation/status/action, irrigation/health`.

- [ ] **Step 3: Verify each control still hits its endpoint with the right field name**

Run:
```bash
# action=ON reaches the device-facing topic
docker exec -d irw-mqtt sh -c "mosquitto_sub -t irrigation/action -C 1 > /tmp/act.txt 2>&1"; sleep 1
docker exec irw-app python -c "import urllib.request,base64;req=urllib.request.Request('http://127.0.0.1:5000/',data=b'action=ON',headers={'Authorization':'Basic '+base64.b64encode(b'u:p').decode(),'X-Requested-With':'XMLHttpRequest','Content-Type':'application/x-www-form-urlencoded'});print(urllib.request.urlopen(req).read().decode())"
sleep 1; echo -n "device received: "; docker exec irw-mqtt cat /tmp/act.txt
# intensity uses field 'slider'
docker exec irw-app python -c "import urllib.request;print(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:5000/intensity',data=b'slider=80')).read().decode())"
# pump uses field 'pump_id'
docker exec irw-app python -c "import urllib.request;print(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:5000/pump',data=b'pump_id=2')).read().decode())"
# status + health round-trip
docker exec irw-mqtt mosquitto_pub -t irrigation/status/action -m ON
docker exec irw-mqtt mosquitto_pub -t irrigation/health -m alive; sleep 2
docker exec irw-app python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:5000/status').read().decode())"
docker exec irw-app python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"
# unauth root is 401
docker exec irw-app python -c "import urllib.request, urllib.error
try:
    urllib.request.urlopen('http://127.0.0.1:5000/')
except urllib.error.HTTPError as e:
    print('root unauth ->', e.code)"
```
Expected:
- `device received: ON`
- intensity JSON `success: true ... value 80`
- pump JSON `success: true ... pump_id 2`
- `/status` -> `{"status":"ON","success":true}`
- `/health` -> `{"status":"online"}`
- `root unauth -> 401`

- [ ] **Step 4: Tear down**

Run:
```bash
docker rm -f irw-app irw-mqtt >/dev/null 2>&1; docker network rm irw-net >/dev/null 2>&1
docker run --rm -v /tmp:/c alpine sh -c "rm -rf /c/irw-data /c/irw-mqtt.conf /c/act.txt" >/dev/null 2>&1 || true
echo "cleaned"
```
Expected: `cleaned`. If any assertion in Step 3 failed, STOP and fix the template/JS before continuing.

---

### Task 4: Visual + theme render verification

**Files:** none (verification only).

- [ ] **Step 1: Render the live template (light and dark) via headless Chromium**

The template needs Flask context (`url_for`). Render the served page from a running container instead of the raw file. Start a minimal app container (no broker needed; the page renders without MQTT):

```bash
cd /1.git-repos/irrigatop/web && docker build -q -t irrigatop-web .
docker rm -f irw-render >/dev/null 2>&1
docker run -d --name irw-render -p 5099:5000 \
  -e MQTT_BROKER=127.0.0.1 -e MQTT_PORT=1883 \
  -e BASIC_AUTH_USERNAME=u -e BASIC_AUTH_PASSWORD=p \
  -v /tmp/irw-render-data:/app/instance irrigatop-web
sleep 20
```

- [ ] **Step 2: Screenshot both themes**

The page is behind basic auth and needs JS to apply the theme; use the `?theme=` param and embed credentials in the URL. Run headless Chromium against the host port:

```bash
cd /tmp && rm -f shot-light.png shot-dark.png
for t in light dark; do
  docker run --rm --network host -v /tmp:/work zenika/alpine-chrome:with-puppeteer \
    chromium-browser --headless --no-sandbox --disable-gpu --hide-scrollbars \
    --window-size=430,900 --virtual-time-budget=5000 --screenshot=/work/shot-$t.png \
    "http://u:p@localhost:5099/?theme=$t" 2>&1 | grep -iE "bytes written"
done
ls -la /tmp/shot-light.png /tmp/shot-dark.png
```
Expected: two PNGs written. (If basic-auth-in-URL is rejected by Chromium, instead set the theme via localStorage is not possible headless; fall back to temporarily setting `BASIC_AUTH` env to empty is NOT allowed — keep auth. As a fallback, render the approved prototype file `docs/superpowers/specs/assets/web-ui-redesign-prototype.html?theme=$t` which is visually identical to the template body.)

- [ ] **Step 3: Inspect the screenshots**

Open `/tmp/shot-light.png` and `/tmp/shot-dark.png` (Read tool). Confirm: wordmark in serif, segmented pump toggle, editorial status line, ON/OFF/PULSE buttons, big serif intensity numeral, correct theme colors (warm paper vs. green-black), and the sun/moon icon matches the theme.

- [ ] **Step 4: Tear down**

```bash
docker rm -f irw-render >/dev/null 2>&1
docker run --rm -v /tmp:/c alpine sh -c "rm -rf /c/irw-render-data" >/dev/null 2>&1 || true
echo "cleaned"
```

---

### Task 5: Final review commit

- [ ] **Step 1: Confirm only the two intended files changed**

Run:
```bash
cd /1.git-repos/irrigatop && git status --short && git log --oneline -3
```
Expected: working tree clean (Tasks 1 and 2 already committed); the two feature commits present.

- [ ] **Step 2:** If any follow-up tweaks were made during verification, commit them with a clear message. Otherwise nothing to do.

---

## Notes / known follow-ups (out of scope for this plan)

- **Self-hosting fonts:** the design loads Fraunces + Hanken Grotesk from Google Fonts with `Georgia`/`system-ui` fallbacks. Self-hosting under `web/static/fonts/` to remove the external dependency is a recommended future hardening, not required here.
- The firmware-served fallback page (`data/index.html`) is intentionally untouched.
- **SRI hardening:** the jQuery CDN tag now carries `integrity`/`crossorigin`
  (the old template loaded it without Subresource Integrity). The Google Fonts
  stylesheet link cannot use a stable SRI hash, so it relies on the
  `Georgia`/`system-ui` fallback stacks if the request is blocked.
