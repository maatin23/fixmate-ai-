# FixMate AI

**Your Devices. Diagnosed Smarter.**

FixMate AI is a safety-first repair triage app built with Python and Streamlit. Describe a fault, attach photos, and get a structured AI assessment that ranks possible causes, separates safe checks from advanced repair work, and states its uncertainty instead of pretending to be certain.

The app uses the real OpenAI API for diagnosis, vision inspection and follow-up chat. It does **not** generate mock reports when the API is unavailable. Without a configured key, AI features stay offline and the interface explains what is missing.

---

## Highlights

- **Premium dark interface** — custom navbar, animated diagnostic visual, glass panels, ambient background and micro-interactions rather than default Streamlit styling.
- **Eight device categories** — smartphones, laptops, desktop PCs, washing machines, refrigerators, air conditioners, televisions and other electronics.
- **Guided intake** — manufacturer/model, age, onset, symptoms, unusual signs, error codes and a free-text description.
- **Structured AI report** — summary, severity, confidence, ranked causes with distinguishing tests, safe checks, advanced steps, tools, difficulty, estimated time, professional-repair recommendation, uncertainty, stop conditions and prevention notes.
- **Vision inspection** — up to four JPG/PNG/WebP photos (10 MB each), resized in memory and inspected by a real vision model. Findings distinguish what is visible from what a photo cannot determine.
- **Follow-up chat** — ask about the loaded report, request simpler explanations, or clarify repair steps. Conversation context is kept for the current browser session.
- **Local dashboard** — totals, category coverage, professional-referral rate, a real seven-day activity chart and recent sessions, all computed from stored records only.
- **Searchable history** — SQLite-backed history with search, category filters, report reopening and per-record or full-history deletion.
- **Deterministic safety layer** — hazard patterns are checked in code before/after the model call. Critical or high-risk patterns force a professional referral and withhold advanced steps. Unsafe live-work instructions are filtered.

---

## Safety model

FixMate is advisory. It is not a confirmed diagnosis and it does not replace an in-person inspection by a qualified technician.

A deterministic layer in `safety.py` runs alongside the model:

- **Never instructs work on live electrical equipment.**
- **Warns about high-voltage components and capacitors**, and blocks attempts to bypass interlocks or work on energized parts.
- **Warns about swollen or damaged lithium-ion batteries** and blocks instructions to press, puncture, open or charge them.
- **Avoids dangerous refrigerant handling** and never suggests charging, venting or opening a pressurized system.
- **Forces a professional referral** when critical or high-risk hazards are detected, and raises urgency for critical patterns.
- **Withholds advanced repair steps** for high/critical hazards.
- **Filters unsafe model output** for live work, capacitor discharge, refrigerant handling and battery damage.
- **Distinguishes basic checks from advanced repairs** throughout the interface and report.
- Shows stop conditions and uncertainty on every report.

If you see smoke, sparks, a burning smell or a swollen battery: stop using the device, do not charge it, keep away from flammable material, and seek qualified help. For an active fire, evacuate and call emergency services.

---

## How it works

1. **Intake** — the user selects a device category and provides the observed evidence.
2. **Pre-flight safety scan** — text and selected signs are scanned for known hazard patterns before the model is called.
3. **AI diagnosis** — the OpenAI model returns a JSON object constrained to the report schema.
4. **Validation and guardrails** — the response is normalized, invalid responses are rejected, and the safety layer applies hard overrides.
5. **Storage** — a valid report is written to the local SQLite database.
6. **Follow-up** — optional image inspection and chat use the stored report as context.

API failures, malformed JSON, empty responses and truncated output produce a clear error and **no saved report**. The app never presents a failed request as a successful diagnosis.

---

## Tech stack

| Layer | Technology |
| --- | --- |
| UI | Streamlit 1.66.1, custom HTML/CSS, inline SVG icons |
| AI | OpenAI Python SDK 2.54.0 (chat completions, JSON object mode, vision) |
| Storage | SQLite (WAL mode), parameterized queries |
| Images | Pillow (validation, EXIF orientation, resize, JPEG conversion) |
| Config | python-dotenv, Streamlit secrets, environment variables |

Tested with Python 3.13 on Windows. Python 3.10+ is required.

---

## Project structure

```text
fixmate_ai/
├── app.py                     # Streamlit entry point and page routing
├── config.py                  # Settings, device categories, intake options
├── ai_service.py              # OpenAI calls, JSON parsing and error mapping
├── diagnostic_engine.py       # Schema normalization, safety orchestration
├── safety.py                  # Deterministic hazard rules and guardrails
├── image_analysis.py          # Image validation, resizing and vision pipeline
├── database.py                # SQLite schema and history/stat queries
├── prompts.py                 # System prompts for diagnosis, vision, chat
├── state.py                   # Session-state helpers and navigation
├── styles.py                  # CSS/background injection
├── utils.py                   # Escaping and formatting helpers
├── components/                # Navbar, cards, icons, chat, report renderers
├── pages/                     # Home, diagnosis, dashboard, history, chat, about
├── assets/                    # Design-system CSS and favicon
├── tests/test_core.py         # Network-free safety, validation and DB tests
├── .streamlit/
│   ├── config.toml            # Dark theme; hides error details and sidebar nav
│   └── secrets.toml.example   # Cloud secrets template
├── .env.example               # Local environment template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Windows setup

Open PowerShell in the `fixmate_ai` folder.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

If PowerShell blocks activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

In **cmd.exe** use `.venv\Scripts\activate.bat`. In **Git Bash** use `source .venv/Scripts/activate`.

---

## Configure the OpenAI connection

Edit `.env`:

```env
OPENAI_API_KEY=sk-your-real-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=
```

- `OPENAI_API_KEY` is required for any live AI feature.
- `OPENAI_MODEL` is used for diagnosis and chat; it must support JSON object responses.
- `OPENAI_VISION_MODEL` must accept image input. If omitted, the text model is used.
- The defaults (`gpt-4o-mini`) support both text and vision.
- `OPENAI_BASE_URL` is optional and only needed for an OpenAI-compatible gateway. Vision support depends on that gateway.
- A custom database path can be set with `FIXMATE_DB_PATH` (useful for tests or a mounted disk).

Secrets are read in this order: **Streamlit secrets → environment variables (including `.env`)**. Restart the app after changing `.env`.

For Streamlit Community Cloud, add the same keys under **App settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-your-real-key"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_VISION_MODEL = "gpt-4o-mini"
```

### API key security

- The key is read server-side only and is never rendered into HTML/JavaScript.
- `.env`, `.streamlit/secrets.toml` and database files are excluded by `.gitignore`.
- `showErrorDetails = false` is set in `.streamlit/config.toml`, so raw Python tracebacks are not shown to visitors.
- Error messages are sanitized; they describe the problem without echoing the key.
- Never commit `.env` or `secrets.toml`. If a key is exposed, revoke it in the OpenAI dashboard and create a new one.

---

## Run locally

```powershell
streamlit run app.py
```

Open `http://localhost:8501`. If the port is busy, use `streamlit run app.py --server.port 8502`.

On first run the app creates `data/fixmate.db`. The initial history is empty — there is no demo data.

### What happens without a key

The intake form remains available, but submitting shows a setup error and **no report is created or saved**. Chat prompts and send controls are disabled. Vision inspection reports that a configured model is required. The About page shows the API connection as not configured.

---

## Using FixMate

1. Start on the landing page and choose **Start diagnosis**, or pick a device from the device lab.
2. Complete the intake. Be specific about what changed and what you have already tried.
3. Generate the report and review severity, confidence, causes, safe checks, uncertainty and stop conditions. Do not skip safety warnings.
4. Open **Vision inspection** to add photos and run a visible-damage pass.
5. Open **Follow-up chat** to unpack the report or prepare questions for a technician.
6. Use **Dashboard** for real usage metrics and **History** to search, reopen, delete or clear stored records.

Every interactive control is wired; if an API call cannot run, the app shows the reason.

---

## Data, privacy and local-only storage

- **History is stored locally** in a SQLite file on the machine running the app. There are **no accounts, no multi-user cloud sync and no shared history between visitors**.
- On Streamlit Community Cloud, the filesystem is ephemeral. **History can be lost when the app restarts or redeploys.** Do not treat it as durable cloud storage.
- Uploaded **photo files are not saved** to disk or to the database. They are validated and resized in memory, sent to the configured vision model, and discarded. Only the resulting text findings are stored with the session.
- **Chat messages are session-only** and are not written to the history database.
- Intake details, reports and photos are sent to the configured AI provider for processing. Do not upload faces, serial numbers, documents or other sensitive content.
- You can delete individual records or clear all history from the History page. Deletion is permanent for the local database.
- Dashboard values and charts are derived from stored records only; empty states are shown instead of invented statistics.

---

## Deploy to Streamlit Community Cloud

1. Create a GitHub repository. Prefer **this `fixmate_ai` folder as the repository root** so `requirements.txt`, `.streamlit/` and `app.py` are detected.
2. Confirm `.env` and `.streamlit/secrets.toml` are not committed (`.gitignore` covers them).
3. Go to [share.streamlit.io](https://share.streamlit.io), create a new app, choose the repository and branch, and set **Main file path** to `app.py`.
4. In **Advanced settings**, select Python 3.12 or 3.13 (any Python 3.10+ version works) and paste the secrets block shown above.
5. Deploy. Dependencies install from `requirements.txt`.
6. Add the key only through the Cloud secrets UI — never in source or README.

If you keep the parent folder as the repository root instead, set the main file path to `fixmate_ai/app.py` and make `requirements.txt` available at the repository root.

**Hosting caveat:** the managed filesystem resets between restarts/deploys, so SQLite history is temporary. This first version intentionally has no external database or multi-user synchronization layer.

---

## Tests

Run the network-free core tests from the project folder:

```powershell
python -m unittest discover -s tests -v
```

They cover:

- Hazard detection and forced professional referral for swollen batteries and refrigerant.
- Removal of unsafe live-work instructions.
- Rejection of incomplete AI reports and normalization of invalid enum values.
- Professional escalation for severe visible image findings.
- SQLite save, list, stats and delete round-trips.

Recommended manual smoke test:

1. Without a key: submit the intake and confirm the setup error appears, no report is shown, and no DB record is created.
2. With a key: generate a report, reload the app, and reopen it from History.
3. Upload a photo, run vision inspection, reload, and confirm the findings persist.
4. Ask a chat follow-up, clear the conversation, and confirm the empty state returns.
5. Test a hazardous description (for example a swollen battery) and confirm the referral and withheld advanced steps.
6. Search/filter History, cancel a delete, confirm a delete, then clear all records.
7. Resize the browser to a narrow viewport and confirm content stacks without horizontal scrolling.

To intentionally test failure handling, use an invalid key or disconnect the network. You should see an error and **no fabricated report or chat reply**.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| “needs an OpenAI API key” | Add `OPENAI_API_KEY` to `.env` or Cloud secrets, then restart. |
| Authentication error | Verify the key is current, has billing/usage enabled, and can access the selected model. |
| Model not available | Set `OPENAI_MODEL` / `OPENAI_VISION_MODEL` to models enabled for your account. |
| Rate limit or quota | Wait and retry, or check usage limits on the OpenAI account. |
| Timeout | Check the connection; multi-image vision requests take longer. Retry with fewer/smaller images. |
| Port already in use | Run with `--server.port 8502` or stop the other process. |
| History disappeared | On Community Cloud the filesystem can reset. Locally, confirm `data/fixmate.db` exists and any custom `FIXMATE_DB_PATH` is correct. |
| Photo rejected | Use JPG, PNG or WebP under 10 MB. Avoid corrupt files and extreme dimensions. |
| CSS changes not appearing | Restart the Streamlit process if you modified files outside a running reload. |

---

## Known limitations

- AI guidance can be wrong. Confidence and uncertainty are estimates, not guarantees.
- Photos reveal visible condition only; internal faults, live electrical state and hidden damage cannot be judged from an image.
- The app does not provide disassembly instructions for mains-powered, high-voltage, refrigerant or battery-damaged equipment.
- Chat history and vision uploads are not stored across sessions. Only the report and text findings are persisted.
- History is local to one deployment and one SQLite file — no accounts, sharing or cloud sync.
- No automated browser test suite ships with the app; the core safety/database tests and manual checklist above cover the critical paths.

---

## Model cost

Each diagnosis is one text completion (up to 2,600 output tokens), each vision pass is one vision completion with up to four resized images (up to 1,600 output tokens), and each chat reply is one completion (up to 1,500 output tokens). Actual cost depends on the models you configure and current provider pricing. Use your OpenAI usage dashboard to monitor spending; the repository does not include a key or billing account.

---

**FixMate AI** — advisory repair triage with visible uncertainty and hard safety boundaries.
