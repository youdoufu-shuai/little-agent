document.addEventListener('DOMContentLoaded', () => {
    // Random Theme Initialization
    const initLightMode = Math.random() > 0.5;
    
    // Logo Constants
    // Light Mode: Use refined cutout (internal white preserved)
    const LOGO_LIGHT = 'static/images/logo_light_mode.png';
    // Dark Mode: Use legacy cutout (all white removed)
    const LOGO_DARK = 'static/images/logo_dark_mode.png';
    
    // Apply Theme Immediately
    const splashScreen = document.getElementById('splash-screen');
    const splashLogo = document.querySelector('.splash-logo');
    
    if (initLightMode) {
        document.documentElement.setAttribute('data-theme', 'light');
        if (splashScreen) splashScreen.classList.add('light-mode');
        if (splashLogo) splashLogo.src = LOGO_LIGHT;
    } else {
        // Default is dark
        // Explicitly set dark logo for splash
        if (splashLogo) splashLogo.src = LOGO_DARK;
    }

    // Splash Screen Logic
    if (splashScreen) {
        // Initialize sequence
        setTimeout(() => {
            // After 2.5s (loading bar completion), fade out
            splashScreen.style.opacity = '0';
            splashScreen.style.visibility = 'hidden';
            
            // Allow interaction after fade
            setTimeout(() => {
                splashScreen.style.display = 'none';
            }, 800);
        }, 2500);
    }

    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const themeBtn = document.getElementById('theme-btn');
    const themeIcon = themeBtn.querySelector('i');
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');

    let currentImage = null;
    let currentSessionId = null;

    // Load History on Start
    loadHistory();

    // Theme Switching Logic
    let isLightMode = initLightMode;
    
    // Set initial icon state
    if (isLightMode) {
        themeIcon.className = 'fas fa-moon';
    } else {
        themeIcon.className = 'fas fa-sun';
    }
    
    // Initial Logo Update for sidebar/avatars (if any exist on load)
    updateLogos(isLightMode);
    
    function updateLogos(lightMode) {
        const logoSrc = lightMode ? LOGO_LIGHT : LOGO_DARK;
        
        // Update Sidebar Logo
        const sidebarLogo = document.getElementById('sidebar-logo');
        if (sidebarLogo) sidebarLogo.src = logoSrc;
        
        // Update All Agent Avatars
        document.querySelectorAll('.agent-avatar').forEach(img => {
            img.src = logoSrc;
        });
    }

    themeBtn.addEventListener('click', () => {
        isLightMode = !isLightMode;
        if (isLightMode) {
            document.documentElement.setAttribute('data-theme', 'light');
            themeIcon.className = 'fas fa-moon';
        } else {
            document.documentElement.removeAttribute('data-theme');
            themeIcon.className = 'fas fa-sun';
        }
        updateLogos(isLightMode);
    });

    // New Chat Button
    newChatBtn.addEventListener('click', () => {
        currentSessionId = null;
        chatContainer.innerHTML = '<div class="message agent">系统初始化完成。双脑架构已上线。今天我能为您做些什么？</div>';
        // Clear active class from history
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    });

    // DB Config Modal Logic (Legacy - Removed)
    // const dbModal = document.getElementById('db-modal');

    // Personas Modal Logic
    const personasBtn = document.getElementById('personas-btn');
    const personasModal = document.getElementById('personas-modal');
    const closePersonasModal = personasModal.querySelector('.close-modal');
    const addPersonaBtn = document.getElementById('add-persona-btn');
    const personaForm = document.getElementById('persona-form');
    const savePersonaBtn = document.getElementById('save-persona-btn');
    const cancelPersonaBtn = document.getElementById('cancel-persona-btn');
    const personasList = document.getElementById('personas-list');
    
    // DB Viewer Modal Logic
    const dbViewerBtn = document.getElementById('db-viewer-btn');
    const dbViewerModal = document.getElementById('db-viewer-modal');
    const closeDbViewerModal = dbViewerModal.querySelector('.close-modal');
    const tablesList = document.getElementById('tables-list');
    const tableDataContainer = document.getElementById('table-data-container');
    const sqlQueryInput = document.getElementById('sql-query-input');
    const runQueryBtn = document.getElementById('run-query-btn');
    const currentTableNameDisplay = document.getElementById('current-table-name');
    
    // New DB Config Integration
    const toggleDbConfigBtn = document.getElementById('toggle-db-config');
    const dbConfigPanel = document.getElementById('db-config-panel');
    const saveConnectDbBtn = document.getElementById('save-connect-db-btn');
    const refreshDbsBtn = document.getElementById('refresh-dbs-btn');
    
    // Toggle Config Panel
    toggleDbConfigBtn.addEventListener('click', () => {
        if (dbConfigPanel.style.display === 'none') {
            dbConfigPanel.style.display = 'block';
        } else {
            dbConfigPanel.style.display = 'none';
        }
    });

    // Save & Connect
    saveConnectDbBtn.addEventListener('click', () => {
        const config = {
            host: document.getElementById('db-host').value,
            port: parseInt(document.getElementById('db-port').value) || 3306,
            user: document.getElementById('db-user').value,
            password: document.getElementById('db-password').value,
            database: null // We don't save a specific DB as default anymore, user selects it
        };
        localStorage.setItem('db_config', JSON.stringify(config));
        
        // Hide panel
        dbConfigPanel.style.display = 'none';
        
        // Try to load databases
        loadDatabases();
    });

    // Refresh DBs
    refreshDbsBtn.addEventListener('click', loadDatabases);

    // --- Personas Implementation ---
    personasBtn.addEventListener('click', async () => {
        personasModal.style.display = 'block';
        await loadPersonas();
    });

    closePersonasModal.addEventListener('click', () => {
        personasModal.style.display = 'none';
        personaForm.style.display = 'none';
    });

    addPersonaBtn.addEventListener('click', () => {
        personaForm.style.display = 'block';
        document.getElementById('persona-name').value = '';
        document.getElementById('persona-desc').value = '';
        document.getElementById('persona-prompt').value = '';
        personaForm.scrollIntoView({ behavior: 'smooth' });
    });

    cancelPersonaBtn.addEventListener('click', () => {
        personaForm.style.display = 'none';
    });

    savePersonaBtn.addEventListener('click', async () => {
        const name = document.getElementById('persona-name').value.trim();
        const desc = document.getElementById('persona-desc').value.trim();
        const prompt = document.getElementById('persona-prompt').value.trim();

        if (!name || !prompt) {
            alert('名称和提示词不能为空');
            return;
        }

        try {
            const res = await fetch('/api/personas', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description: desc, system_prompt: prompt })
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to save');
            }

            personaForm.style.display = 'none';
            loadPersonas();
        } catch (e) {
            alert('保存失败: ' + e.message);
        }
    });

    async function loadPersonas() {
        try {
            const res = await fetch('/api/personas');
            const personas = await res.json();
            
            personasList.innerHTML = '';
            personas.forEach(p => {
                const div = document.createElement('div');
                div.style.padding = '10px';
                div.style.marginBottom = '10px';
                div.style.border = '1px solid var(--border-color)';
                div.style.borderRadius = '5px';
                div.style.background = p.is_active ? 'rgba(74, 158, 255, 0.1)' : 'var(--bg-secondary)';
                div.style.display = 'flex';
                div.style.justifyContent = 'space-between';
                div.style.alignItems = 'center';

                div.innerHTML = `
                    <div>
                        <div style="font-weight: bold; ${p.is_active ? 'color: var(--accent-color);' : ''}">
                            ${p.name} ${p.is_active ? '<span style="font-size:0.8rem; border:1px solid var(--accent-color); padding:1px 4px; border-radius:4px; margin-left:5px;">当前</span>' : ''}
                        </div>
                        <div style="font-size: 0.85rem; color: #888; margin-top: 3px;">${p.description}</div>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        ${!p.is_active ? `<button class="action-btn activate-btn" style="font-size: 0.8rem;">启用</button>` : ''}
                        ${p.id !== 'default' ? `<button class="delete-btn" style="color: #ff4a4a;"><i class="fas fa-trash"></i></button>` : ''}
                    </div>
                `;

                // Bind events
                if (!p.is_active) {
                    div.querySelector('.activate-btn').addEventListener('click', async () => {
                        await fetch(`/api/personas/${p.id}/activate`, { method: 'PUT' });
                        loadPersonas();
                        // Update UI hint if needed, or just let user close modal
                        alert(`已切换到人设：${p.name}`);
                    });
                }
                
                if (p.id !== 'default') {
                    div.querySelector('.delete-btn').addEventListener('click', async () => {
                        if (confirm('确定要删除这个配置吗？')) {
                            await fetch(`/api/personas/${p.id}`, { method: 'DELETE' });
                            loadPersonas();
                        }
                    });
                }

                personasList.appendChild(div);
            });
        } catch (e) {
            personasList.innerHTML = '<div style="color:red">加载失败</div>';
        }
    }

    // --- DB Viewer Implementation ---
    const dbSelect = document.getElementById('db-select');
    let currentDatabase = null;

    dbViewerBtn.addEventListener('click', () => {
        dbViewerModal.style.display = 'block';
        loadDatabases();
    });

    closeDbViewerModal.addEventListener('click', () => {
        dbViewerModal.style.display = 'none';
    });
    
    dbSelect.addEventListener('change', (e) => {
        currentDatabase = e.target.value;
        if (currentDatabase) {
            loadTables(currentDatabase);
        } else {
            tablesList.innerHTML = '<div style="padding:10px; color:#888; font-size:0.8rem;">请选择数据库</div>';
        }
    });

    function getDbConfig() {
        const saved = localStorage.getItem('db_config');
        if (!saved) return null;
        return JSON.parse(saved);
    }

    async function loadDatabases() {
        const config = getDbConfig();
        if (!config) {
            // Show config panel if no config
            dbConfigPanel.style.display = 'block';
            dbSelect.innerHTML = '<option value="">请先配置连接</option>';
            return;
        }

        dbSelect.innerHTML = '<option>加载中...</option>';
        tablesList.innerHTML = '';
        
        try {
            const res = await fetch('/api/db/databases', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail);
            }
            
            const databases = await res.json();
            
            dbSelect.innerHTML = '<option value="">-- 选择数据库 --</option>';
            databases.forEach(row => {
                const dbName = Object.values(row)[0];
                const option = document.createElement('option');
                option.value = dbName;
                option.textContent = dbName;
                if (config.database && dbName === config.database) {
                    option.selected = true;
                    currentDatabase = dbName;
                }
                dbSelect.appendChild(option);
            });
            
            if (currentDatabase) {
                loadTables(currentDatabase);
            }

        } catch (e) {
            dbSelect.innerHTML = '<option>加载失败</option>';
            alert('无法加载数据库列表: ' + e.message + '\n请检查配置是否正确。');
            dbConfigPanel.style.display = 'block'; // Show config on error
        }
    }

    async function loadTables(dbName) {
        const config = getDbConfig();
        // Override database name
        config.database = dbName;
        
        tablesList.innerHTML = '<div style="padding:10px; color:#888;">加载中...</div>';
        
        try {
            const res = await fetch('/api/db/tables', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail);
            }
            
            const tables = await res.json();
            
            tablesList.innerHTML = '';
            if (!tables || tables.length === 0) {
                tablesList.innerHTML = '<div style="padding:10px;">无数据表</div>';
                return;
            }

            tables.forEach(row => {
                const name = Object.values(row)[0];
                
                const item = document.createElement('div');
                item.textContent = name;
                item.style.padding = '8px 10px';
                item.style.cursor = 'pointer';
                item.style.borderBottom = '1px solid var(--border-color)';
                item.className = 'table-item';
                
                item.addEventListener('mouseover', () => item.style.background = 'rgba(255,255,255,0.05)');
                item.addEventListener('mouseout', () => item.style.background = 'transparent');
                
                item.addEventListener('click', () => {
                    loadTableData(name);
                });
                
                tablesList.appendChild(item);
            });

        } catch (e) {
            tablesList.innerHTML = `<div style="padding:10px; color:red;">错误: ${e.message}</div>`;
        }
    }

    async function loadTableData(tableName) {
        if (!currentDatabase) return;
        currentTableNameDisplay.textContent = `表: ${tableName} (${currentDatabase})`;
        const config = getDbConfig();
        config.database = currentDatabase;
        
        const query = `SELECT * FROM ${tableName} LIMIT 50`;
        executeDbQuery(config, query);
    }

    runQueryBtn.addEventListener('click', () => {
        const config = getDbConfig();
        if (currentDatabase) config.database = currentDatabase;
        
        const query = sqlQueryInput.value.trim();
        if (!query) return;
        executeDbQuery(config, query);
    });

    async function executeDbQuery(config, query) {
        if (!config) return;
        tableDataContainer.innerHTML = '<div style="padding:20px;">查询中...</div>';
        
        try {
            const res = await fetch('/api/db/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config, query })
            });
            
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail);
            }
            
            const data = await res.json();
            renderTableData(data);
        } catch (e) {
            tableDataContainer.innerHTML = `<div style="padding:20px; color:red;">查询错误: ${e.message}</div>`;
        }
    }

    function renderTableData(data) {
        if (!data || data.length === 0) {
            tableDataContainer.innerHTML = '<div style="padding:20px;">无结果</div>';
            return;
        }

        // Create HTML Table
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.style.fontSize = '0.85rem';

        // Headers
        const headers = Object.keys(data[0]);
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headers.forEach(h => {
            const th = document.createElement('th');
            th.textContent = h;
            th.style.textAlign = 'left';
            th.style.padding = '8px';
            th.style.borderBottom = '1px solid #666';
            th.style.background = 'rgba(0,0,0,0.3)';
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        data.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(h => {
                const td = document.createElement('td');
                td.textContent = row[h];
                td.style.padding = '8px';
                td.style.borderBottom = '1px solid #444';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        tableDataContainer.innerHTML = '';
        tableDataContainer.appendChild(table);
    }
    
    // Close modals on outside click
    window.addEventListener('click', (e) => {
        // if (e.target === dbModal) dbModal.style.display = 'none';
        if (e.target === personasModal) personasModal.style.display = 'none';
        if (e.target === dbViewerModal) dbViewerModal.style.display = 'none';
    });

    // Load saved config
    const savedDbConfig = localStorage.getItem('db_config');
    if (savedDbConfig) {
        const config = JSON.parse(savedDbConfig);
        document.getElementById('db-host').value = config.host || 'localhost';
        document.getElementById('db-port').value = config.port || 3306;
        document.getElementById('db-user').value = config.user || 'root';
        document.getElementById('db-password').value = config.password || '';
        // document.getElementById('db-name').value = config.database || '';
    }

    // Old DB Config listeners removed

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = '24px';
    });

    // Handle Enter key
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // Handle Image Upload
    imageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            currentImage = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });

    async function loadHistory() {
        try {
            const res = await fetch('/api/sessions');
            const sessions = await res.json();
            historyList.innerHTML = '';
            
            sessions.forEach(session => {
                const li = document.createElement('li');
                li.className = 'history-item';
                li.dataset.id = session.id;
                if (session.id === currentSessionId) li.classList.add('active');
                
                li.innerHTML = `
                    <span><i class="fas fa-comment-alt" style="margin-right:8px; opacity:0.7;"></i>${session.title}</span>
                    <button class="delete-btn" title="删除对话"><i class="fas fa-trash"></i></button>
                `;
                
                // Click to load
                li.addEventListener('click', (e) => {
                    if (e.target.closest('.delete-btn')) return; // Ignore delete click
                    loadSession(session.id);
                });

                // Delete button
                const delBtn = li.querySelector('.delete-btn');
                delBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if(confirm('确定要删除这个对话吗？')) {
                        await fetch(`/api/sessions/${session.id}`, { method: 'DELETE' });
                        if (currentSessionId === session.id) {
                            newChatBtn.click();
                        }
                        loadHistory();
                    }
                });

                historyList.appendChild(li);
            });
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    async function loadSession(sessionId) {
        currentSessionId = sessionId;
        
        // Update Active State
        document.querySelectorAll('.history-item').forEach(el => {
            if (el.dataset.id === sessionId) el.classList.add('active');
            else el.classList.remove('active');
        });

        chatContainer.innerHTML = ''; // Clear current view
        const loadingId = appendLoading();

        try {
            const res = await fetch(`/api/sessions/${sessionId}`);
            const session = await res.json();
            
            removeLoading(loadingId);
            
            // Replay messages
            if (session.messages && session.messages.length > 0) {
                session.messages.forEach(msg => {
                   // Filter: Show User messages, and Agent messages that are NOT tool calls (final responses)
                   // Hide 'tool' role and 'assistant' messages that initiate tools
                   if (msg.role === 'user') {
                       appendMessage('user', msg.content);
                   } else if (msg.role === 'assistant') {
                       // Only show if it does NOT have tool_calls (or tool_calls is empty)
                       if (!msg.tool_calls || msg.tool_calls.length === 0) {
                           appendMessage('agent', msg.content);
                       }
                   }
                });
            } else {
                 chatContainer.innerHTML = '<div class="message agent">暂无消息。</div>';
            }
            scrollToBottom();
        } catch (error) {
            removeLoading(loadingId);
            appendMessage('agent', '无法加载历史记录。');
        }
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text && !currentImage) return;

        // Clear input
        userInput.value = '';
        userInput.style.height = '24px';
        
        // Add User Message locally
        appendMessage('user', text, currentImage ? imagePreview.src : null);
        
        // Hide preview
        imagePreview.style.display = 'none';
        
        const loadingId = appendLoading();
        
        // Prepare payload
        const formData = new FormData();
        formData.append('text', text);
        if (currentSessionId) {
            formData.append('session_id', currentSessionId);
        }
        
        // Get DB Config
        const dbConfig = localStorage.getItem('db_config');
        if (dbConfig) {
            formData.append('db_config', dbConfig);
        }
        
        if (currentImage) {
            formData.append('file', currentImage);
        }

        const endpoint = currentImage ? '/api/vision' : '/api/chat';
        let options = {};

        if (currentImage) {
            options = {
                method: 'POST',
                body: formData
            };
        } else {
            // For JSON endpoint
            const payload = { text: text };
            if (currentSessionId) payload.session_id = currentSessionId;
            if (dbConfig) payload.db_config = JSON.parse(dbConfig);
            
            options = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            };
        }

        currentImage = null;
        imageUpload.value = ''; // Reset file input

        try {
            const response = await fetch(endpoint, options);
            const data = await response.json();
            
            removeLoading(loadingId);
            
            if (data.response) {
                appendMessage('agent', data.response, null, true); // Enable animation
            }
            
            // Update session ID if newly created
            if (data.session_id) {
                if (currentSessionId !== data.session_id) {
                    currentSessionId = data.session_id;
                    loadHistory(); // Refresh list to show new chat
                } else {
                    // Just refresh title maybe? For now just refresh list occasionally or rely on next reload
                    // To keep it simple, we refresh history list on every message to update timestamps/titles
                    loadHistory(); 
                }
            }

        } catch (error) {
            console.error('Error:', error);
            removeLoading(loadingId);
            appendMessage('agent', '错误: 无法连接到代理系统。');
        }
    }

    function appendMessage(role, text, imageUrl = null, animate = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        let contentHtml = '';
        if (role === 'agent') {
            const logoSrc = isLightMode ? LOGO_LIGHT : LOGO_DARK;
            contentHtml = `<div class="msg-header"><img src="${logoSrc}" class="agent-avatar"> Way Agent</div>`;
        } else {
            contentHtml = `<div class="msg-header">User <i class="fas fa-user"></i></div>`;
        }

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (imageUrl) {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.style.maxWidth = '100%';
            img.style.borderRadius = '10px';
            img.style.marginBottom = '10px';
            contentDiv.appendChild(img);
        }
        
        // Append header
        msgDiv.innerHTML = contentHtml;
        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);

        if (text) {
            if (animate && role === 'agent') {
                // Typewriter effect for agent
                typeText(contentDiv, text);
            } else {
                // Instant render
                contentDiv.innerHTML = marked.parse(text);
            }
        } else if (role === 'agent' && !imageUrl) {
            contentDiv.innerHTML = `<span style="color:var(--text-muted); font-style:italic;">[执行工具操作中...]</span>`;
        }

        scrollToBottom();
    }

    function typeText(element, text) {
        let index = 0;
        const speed = 10; // ms per char
        
        // We will stream the RAW markdown text first, then render it
        // This gives a "hacker" feel and avoids broken HTML tags
        
        function type() {
            if (index < text.length) {
                // Add a few characters at a time for speed
                const chunk = text.slice(index, index + 3);
                index += 3;
                
                element.textContent += chunk;
                scrollToBottom();
                setTimeout(type, speed);
            } else {
                // Finished typing, render Markdown
                element.innerHTML = marked.parse(text);
                // Highlight code blocks if we had a highlighter (optional)
                scrollToBottom();
            }
        }
        
        type();
    }

    function appendLoading() {
        const id = 'loading-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message agent';
        msgDiv.id = id;
        
        const logoSrc = isLightMode ? LOGO_LIGHT : LOGO_DARK;
        // Use new CSS typing indicator
        msgDiv.innerHTML = `
            <div class="msg-header"><img src="${logoSrc}" class="agent-avatar"> Way Agent</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeLoading(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
