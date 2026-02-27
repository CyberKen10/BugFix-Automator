"""Interfaz visual web para operar BugFix Automator."""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
from typing import Any
from urllib.parse import urlparse

from bugfix_automator.config import JiraConfig, load_env_file


HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>BugFix Automator</title>
  <style>
    :root{
      --bg:#0b1020;--surface:#121a33;--surface-2:#1b2647;
      --text:#e8edf7;--muted:#a9b5d0;
      --brand:#3a82f7;--brand-2:#6f5cff;
      --ok:#14b86f;--danger:#ff5f7a;
      --border:rgba(255,255,255,.12);
    }
    *{box-sizing:border-box}
    body{margin:0;font-family:Inter,Segoe UI,Roboto,sans-serif;background:radial-gradient(circle at 20% -10%,#2a3a74 0%,transparent 45%),var(--bg);color:var(--text)}
    .layout{display:grid;grid-template-columns:260px 1fr;min-height:100vh}
    .sidebar{background:rgba(10,15,30,.75);backdrop-filter:blur(12px);border-right:1px solid var(--border);padding:28px 20px}
    .brand{font-weight:700;font-size:1.2rem;letter-spacing:.4px;margin-bottom:28px}
    .badge{display:inline-block;padding:6px 10px;border:1px solid var(--border);border-radius:999px;font-size:.75rem;color:var(--muted)}
    .main{padding:28px;display:flex;flex-direction:column;gap:18px}
    .card{background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid var(--border);border-radius:16px;padding:20px}
    .grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    .kpi{padding:16px;background:var(--surface);border:1px solid var(--border);border-radius:14px}
    .kpi small{color:var(--muted);display:block;margin-bottom:5px}
    .kpi strong{font-size:1.3rem;word-break:break-word}
    label{display:block;font-size:.85rem;color:var(--muted);margin-bottom:6px;font-weight:500}
    .input{background:var(--surface);color:var(--text);border:1px solid var(--border);padding:11px 12px;border-radius:10px;width:100%;font-size:.9rem}
    .input:focus{outline:none;border-color:var(--brand)}
    .btn{background:linear-gradient(90deg,var(--brand),var(--brand-2));color:#fff;border:0;padding:12px 18px;border-radius:10px;font-weight:600;cursor:pointer;font-size:.9rem}
    .btn:disabled{opacity:.55;cursor:not-allowed}
    .btn-add{background:var(--surface-2);color:var(--text);border:1px solid var(--border);padding:10px 14px;border-radius:10px;cursor:pointer;font-size:.85rem;white-space:nowrap}
    .btn-add:hover{background:var(--brand);border-color:var(--brand)}
    .form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
    .chips{display:flex;flex-wrap:wrap;gap:6px;min-height:34px;margin-bottom:8px}
    .chip{display:inline-flex;align-items:center;gap:4px;padding:5px 10px;background:rgba(58,130,247,.18);border:1px solid rgba(58,130,247,.4);border-radius:999px;font-size:.82rem;color:var(--text)}
    .chip.round-chip{background:rgba(111,92,255,.18);border-color:rgba(111,92,255,.4)}
    .chip button{background:none;border:none;color:var(--muted);cursor:pointer;font-size:1rem;padding:0 2px;line-height:1}
    .chip button:hover{color:var(--danger)}
    .status-add{display:flex;gap:8px}
    table{width:100%;border-collapse:collapse;font-size:.82rem}
    th,td{padding:8px 8px;border-bottom:1px solid var(--border);text-align:left}
    th{color:#c8d4ef;font-weight:600;white-space:nowrap;font-size:.78rem}
    td a{color:var(--brand);text-decoration:none}
    td a:hover{text-decoration:underline}
    .muted{color:var(--muted)}
    .msg{margin-top:10px;font-size:.9rem}
    .msg.ok{color:var(--ok)}.msg.err{color:var(--danger)}
    .empty-msg{text-align:center;color:var(--muted);padding:28px}
    @keyframes spin{to{transform:rotate(360deg)}}
    .spinner{display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle;margin-right:6px}
    @media(max-width:960px){.layout{grid-template-columns:1fr}.sidebar{display:none}.grid{grid-template-columns:1fr}.form-row{grid-template-columns:1fr}}
  </style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">BugFix Automator</div>
    <span class="badge">Enterprise Console</span>
    <p class="muted" style="margin-top:16px;line-height:1.6">
      Consulta issues de Jira por estado, estructura un Google Sheet existente
      con el formato BFV est&aacute;ndar y exporta los links autom&aacute;ticamente.
    </p>
    <p class="muted" style="line-height:1.5;font-size:.78rem">
      <strong style="color:var(--text)">Tip:</strong> Crea un Sheet vac&iacute;o en
      <a href="https://sheets.new" target="_blank" style="color:var(--brand)">sheets.new</a>,
      comp&aacute;rtelo con el Service Account como Editor, y pega la URL aqu&iacute;.
    </p>
  </aside>

  <main class="main">
    <section class="card">
      <h2 style="margin:0 0 16px">Configuraci&oacute;n</h2>
      <form id="runForm">
        <div class="form-row" style="margin-bottom:14px">
          <div>
            <label for="jiraUrl">Link del Epic / Proyecto en Jira</label>
            <input id="jiraUrl" class="input" placeholder="https://empresa.atlassian.net/browse/PROJ-123" required />
          </div>
          <div>
            <label for="sheetUrl">URL del Google Sheet destino</label>
            <input id="sheetUrl" class="input" placeholder="https://docs.google.com/spreadsheets/d/..." required />
          </div>
        </div>

        <div style="margin-bottom:16px">
          <label>Estados a buscar en Jira</label>
          <div class="chips" id="statusChips"></div>
          <div class="status-add">
            <input id="newStatus" class="input" style="flex:1" placeholder="Escribe un estado (ej: QA Failed) y pulsa Enter" />
            <button type="button" class="btn-add" id="addStatusBtn">+ Agregar</button>
          </div>
        </div>

        <div style="margin-bottom:14px">
          <label for="testerName">Nombre del Tester</label>
          <input id="testerName" class="input" placeholder="Ej: Juan, Maria..." />
        </div>

        <div style="margin-bottom:16px">
          <label>Tabs de Rondas adicionales (opcional)</label>
          <div class="chips" id="roundChips"></div>
          <div class="status-add">
            <input id="newRound" class="input" type="number" min="2" style="flex:1" placeholder="N&uacute;mero de ronda (ej: 2, 3, 4...)" />
            <button type="button" class="btn-add" id="addRoundBtn">+ Agregar Round</button>
          </div>
        </div>

        <button id="runBtn" class="btn" type="submit" style="width:100%">Generar Sheet con issues</button>
      </form>
    </section>

    <section class="grid">
      <div class="kpi"><small>Issues encontrados</small><strong id="kpiIssues">0</strong></div>
      <div class="kpi"><small>Estados filtrados</small><strong id="kpiStatuses" class="muted">&mdash;</strong></div>
      <div class="kpi"><small>Sheet generado</small><strong id="kpiSheet" class="muted">Sin ejecutar</strong></div>
    </section>

    <section class="card">
      <h3 style="margin-top:0">Contenido del Sheet &mdash; Hoja <em>Issues</em></h3>
      <div id="statusMsg" class="msg"></div>
      <div style="overflow:auto;margin-top:10px">
        <table>
          <thead>
            <tr>
              <th>Tester</th><th>URL Ticket</th><th>Estado</th>
            </tr>
          </thead>
          <tbody id="rows">
            <tr><td colspan="3" class="empty-msg">Configura los campos y genera un reporte para ver resultados</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </main>
</div>

<script>
(function(){
  var form = document.getElementById('runForm');
  var btn  = document.getElementById('runBtn');
  var rows = document.getElementById('rows');
  var msgEl = document.getElementById('statusMsg');
  var chipsEl = document.getElementById('statusChips');
  var roundChipsEl = document.getElementById('roundChips');
  var newStatusInput = document.getElementById('newStatus');
  var newRoundInput = document.getElementById('newRound');
  var BTN_LABEL = 'Generar Sheet con issues';
  var COLS = 3;

  var statuses = ['For Review'];
  var rounds = [];

  function setMsg(text, ok) {
    msgEl.className = 'msg ' + (ok ? 'ok' : 'err');
    msgEl.textContent = text;
  }

  function renderChips() {
    chipsEl.innerHTML = '';
    statuses.forEach(function(s) {
      var chip = document.createElement('span');
      chip.className = 'chip';
      chip.appendChild(document.createTextNode(s + ' '));
      var x = document.createElement('button');
      x.type = 'button';
      x.innerHTML = '&times;';
      x.addEventListener('click', function() {
        statuses = statuses.filter(function(v){ return v !== s; });
        renderChips();
      });
      chip.appendChild(x);
      chipsEl.appendChild(chip);
    });
  }

  function renderRoundChips() {
    roundChipsEl.innerHTML = '';
    rounds.sort(function(a,b){ return a-b; });
    rounds.forEach(function(n) {
      var chip = document.createElement('span');
      chip.className = 'chip round-chip';
      chip.appendChild(document.createTextNode('Round ' + n + ' '));
      var x = document.createElement('button');
      x.type = 'button';
      x.innerHTML = '&times;';
      x.addEventListener('click', function() {
        rounds = rounds.filter(function(v){ return v !== n; });
        renderRoundChips();
      });
      chip.appendChild(x);
      roundChipsEl.appendChild(chip);
    });
  }

  function addStatus() {
    var val = newStatusInput.value.trim();
    if (!val || statuses.indexOf(val) !== -1) return;
    statuses.push(val);
    renderChips();
    newStatusInput.value = '';
  }

  function addRound() {
    var val = parseInt(newRoundInput.value, 10);
    if (isNaN(val) || val < 2 || rounds.indexOf(val) !== -1) return;
    rounds.push(val);
    renderRoundChips();
    newRoundInput.value = '';
  }

  document.getElementById('addStatusBtn').addEventListener('click', addStatus);
  newStatusInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); addStatus(); }
  });
  document.getElementById('addRoundBtn').addEventListener('click', addRound);
  newRoundInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') { e.preventDefault(); addRound(); }
  });

  function showEmpty(text) {
    rows.innerHTML = '';
    var tr = document.createElement('tr');
    var td = document.createElement('td');
    td.colSpan = COLS;
    td.className = 'empty-msg';
    td.textContent = text;
    tr.appendChild(td);
    rows.appendChild(tr);
  }

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!statuses.length) { setMsg('Agrega al menos un estado.', false); return; }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Generando Sheet&hellip;';
    setMsg('Consultando Jira y configurando Google Sheet con estructura BFV&hellip;', true);

    try {
      var payload = JSON.stringify({
        jira_url:  document.getElementById('jiraUrl').value.trim(),
        sheet_url: document.getElementById('sheetUrl').value.trim(),
        tester:    document.getElementById('testerName').value.trim(),
        statuses:  statuses,
        rounds:    rounds
      });
      var r = await fetch('/api/generate', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: payload
      });
      var data = await r.json();
      if (!r.ok) throw new Error(data.error || 'Error desconocido');

      document.getElementById('kpiIssues').textContent = data.total_issues;
      document.getElementById('kpiStatuses').textContent = statuses.join(', ');

      var kpiSheet = document.getElementById('kpiSheet');
      kpiSheet.textContent = '';
      var a = document.createElement('a');
      a.href = data.sheet_url;
      a.target = '_blank';
      a.style.color = '#9ec0ff';
      a.textContent = 'Abrir Sheet';
      kpiSheet.appendChild(a);

      rows.innerHTML = '';
      if (!data.issues || !data.issues.length) {
        showEmpty('No se encontraron issues con esos estados.');
      } else {
        data.issues.forEach(function(row) {
          var tr = document.createElement('tr');

          var tdTester = document.createElement('td');
          tdTester.textContent = row[0] || '';
          tr.appendChild(tdTester);

          var tdUrl = document.createElement('td');
          var url = row[1] || '';
          if (url) {
            var lnk = document.createElement('a');
            lnk.href = url;
            lnk.target = '_blank';
            lnk.textContent = url.split('/').pop();
            tdUrl.appendChild(lnk);
          }
          tr.appendChild(tdUrl);

          var tdEstado = document.createElement('td');
          tdEstado.textContent = row[2] || '';
          tr.appendChild(tdEstado);

          rows.appendChild(tr);
        });
      }
      setMsg('Sheet configurado con ' + data.total_issues + ' issues. Abre el link para ver y editar.', true);
    } catch(err) {
      setMsg(String(err), false);
    } finally {
      btn.disabled = false;
      btn.textContent = BTN_LABEL;
    }
  });

  renderChips();
  renderRoundChips();
})();
</script>
</body>
</html>
"""


class BFVServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/generate":
            self.send_response(404)
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            payload = json.loads(raw_body)

            jira_url = payload.get("jira_url", "")
            statuses = payload.get("statuses", [])
            sheet_url = payload.get("sheet_url", "")
            tester = payload.get("tester", "")
            round_numbers = payload.get("rounds", [])

            if not jira_url:
                raise ValueError("Falta el link del proyecto Jira")
            if not statuses:
                raise ValueError("Agrega al menos un estado a buscar")
            if not sheet_url:
                raise ValueError("Falta la URL del Google Sheet destino")

            result = run_generation(jira_url, statuses, sheet_url, round_numbers, tester)
            self._json_response(result, 200)
        except Exception as exc:
            import traceback
            with open("D:/Chamba/BugFix-Automator/error.log", "w") as f:
                traceback.print_exc(file=f)
            self._json_response({"error": str(exc)}, 500)

    def _json_response(self, payload: dict[str, Any], status_code: int) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_generation(
    jira_url: str,
    statuses: list[str],
    sheet_url: str,
    round_numbers: list[int] | None = None,
    tester: str = "",
) -> dict[str, Any]:
    from bugfix_automator.drive_client import DriveClient
    from bugfix_automator.jira_client import JiraClient

    load_env_file()

    jira_email = os.environ.get("JIRA_EMAIL", "")
    jira_token = os.environ.get("JIRA_API_TOKEN", "")
    if not jira_email or not jira_token:
        raise ValueError("Faltan JIRA_EMAIL o JIRA_API_TOKEN en variables de entorno")

    sa_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
    if not sa_file:
        raise ValueError("Falta GOOGLE_SERVICE_ACCOUNT_FILE en variables de entorno")

    parsed = urlparse(jira_url.rstrip("/"))
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path_parts = [p for p in parsed.path.split("/") if p]
    project: str | None = None
    parent_key: str | None = None
    for i, part in enumerate(path_parts):
        if part == "projects" and i + 1 < len(path_parts):
            project = path_parts[i + 1]
            break
        if part == "browse" and i + 1 < len(path_parts):
            issue_key = path_parts[i + 1]
            if "-" in issue_key:
                parent_key = issue_key
                project = issue_key.rsplit("-", 1)[0]
            break

    sheet_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", sheet_url)
    if not sheet_match:
        raise ValueError(
            "No se pudo extraer el ID del Google Sheet de la URL. "
            "Formato esperado: https://docs.google.com/spreadsheets/d/ID/..."
        )
    spreadsheet_id = sheet_match.group(1)

    jira_config = JiraConfig(base_url=base_url, email=jira_email, api_token=jira_token)
    jira_client = JiraClient(jira_config)

    all_issues = []
    for status in statuses:
        fetched = jira_client.fetch_issues_by_status(
            status=status, project=project, parent_key=parent_key,
        )
        all_issues.extend(fetched)

    now = datetime.now(timezone.utc)
    project_label = project or "Project"
    title = f"BFV {now.strftime('%B')} {now.year} {project_label}"

    default_status = statuses[0] if statuses else "For review"

    drive_client = DriveClient(sa_file)
    spreadsheet = drive_client.setup_bfv_spreadsheet(
        spreadsheet_id=spreadsheet_id,
        title=title,
        jira_base_url=base_url,
        issues=all_issues,
        round_numbers=round_numbers or [],
        default_status=default_status,
        tester=tester,
    )

    raw = drive_client.read_rows(spreadsheet_id, range_="Issues!A4:J")

    ui_rows = []
    for row in raw:
        padded = row + [""] * (10 - len(row))
        ui_rows.append([padded[1], padded[2], padded[5]])

    return {
        "total_issues": len(ui_rows),
        "sheet_url": spreadsheet.get("spreadsheetUrl", ""),
        "issues": ui_rows,
    }


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = BFVServer((host, port), WebHandler)
    print(f"BugFix Automator UI disponible en http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        print("\nServidor detenido.")


if __name__ == "__main__":
    run_server()
