"""Interfaz visual web para operar BugFix Automator."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any

from bugfix_automator.config import load_config_from_env, load_env_file


HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>BugFix Automator — Enterprise Console</title>
  <style>
    :root {
      --bg:#0b1020;
      --surface:#121a33;
      --surface-2:#1b2647;
      --text:#e8edf7;
      --muted:#a9b5d0;
      --brand:#3a82f7;
      --brand-2:#6f5cff;
      --ok:#14b86f;
      --danger:#ff5f7a;
      --border:rgba(255,255,255,0.12);
    }
    *{box-sizing:border-box}
    body{margin:0;font-family:Inter,Segoe UI,Roboto,sans-serif;background:radial-gradient(circle at 20% -10%,#2a3a74 0%,transparent 45%),var(--bg);color:var(--text)}
    .layout{display:grid;grid-template-columns:260px 1fr;min-height:100vh}
    .sidebar{background:rgba(10,15,30,.75);backdrop-filter: blur(12px);border-right:1px solid var(--border);padding:28px 20px}
    .brand{font-weight:700;font-size:1.2rem;letter-spacing:.4px;margin-bottom:28px}
    .badge{display:inline-block;padding:6px 10px;border:1px solid var(--border);border-radius:999px;font-size:.75rem;color:var(--muted)}
    .main{padding:28px;display:flex;flex-direction:column;gap:18px}
    .card{background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid var(--border);border-radius:16px;padding:20px}
    .hero{display:flex;justify-content:space-between;align-items:center;gap:12px}
    .hero h1{margin:0;font-size:1.45rem}
    .hero p{margin:6px 0 0;color:var(--muted)}
    .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
    .kpi{padding:16px;background:var(--surface);border:1px solid var(--border);border-radius:14px}
    .kpi small{color:var(--muted);display:block;margin-bottom:5px}
    .kpi strong{font-size:1.35rem}
    .form{display:flex;gap:10px;flex-wrap:wrap}
    .input{background:var(--surface);color:var(--text);border:1px solid var(--border);padding:11px 12px;border-radius:10px;min-width:250px}
    .btn{background:linear-gradient(90deg,var(--brand),var(--brand-2));color:#fff;border:0;padding:11px 16px;border-radius:10px;font-weight:600;cursor:pointer}
    .btn:disabled{opacity:.55;cursor:not-allowed}
    table{width:100%;border-collapse:collapse;font-size:.92rem}
    th,td{padding:10px;border-bottom:1px solid var(--border);text-align:left}
    th{color:#c8d4ef;font-weight:600}
    .muted{color:var(--muted)}
    .pill{display:inline-block;padding:4px 9px;border-radius:999px;background:rgba(58,130,247,.2);border:1px solid rgba(58,130,247,.45)}
    .status{margin-top:10px;font-size:.9rem}
    .status.ok{color:var(--ok)}
    .status.err{color:var(--danger)}
    @media (max-width: 960px){.layout{grid-template-columns:1fr}.sidebar{display:none}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
  </style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">BugFix Automator</div>
    <span class="badge">Enterprise Console</span>
    <p class="muted" style="margin-top:16px;line-height:1.6">Dashboard moderno para verificar tickets en Jira y publicar reportes automáticos en Google Sheets.</p>
  </aside>
  <main class="main">
    <section class="card hero">
      <div>
        <h1>Verificación de bugs automatizada</h1>
        <p>Estado objetivo: <span class="pill" id="statusTarget">For Review</span></p>
      </div>
      <form id="runForm" class="form">
        <input id="statusInput" class="input" placeholder="For Review" />
        <button id="runBtn" class="btn" type="submit">Generar reporte</button>
      </form>
    </section>

    <section class="grid">
      <div class="kpi"><small>Issues procesados</small><strong id="kpiIssues">0</strong></div>
      <div class="kpi"><small>Tiempo total (min)</small><strong id="kpiTime">0</strong></div>
      <div class="kpi"><small>Total OO</small><strong id="kpiOO">0</strong></div>
      <div class="kpi"><small>Último reporte</small><strong id="kpiLink" class="muted">Sin ejecutar</strong></div>
    </section>

    <section class="card">
      <h3 style="margin-top:0">Últimos resultados</h3>
      <div id="statusMsg" class="status"></div>
      <div style="overflow:auto;margin-top:10px">
        <table>
          <thead>
            <tr>
              <th>Issue Key</th><th>Summary</th><th>Status</th><th>Assignee</th><th>Tiempo (min)</th><th>Cantidad OO</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </section>
  </main>
</div>
<script>
const form = document.getElementById('runForm');
const btn = document.getElementById('runBtn');
const rows = document.getElementById('rows');
const statusMsg = document.getElementById('statusMsg');

function setStatus(msg, ok=true){
  statusMsg.className = 'status ' + (ok ? 'ok':'err');
  statusMsg.textContent = msg;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  btn.disabled = true;
  const status = document.getElementById('statusInput').value || 'For Review';
  document.getElementById('statusTarget').textContent = status;
  setStatus('Procesando issues y generando Google Sheet...');
  try {
    const r = await fetch('/api/generate', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({status})
    });
    const data = await r.json();
    if(!r.ok) throw new Error(data.error || 'Error desconocido');

    document.getElementById('kpiIssues').textContent = data.total_issues;
    document.getElementById('kpiTime').textContent = data.total_tiempo_minutos;
    document.getElementById('kpiOO').textContent = data.total_oo;
    document.getElementById('kpiLink').innerHTML = `<a href="${data.spreadsheet_url}" target="_blank" style="color:#9ec0ff">Abrir Sheet</a>`;

    rows.innerHTML = '';
    for(const issue of data.issues){
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${issue.issue_key}</td><td>${issue.summary}</td><td>${issue.status}</td><td>${issue.assignee}</td><td>${issue.tiempo_minutos}</td><td>${issue.cantidad_oo}</td>`;
      rows.appendChild(tr);
    }
    setStatus('Reporte generado correctamente.');
  } catch (err){
    setStatus(String(err), false);
  } finally {
    btn.disabled = false;
  }
});
</script>
</body>
</html>
"""


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
            status = payload.get("status", "For Review")
            result = run_generation(status)
            self._json_response(result, 200)
        except Exception as exc:  # captura para feedback UI
            self._json_response({"error": str(exc)}, 500)

    def _json_response(self, payload: dict[str, Any], status_code: int) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_generation(status: str) -> dict[str, Any]:
    from bugfix_automator.drive_client import DriveClient
    from bugfix_automator.jira_client import JiraClient
    from bugfix_automator.processor import process_issues
    from bugfix_automator.report_generator import generate_report

    load_env_file()
    config = load_config_from_env()

    jira_client = JiraClient(config.jira)
    drive_client = DriveClient(config.google.service_account_file)

    issues = jira_client.fetch_issues_by_status(status=status)
    report = process_issues(issues)
    spreadsheet = generate_report(
        drive_client=drive_client,
        report=report,
        folder_id=config.google.drive_folder_id,
        title_prefix=f"Bug Verification - {status}",
    )

    return {
        "status": status,
        "total_issues": len(report.issues),
        "total_tiempo_minutos": report.total_tiempo_minutos,
        "total_oo": report.total_oo,
        "spreadsheet_url": spreadsheet.get("spreadsheetUrl", ""),
        "issues": [issue.__dict__ for issue in report.issues],
    }


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), WebHandler)
    print(f"BugFix Automator UI disponible en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
