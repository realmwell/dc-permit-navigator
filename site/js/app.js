/**
 * DC Permit Navigator - Frontend Controller
 *
 * Handles:
 * - Tab navigation (chat, directory, about)
 * - Chat interface (send questions, display answers)
 * - Permit directory (search, filter, expand/collapse cards)
 */

(function () {
    'use strict';

    // --- Configuration ---
    // Set this to your Lambda Function URL after deployment
    const API_URL = window.PERMIT_NAV_API_URL || '';

    // --- Tab Navigation ---
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.dataset.tab;

            navLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            link.classList.add('active');
            document.getElementById(tab).classList.add('active');

            history.replaceState(null, '', `#${tab}`);
        });
    });

    // Handle initial hash
    const initialTab = window.location.hash.replace('#', '') || 'chat';
    const initialLink = document.querySelector(`[data-tab="${initialTab}"]`);
    if (initialLink) {
        initialLink.click();
    }

    // --- Chat ---
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('send-btn');
    const sendText = sendBtn.querySelector('.send-text');
    const sendLoading = sendBtn.querySelector('.send-loading');

    let isLoading = false;

    function addMessage(content, isUser = false) {
        const msg = document.createElement('div');
        msg.className = `message ${isUser ? 'user' : 'bot'}`;

        const bubble = document.createElement('div');
        bubble.className = 'message-content';

        if (isUser) {
            bubble.textContent = content;
        } else {
            bubble.innerHTML = content;
        }

        msg.appendChild(bubble);
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return msg;
    }

    function addTypingIndicator() {
        const msg = document.createElement('div');
        msg.className = 'message bot';
        msg.id = 'typing-indicator';

        msg.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;

        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    function setLoading(loading) {
        isLoading = loading;
        sendBtn.disabled = loading;
        chatInput.disabled = loading;
        sendText.style.display = loading ? 'none' : '';
        sendLoading.style.display = loading ? '' : 'none';
    }

    /**
     * Convert basic markdown to HTML for bot responses.
     * Handles: bold, italic, links, headers, lists, code, paragraphs.
     */
    function markdownToHtml(text) {
        let html = text;

        // Code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Headers
        html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
        // Bold
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        // Unordered lists
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
        // Numbered lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        // Paragraphs (double newlines)
        html = html.replace(/\n\n/g, '</p><p>');
        // Single newlines within paragraphs
        html = html.replace(/\n/g, '<br>');
        // Wrap in paragraph
        html = '<p>' + html + '</p>';
        // Clean up empty paragraphs
        html = html.replace(/<p>\s*<\/p>/g, '');
        // Clean up paragraphs wrapping block elements
        html = html.replace(/<p>(<h[34]>)/g, '$1');
        html = html.replace(/(<\/h[34]>)<\/p>/g, '$1');
        html = html.replace(/<p>(<ul>)/g, '$1');
        html = html.replace(/(<\/ul>)<\/p>/g, '$1');
        html = html.replace(/<p>(<pre>)/g, '$1');
        html = html.replace(/(<\/pre>)<\/p>/g, '$1');

        return html;
    }

    async function sendQuestion(question) {
        addMessage(question, true);
        setLoading(true);
        addTypingIndicator();

        // If no API URL configured, use local directory fallback
        if (!API_URL) {
            removeTypingIndicator();
            setLoading(false);

            const results = localSearch(question);
            if (results.length > 0) {
                let html = '<p>Based on your question, here are the most relevant permits I found:</p>';
                results.forEach(p => {
                    const agency = getAgencyName(p.agency);
                    html += `<p><strong>${p.name}</strong> (${agency})<br>`;
                    html += `${p.description}`;
                    if (p.fees) html += `<br><em>Fees:</em> ${p.fees}`;
                    if (p.apply_url) html += `<br><a href="${p.apply_url}" target="_blank">Apply here</a>`;
                    html += '</p>';
                });
                html += '<p><em>Note: The AI-powered answer engine is not yet connected. Switch to the <a href="#directory">Permit Directory</a> tab to browse all 103 permits.</em></p>';
                addMessage(html);
            } else {
                addMessage('<p>I couldn\'t find a close match. Try browsing the <a href="#directory">Permit Directory</a> tab, or rephrase your question.</p>');
            }
            return;
        }

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            });

            removeTypingIndicator();

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                if (response.status === 429) {
                    addMessage('<p>' + (err.answer || 'Daily query limit reached. Please try again tomorrow or browse the permit directory.') + '</p>');
                } else {
                    addMessage('<p>Sorry, something went wrong. Please try again or browse the <a href="#directory">Permit Directory</a>.</p>');
                }
                setLoading(false);
                return;
            }

            const data = await response.json();
            let html = markdownToHtml(data.answer);

            // Add sources
            if (data.sources && data.sources.length > 0) {
                html += '<div class="sources"><strong>Sources:</strong>';
                data.sources.forEach(s => {
                    html += `${s.permit_name} (${s.agency})<br>`;
                });
                html += '</div>';
            }

            addMessage(html);
        } catch (err) {
            removeTypingIndicator();
            addMessage('<p>Sorry, I couldn\'t reach the server. Please try again or browse the <a href="#directory">Permit Directory</a>.</p>');
            console.error('Chat error:', err);
        }

        setLoading(false);
    }

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question || isLoading) return;
        chatInput.value = '';
        sendQuestion(question);
    });

    // --- Local Search Fallback (when API isn't connected) ---
    function localSearch(query) {
        if (!window.PERMITS_DATA) return [];
        const q = query.toLowerCase();
        const words = q.split(/\s+/).filter(w => w.length > 2);

        const scored = window.PERMITS_DATA.permits.map(p => {
            const text = `${p.name} ${p.description} ${p.category} ${p.requirements || ''} ${p.notes || ''}`.toLowerCase();
            let score = 0;
            words.forEach(w => {
                if (text.includes(w)) score++;
                // Bonus for name match
                if (p.name.toLowerCase().includes(w)) score += 2;
                // Bonus for category match
                if (p.category.toLowerCase().includes(w)) score += 1;
            });
            return { ...p, score };
        });

        return scored
            .filter(p => p.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 5);
    }

    function getAgencyName(agencyId) {
        if (!window.PERMITS_DATA) return agencyId;
        const agency = window.PERMITS_DATA.agencies.find(a => a.id === agencyId);
        return agency ? agency.name : agencyId;
    }

    // --- Permit Directory ---
    function initDirectory() {
        if (!window.PERMITS_DATA) {
            document.getElementById('permit-list').innerHTML = '<p>Error loading permit data.</p>';
            return;
        }

        const data = window.PERMITS_DATA;
        const permits = data.permits;
        const agencies = {};
        data.agencies.forEach(a => { agencies[a.id] = a; });

        // Update count
        document.getElementById('permit-count').textContent = permits.length;

        // Populate category filter
        const categories = [...new Set(permits.map(p => p.category))].sort();
        const categorySelect = document.getElementById('category-filter');
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            categorySelect.appendChild(opt);
        });

        // Populate agency filter
        const agencyIds = [...new Set(permits.map(p => p.agency))].sort();
        const agencySelect = document.getElementById('agency-filter');
        agencyIds.forEach(id => {
            const agency = agencies[id];
            if (agency) {
                const opt = document.createElement('option');
                opt.value = id;
                opt.textContent = agency.name;
                agencySelect.appendChild(opt);
            }
        });

        function renderPermits(filtered) {
            const container = document.getElementById('permit-list');
            const resultCount = document.getElementById('result-count');

            resultCount.textContent = `Showing ${filtered.length} of ${permits.length} permits`;

            if (filtered.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:var(--text-light);padding:2rem;">No permits match your search.</p>';
                return;
            }

            container.innerHTML = filtered.map(p => {
                const agency = agencies[p.agency] || {};
                const agencyName = agency.name || p.agency;
                const agencyUrl = agency.url || '#';
                const formerly = agency.formerly ? ` (formerly ${agency.formerly})` : '';

                return `
                    <div class="permit-card" data-id="${p.id}">
                        <div class="permit-card-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <div class="permit-card-title">
                                <h3>${p.name}</h3>
                                <div class="permit-card-meta">
                                    <span class="agency">${agencyName}</span>
                                    <span class="category">${p.category}</span>
                                </div>
                            </div>
                            <span class="permit-card-toggle">&#9662;</span>
                        </div>
                        <div class="permit-card-details">
                            <div class="detail-row">
                                <span class="detail-label">Description</span>
                                <span class="detail-value">${p.description}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Agency</span>
                                <span class="detail-value"><a href="${agencyUrl}" target="_blank">${agencyName}</a>${formerly}</span>
                            </div>
                            ${p.requirements ? `
                            <div class="detail-row">
                                <span class="detail-label">Requirements</span>
                                <span class="detail-value">${p.requirements}</span>
                            </div>` : ''}
                            ${p.fees ? `
                            <div class="detail-row">
                                <span class="detail-label">Fees</span>
                                <span class="detail-value">${p.fees}</span>
                            </div>` : ''}
                            ${p.processing_time ? `
                            <div class="detail-row">
                                <span class="detail-label">Processing Time</span>
                                <span class="detail-value">${p.processing_time}</span>
                            </div>` : ''}
                            ${p.how_to_apply ? `
                            <div class="detail-row">
                                <span class="detail-label">How to Apply</span>
                                <span class="detail-value">${p.how_to_apply}</span>
                            </div>` : ''}
                            ${p.notes ? `
                            <div class="detail-row">
                                <span class="detail-label">Notes</span>
                                <span class="detail-value">${p.notes}</span>
                            </div>` : ''}
                            ${p.apply_url ? `
                            <a href="${p.apply_url}" target="_blank" class="apply-btn">Apply / Learn More &rarr;</a>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        }

        function filterPermits() {
            const search = document.getElementById('search-input').value.toLowerCase().trim();
            const category = document.getElementById('category-filter').value;
            const agency = document.getElementById('agency-filter').value;

            let filtered = permits;

            if (category !== 'all') {
                filtered = filtered.filter(p => p.category === category);
            }

            if (agency !== 'all') {
                filtered = filtered.filter(p => p.agency === agency);
            }

            if (search) {
                const words = search.split(/\s+/);
                filtered = filtered.filter(p => {
                    const text = `${p.name} ${p.description} ${p.category} ${p.requirements || ''} ${p.fees || ''} ${p.notes || ''}`.toLowerCase();
                    return words.every(w => text.includes(w));
                });
            }

            renderPermits(filtered);
        }

        // Event listeners for filters
        document.getElementById('search-input').addEventListener('input', filterPermits);
        document.getElementById('category-filter').addEventListener('change', filterPermits);
        document.getElementById('agency-filter').addEventListener('change', filterPermits);

        // Initial render
        renderPermits(permits);
    }

    // Init directory when data is available
    if (window.PERMITS_DATA) {
        initDirectory();
    } else {
        // Wait for data script to load
        window.addEventListener('load', initDirectory);
    }
})();
