/**
 * AI Office — Main Application JS v2.1
 * Handles SSE, API calls, agent interaction, tool dashboards, settings modal,
 * coffee shop interaction, live updates, particles & animations.
 */

const API = '';
let selectedAgent = null;
let officeState = {};
let currentTab = 'office';
let settingsData = null;

// ─── Particle System ─────────────────────────────────────
function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    function spawnParticle() {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.top = (80 + Math.random() * 70) + '%';
        p.style.animationDuration = (8 + Math.random() * 12) + 's';
        p.style.opacity = (0.15 + Math.random() * 0.3);
        const size = 1 + Math.random() * 2;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        container.appendChild(p);
        setTimeout(() => p.remove(), 20000);
    }

    for (let i = 0; i < 12; i++) {
        setTimeout(spawnParticle, Math.random() * 5000);
    }
    setInterval(spawnParticle, 1500);
}

// ─── Wall Clock ──────────────────────────────────────────
function updateClock() {
    const el = document.getElementById('wall-clock-time');
    if (!el) return;
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    el.textContent = h + ':' + m;
}

// ─── Toast Notifications ─────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'success') toast.style.borderLeftColor = '#40c057';
    else if (type === 'error') toast.style.borderLeftColor = '#e94560';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ─── SSE Connection ──────────────────────────────────────
function connectSSE() {
    const es = new EventSource(`${API}/api/events`);

    es.addEventListener('status', (e) => {
        try {
            const newState = JSON.parse(e.data);
            if (newState.cycle && newState.cycle !== officeState.cycle) {
                showToast(`Cycle ${newState.cycle} started`, 'success');
            }
            officeState = newState;
            updateOffice(officeState);
        } catch {}
    });

    es.addEventListener('ping', () => {});

    es.onerror = () => {
        es.close();
        setTimeout(connectSSE, 3000);
    };
}

// ─── Update Office View ──────────────────────────────────
function updateOffice(state) {
    const pill = document.getElementById('status-pill');
    if (state.running) {
        pill.textContent = `CYCLE ${state.cycle || 0}`;
        pill.className = 'status-pill';
    } else {
        pill.textContent = 'STOPPED';
        pill.className = 'status-pill stopped';
    }

    if (state.agents) {
        for (const [id, data] of Object.entries(state.agents)) {
            updateAgentSprite(id, data);
        }
    }
}

function updateAgentSprite(id, data) {
    const el = document.getElementById(`agent-${id}`);
    if (!el) return;

    const dot = el.querySelector('.agent-status-dot');
    if (dot) {
        dot.className = `agent-status-dot ${data.status || 'idle'}`;
    }

    if (data.status === 'working') {
        el.classList.add('working');
    } else {
        el.classList.remove('working');
    }

    const bubble = el.querySelector('.speech-bubble');
    if (bubble && data.current_task) {
        bubble.textContent = data.current_task.substring(0, 40);
        el.classList.add('speaking');
    } else if (bubble) {
        bubble.textContent = data.status || 'idle';
        el.classList.remove('speaking');
    }
}

// ─── Tab Switching (Office / Email / Telegram / Web) ─────
function switchTab(tab) {
    currentTab = tab;
    // Update tab buttons
    document.querySelectorAll('.tool-tab').forEach(el => {
        el.classList.toggle('active', el.dataset.tab === tab);
    });

    const officeView = document.getElementById('office-view');
    const toolsPanel = document.getElementById('tools-panel');

    if (tab === 'office') {
        officeView.style.display = '';
        toolsPanel.style.display = 'none';
    } else {
        officeView.style.display = 'none';
        toolsPanel.style.display = '';
        // Show the correct dashboard
        document.querySelectorAll('.tool-dashboard').forEach(el => el.style.display = 'none');
        const panel = document.getElementById(`tab-${tab}`);
        if (panel) panel.style.display = '';
        // Load dash data
        loadToolDashboard(tab);
    }
}

// ─── Tool Dashboards ─────────────────────────────────────
async function loadToolDashboard(tool) {
    if (tool === 'email') await loadEmailDashboard();
    else if (tool === 'telegram') await loadTelegramDashboard();
    else if (tool === 'web') await loadWebDashboard();
}

async function loadEmailDashboard() {
    const stats = await apiFetch('/api/tools/email/stats');
    if (stats) {
        setText('email-status', stats.configured ? '✅ Configured' : '❌ Not configured');
        setText('email-sent', stats.sent || 0);
        setText('email-failed', stats.failed || 0);
        setText('email-templates', stats.templates || '—');
    }
    const log = await apiFetch('/api/tools/email/log');
    const logEl = document.getElementById('email-log');
    if (logEl && log) {
        logEl.innerHTML = log.length ? log.slice(-20).map(e =>
            `<div class="log-entry"><span class="log-time">${formatTime(e.time)}</span> <span class="${e.ok ? 'log-ok' : 'log-err'}">${e.ok ? '✓' : '✗'}</span> → ${escapeHtml(e.to)} — ${escapeHtml(e.subject || '')}</div>`
        ).join('') : '<em>No emails sent yet</em>';
    }
}

async function loadTelegramDashboard() {
    const stats = await apiFetch('/api/tools/telegram/stats');
    if (stats) {
        setText('tg-status', stats.configured ? '✅ Configured' : '❌ Not configured');
        setText('tg-sent', stats.sent || 0);
        setText('tg-failed', stats.failed || 0);
        setText('tg-bot', stats.bot_name || '—');
    }
    const log = await apiFetch('/api/tools/telegram/log');
    const logEl = document.getElementById('tg-log');
    if (logEl && log) {
        logEl.innerHTML = log.length ? log.slice(-20).map(e =>
            `<div class="log-entry"><span class="log-time">${formatTime(e.time)}</span> <span class="${e.ok ? 'log-ok' : 'log-err'}">${e.ok ? '✓' : '✗'}</span> ${escapeHtml((e.text || '').substring(0, 60))}</div>`
        ).join('') : '<em>No messages sent yet</em>';
    }
}

async function loadWebDashboard() {
    const stats = await apiFetch('/api/tools/web/stats');
    if (stats) {
        setText('web-searches', stats.searches || 0);
        setText('web-fetched', stats.fetched || 0);
        setText('web-cached', stats.cached || 0);
        setText('web-results', stats.total_results || 0);
    }
    const log = await apiFetch('/api/tools/web/log');
    const logEl = document.getElementById('web-log');
    if (logEl && log) {
        logEl.innerHTML = log.length ? log.slice(-20).map(e =>
            `<div class="log-entry"><span class="log-time">${formatTime(e.time)}</span> <span class="log-info">${escapeHtml(e.type || 'fetch')}</span> ${escapeHtml((e.query || e.url || '').substring(0, 60))}</div>`
        ).join('') : '<em>No web activity yet</em>';
    }
}

// ─── Quick Actions (Tools) ───────────────────────────────
async function sendQuickEmail() {
    const to = document.getElementById('email-to')?.value?.trim();
    const subject = document.getElementById('email-subject')?.value?.trim();
    const body = document.getElementById('email-body')?.value?.trim();
    if (!to || !subject || !body) { showToast('Fill all email fields', 'error'); return; }
    const result = await apiPost('/api/tools/email/send', { to, subject, body });
    showToast(result?.ok ? 'Email sent!' : (result?.error || 'Send failed'), result?.ok ? 'success' : 'error');
    if (result?.ok) {
        document.getElementById('email-to').value = '';
        document.getElementById('email-subject').value = '';
        document.getElementById('email-body').value = '';
        loadEmailDashboard();
    }
}

async function sendQuickTelegram() {
    const text = document.getElementById('tg-text')?.value?.trim();
    if (!text) { showToast('Enter a message', 'error'); return; }
    const result = await apiPost('/api/tools/telegram/send', { text });
    showToast(result?.ok ? 'Message sent!' : (result?.error || 'Send failed'), result?.ok ? 'success' : 'error');
    if (result?.ok) {
        document.getElementById('tg-text').value = '';
        loadTelegramDashboard();
    }
}

async function doWebSearch() {
    const query = document.getElementById('web-query')?.value?.trim();
    if (!query) { showToast('Enter a search query', 'error'); return; }
    const panel = document.getElementById('web-results-panel');
    if (panel) { panel.style.display = ''; panel.innerHTML = '<em>Searching...</em>'; }
    const result = await apiPost('/api/tools/web/search', { query });
    if (panel && result?.results) {
        panel.innerHTML = result.results.map(r =>
            `<div class="log-entry"><span class="log-info">${escapeHtml(r.title || '')}</span><br><span class="log-time">${escapeHtml(r.url || '')}</span></div>`
        ).join('') || '<em>No results</em>';
    } else if (panel) {
        panel.innerHTML = '<em>Search completed</em>';
    }
    loadWebDashboard();
}

// ─── Settings Modal (Coffee Shop) ────────────────────────
async function openSettings() {
    document.getElementById('settings-modal').style.display = '';
    showToast('☕ Welcome to the Cafe!');
    await loadSettings();
}

function closeSettings() {
    document.getElementById('settings-modal').style.display = 'none';
}

function switchSettingsTab(tab) {
    document.querySelectorAll('.stab').forEach(el => {
        el.classList.toggle('active', el.textContent.toLowerCase().includes(tab));
    });
    document.querySelectorAll('.settings-panel').forEach(el => el.classList.remove('active'));
    const panel = document.getElementById(`stab-${tab}`);
    if (panel) panel.classList.add('active');
}

async function loadSettings() {
    const config = await apiFetch('/api/config');
    if (!config) return;
    settingsData = config;

    // General
    setText('s-company', config.company_name || '—');
    setText('s-product', config.product_name || '—');
    setText('s-github', config.github_url || '—');
    setText('s-discord', config.discord_url || '—');

    const f = config.features || {};
    setToggle('s-delegation', f.delegation);
    setToggle('s-cross-agent', f.cross_agent_context);
    setToggle('s-mem-cleanup', f.memory_cleanup);

    // LLM
    setText('s-llm-provider', config.llm_provider || '—');
    setText('s-llm-model', config.llm_model || '—');
    setToggle('s-llm-status', config.llm_configured);
    setText('s-max-tokens', config.max_tokens_per_call || '—');
    setText('s-retries', config.max_retries || '—');
    setText('s-rate-delay', (config.rate_limit_delay || '—') + 's');
    setText('s-mem-items', config.memory_context_items || '—');

    // Agents
    setText('s-tasks-cycle', config.tasks_per_cycle || '—');
    setText('s-task-timeout', (config.task_timeout || '—') + 's');
    setText('s-task-delay', (config.task_delay || '—') + 's');
    setText('s-cycle-delay', (config.cycle_delay || '—') + 's');
    setText('s-agent-timeout', (config.agent_cycle_timeout || '—') + 's');
    setText('s-mem-max', config.max_memory_entries || '—');

    // Agent powers
    const powersEl = document.getElementById('s-agent-powers');
    if (powersEl && config.agent_powers) {
        powersEl.innerHTML = Object.entries(config.agent_powers).map(([name, info]) =>
            `<div class="agent-power-item"><span class="power-name">${escapeHtml(name)}</span><span class="power-count">(${info.count} types)</span><div class="power-types">${escapeHtml(info.types)}</div></div>`
        ).join('');
    }

    // Tools
    const tools = config.tools || {};
    setText('s-smtp-host', tools.smtp_host || '—');
    setText('s-email-from', tools.email_from || '—');
    setToggle('s-email-report', tools.email_daily_report);
    setText('s-email-delay', (tools.email_bulk_delay || '—') + 's');
    setToggle('s-tg-configured', tools.telegram_configured);
    setToggle('s-tg-cycles', tools.telegram_notify_cycles);
    setToggle('s-tg-alerts', tools.telegram_notify_alerts);
    setToggle('s-tg-polling', tools.telegram_polling);
    setText('s-web-results', tools.web_search_results || '—');
    setText('s-web-cache', (tools.web_cache_ttl || '—') + 's');
    setText('s-web-timeout', (tools.web_request_timeout || '—') + 's');
    setText('s-web-chars', tools.web_max_page_chars || '—');

    // Schedule
    setText('s-work-hours', config.work_hours || '—');
    setText('s-report-hour', config.report_hour || '—');
    setText('s-timezone', config.timezone || '—');

    // DB stats
    if (config.db_stats) {
        const dbEl = document.getElementById('s-db-stats');
        if (dbEl) {
            dbEl.innerHTML = Object.entries(config.db_stats).map(([k, v]) =>
                `<div class="db-stat"><span class="stat-label">${escapeHtml(k)}</span><span class="stat-value">${v}</span></div>`
            ).join('');
        }
    }
}

// ─── Agent Selection ─────────────────────────────────────
function selectAgent(agentId) {
    document.querySelectorAll('.agent-sprite').forEach(el => el.classList.remove('selected'));
    document.querySelectorAll('.agent-detail').forEach(el => el.classList.remove('active'));

    const spriteEl = document.getElementById(`agent-${agentId}`);
    if (spriteEl) spriteEl.classList.add('selected');

    selectedAgent = agentId;

    const detailEl = document.getElementById(`detail-${agentId}`);
    if (detailEl) detailEl.classList.add('active');

    loadAgentTasks(agentId);
    loadAgentMemory(agentId);
}

// ─── API Calls ───────────────────────────────────────────
async function apiFetch(path) {
    try {
        const resp = await fetch(`${API}${path}`);
        return await resp.json();
    } catch (e) {
        console.error(`API error ${path}:`, e);
        return null;
    }
}

async function apiPost(path, body = {}) {
    try {
        const resp = await fetch(`${API}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        return await resp.json();
    } catch (e) {
        console.error(`API POST error ${path}:`, e);
        return null;
    }
}

async function loadAgentTasks(agentId) {
    const tasks = await apiFetch(`/api/agents/${encodeURIComponent(agentId)}/tasks`);
    const container = document.getElementById('task-list');
    if (!container || !tasks) return;

    container.innerHTML = tasks.slice(0, 15).map(t => `
        <li class="task-item">
            <span class="task-status ${t.status}"></span>
            <span>[${escapeHtml(t.task_type)}] ${escapeHtml(t.description?.substring(0, 60) || '')}</span>
        </li>
    `).join('');
}

async function loadAgentMemory(agentId) {
    const mem = await apiFetch(`/api/agents/${encodeURIComponent(agentId)}/memory`);
    const container = document.getElementById(`memory-${agentId}`);
    if (!container || !mem) return;

    let html = '';
    for (const [cat, entries] of Object.entries(mem)) {
        html += `<div style="color:var(--accent);margin-top:4px">[${escapeHtml(cat)}]</div>`;
        for (const [k, v] of Object.entries(entries)) {
            html += `<div style="font-size:6px;color:var(--text-dim);padding-left:8px">${escapeHtml(k)}: ${escapeHtml(v?.substring(0, 80) || '')}</div>`;
        }
    }
    container.innerHTML = html || '<em style="color:#666">No memories yet</em>';
}

async function loadMessages() {
    const msgs = await apiFetch('/api/messages?limit=30');
    const container = document.getElementById('msg-feed');
    if (!container || !msgs) return;

    container.innerHTML = msgs.map(m => `
        <div class="msg-item">
            <span class="msg-from">${escapeHtml(m.from_agent)}</span> →
            <span class="msg-to">${escapeHtml(m.to_agent)}</span>:
            ${escapeHtml(m.content?.substring(0, 80) || '')}
            <span class="msg-time">${formatTime(m.created_at)}</span>
        </div>
    `).join('');
}

// ─── Director Commands ───────────────────────────────────
async function sendDirectorMessage() {
    const input = document.getElementById('director-msg');
    const select = document.getElementById('director-to');
    if (!input || !input.value.trim()) return;

    const msg = input.value.trim();
    const to = select.value;
    await apiPost('/api/director/message', { to, message: msg });
    input.value = '';
    showToast(`Message sent to ${to.toUpperCase()}`);
    loadMessages();
}

async function generateReport() {
    const btn = event.target;
    btn.textContent = '⏳ SENDING...';
    btn.disabled = true;
    const result = await apiPost('/api/reports/generate');
    btn.textContent = '📊 REPORT';
    btn.disabled = false;
    showToast(result?.status === 'ok' ? 'Report generated!' : 'Report sent', 'success');
}

async function stopOffice() {
    await apiPost('/api/office/stop');
    showToast('Office stopped', 'error');
}

async function restartOffice() {
    await apiPost('/api/office/restart');
    showToast('Office restarting...', 'success');
}

// ─── Helpers ─────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

function formatTime(ts) {
    if (!ts) return '';
    try {
        const d = new Date(ts);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return ts;
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
}

function setToggle(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    if (val === true || val === 'true') {
        el.textContent = '✅ ON';
        el.className = 'setting-value on';
    } else if (val === false || val === 'false') {
        el.textContent = '❌ OFF';
        el.className = 'setting-value off';
    } else {
        el.textContent = '—';
        el.className = 'setting-value';
    }
}

// ─── Initialization ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    connectSSE();
    initParticles();
    updateClock();
    setInterval(updateClock, 10000);

    // Agent click handlers
    document.querySelectorAll('.agent-sprite').forEach(el => {
        el.addEventListener('click', () => {
            const id = el.id.replace('agent-', '');
            selectAgent(id);
        });
    });

    // Director input enter key
    const dirInput = document.getElementById('director-msg');
    if (dirInput) {
        dirInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendDirectorMessage();
        });
    }

    // Settings modal ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSettings();
    });

    // Refresh messages periodically
    setInterval(loadMessages, 5000);

    // Refresh selected agent tasks
    setInterval(() => {
        if (selectedAgent) loadAgentTasks(selectedAgent);
    }, 8000);

    // Refresh active tool dashboard
    setInterval(() => {
        if (currentTab !== 'office') loadToolDashboard(currentTab);
    }, 10000);

    // Initial loads
    loadMessages();
    selectAgent('ceo');
});
