/**
 * AI Office — Main Application JS v2.0
 * Handles SSE, API calls, agent interaction, live updates, particles & animations.
 */

const API = '';
let selectedAgent = null;
let officeState = {};

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

    // Initial batch
    for (let i = 0; i < 12; i++) {
        setTimeout(spawnParticle, Math.random() * 5000);
    }
    // Continuous
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
            // Detect cycle change for toast
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
    // Update top bar
    const pill = document.getElementById('status-pill');
    if (state.running) {
        pill.textContent = `CYCLE ${state.cycle || 0}`;
        pill.className = 'status-pill';
    } else {
        pill.textContent = 'STOPPED';
        pill.className = 'status-pill stopped';
    }

    // Update agents
    if (state.agents) {
        for (const [id, data] of Object.entries(state.agents)) {
            updateAgentSprite(id, data);
        }
    }
}

function updateAgentSprite(id, data) {
    const el = document.getElementById(`agent-${id}`);
    if (!el) return;

    // Update status dot
    const dot = el.querySelector('.agent-status-dot');
    if (dot) {
        dot.className = `agent-status-dot ${data.status || 'idle'}`;
    }

    // Toggle working class for arm animation
    if (data.status === 'working') {
        el.classList.add('working');
    } else {
        el.classList.remove('working');
    }

    // Update speech bubble
    const bubble = el.querySelector('.speech-bubble');
    if (bubble && data.current_task) {
        bubble.textContent = data.current_task.substring(0, 40);
        el.classList.add('speaking');
    } else if (bubble) {
        bubble.textContent = data.status || 'idle';
        el.classList.remove('speaking');
    }
}

// ─── Agent Selection ─────────────────────────────────────
function selectAgent(agentId) {
    // Remove previous selection
    document.querySelectorAll('.agent-sprite').forEach(el => el.classList.remove('selected'));
    document.querySelectorAll('.agent-detail').forEach(el => el.classList.remove('active'));

    // Select new
    const spriteEl = document.getElementById(`agent-${agentId}`);
    if (spriteEl) spriteEl.classList.add('selected');

    selectedAgent = agentId;

    // Show detail panel
    const detailEl = document.getElementById(`detail-${agentId}`);
    if (detailEl) detailEl.classList.add('active');

    // Fetch data
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
    const container = document.getElementById('memory-content');
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
    div.textContent = str;
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

// ─── Initialization ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    connectSSE();
    initParticles();
    updateClock();
    setInterval(updateClock, 10000);

    // Attach click handlers to agents
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

    // Refresh messages periodically
    setInterval(loadMessages, 5000);

    // Refresh selected agent tasks
    setInterval(() => {
        if (selectedAgent) loadAgentTasks(selectedAgent);
    }, 8000);

    // Initial loads
    loadMessages();
    selectAgent('ceo');
});
