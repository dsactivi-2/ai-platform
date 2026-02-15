# AI Platform — Benutzerhandbuch

**Version:** 1.0
**Stand:** 15. Februar 2026
**Portal:** https://gateway-production-c725.up.railway.app/

---

## Inhaltsverzeichnis

| Nr. | Kapitel | Seite |
|-----|---------|-------|
| 1 | Einfuehrung & Zugang | 3 |
| 1.1 | Was ist die AI Platform? | 3 |
| 1.2 | Login & Authentifizierung | 3 |
| 1.3 | Portal-Uebersicht | 4 |
| 1.4 | Alle URLs auf einen Blick | 4 |
| 2 | Dify — LLM App Builder | 5 |
| 2.1 | Erster Login & Account erstellen | 5 |
| 2.2 | Apps erstellen | 6 |
| 2.3 | Workflow Builder | 7 |
| 2.4 | RAG / Knowledge Base | 8 |
| 2.5 | Agent Tools einrichten | 9 |
| 2.6 | Chat Interface nutzen | 10 |
| 2.7 | Modell-Verwaltung | 10 |
| 2.8 | Plugin System | 11 |
| 2.9 | API-Zugriff | 11 |
| 3 | Lyzr Search — AI-Suche | 13 |
| 3.1 | Suche starten | 13 |
| 3.2 | Chat-Modus | 13 |
| 3.3 | Quellen & verwandte Fragen | 14 |
| 3.4 | API-Nutzung | 14 |
| 4 | Lyzr Governor — AI Governance | 16 |
| 4.1 | Dashboard | 16 |
| 4.2 | Policies erstellen | 16 |
| 4.3 | Approval Workflows | 17 |
| 4.4 | Compliance Berichte (GDPR/SOC2) | 18 |
| 4.5 | Event Tracking | 18 |
| 5 | Lyzr Crawl — Web Crawler | 19 |
| 5.1 | Crawl-Job starten | 19 |
| 5.2 | Content Extraction | 20 |
| 5.3 | Job-Verwaltung | 20 |
| 5.4 | Stealth Mode & Robots.txt | 21 |
| 5.5 | API-Referenz | 21 |
| 6 | Agent Simulation Engine | 22 |
| 6.1 | Simulation erstellen | 22 |
| 6.2 | Szenarien & Personas | 23 |
| 6.3 | Evaluationen ausfuehren | 23 |
| 6.4 | Hardening & Stress-Tests | 24 |
| 7 | Skills Kit | 25 |
| 7.1 | Skills Adapters durchsuchen | 25 |
| 7.2 | Kit Agents verwalten | 25 |
| 7.3 | Custom Skills erstellen | 26 |
| 8 | CrewAI Studio — Multi-Agent Teams | 27 |
| 8.1 | Agents erstellen | 27 |
| 8.2 | Tasks definieren | 28 |
| 8.3 | Crews zusammenstellen | 29 |
| 8.4 | Crew ausfuehren | 29 |
| 8.5 | Tools anbinden | 30 |
| 8.6 | Crew exportieren | 31 |
| 9 | Policy Gateway | 32 |
| 9.1 | Policy Enforcement | 32 |
| 10 | Storage | 33 |
| 10.1 | Dateien hochladen & abrufen | 33 |
| 11 | Administration | 34 |
| 11.1 | Monorepo-Struktur | 34 |
| 11.2 | Deployment & Updates | 34 |
| 11.3 | Infrastruktur-Services | 35 |
| 11.4 | Zugangsdaten-Uebersicht | 36 |
| 11.5 | Fehlerbehebung | 37 |

---

<!-- Seite 3 -->
## Seite 3

# 1. Einfuehrung & Zugang

## 1.1 Was ist die AI Platform?

Die AI Platform ist eine integrierte Sammlung von KI-Werkzeugen, die ueber ein zentrales Portal erreichbar sind. Sie kombiniert drei grosse Frameworks:

- **Dify** — Visueller App-Builder fuer LLM-Anwendungen (Chatbots, Workflows, RAG)
- **Lyzr** — Spezialisierte KI-Tools (Search, Governance, Crawling, Agent Testing, Skills)
- **CrewAI** — Multi-Agent-Teams die zusammenarbeiten

Alle Tools laufen auf Railway (Cloud-Hosting) und sind ueber HTTPS geschuetzt.

## 1.2 Login & Authentifizierung

### Gateway-Login (fuer alle Tools)

Beim Klick auf ein Tool im Portal erscheint ein Browser-Login-Dialog:

```
Benutzername: admin
Passwort:     DjeLD-YE23momovV
```

Dieser Login schuetzt den Zugang zu allen Tools ueber das Gateway. Nach einmaliger Eingabe bleibt die Session im Browser aktiv.

### Dify-Login (zusaetzlich)

Nach dem Gateway-Login hat Dify einen eigenen Login. Beim **allerersten Zugriff**:

```
Ersteinrichtungs-Passwort: rYST6F1P
```

Damit erstellst du deinen Dify-Admin-Account (E-Mail + eigenes Passwort). Danach nutzt du nur noch deinen eigenen Dify-Account.

### Direkte URLs (ohne Gateway)

Jedes Tool hat auch eine eigene direkte URL (siehe Tabelle auf Seite 4). Bei direktem Zugriff entfaellt der Gateway-Login — das Tool ist dann nur durch seine eigene Authentifizierung geschuetzt (falls vorhanden).

---

<!-- Seite 4 -->
## Seite 4

## 1.3 Portal-Uebersicht

Das Portal erreichst du unter:
**https://gateway-production-c725.up.railway.app/**

Es zeigt eine dunkle Oberflaeche mit Kacheln fuer jedes Tool, eingeteilt in:

- **Hauptanwendungen** — Dify, Lyzr Search, Lyzr Governor
- **Tools & APIs** — Crawl, Agent Simulator, Skills Kit
- **Agent Frameworks** — CrewAI Studio, LangGraph (geplant)

Klicke auf eine Kachel um das entsprechende Tool zu oeffnen. Beim ersten Klick erscheint der Gateway-Login.

## 1.4 Alle URLs auf einen Blick

### Ueber das Portal (Gateway-Login erforderlich)

| Tool | Portal-Route | Direkte URL |
|------|-------------|-------------|
| Portal | `/` | https://gateway-production-c725.up.railway.app/ |
| Dify | `/dify/` | https://web-production-e7d98.up.railway.app/ |
| Lyzr Search | `/search/` | https://perplexity-frontend-production.up.railway.app/ |
| Lyzr Governor | `/governance/` | https://governor-production-a7da.up.railway.app/ |
| Lyzr Crawl | `/crawl/` | https://lyzr-crawl-production.up.railway.app/ |
| Agent Simulator | `/simulate/` | https://agent-simulation-production.up.railway.app/ |
| Skills Kit | `/skills/` | https://lyzr-skills-kit-production.up.railway.app/ |
| CrewAI Studio | `/crewai/` | https://crewai-studio-production-0433.up.railway.app/ |

### API Endpoints (kein Gateway-Login, eigene Auth)

| Endpoint | URL | Auth |
|----------|-----|------|
| Dify API | https://api-production-319f.up.railway.app/api/ | Dify API Key |
| Dify API v1 | https://api-production-319f.up.railway.app/v1/ | Dify API Key |
| Search API | https://perplexity-backend-production.up.railway.app/docs | Keine |
| Policy Gateway | https://policy-gateway-production.up.railway.app/ | Keine |
| Storage | https://storage-production-afed.up.railway.app/ | S3 Keys |

---

<!-- Seite 5 -->
## Seite 5

# 2. Dify — LLM App Builder

Dify ist der Kern der Plattform. Damit baust du KI-Anwendungen visuell — ohne programmieren zu muessen.

**Zugang:** Portal → Dify oder direkt https://web-production-e7d98.up.railway.app/

## 2.1 Erster Login & Account erstellen

**Schritt 1:** Oeffne Dify ueber das Portal oder die direkte URL.

**Schritt 2:** Beim allerersten Zugriff siehst du die Einrichtungsseite. Gib ein:
- E-Mail-Adresse (wird dein Login)
- Benutzername
- Eigenes Passwort
- Ersteinrichtungs-Passwort: `rYST6F1P`

**Schritt 3:** Klicke auf "Einrichten". Dein Admin-Account wird erstellt.

**Schritt 4:** Ab jetzt meldest du dich mit deiner E-Mail und deinem Passwort an.

### LLM-Provider konfigurieren

Bevor du Apps bauen kannst, musst du mindestens einen LLM-Provider einrichten:

1. Gehe zu **Einstellungen** (Zahnrad-Symbol oben rechts)
2. Waehle **Modell-Provider**
3. Klicke auf den gewuenschten Provider (z.B. OpenAI, Anthropic, Ollama)
4. Gib deinen API-Key ein
5. Speichern

Unterstuetzte Provider: OpenAI, Anthropic (Claude), Google (Gemini), Azure OpenAI, Ollama (lokal), Llama, Mistral, und weitere.

---

<!-- Seite 6 -->
## Seite 6

## 2.2 Apps erstellen

Dify bietet vier App-Typen:

### Chatbot
Ein konversationsbasierter Assistent mit Gedaechtnis.

1. Klicke **"App erstellen"** → **Chatbot**
2. Gib einen Namen und eine Beschreibung ein
3. Waehle das LLM-Modell (z.B. GPT-4, Claude 3)
4. Schreibe den **System-Prompt** (Anweisungen fuer den Bot)
5. Optional: Fuege Variablen hinzu (z.B. `{{sprache}}`)
6. Klicke **"Veroeffentlichen"**

### Text-Generator
Erzeugt Text basierend auf einer Eingabe (kein Chat-Verlauf).

1. **"App erstellen"** → **Text-Generator**
2. Definiere Eingabefelder (z.B. "Thema", "Laenge")
3. Schreibe den Prompt mit Platzhaltern: `Schreibe einen Artikel ueber {{Thema}}`
4. Veroeffentlichen

### Agent
Ein intelligenter Assistent der Tools nutzen kann (Web-Suche, Berechnungen, API-Aufrufe).

1. **"App erstellen"** → **Agent**
2. Waehle Tools aus (siehe Kapitel 2.5)
3. Definiere den System-Prompt
4. Der Agent entscheidet selbst, wann er welches Tool nutzt

### Workflow
Komplexe Ablaeufe mit Verzweigungen — siehe Kapitel 2.3.

---

<!-- Seite 7 -->
## Seite 7

## 2.3 Workflow Builder

Der Workflow Builder ist Difys maechtigstes Feature. Du erstellst visuelle Ablaeufe per Drag-and-Drop.

### Workflow erstellen

1. **"App erstellen"** → **Workflow**
2. Du siehst eine Arbeitsflaeche mit einem **Start**-Knoten
3. Klicke auf **"+"** um Knoten hinzuzufuegen

### Verfuegbare Knoten

| Knoten | Funktion |
|--------|----------|
| **Start** | Eingabe-Parameter definieren |
| **LLM** | Sprachmodell-Aufruf mit Prompt |
| **Knowledge Retrieval** | Daten aus der Wissensbasis abrufen |
| **Code** | Python/JavaScript Code ausfuehren (laeuft in der Sandbox) |
| **HTTP Request** | Externe APIs aufrufen |
| **IF/ELSE** | Bedingungen und Verzweigungen |
| **Iteration** | Schleifen ueber Listen |
| **Variable Aggregator** | Variablen zusammenfuehren |
| **Template** | Text-Vorlagen mit Variablen fuellen |
| **End** | Ausgabe definieren |

### Workflow testen

1. Klicke **"Ausfuehren"** (Play-Button oben rechts)
2. Gib Test-Eingaben ein
3. Beobachte den Ablauf — jeder Knoten zeigt seinen Status
4. Gruene Knoten = erfolgreich, Rote = Fehler
5. Klicke auf einen Knoten um sein Ergebnis zu sehen

### Workflow veroeffentlichen

1. Klicke **"Veroeffentlichen"**
2. Waehle ob als **API** oder **Web-App**
3. Du erhaeltst eine URL oder einen API-Endpoint

---

<!-- Seite 8 -->
## Seite 8

## 2.4 RAG / Knowledge Base

RAG (Retrieval Augmented Generation) erlaubt deinen Apps, Antworten basierend auf deinen eigenen Dokumenten zu geben.

### Wissensbasis erstellen

1. Gehe zu **"Wissen"** im Hauptmenue
2. Klicke **"Wissensbasis erstellen"**
3. Gib einen Namen ein (z.B. "Firmen-Handbuch")

### Dokumente hochladen

1. Oeffne die Wissensbasis
2. Klicke **"Dokument hinzufuegen"**
3. Unterstuetzte Formate:
   - **PDF** — Berichte, Handbuecher, Vertraege
   - **TXT/Markdown** — Textdateien
   - **DOCX** — Word-Dokumente
   - **CSV** — Tabellen
   - **HTML** — Webseiten
4. Waehle die **Chunk-Methode**:
   - **Automatisch** — Dify teilt das Dokument intelligent auf
   - **Manuell** — Du bestimmst die Abschnitt-Groesse
5. Waehle das **Embedding-Modell** (z.B. OpenAI text-embedding-3-small)
6. Klicke **"Speichern und verarbeiten"**

### Wissensbasis in App nutzen

1. Oeffne eine App (Chatbot, Agent oder Workflow)
2. Im Prompt-Bereich klicke **"Kontext hinzufuegen"**
3. Waehle deine Wissensbasis aus
4. Im System-Prompt schreibe: `Beantworte Fragen basierend auf dem bereitgestellten Kontext.`

Die App durchsucht nun automatisch die Wissensbasis und nutzt relevante Abschnitte fuer ihre Antworten.

---

<!-- Seite 9 -->
## Seite 9

## 2.5 Agent Tools einrichten

Tools erweitern die Faehigkeiten deiner Agents und Workflows.

### Eingebaute Tools

| Tool | Funktion |
|------|----------|
| **Google Search** | Web-Suche ueber Google |
| **Wikipedia** | Wikipedia-Artikel abrufen |
| **Wolfram Alpha** | Mathematische Berechnungen |
| **Web Scraper** | Webseiten-Inhalte extrahieren |
| **Wetter** | Aktuelle Wetterdaten |
| **Uhrzeit** | Aktuelle Zeit und Datum |

### Eigene Tools hinzufuegen (Custom Tools)

1. Gehe zu **"Tools"** im Hauptmenue
2. Klicke **"Custom Tool erstellen"**
3. Gib die **OpenAPI-Spezifikation** deiner API ein (JSON oder YAML)
4. Dify erkennt automatisch alle Endpoints
5. Konfiguriere Authentifizierung falls noetig (API Key, Bearer Token)
6. Speichern

### Tools in App verwenden

1. Oeffne eine App vom Typ **Agent**
2. Unter **"Tools"** klicke **"Tool hinzufuegen"**
3. Waehle das gewuenschte Tool
4. Der Agent entscheidet selbst wann er das Tool nutzt

### Plattform-eigene APIs als Tools

Du kannst die anderen Plattform-Services als Tools einbinden:

| Service | API-URL fuer Custom Tool |
|---------|------------------------|
| Lyzr Search | `https://perplexity-backend-production.up.railway.app/` |
| Lyzr Crawl | `https://lyzr-crawl-production.up.railway.app/` |
| Agent Simulation | `https://agent-simulation-production.up.railway.app/api/` |
| Skills Kit | `https://lyzr-skills-kit-production.up.railway.app/api/` |

---

<!-- Seite 10 -->
## Seite 10

## 2.6 Chat Interface nutzen

Jede veroeffentlichte Chatbot-App hat ein fertiges Chat-Interface.

### Als Entwickler testen

1. Oeffne die App im Dify-Dashboard
2. Klicke auf **"Ausfuehren"** (rechte Seite)
3. Tippe deine Nachricht und druecke Enter
4. Die Antwort erscheint in Echtzeit (Streaming)

### Fuer Endbenutzer freigeben

1. Klicke **"Veroeffentlichen"** → **"Web-App starten"**
2. Du erhaeltst eine oeffentliche URL
3. Diese URL kannst du teilen — Nutzer brauchen keinen Dify-Account
4. Optional: Passe das Erscheinungsbild an (Logo, Farben, Begruessung)

### Chat-Verlauf

- Jede Konversation wird gespeichert
- Unter **"Logs"** siehst du alle Gespraeche
- Du kannst Konversationen nach Qualitaet bewerten
- Feedback hilft bei der Prompt-Optimierung

## 2.7 Modell-Verwaltung

### Modelle konfigurieren

1. **Einstellungen** → **Modell-Provider**
2. Pro Provider gibst du den API-Key ein
3. Danach stehen alle Modelle dieses Providers zur Verfuegung

### Modell pro App waehlen

Jede App kann ein anderes Modell nutzen. In den App-Einstellungen:
- **Modell** — Welches LLM (z.B. gpt-4o, claude-3-5-sonnet)
- **Temperatur** — 0 = praezise, 1 = kreativ
- **Max Tokens** — Maximale Antwortlaenge
- **Top-P** — Sampling-Parameter

### Empfohlene Modelle nach Aufgabe

| Aufgabe | Empfohlenes Modell |
|---------|-------------------|
| Allgemeiner Chatbot | GPT-4o oder Claude 3.5 Sonnet |
| Code-Generierung | GPT-4o oder Claude 3.5 Sonnet |
| Einfache Aufgaben | GPT-4o-mini oder Claude 3.5 Haiku |
| Dokument-Analyse | Claude 3.5 Sonnet (langes Kontextfenster) |
| Kreatives Schreiben | GPT-4o mit Temperatur 0.8 |

---

<!-- Seite 11 -->
## Seite 11

## 2.8 Plugin System

Plugins erweitern Dify um zusaetzliche Funktionen.

### Plugin installieren

1. Gehe zu **"Plugins"** im Hauptmenue
2. Durchsuche den Plugin-Marktplatz
3. Klicke auf ein Plugin → **"Installieren"**
4. Das Plugin erscheint in deinen verfuegbaren Tools

### Plugin-Typen

| Typ | Beschreibung |
|-----|-------------|
| **Tool-Plugins** | Neue Tools fuer Agents (z.B. Slack, E-Mail, Datenbank) |
| **Model-Plugins** | Zusaetzliche LLM-Provider |
| **Extension-Plugins** | Neue Funktionen fuer die Plattform |

Plugins laufen isoliert im Plugin Daemon und beeinflussen die Hauptanwendung nicht.

## 2.9 API-Zugriff

Jede Dify-App kann ueber die API genutzt werden.

### API-Key erstellen

1. Oeffne eine App
2. Klicke auf **"API-Zugang"** (links)
3. Klicke **"API-Key erstellen"**
4. Kopiere den Key — er wird nur einmal angezeigt

### Chat-Nachricht senden

```
POST https://api-production-319f.up.railway.app/v1/chat-messages
```

**Headers:**
```
Authorization: Bearer <dein-api-key>
Content-Type: application/json
```

**Body:**
```json
{
  "inputs": {},
  "query": "Was ist kuenstliche Intelligenz?",
  "response_mode": "streaming",
  "user": "benutzer-123"
}
```

---

<!-- Seite 12 -->
## Seite 12

### Text-Generierung

```
POST https://api-production-319f.up.railway.app/v1/completion-messages
```

**Body:**
```json
{
  "inputs": {"thema": "KI im Gesundheitswesen"},
  "response_mode": "blocking",
  "user": "benutzer-123"
}
```

### Workflow ausfuehren

```
POST https://api-production-319f.up.railway.app/v1/workflows/run
```

**Body:**
```json
{
  "inputs": {"eingabe": "Analysiere diese Daten"},
  "response_mode": "streaming",
  "user": "benutzer-123"
}
```

### Datei hochladen (fuer Dokument-Analyse)

```
POST https://api-production-319f.up.railway.app/v1/files/upload
```

**Headers:**
```
Authorization: Bearer <dein-api-key>
Content-Type: multipart/form-data
```

### Antwort-Modi

| Modus | Beschreibung |
|-------|-------------|
| `blocking` | Wartet bis die komplette Antwort fertig ist |
| `streaming` | Gibt die Antwort wortweise zurueck (Server-Sent Events) |

Streaming wird fuer Chat-Anwendungen empfohlen, da der Nutzer die Antwort sofort sieht.

---

<!-- Seite 13 -->
## Seite 13

# 3. Lyzr Search — AI-Suche

Lyzr Search ist eine Perplexity-aehnliche Suchmaschine die Fragen in natuerlicher Sprache beantwortet und Quellen anzeigt.

**Zugang:** Portal → Lyzr Search oder direkt https://perplexity-frontend-production.up.railway.app/

## 3.1 Suche starten

1. Oeffne Lyzr Search
2. Gib deine Frage in das Suchfeld ein, z.B.:
   - "Was sind die Vorteile von Kubernetes?"
   - "Erklaere mir Machine Learning"
   - "Aktuelle Nachrichten ueber kuenstliche Intelligenz"
3. Druecke Enter
4. Die KI durchsucht mehrere Suchmaschinen gleichzeitig (via SearXNG)
5. Die Ergebnisse werden von einem LLM zusammengefasst
6. Du erhaeltst eine strukturierte Antwort mit Quellenangaben

### Suchmaschinen im Hintergrund

SearXNG aggregiert Ergebnisse von ueber 70 Suchmaschinen:
- Google, Bing, DuckDuckGo
- Wikipedia, StackOverflow
- GitHub, Reddit
- Wissenschaftliche Datenbanken
- Nachrichtenportale

## 3.2 Chat-Modus

Nach der ersten Suche kannst du Folgefragen stellen:

1. Die erste Antwort erscheint
2. Tippe eine Folgefrage ein, z.B.: "Kannst du das genauer erklaeren?"
3. Die KI beruecksichtigt den Kontext der vorherigen Fragen
4. So kannst du ein Thema Schritt fuer Schritt vertiefen

Der Chat-Modus merkt sich den gesamten Gespraechsverlauf.

---

<!-- Seite 14 -->
## Seite 14

## 3.3 Quellen & verwandte Fragen

### Quellenangaben

Jede Antwort zeigt die verwendeten Quellen:
- Titel der Quelle
- URL zum Original-Artikel
- Klicke auf eine Quelle um sie im Original zu lesen

### Verwandte Fragen

Nach jeder Antwort werden automatisch verwandte Fragen vorgeschlagen:
- Klicke auf eine vorgeschlagene Frage um sie sofort zu suchen
- Die Vorschlaege basieren auf dem aktuellen Thema
- Hilft beim Erkunden neuer Aspekte

## 3.4 API-Nutzung

### Swagger-Dokumentation

Interaktive API-Docs: https://perplexity-backend-production.up.railway.app/docs

### Einfache Suche

```
POST https://perplexity-backend-production.up.railway.app/v1/search
```

**Body:**
```json
{
  "query": "Was ist Docker?"
}
```

### Chat (mit Kontext)

```
POST https://perplexity-backend-production.up.railway.app/chat
```

**Body:**
```json
{
  "query": "Erklaere mir Container",
  "history": []
}
```

---

<!-- Seite 15 -->
## Seite 15

### OpenAI-kompatibler Endpoint

Lyzr Search bietet einen OpenAI-kompatiblen Endpoint. Das bedeutet: Jede App die mit der OpenAI API funktioniert, kann auch Lyzr Search nutzen.

```
POST https://perplexity-backend-production.up.railway.app/v1/chat/completions
```

**Body:**
```json
{
  "model": "default",
  "messages": [
    {"role": "user", "content": "Was ist Kubernetes?"}
  ]
}
```

### Verfuegbare Modelle abfragen

```
GET https://perplexity-backend-production.up.railway.app/v1/models
```

Gibt eine Liste aller konfigurierten Sprachmodelle zurueck.

### Health Check

```
GET https://perplexity-backend-production.up.railway.app/health
```

Antwort: `{"status": "ok"}` wenn der Service laeuft.

---

<!-- Seite 16 -->
## Seite 16

# 4. Lyzr Governor — AI Governance

Der Governor ueberwacht und kontrolliert KI-Aktivitaeten. Damit stellst du sicher, dass KI-Systeme regelkonform arbeiten.

**Zugang:** Portal → Lyzr Governor oder direkt https://governor-production-a7da.up.railway.app/

## 4.1 Dashboard

Das Dashboard zeigt auf einen Blick:

- **Aktive Policies** — Wie viele Richtlinien sind aktiv
- **Approval Queue** — Offene Genehmigungsanfragen
- **Compliance Score** — Gesamtbewertung der Regelkonformitaet
- **Letzte Events** — Timeline der juengsten KI-Aktivitaeten
- **Statistiken** — Grafiken zu Nutzung, Ablehnungen, Genehmigungen

Die Daten werden ueber WebSocket in Echtzeit aktualisiert.

## 4.2 Policies erstellen

Policies sind Regeln die KI-Aktionen kontrollieren.

### Neue Policy anlegen

1. Gehe zu **"Policies"** im Dashboard
2. Klicke **"Neue Policy"**
3. Konfiguriere:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| **Name** | Kurzbezeichnung | "Keine personenbezogenen Daten" |
| **Typ** | `audit`, `authorization`, `approval` | `authorization` |
| **Regel** | Bedingung die geprueft wird | "Input darf keine E-Mail-Adressen enthalten" |
| **Aktion** | Was passiert bei Verstoss | `block`, `warn`, `log` |
| **Prioritaet** | Reihenfolge der Auswertung | 1 (hoechste) bis 10 |

4. Speichern und aktivieren

### Policy-Typen

| Typ | Funktion |
|-----|----------|
| **Audit** | Protokolliert die Aktion, blockiert nicht |
| **Authorization** | Prueft ob die Aktion erlaubt ist, blockiert bei Verstoss |
| **Approval** | Erfordert manuelle Genehmigung vor Ausfuehrung |

---

<!-- Seite 17 -->
## Seite 17

## 4.3 Approval Workflows

Fuer sensible KI-Aktionen kannst du Genehmigungsprozesse einrichten.

### Workflow einrichten

1. Erstelle eine Policy vom Typ **"Approval"**
2. Definiere die **Bedingung** (z.B. "Wenn das Modell GPT-4 ist UND die Anfrage mehr als 1000 Tokens hat")
3. Lege **Genehmiger** fest (E-Mail oder Rolle)
4. Definiere **Eskalation** (nach X Stunden ohne Antwort → naechster Genehmiger)

### Genehmigung bearbeiten

1. Gehe zu **"Approvals"** im Dashboard
2. Offene Anfragen werden mit Details angezeigt:
   - Wer hat die Anfrage gestellt
   - Welche Policy wurde ausgeloest
   - Was ist der Inhalt der Anfrage
3. Klicke **"Genehmigen"** oder **"Ablehnen"**
4. Optional: Fuege einen Kommentar hinzu

### Mehrstufige Genehmigung

Fuer besonders kritische Aktionen:

1. **Stufe 1:** Team-Lead genehmigt
2. **Stufe 2:** Compliance-Officer genehmigt
3. **Stufe 3:** Geschaeftsfuehrung genehmigt

Jede Stufe muss genehmigen bevor die Aktion ausgefuehrt wird.

---

<!-- Seite 18 -->
## Seite 18

## 4.4 Compliance Berichte (GDPR/SOC2)

### GDPR-Bericht generieren

1. Gehe zu **"Compliance"** → **"GDPR"**
2. Waehle den Zeitraum
3. Klicke **"Bericht generieren"**
4. Der Bericht enthaelt:
   - Verarbeitete personenbezogene Daten
   - Rechtsgrundlagen
   - Loeschprotokolle
   - Verarbeitungsverzeichnis

### SOC2-Bericht generieren

1. Gehe zu **"Compliance"** → **"SOC2"**
2. Waehle den Zeitraum
3. Der Bericht deckt ab:
   - Sicherheitskontrollen
   - Verfuegbarkeit
   - Vertraulichkeit
   - Integritaet der Verarbeitung

### Export

Berichte koennen als PDF oder JSON exportiert werden.

## 4.5 Event Tracking

Jede KI-Aktion wird protokolliert:

| Event-Feld | Beschreibung |
|-----------|-------------|
| **Zeitstempel** | Wann die Aktion stattfand |
| **Akteur** | Wer/was die Aktion ausgeloest hat |
| **Aktion** | Was getan wurde (z.B. "LLM-Aufruf", "Dokument-Abfrage") |
| **Policy-Ergebnis** | Genehmigt, Abgelehnt oder Ausstehend |
| **Details** | Input/Output der Aktion (maskiert bei sensiblen Daten) |

Events koennen nach Zeitraum, Typ und Ergebnis gefiltert werden.

---

<!-- Seite 19 -->
## Seite 19

# 5. Lyzr Crawl — Web Crawler

Lyzr Crawl extrahiert Inhalte von Webseiten. Ideal fuer Datensammlung, Content-Monitoring und RAG-Datenbeschaffung.

**Zugang:** Portal → Lyzr Crawl oder direkt https://lyzr-crawl-production.up.railway.app/

**API Key:** `lyzr-crawl-api-key-2026`

## 5.1 Crawl-Job starten

### Ueber die API

```
POST https://lyzr-crawl-production.up.railway.app/v1/crawl
```

**Headers:**
```
X-API-Key: lyzr-crawl-api-key-2026
Content-Type: application/json
```

**Body:**
```json
{
  "url": "https://beispiel.de",
  "max_pages": 10,
  "depth": 2
}
```

### Parameter

| Parameter | Typ | Beschreibung |
|-----------|-----|-------------|
| `url` | String | Start-URL zum Crawlen |
| `max_pages` | Integer | Maximale Anzahl zu crawlender Seiten |
| `depth` | Integer | Wie tief Links verfolgt werden (1 = nur Startseite, 2 = Links auf Startseite, etc.) |
| `include_patterns` | Array | Nur URLs die diesem Muster entsprechen (z.B. `["/blog/*"]`) |
| `exclude_patterns` | Array | URLs die uebersprungen werden sollen |

### Antwort

Du erhaeltst eine **Job-ID** zurueck. Damit fragst du den Status ab:

```
GET https://lyzr-crawl-production.up.railway.app/v1/crawl/{job-id}
```

---

<!-- Seite 20 -->
## Seite 20

## 5.2 Content Extraction

Der Crawler extrahiert fuer jede Seite:

| Feld | Beschreibung |
|------|-------------|
| **title** | Seitentitel |
| **url** | URL der Seite |
| **content** | Bereinigter Textinhalt (ohne HTML-Tags) |
| **html** | Original-HTML |
| **links** | Alle gefundenen Links auf der Seite |
| **metadata** | Meta-Tags (description, keywords, author) |
| **images** | Bild-URLs |
| **timestamp** | Zeitpunkt des Crawls |

### Content fuer RAG nutzen

Die gecrawlten Inhalte koennen direkt als Dokumente in Dify's Knowledge Base importiert werden:

1. Crawle eine Website
2. Exportiere die Ergebnisse als TXT oder Markdown
3. Lade sie in eine Dify-Wissensbasis hoch
4. Nutze sie in deinen Apps

## 5.3 Job-Verwaltung

### Alle Jobs auflisten

```
GET https://lyzr-crawl-production.up.railway.app/v1/jobs
```

### Job-Status pruefen

```
GET https://lyzr-crawl-production.up.railway.app/v1/jobs/{job-id}
```

**Moegliche Status:**
- `queued` — In der Warteschlange
- `running` — Wird gerade ausgefuehrt
- `completed` — Fertig
- `failed` — Fehlgeschlagen

### Live-Updates via WebSocket

Verbinde dich per WebSocket fuer Echtzeit-Updates:
```
ws://lyzr-crawl-production.up.railway.app/ws/{job-id}
```

---

<!-- Seite 21 -->
## Seite 21

## 5.4 Stealth Mode & Robots.txt

### Stealth Mode

Der Crawler kann so konfiguriert werden, dass er wie ein normaler Browser aussieht:
- **User-Agent Rotation** — Wechselt zwischen verschiedenen Browser-Kennungen
- **Request-Verzoegerung** — Wartet zwischen Anfragen um nicht als Bot erkannt zu werden
- **JavaScript-Rendering** — Fuehrt JavaScript aus (fuer Single-Page-Apps)

### Robots.txt

Standardmaessig respektiert der Crawler `robots.txt` Regeln:
- Seiten die in robots.txt gesperrt sind werden uebersprungen
- Du kannst dies ueber den Parameter `respect_robots` steuern

### Sitemap-Parsing

Wenn eine Website eine `sitemap.xml` hat:
- Der Crawler erkennt sie automatisch
- Alle URLs aus der Sitemap werden gecrawlt
- Effizienter als blindes Link-Folgen

## 5.5 API-Referenz

| Methode | Endpoint | Beschreibung |
|---------|----------|-------------|
| `POST` | `/v1/crawl` | Neuen Crawl-Job starten |
| `GET` | `/v1/crawl/{id}` | Job-Ergebnisse abrufen |
| `GET` | `/v1/jobs` | Alle Jobs auflisten |
| `GET` | `/v1/jobs/{id}` | Job-Status pruefen |
| `DELETE` | `/v1/jobs/{id}` | Job abbrechen |
| `GET` | `/health` | Service-Status |
| `WS` | `/ws/{id}` | Live-Updates per WebSocket |

Alle Endpoints erfordern den Header `X-API-Key: lyzr-crawl-api-key-2026`.

---

<!-- Seite 22 -->
## Seite 22

# 6. Agent Simulation Engine

Die Simulation Engine testet KI-Agents unter kontrollierten Bedingungen. Du simulierst Benutzer-Interaktionen und bewertest die Agent-Qualitaet.

**Zugang:** Portal → Agent Simulator oder direkt https://agent-simulation-production.up.railway.app/

## 6.1 Simulation erstellen

### Ueber die API

```
POST https://agent-simulation-production.up.railway.app/api/simulate
```

**Body:**
```json
{
  "agent_config": {
    "model": "gpt-4o",
    "system_prompt": "Du bist ein Kundenservice-Agent."
  },
  "scenario": {
    "name": "Beschwerde-Handling",
    "messages": [
      {"role": "user", "content": "Meine Bestellung ist nicht angekommen!"}
    ]
  },
  "num_runs": 5
}
```

### Parameter

| Parameter | Beschreibung |
|-----------|-------------|
| `agent_config` | Konfiguration des zu testenden Agents |
| `scenario` | Test-Szenario mit vordefinierten Nachrichten |
| `num_runs` | Wie oft die Simulation laufen soll (fuer statistische Auswertung) |
| `evaluation_criteria` | Bewertungskriterien (optional) |

### Alle Simulationen anzeigen

```
GET https://agent-simulation-production.up.railway.app/api/simulations
```

---

<!-- Seite 23 -->
## Seite 23

## 6.2 Szenarien & Personas

### Szenarien

Ein Szenario definiert eine Test-Situation:

| Szenario-Typ | Beschreibung | Beispiel |
|--------------|-------------|---------|
| **Happy Path** | Normaler, erfolgreicher Ablauf | Kunde fragt nach Preis → Agent antwortet |
| **Edge Case** | Grenzfall, ungewoehnliche Eingabe | Leere Nachricht, sehr langer Text |
| **Adversarial** | Versuch den Agent zu manipulieren | Prompt Injection, Jailbreak-Versuche |
| **Multi-Turn** | Mehrstufiges Gespraech | Bestellung → Reklamation → Stornierung |

### Personas

Personas simulieren verschiedene Benutzertypen:

| Persona | Verhalten |
|---------|----------|
| **Freundlicher Kunde** | Hoeflich, klare Fragen |
| **Verwirrter Nutzer** | Unklare Fragen, Tippfehler, Themen-Wechsel |
| **Vergeaergerter Kunde** | Emotional, Beschwerden, Drohungen |
| **Technischer Nutzer** | Detaillierte Fachfragen |
| **Manipulator** | Versucht den Agent auszutricksen |

## 6.3 Evaluationen ausfuehren

### Bewertungskriterien

| Kriterium | Was wird geprueft |
|-----------|------------------|
| **Relevanz** | Ist die Antwort relevant zur Frage? |
| **Korrektheit** | Sind die Fakten korrekt? |
| **Tonalitaet** | Ist der Ton angemessen? |
| **Sicherheit** | Gibt der Agent keine sensiblen Infos preis? |
| **Vollstaendigkeit** | Wird die Frage vollstaendig beantwortet? |

### Batch-Evaluation

Fuehre mehrere Szenarien auf einmal aus und erhalte eine Gesamtbewertung mit Durchschnittswerten pro Kriterium.

---

<!-- Seite 24 -->
## Seite 24

## 6.4 Hardening & Stress-Tests

### Hardening

Teste deinen Agent gegen Angriffe:

| Test | Beschreibung |
|------|-------------|
| **Prompt Injection** | Versuche den System-Prompt zu ueberschreiben |
| **Jailbreak** | Versuche Sicherheitsregeln zu umgehen |
| **Data Leakage** | Pruefe ob der Agent interne Daten preisgibt |
| **Hallucination** | Pruefe ob der Agent falsche Fakten erfindet |
| **Toxicity** | Pruefe ob der Agent beleidigende Inhalte erzeugt |

### Stress-Tests

| Test | Beschreibung |
|------|-------------|
| **Load Test** | Viele gleichzeitige Anfragen |
| **Long Context** | Sehr lange Eingaben |
| **Rapid Fire** | Schnelle aufeinanderfolgende Anfragen |
| **Token Limit** | Anfragen die das Token-Limit ausreizen |

### Ergebnisse interpretieren

Nach jedem Test erhaeltst du:
- **Pass/Fail** pro Testfall
- **Gesamtbewertung** in Prozent
- **Empfehlungen** zur Verbesserung
- **Detaillierte Logs** jeder Interaktion

---

<!-- Seite 25 -->
## Seite 25

# 7. Skills Kit

Das Skills Kit bietet vorgefertigte KI-Faehigkeiten (Skills) und ein Agent-Management-System (Kit).

**Zugang:** Portal → Skills & Kit oder direkt https://lyzr-skills-kit-production.up.railway.app/

## 7.1 Skills Adapters durchsuchen

### Alle Skills anzeigen

```
GET https://lyzr-skills-kit-production.up.railway.app/api/skills/adapters
```

### Verfuegbare Skill-Kategorien

| Kategorie | Beispiel-Skills |
|-----------|----------------|
| **Sales & Marketing** | Lead-Generierung, E-Mail-Kampagnen, Social Media Posts |
| **Content Creation** | Blog-Artikel, Produktbeschreibungen, Zusammenfassungen |
| **Data Analysis** | Daten-Reports, Trend-Analyse, KPI-Tracking |
| **Customer Service** | FAQ-Antworten, Ticket-Klassifizierung, Sentiment-Analyse |
| **HR & Recruiting** | Stellenbeschreibungen, CV-Screening, Interview-Fragen |
| **Legal** | Vertragsanalyse, Compliance-Pruefung |

### Skill-Details abrufen

Jeder Skill enthält:
- **Name** und Beschreibung
- **Input-Parameter** (was der Skill als Eingabe braucht)
- **Output-Format** (was zurueckgegeben wird)
- **Beispiel-Nutzung**

## 7.2 Kit Agents verwalten

### Alle Agents anzeigen

```
GET https://lyzr-skills-kit-production.up.railway.app/api/kit/agents
```

Agents sind vorkonfigurierte KI-Assistenten mit bestimmten Faehigkeiten und Zielen.

---

<!-- Seite 26 -->
## Seite 26

## 7.3 Custom Skills erstellen

### Skill-Format

Skills werden als JSON definiert:

```json
{
  "name": "E-Mail-Zusammenfassung",
  "description": "Fasst lange E-Mails in 3 Saetzen zusammen",
  "category": "productivity",
  "input": {
    "email_text": {
      "type": "string",
      "description": "Der vollstaendige E-Mail-Text"
    }
  },
  "prompt": "Fasse die folgende E-Mail in maximal 3 Saetzen zusammen:\n\n{{email_text}}",
  "output": {
    "type": "string",
    "description": "3-Satz-Zusammenfassung"
  }
}
```

### Skills in Dify nutzen

1. Erstelle einen Custom Skill im Skills Kit
2. Nutze die Skills Kit API als Custom Tool in Dify (siehe Kapitel 2.5)
3. Dein Dify-Agent kann nun den Skill aufrufen

### Skills exportieren

Skills koennen als JSON exportiert und in anderen Projekten wiederverwendet werden:

```
GET https://lyzr-skills-kit-production.up.railway.app/api/skills/adapters?format=export
```

---

<!-- Seite 27 -->
## Seite 27

# 8. CrewAI Studio — Multi-Agent Teams

CrewAI Studio ist eine visuelle Oberflaeche zum Erstellen und Verwalten von KI-Agent-Teams. Mehrere Agents arbeiten zusammen um komplexe Aufgaben zu loesen.

**Zugang:** Portal → CrewAI Studio oder direkt https://crewai-studio-production-0433.up.railway.app/

## 8.1 Agents erstellen

### Neuen Agent anlegen

1. Oeffne CrewAI Studio
2. Gehe zu **"Agents"** in der Seitenleiste
3. Klicke **"Create Agent"**
4. Konfiguriere:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| **Role** | Die Rolle des Agents | "Senior Research Analyst" |
| **Goal** | Was der Agent erreichen soll | "Finde die neuesten Markttrends" |
| **Backstory** | Hintergrundgeschichte fuer Kontext | "Du bist ein erfahrener Analyst mit 10 Jahren Erfahrung..." |
| **LLM** | Welches Sprachmodell | GPT-4o, Claude 3.5 Sonnet |
| **Tools** | Welche Tools der Agent nutzen darf | Web Search, Scraper, CSV Search |
| **Allow Delegation** | Darf der Agent Aufgaben an andere Agents weitergeben | Ja/Nein |
| **Verbose** | Ausfuehrliche Logs | Ja/Nein |

5. Speichern

### Agent-Beispiele

| Agent | Role | Goal |
|-------|------|------|
| **Researcher** | Marktforscher | Aktuelle Trends und Daten finden |
| **Writer** | Content Writer | Erkenntnisse in Berichte umwandeln |
| **Analyst** | Daten-Analyst | Zahlen auswerten und Muster erkennen |
| **Quality Checker** | QA-Spezialist | Ergebnisse pruefen und verbessern |

---

<!-- Seite 28 -->
## Seite 28

## 8.2 Tasks definieren

Tasks sind die Aufgaben die den Agents zugewiesen werden.

### Neuen Task anlegen

1. Gehe zu **"Tasks"** in der Seitenleiste
2. Klicke **"Create Task"**
3. Konfiguriere:

| Feld | Beschreibung | Beispiel |
|------|-------------|---------|
| **Description** | Detaillierte Aufgabenbeschreibung | "Recherchiere die Top 5 KI-Trends fuer 2026 und erstelle eine Zusammenfassung mit Quellen" |
| **Expected Output** | Was als Ergebnis erwartet wird | "Eine Liste mit 5 Trends, je 2-3 Saetze Beschreibung und Quellenlinks" |
| **Agent** | Welcher Agent diese Aufgabe bearbeitet | "Senior Research Analyst" |
| **Context** | Ergebnisse anderer Tasks als Input | (optional) Verknuepfung zu vorherigen Tasks |

### Task-Abhaengigkeiten

Tasks koennen aufeinander aufbauen:

```
Task 1: Researcher → "Finde aktuelle KI-Trends"
    ↓ (Ergebnis als Kontext)
Task 2: Writer → "Schreibe einen Bericht basierend auf den Trends"
    ↓ (Ergebnis als Kontext)
Task 3: Quality Checker → "Pruefe den Bericht auf Fehler"
```

Der Output von Task 1 wird automatisch als Input fuer Task 2 verwendet.

---

<!-- Seite 29 -->
## Seite 29

## 8.3 Crews zusammenstellen

Eine Crew kombiniert Agents und Tasks zu einem Team.

### Neue Crew anlegen

1. Gehe zu **"Crews"** in der Seitenleiste
2. Klicke **"Create Crew"**
3. Konfiguriere:

| Feld | Beschreibung |
|------|-------------|
| **Name** | Name der Crew (z.B. "Content-Team") |
| **Process** | `sequential` (nacheinander) oder `hierarchical` (mit Manager) |
| **Agents** | Welche Agents zur Crew gehoeren |
| **Tasks** | Welche Tasks ausgefuehrt werden |

### Prozess-Typen

| Typ | Beschreibung | Wann nutzen |
|-----|-------------|------------|
| **Sequential** | Tasks werden nacheinander ausgefuehrt, jeder Agent arbeitet seinen Task ab | Klare Reihenfolge, einfache Ablaeufe |
| **Hierarchical** | Ein Manager-Agent verteilt und koordiniert die Arbeit | Komplexe Aufgaben, flexible Zuweisung |

## 8.4 Crew ausfuehren

### Start

1. Oeffne die Crew
2. Klicke **"Run Crew"** (Play-Button)
3. Gib eventuelle Eingabe-Parameter ein
4. Die Ausfuehrung startet

### Live-Verfolgung

Waehrend der Ausfuehrung siehst du:
- Welcher Agent gerade arbeitet
- Welches Tool er gerade nutzt
- Zwischenergebnisse in Echtzeit
- Delegierungen zwischen Agents

### Ergebnis

Nach Abschluss wird das Gesamtergebnis angezeigt — die kombinierte Ausgabe aller Tasks.

---

<!-- Seite 30 -->
## Seite 30

## 8.5 Tools anbinden

Tools geben den Agents Faehigkeiten ueber reines Textgenerieren hinaus.

### Eingebaute Tools

| Tool | Beschreibung | Wann nutzen |
|------|-------------|------------|
| **DuckDuckGoSearch** | Web-Suche ueber DuckDuckGo | Aktuelle Informationen recherchieren |
| **ScrapeWebsite** | Webseiten-Inhalte extrahieren | Daten von bestimmten Seiten holen |
| **ScrapflyScrapeWebsite** | Erweitertes Web Scraping (via Scrapfly) | JavaScript-lastige Seiten |
| **CSVSearch** | CSV-Dateien durchsuchen | Daten in Tabellen analysieren |
| **CustomAPI** | Beliebige REST-APIs aufrufen | Externe Services anbinden |
| **CodeInterpreter** | Python-Code ausfuehren | Berechnungen, Daten-Analyse |
| **FileWrite** | Dateien schreiben | Ergebnisse als Datei speichern |

### Tool einem Agent zuweisen

1. Oeffne den Agent
2. Im Feld **"Tools"** waehle die gewuenschten Tools
3. Speichern

Der Agent entscheidet selbst wann er welches Tool einsetzt.

### Custom API Tool konfigurieren

```json
{
  "name": "Firmendaten-API",
  "base_url": "https://api.beispiel.de",
  "headers": {
    "Authorization": "Bearer <api-key>"
  },
  "endpoints": [
    {
      "method": "GET",
      "path": "/companies/{id}",
      "description": "Firmendaten abrufen"
    }
  ]
}
```

---

<!-- Seite 31 -->
## Seite 31

## 8.6 Crew exportieren

### Als Python-Code

1. Oeffne die Crew
2. Klicke **"Export"**
3. Du erhaeltst ausfuehrbaren Python-Code:

```python
from crewai import Agent, Task, Crew

researcher = Agent(
    role="Senior Research Analyst",
    goal="Finde die neuesten Markttrends",
    backstory="Du bist ein erfahrener Analyst...",
    tools=[search_tool],
    verbose=True
)

research_task = Task(
    description="Recherchiere die Top 5 KI-Trends fuer 2026",
    expected_output="Eine Liste mit 5 Trends...",
    agent=researcher
)

crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    process="sequential"
)

result = crew.kickoff()
print(result)
```

### Export-Nutzung

- **Lokal ausfuehren:** Code in eigener Python-Umgebung starten
- **In Dify integrieren:** Als Code-Node in einem Dify-Workflow
- **Automatisieren:** In CI/CD-Pipeline oder Cron-Job einbinden
- **Anpassen:** Code als Basis fuer eigene Erweiterungen

---

<!-- Seite 32 -->
## Seite 32

# 9. Policy Gateway

Der Policy Gateway ist ein Enforcement-Layer der KI-Anfragen gegen definierte Richtlinien prueft bevor sie ausgefuehrt werden.

**Zugang:** https://policy-gateway-production.up.railway.app/

## 9.1 Policy Enforcement

### Funktionsweise

```
Client → Policy Gateway → Pruefung gegen Policies → Weiterleitung an KI-Service
```

1. Eine KI-Anfrage kommt herein
2. Der Gateway prueft alle aktiven Policies (aus dem Governor)
3. Bei Verstoss: Anfrage wird blockiert mit Fehlermeldung
4. Bei Einhaltung: Anfrage wird an den KI-Service weitergeleitet

### Status pruefen

```
GET https://policy-gateway-production.up.railway.app/health
```

Antwort:
```json
{"status": "healthy"}
```

### API-Info

```
GET https://policy-gateway-production.up.railway.app/
```

Antwort:
```json
{"message": "Policy Gateway API", "status": "running"}
```

### Integration mit Governor

Der Policy Gateway arbeitet zusammen mit dem Lyzr Governor:
- **Governor** = Policies definieren und verwalten (Kapitel 4)
- **Policy Gateway** = Policies in Echtzeit durchsetzen

---

<!-- Seite 33 -->
## Seite 33

# 10. Storage

Der Storage Service bietet S3-kompatiblen Dateispeicher fuer die gesamte Plattform.

**URL:** https://storage-production-afed.up.railway.app/

## 10.1 Dateien hochladen & abrufen

### Zugangsdaten

```
S3 Access Key: A9ASHe2WLonQNCPx
S3 Secret Key: oXE3e85wUzLOXZQ0jsr89Eqj8v01CCbv
Endpoint:      https://storage-production-afed.up.railway.app
```

### Nutzung mit AWS CLI

```bash
# Konfigurieren
aws configure
  AWS Access Key ID: A9ASHe2WLonQNCPx
  AWS Secret Access Key: oXE3e85wUzLOXZQ0jsr89Eqj8v01CCbv

# Datei hochladen
aws s3 cp datei.pdf s3://bucket-name/ \
  --endpoint-url https://storage-production-afed.up.railway.app

# Dateien auflisten
aws s3 ls s3://bucket-name/ \
  --endpoint-url https://storage-production-afed.up.railway.app

# Datei herunterladen
aws s3 cp s3://bucket-name/datei.pdf ./lokal/ \
  --endpoint-url https://storage-production-afed.up.railway.app
```

### Nutzung in Dify

Dify nutzt den Storage automatisch fuer:
- Hochgeladene Dokumente (Knowledge Base)
- Generierte Dateien
- Plugin-Dateien
- Backup-Daten

---

<!-- Seite 34 -->
## Seite 34

# 11. Administration

## 11.1 Monorepo-Struktur

Alle Services liegen in einem GitHub-Repository:

**https://github.com/dsactivi-2/ai-platform**

```
ai-platform/
├── docs/
│   └── USERMANUAL.md        ← Dieses Handbuch
└── services/
    ├── gateway/              ← Portal + Reverse Proxy + Auth
    ├── crewai-studio/        ← Streamlit Multi-Agent UI
    ├── perplexity-backend/   ← FastAPI Search API
    ├── perplexity-frontend/  ← Next.js Search UI
    ├── governor/             ← Governance Dashboard (Python)
    ├── crawl/                ← Web Crawler API (Go)
    ├── agent-simulation/     ← Simulation Engine (Python)
    └── skills-kit/           ← Skills + Kit (Python)
```

## 11.2 Deployment & Updates

### Automatisches Deployment

Jeder `git push` auf den `master`-Branch loest automatisch ein Deployment aus. Durch **Watch Paths** wird nur der geaenderte Service neu gebaut.

### Service manuell updaten

1. Aendere Dateien im entsprechenden `services/`-Ordner
2. Committe und pushe:
```bash
cd ai-platform
git add services/gateway/
git commit -m "Gateway: Update XYZ"
git push origin master
```
3. Railway baut nur den Gateway-Service neu (ca. 30-60 Sekunden)

### Alle Services neu bauen

Ueber die Railway API:
```bash
# Einzelnen Service deployen
railway service deploy <service-name>
```

---

<!-- Seite 35 -->
## Seite 35

## 11.3 Infrastruktur-Services

Diese Services laufen im Hintergrund und sind nur intern erreichbar.

### Postgres (Relationale Datenbank)

| | |
|---|---|
| **Host** | `postgres.railway.internal` |
| **User** | `postgres` |
| **Passwort** | `VzOTQkxATtPYprGwOyVmtLeayAJUemgQ` |
| **Genutzt von** | Dify (Apps, User, Workflows, Logs) |

### MongoDB (Dokument-Datenbank)

| | |
|---|---|
| **Host** | `mongodb.railway.internal` |
| **User** | `mongo` |
| **Passwort** | `LkMQzWPPwPpKzrIsCdsxMphsGqRfpXOI` |
| **Genutzt von** | Crawl (Ergebnisse), Governor (Events) |

### Redis (Cache & Queue)

| | |
|---|---|
| **Host** | `redis.railway.internal` |
| **User** | `default` |
| **Passwort** | `w0wA!0*rtSp!UfLUWUc-zk_Uj21bCXgd` |
| **Genutzt von** | Dify (Sessions, Worker-Queue) |

### Weaviate (Vektor-Datenbank)

| | |
|---|---|
| **Host** | `weaviate.railway.internal` |
| **API Key** | `S4bEOzkZ` |
| **Genutzt von** | Dify (RAG Embeddings, Semantic Search) |

### Qdrant (Vektor-Datenbank)

| | |
|---|---|
| **Host** | `qdrant.railway.internal` |
| **Auth** | Keine |
| **Genutzt von** | Alternative Vektor-Suche |

### SearXNG (Meta-Suchmaschine)

| | |
|---|---|
| **Host** | `searxng.railway.internal` |
| **Auth** | Keine |
| **Genutzt von** | Lyzr Search (aggregiert 70+ Suchmaschinen) |

---

<!-- Seite 36 -->
## Seite 36

## 11.4 Zugangsdaten-Uebersicht

### Gateway (fuer alle Tools)

| | |
|---|---|
| **User** | `admin` |
| **Passwort** | `DjeLD-YE23momovV` |

### Dify

| | |
|---|---|
| **Ersteinrichtungs-Passwort** | `rYST6F1P` |
| **API Secret Key** | `Sis6aRp9xFy3fbuMJUiS3jDfRaCb4e1S` |

### Lyzr Crawl

| | |
|---|---|
| **API Key** | `lyzr-crawl-api-key-2026` |

### Storage (S3)

| | |
|---|---|
| **Access Key** | `A9ASHe2WLonQNCPx` |
| **Secret Key** | `oXE3e85wUzLOXZQ0jsr89Eqj8v01CCbv` |

### Datenbanken

| Service | User | Passwort |
|---------|------|----------|
| Postgres | `postgres` | `VzOTQkxATtPYprGwOyVmtLeayAJUemgQ` |
| MongoDB | `mongo` | `LkMQzWPPwPpKzrIsCdsxMphsGqRfpXOI` |
| Redis | `default` | `w0wA!0*rtSp!UfLUWUc-zk_Uj21bCXgd` |
| Weaviate | — | API Key: `S4bEOzkZ` |

---

<!-- Seite 37 -->
## Seite 37

## 11.5 Fehlerbehebung

### Service antwortet nicht (502/503)

1. Pruefe ob der Service laeuft: Oeffne die direkte URL
2. Wenn nur ueber Gateway nicht erreichbar: Pruefe Railway Dashboard ob der Service "Running" ist
3. Loesung: Service in Railway neu starten

### Gateway-Login funktioniert nicht

1. Stelle sicher dass Benutzername und Passwort korrekt sind (Gross/Kleinschreibung beachten)
2. Browser-Cache leeren oder Inkognito-Fenster verwenden
3. Login: `admin` / `DjeLD-YE23momovV`

### Dify zeigt "Internal Server Error"

1. Pruefe ob die Datenbank (Postgres) laeuft
2. Pruefe ob Redis laeuft
3. Im Railway Dashboard die Logs des API-Service pruefen

### Lyzr Search gibt keine Ergebnisse

1. Pruefe ob SearXNG laeuft (interner Service)
2. Pruefe ob ein LLM-Provider konfiguriert ist
3. Backend-Logs pruefen

### CrewAI Studio laed nicht

1. Pruefe die direkte URL: https://crewai-studio-production-0433.up.railway.app/
2. Streamlit braucht manchmal 10-15 Sekunden beim ersten Laden
3. Pruefe ob ein LLM API-Key als Umgebungsvariable gesetzt ist

### Crawl-Jobs schlagen fehl

1. Pruefe den API Key: `lyzr-crawl-api-key-2026`
2. Pruefe ob MongoDB und RabbitMQ laufen (Health-Endpoint)
3. Manche Webseiten blockieren Crawler — versuche den Stealth Mode

### Deployment schlaegt fehl

1. Pruefe die Build-Logs im Railway Dashboard
2. Haeufige Ursache: Dockerfile-Fehler oder fehlende Abhaengigkeiten
3. Pruefe ob das Root Directory korrekt gesetzt ist

---

**Ende des Benutzerhandbuchs**

*Version 1.0 — Stand: 15. Februar 2026*
*AI Platform — Dify + Lyzr + CrewAI*
