# Configuración completa paso a paso (desde cero)

Este documento te guía **de inicio a fin** para dejar BugFix Automator funcionando correctamente con:

- Jira Cloud API
- Google Drive + Google Sheets API
- Ejecución por CLI o interfaz web moderna

---

## 1) Requisitos previos

Antes de empezar, verifica que tienes:

1. Una cuenta de Jira Cloud con permisos para leer issues.
2. Una cuenta de Google (para Google Cloud + Drive/Sheets).
3. Python 3.10 o superior.
4. Git instalado.

### Comandos recomendados para verificar herramientas

```bash
python --version
git --version
```

---

## 2) Clonar el proyecto

```bash
git clone <URL_DEL_REPOSITORIO>
cd BugFix-Automator
```

Si ya tienes el repo local, solo asegúrate de estar en la raíz:

```bash
cd /ruta/a/BugFix-Automator
```

---

## 3) Crear y activar entorno virtual

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 4) Instalar dependencias

```bash
pip install -e .[dev]
```

Si tu entorno tiene restricciones de red/proxy, configura primero `pip` con tu mirror interno o proxy corporativo.

---

## 5) Configurar Jira (API Token)

### 5.1 Generar token

1. Entra a: https://id.atlassian.com/manage-profile/security/api-tokens
2. Crea un API token nuevo.
3. Guarda el token en un lugar seguro.

### 5.2 Datos que necesitas para `.env`

- `JIRA_BASE_URL` → por ejemplo: `https://tuempresa.atlassian.net`
- `JIRA_EMAIL` → tu email de Jira Cloud
- `JIRA_API_TOKEN` → token creado en el paso anterior
- `JIRA_STATUS` → por ejemplo `For Review`

---

## 6) Configurar Google Cloud (Sheets + Drive)

## 6.1 Crear proyecto en Google Cloud

1. Ir a: https://console.cloud.google.com/
2. Crear proyecto nuevo (o usar uno existente).

## 6.2 Habilitar APIs

En ese proyecto, habilita:

- Google Sheets API
- Google Drive API

## 6.3 Crear Service Account

1. Ve a **IAM & Admin > Service Accounts**.
2. Crea una cuenta de servicio.
3. Crea una clave JSON y descárgala.
4. Guarda ese archivo en el repo, por ejemplo:

```text
./service-account.json
```

> Recomendación: no subir este archivo al repositorio remoto.

## 6.4 Compartir carpeta de Drive con la Service Account

1. Crea una carpeta en Google Drive (opcional, pero recomendado).
2. Copia el `folderId` de la URL de la carpeta.
3. Comparte la carpeta con el email de la service account (permiso Editor).

---

## 7) Crear archivo de entorno `.env`

Copia el ejemplo:

```bash
cp .env.example .env
```

Edita `.env` con valores reales:

```env
JIRA_BASE_URL=https://tuempresa.atlassian.net
JIRA_EMAIL=tu_email@empresa.com
JIRA_API_TOKEN=tu_token_jira
JIRA_STATUS=For Review
GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json
GOOGLE_DRIVE_FOLDER_ID=<ID_DE_TU_CARPETA_DRIVE>
```

### Significado de cada variable

- `JIRA_BASE_URL`: dominio de Jira Cloud.
- `JIRA_EMAIL`: usuario para autenticar Jira.
- `JIRA_API_TOKEN`: token de Jira.
- `JIRA_STATUS`: estado que se filtrará por defecto.
- `GOOGLE_SERVICE_ACCOUNT_FILE`: ruta al JSON de credenciales Google.
- `GOOGLE_DRIVE_FOLDER_ID`: carpeta destino del spreadsheet (opcional pero recomendado).

---

## 8) Probar que todo está correcto (tests)

```bash
pytest -q
```

Si pasa, debería mostrar `4 passed` (o más en el futuro).

---

## 9) Ejecutar en modo CLI

```bash
python -m bugfix_automator.main
```

### Ejecutar con estado específico

```bash
python -m bugfix_automator.main --status "For Review"
```

### Resultado esperado en consola

- Mensaje de reporte generado.
- Cantidad de issues.
- Tiempo total en minutos.
- Total de ocurrencias `OO`.
- URL de Google Sheet generado.

---

## 10) Ejecutar en modo visual (dashboard)

```bash
python -m bugfix_automator.main --web --port 8080
```

Luego abre en tu navegador:

```text
http://localhost:8080
```

Desde ahí puedes:

1. Indicar el estado Jira.
2. Clic en **Generar reporte**.
3. Ver KPIs y tabla de issues.
4. Abrir el Google Sheet generado.

---

## 11) Estructura del reporte generado

El spreadsheet incluye estas columnas:

1. Issue Key
2. Summary
3. Status
4. Assignee
5. Tiempo (minutos)
6. Cantidad de OO

Además agrega una fila final `TOTAL` con:

- Suma de tiempo (minutos)
- Suma total de ocurrencias `OO`

---

## 12) Checklist final de validación

Si algo falla, revisa este checklist:

- [ ] `JIRA_BASE_URL` correcto y sin slash al final extra.
- [ ] `JIRA_EMAIL` y `JIRA_API_TOKEN` válidos.
- [ ] Estado Jira existe (`For Review` u otro).
- [ ] APIs de Google habilitadas (Drive + Sheets).
- [ ] JSON de service account existe en la ruta configurada.
- [ ] Carpeta Drive compartida con la service account.
- [ ] `GOOGLE_DRIVE_FOLDER_ID` correcto.

---

## 13) Problemas comunes y solución

### Error: autenticación Jira

- Verifica email/token.
- Revisa que la URL sea Jira Cloud (`*.atlassian.net`).

### Error: permiso en Google Drive

- Comparte la carpeta con la service account.
- Asegúrate de que tenga permiso Editor.

### Error: no encuentra archivo JSON

- Revisa `GOOGLE_SERVICE_ACCOUNT_FILE`.
- Confirma que el archivo exista en esa ruta.

### Error en entorno corporativo/proxy

- Configura `pip` y red con proxy corporativo.
- Si usas CI, agrega variables de proxy y secretos.

---

## 14) Recomendaciones de producción

1. No guardar tokens en texto plano fuera de `.env` local o un gestor de secretos.
2. No subir `service-account.json` al repositorio.
3. Ejecutar con usuario técnico dedicado (service account y cuenta Jira de integración).
4. Agregar logs estructurados y monitoreo si escalan uso.
5. Programar ejecución automática (cron/GitHub Actions/Cloud Run jobs) según necesidad.

---

## 15) Flujo resumido de operación diaria

1. Abrir dashboard o correr CLI.
2. Elegir estado Jira objetivo.
3. Ejecutar generación.
4. Revisar KPIs y tabla.
5. Abrir Google Sheet y compartir con el equipo.

¡Listo! Con esto queda el proyecto completamente configurado y operativo de punta a punta.
