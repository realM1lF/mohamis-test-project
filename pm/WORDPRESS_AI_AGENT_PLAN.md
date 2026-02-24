# WordPress AI Agent Plugin - Projektplan

> Ein WordPress-Plugin mit KI-Mitarbeiter, inspiriert von Mohami aber nativ für WordPress.

---

## 🎯 Vision

Ein WordPress-Plugin, das einen KI-Mitarbeiter ("WP-Agent") in den WordPress Admin integriert:

- 💬 **Chat-Interface** im Admin-Bereich (Floating Widget + Dashboard)
- 🧠 **Gedächtnis-System** mit 4 Schichten (Session, User, Global, Persistent)
- 🛠️ **Tool-Use**: KI kann WordPress-Funktionen ausführen (Posts, Seiten, Einstellungen)
- 🎭 **Persönlichkeit**: Konfigurierbar via Markdown (Soul, Rules, Knowledge)
- 🚀 **Deployment**: Läuft auf Shared Hosting (Pure PHP) bis VPS (Docker)

---

## 🏗️ Architektur-Entscheidungen

### 1. Technologie-Stack

| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| **Backend** | PHP 8.1+ | WordPress-nativ, keine externen Dependencies |
| **LLM Client** | Prism PHP oder OpenAI PHP SDK | Moderne PHP Libraries, PSR-4 |
| **Frontend** | React + @wordpress/components | Gutenberg-kompatibel, WP-Design-Language |
| **State** | @wordpress/data | Redux-ähnlich, WP-nativ |
| **Real-time** | SSE (Server-Sent Events) | Text-Streaming wie ChatGPT |
| **Memory** | MySQL Custom Tables + wp_usermeta | WordPress-Standard, performant |
| **Auth** | Application Passwords | Sicher, einfach für externe Clients |

### 2. Plugin-Architektur (MVC-lite)

```
mohami-wp-agent/
├── mohami-wp-agent.php          # Main Plugin File
├── composer.json                # PSR-4 Autoloading
├── uninstall.php
│
├── assets/                      # Build-Assets
│   ├── css/
│   └── js/
│       ├── chat-widget.js       # React Chat
│       └── admin.js
│
├── src/                         # PHP Source (PSR-4)
│   ├── Core/
│   │   ├── Plugin.php           # Main Class (Singleton)
│   │   ├── Router.php           # REST API Router
│   │   └── Assets.php           # Script/Style Loader
│   │
│   ├── Admin/
│   │   ├── ChatWidget.php       # Floating Chat
│   │   ├── DashboardWidget.php  # Dashboard Integration
│   │   └── SettingsPage.php     # Plugin Settings
│   │
│   ├── API/
│   │   ├── REST/
│   │   │   ├── ChatController.php
│   │   │   ├── ToolController.php
│   │   │   └── AuthMiddleware.php
│   │   └── WordPress/
│   │       ├── Posts.php        # Post Tools
│   │       ├── Pages.php        # Page Tools
│   │       ├── Settings.php     # Options Tools
│   │       └── Media.php        # Media Tools
│   │
│   ├── AI/
│   │   ├── Client.php           # LLM Client (Prism)
│   │   ├── Conversation.php     # Chat Handler
│   │   ├── Streaming.php        # SSE Implementation
│   │   └── Tools/               # AI Tools
│   │       ├── PostTool.php
│   │       ├── PageTool.php
│   │       └── SettingTool.php
│   │
│   ├── Memory/
│   │   ├── SessionMemory.php    # Schicht 1: Session
│   │   ├── UserMemory.php       # Schicht 2: User Meta
│   │   ├── GlobalMemory.php     # Schicht 3: Options
│   │   └── PersistentMemory.php # Schicht 4: Custom Tables
│   │
│   ├── Database/
│   │   ├── Tables.php           # Table Definitions
│   │   ├── Migrations.php       # DB Updates
│   │   └── ConversationRepository.php
│   │
│   └── Agent/
│       ├── Identity.php         # Soul/Rules/Knowledge Loader
│       ├── Personality.php      # Personality Engine
│       └── Config.php           # Agent Configuration
│
├── templates/                   # PHP Templates
│   └── admin/
│       ├── chat-widget.php
│       └── settings-page.php
│
└── languages/                   # i18n
```

---

## 📋 Phase 1: Foundation (Woche 1-2)

### 1.1 Plugin Boilerplate
- [ ] Composer Setup mit PSR-4 Autoloading
- [ ] Main Plugin File mit Activation/Deactivation Hooks
- [ ] Namespace: `Mohami\WPAgent`
- [ ] WordPress Coding Standards einrichten

### 1.2 Datenbank-Schema
```sql
-- Conversations
CREATE TABLE wp_mohami_conversations (
    id bigint(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id varchar(64) NOT NULL,
    user_id bigint(20) UNSIGNED DEFAULT NULL,
    role enum('user', 'assistant', 'system') NOT NULL,
    content longtext NOT NULL,
    context_hash varchar(32),
    created_at datetime DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_user_time (user_id, created_at)
);

-- AI Actions (Tool Executions)
CREATE TABLE wp_mohami_actions (
    id bigint(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_id bigint(20) UNSIGNED,
    action_type varchar(50) NOT NULL,
    object_type varchar(50) NOT NULL,
    object_id bigint(20),
    parameters longtext,
    result longtext,
    status varchar(20),
    executed_at datetime DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_conversation (conversation_id),
    INDEX idx_action (action_type, object_type)
);

-- Memory (Long-term)
CREATE TABLE wp_mohami_memory (
    id bigint(20) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id bigint(20) UNSIGNED DEFAULT NULL,
    memory_type varchar(50) NOT NULL,
    content longtext NOT NULL,
    embedding_hash varchar(64),
    context varchar(255),
    created_at datetime DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_type (user_id, memory_type),
    FULLTEXT INDEX idx_content (content)
);
```

### 1.3 Basis REST API
- [ ] Namespace: `mohami-agent/v1`
- [ ] Endpoints:
  - `POST /chat` - Sende Nachricht
  - `GET /chat/{session_id}/history` - Lade Historie
  - `DELETE /chat/{session_id}` - Lösche Session
- [ ] Auth Middleware (Application Passwords)
- [ ] Rate Limiting (Transients)

---

## 📋 Phase 2: Chat Interface (Woche 3-4)

### 2.1 Admin Integration
- [ ] Floating Chat Widget (admin_footer hook)
- [ ] Dashboard Widget (wp_add_dashboard_widget)
- [ ] Admin Menu Page (Einstellungen)

### 2.2 React Frontend
- [ ] Setup mit @wordpress/scripts
- [ ] ChatWindow Component
- [ ] MessageBubble Component (User/AI)
- [ ] InputArea Component
- [ ] ToolExecutionCard Component

### 2.3 Real-time Streaming
- [ ] SSE Endpoint Implementation
- [ ] Text-Streaming (zeichenweise Anzeige)
- [ ] Typing Indicator
- [ ] Connection Error Handling

---

## 📋 Phase 3: AI Integration (Woche 5-6)

### 3.1 LLM Client
- [ ] Prism PHP SDK Integration
- [ ] Unterstützung für:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Lokale Modelle (via Ollama - optional)
- [ ] Konfigurierbarer API-Key

### 3.2 Tool System
- [ ] Tool Registry
- [ ] Tool Definition Schema (JSON)
- [ ] Tool Execution Engine
- [ ] Erste Tools:
  - `get_posts` - Beiträge auflisten
  - `create_post` - Beitrag erstellen
  - `update_post` - Beitrag aktualisieren
  - `get_post` - Beitrag lesen

### 3.3 System Prompt
- [ ] Dynamischer Prompt Builder
- [ ] WordPress Context Injection
  - Aktueller User
  - Aktuelle Seite im Admin
  - Verfügbare Tools
- [ ] Personality Injection (Soul.md)

---

## 📋 Phase 4: Memory System (Woche 7-8)

### 4.1 4-Schichten-Implementierung

| Schicht | Implementierung | Use Case |
|---------|----------------|----------|
| **Session** | `$_SESSION` / Transients | Aktive Konversation |
| **User** | `wp_usermeta` | Benutzer-Präferenzen |
| **Global** | `wp_options` | Plugin-Einstellungen |
| **Persistent** | Custom Table `wp_mohami_memory` | Gelernte Fakten, Episoden |

### 4.2 Memory Features
- [ ] Konversationshistorie speichern/laden
- [ ] Context Window Management
- [ ] Memory Injection in Prompts
- [ ] User-Präferenzen lernen

### 4.3 Agent Identity
- [ ] Soul.md Parser
- [ ] Rules.md Parser
- [ ] Knowledge.md Parser
- [ ] Dynamische Personality Loading

---

## 📋 Phase 5: WordPress Tools (Woche 9-10)

### 5.1 Content Tools
- [ ] Posts CRUD
- [ ] Pages CRUD
- [ ] Media Library Zugriff
- [ ] Taxonomies (Categories, Tags)

### 5.2 Settings Tools
- [ ] Option Lesen (`get_option`)
- [ ] Option Schreiben (`update_option`)
- [ ] Theme Einstellungen
- [ ] Plugin Einstellungen

### 5.3 User Tools
- [ ] User Liste
- [ ] User Profil anpassen
- [ ] Rollen & Rechte prüfen

### 5.4 Safety
- [ ] Capability Checks (immer!)
- [ ] Nonce Verification
- [ ] Input Sanitization
- [ ] Output Escaping
- [ ] Action Logging

---

## 📋 Phase 6: UI/UX Polish (Woche 11-12)

### 6.1 Design System
- [ ] WordPress Design Language
- [ ] Dark Mode Support (WP-Admin Theme)
- [ ] Responsive Design
- [ ] Animationen (Typing, Tool-Execution)

### 6.2 User Experience
- [ ] Quick Actions (Vorschläge)
- [ ] Keyboard Shortcuts
- [ ] Toast Notifications
- [ ] Error Handling & Recovery

### 6.3 Onboarding
- [ ] Setup Wizard
- [ ] API-Key Konfiguration
- [ ] Erster Test-Chat
- [ ] Dokumentation im Plugin

---

## 📋 Phase 7: Testing & Release (Woche 13-14)

### 7.1 Testing
- [ ] Unit Tests (PHPUnit)
- [ ] Integration Tests (REST API)
- [ ] E2E Tests (Playwright)
- [ ] Security Audit
- [ ] Performance Testing

### 7.2 Deployment
- [ ] WordPress.org Plugin Directory vorbereiten
- [ ] README.txt
- [ ] Screenshots
- [ ] Changelog

### 7.3 Dokumentation
- [ ] User Documentation
- [ ] Developer Documentation
- [ ] API Documentation

---

## 🔧 Technische Details

### WordPress Hooks

```php
// Admin-Integration
add_action('admin_footer', [$this, 'render_chat_widget']);
add_action('admin_enqueue_scripts', [$this, 'enqueue_chat_assets']);
add_action('wp_dashboard_setup', [$this, 'register_dashboard_widget']);

// REST API
add_action('rest_api_init', [$this, 'register_rest_routes']);

// Datenbank
register_activation_hook(__FILE__, [$this, 'activate']);
register_deactivation_hook(__FILE__, [$this, 'deactivate']);
```

### REST API Endpunkte

```php
// Chat
POST   /wp-json/mohami-agent/v1/chat
GET    /wp-json/mohami-agent/v1/chat/{session_id}/history
DELETE /wp-json/mohami-agent/v1/chat/{session_id}

// Tools
POST   /wp-json/mohami-agent/v1/tools/execute
GET    /wp-json/mohami-agent/v1/tools/list

// Memory
GET    /wp-json/mohami-agent/v1/memory
POST   /wp-json/mohami-agent/v1/memory
DELETE /wp-json/mohami-agent/v1/memory/{id}

// Settings
GET    /wp-json/mohami-agent/v1/settings
POST   /wp-json/mohami-agent/v1/settings
```

### Sicherheit

```php
// Capability Checks
if (!current_user_can('manage_options')) {
    return new WP_Error('unauthorized', 'Insufficient permissions', ['status' => 403]);
}

// Nonce Verification
wp_verify_nonce($request->get_header('X-WP-Nonce'), 'wp_rest');

// Rate Limiting
$transient_key = 'mohami_rate_' . get_current_user_id();
$requests = get_transient($transient_key);
if ($requests > 50) {
    return new WP_Error('rate_limited', 'Too many requests', ['status' => 429]);
}
set_transient($transient_key, $requests + 1, HOUR_IN_SECONDS);
```

---

## 📦 Deployment-Optionen

### Option A: Pure PHP (Shared Hosting)
- Externe LLM APIs (OpenAI, Anthropic)
- MySQL für Memory
- Keine zusätzliche Infrastruktur

### Option B: Docker (VPS)
- Lokal: Ollama + Chroma + WordPress
- Full Control
- Self-Hosted LLMs

### Option C: Hybrid (Empfohlen)
- Plugin: Frontend + API Bridge
- Extern: SaaS-API für komplexe KI
- Best of both worlds

---

## 🚀 Roadmap

| Phase | Zeit | Milestone |
|-------|------|-----------|
| 1 | Woche 1-2 | Plugin Foundation |
| 2 | Woche 3-4 | Chat Interface |
| 3 | Woche 5-6 | AI Integration |
| 4 | Woche 7-8 | Memory System |
| 5 | Woche 9-10 | WordPress Tools |
| 6 | Woche 11-12 | UI/UX Polish |
| 7 | Woche 13-14 | Testing & Release |

**Gesamt: 14 Wochen (~3 Monate)**

---

## 💡 Besonderheiten

### Vorteile gegenüber Mohami
- ✅ Läuft auf Shared Hosting (kein Docker nötig)
- ✅ Native WordPress-Integration
- ✅ Keine separate Infrastruktur
- ✅ Einfache Installation (Plugin-Verzeichnis)

### Technische Innovationen
- 🆕 WordPress Abilities API (neuer Standard)
- 🆕 MCP Adapter Support
- 🆕 React + @wordpress/components
- 🆕 SSE Streaming

---

**Soll ich mit Phase 1 beginnen?**
