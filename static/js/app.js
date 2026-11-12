
const chat = document.getElementById('chat');
const form = document.getElementById('chatForm');
const question = document.getElementById('question');
const trace = document.getElementById('trace');
const sourceUsed = document.getElementById('sourceUsed');

// Safely escape HTML
function escapeHtml(value = '') {
    return String(value).replace(/[&<>'"]/g, char => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[char]));
}

function formatText(value = '') {
    return escapeHtml(value).replace(/\n/g, '<br>');
}

// Safely parse API responses
async function parseResponse(response) {
    const text = await response.text();

    if (!text) {
        throw new Error(
            `Empty server response. HTTP ${response.status}`
        );
    }

    let data;

    try {
        data = JSON.parse(text);
    } catch (error) {
        console.error('Invalid API response:', {
            status: response.status,
            url: response.url,
            contentType: response.headers.get('content-type'),
            body: text.substring(0, 1000)
        });

        throw new Error(
            `Server returned invalid JSON. HTTP ${response.status}. Check browser console.`
        );
    }

    if (!response.ok) {
        throw new Error(
            data.detail || data.error || `HTTP ${response.status}`
        );
    }

    return data;
}

// Add chat message
function addMessage(role, text, source = '', citations = []) {
    const wrap = document.createElement('div');
    wrap.className = `message ${role}`;

    const citeHtml = citations.length
        ? `<div class="citations">
            <strong>Sources</strong><br>
            ${citations.map(c =>
                c.url
                    ? `<a href="${escapeHtml(c.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(c.title || 'Source')}</a>`
                    : escapeHtml(c.title || 'Source')
            ).join('<br>')}
           </div>`
        : '';

    wrap.innerHTML = `
        <div class="avatar">AI</div>
        <div class="bubble">
            ${formatText(text)}
            ${source ? `<div class="answer-source">Source: ${escapeHtml(source)}</div>` : ''}
            ${citeHtml}
        </div>
    `;

    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
}

// Render workflow trace
function renderTrace(items = []) {
    trace.innerHTML = items.length
        ? items.map(item =>
            `<div class="trace-item">${escapeHtml(item)}</div>`
          ).join('')
        : '<div class="empty">No trace.</div>';
}

// Chat API
async function askAgent(q) {
    addMessage('user', q);

    question.value = '';
    renderTrace(['Running LangGraph workflow...']);
    sourceUsed.textContent = 'Running';

    const btn = form.querySelector('button');
    btn.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                question: q
            })
        });

        const data = await parseResponse(response);

        addMessage(
            'assistant',
            data.answer || 'No answer received.',
            data.source_used || '',
            data.citations || []
        );

        renderTrace(data.trace || []);
        sourceUsed.textContent = data.source_used || 'Unknown';

    } catch (error) {
        console.error('Chat API error:', error);

        addMessage(
            'assistant',
            `Error: ${error.message}`
        );

        renderTrace(['Request failed. Check Render runtime logs.']);
        sourceUsed.textContent = 'Error';

    } finally {
        btn.disabled = false;
    }
}

// Chat form submission
form.addEventListener('submit', event => {
    event.preventDefault();

    const q = question.value.trim();

    if (q) {
        askAgent(q);
    }
});

// Example questions
document.querySelectorAll('.example').forEach(button => {
    button.addEventListener('click', () => {
        askAgent(button.textContent.trim());
    });
});

// Document upload modal
const modal = document.getElementById('uploadModal');

document.getElementById('openUpload').onclick = () => {
    modal.classList.remove('hidden');
};

document.getElementById('closeUpload').onclick = () => {
    modal.classList.add('hidden');
};

// Document upload API
document.getElementById('uploadBtn').onclick = async () => {
    const file = document.getElementById('fileInput').files[0];
    const key = document.getElementById('adminKey').value;
    const status = document.getElementById('uploadStatus');

    if (!file) {
        status.textContent = 'Choose a file first.';
        return;
    }

    status.textContent = 'Indexing document...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/ingest', {
            method: 'POST',
            headers: {
                'X-Admin-Key': key,
                'Accept': 'application/json'
            },
            body: formData
        });

        const data = await parseResponse(response);

        status.textContent =
            `Indexed ${data.file}: ${data.chunks} chunks.`;

    } catch (error) {
        console.error('Upload API error:', error);
        status.textContent = `Error: ${error.message}`;
    }
};
