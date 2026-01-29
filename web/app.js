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
    const stopBtn = document.getElementById('stop-btn');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const filePreview = document.getElementById('file-preview');
    const themeBtn = document.getElementById('theme-btn');
    const themeIcon = themeBtn.querySelector('.icon');
    const modeDailyBtn = document.getElementById('mode-daily');
    const modeWorkBtn = document.getElementById('mode-work');
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const micBtn = document.getElementById('mic-btn');
    const executionTimer = document.getElementById('execution-timer');
    const autoTtsToggle = document.getElementById('auto-tts-toggle');

    let currentImage = null;
    let currentSessionId = null;
    let currentAgentName = 'Way Agent';
    let timerInterval = null;

    // Timer Functions
    function startTimer() {
        if (!executionTimer) return;
        executionTimer.style.display = 'block';
        executionTimer.textContent = '00:00';
        let seconds = 0;
        
        if (timerInterval) clearInterval(timerInterval);
        
        timerInterval = setInterval(() => {
            seconds++;
            const m = Math.floor(seconds / 60).toString().padStart(2, '0');
            const s = (seconds % 60).toString().padStart(2, '0');
            executionTimer.textContent = `${m}:${s}`;
        }, 1000);
    }

    function stopTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        if (executionTimer) {
            executionTimer.style.display = 'none';
        }
    }

    // Initialize: Update Brand Name first, then Load History
    (async () => {
        await updateBrandName();
        loadHistory();
        showWelcomeMessage();
    })();

    // Theme Switching Logic
    let isLightMode = initLightMode;
    
    // Set initial icon state
    if (isLightMode) {
        // Switch to Moon Icon
        const useEl = themeIcon.querySelector('use');
        if(useEl) useEl.setAttribute('href', '#icon-moon');
    } else {
        // Switch to Sun Icon
        const useEl = themeIcon.querySelector('use');
        if(useEl) useEl.setAttribute('href', '#icon-sun');
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
        const useEl = themeIcon.querySelector('use');
        
        if (isLightMode) {
            document.documentElement.setAttribute('data-theme', 'light');
            if(useEl) useEl.setAttribute('href', '#icon-moon');
        } else {
            document.documentElement.removeAttribute('data-theme');
            if(useEl) useEl.setAttribute('href', '#icon-sun');
        }
        updateLogos(isLightMode);
    });

    // Mode Switcher Logic
    function updateModeSwitcherUI(activePersonaId) {
        if (!modeDailyBtn || !modeWorkBtn) return;
        
        // Remove active class from all
        modeDailyBtn.classList.remove('active');
        modeWorkBtn.classList.remove('active');
        
        // Add active class based on ID
        if (activePersonaId === 'work_mode') {
            modeWorkBtn.classList.add('active');
        } else {
            // Default to daily for 'default' or any other
            modeDailyBtn.classList.add('active');
        }
    }

    async function switchMode(modeId) {
        try {
            const res = await fetch('/api/personas/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ persona_id: modeId })
            });
            
            if (res.ok) {
                await updateBrandName(); // This will also update the UI via our modification
                
                // Show toast/notification
                const modeName = modeId === 'work_mode' ? '工作模式' : '日常模式';
                const toast = document.createElement('div');
                toast.className = 'toast';
                toast.textContent = `已切换至：${modeName}`;
                toast.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: var(--accent-color);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    z-index: 1000;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    animation: fadeIn 0.3s, fadeOut 0.3s 1.7s forwards;
                `;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 2000);
            }
        } catch (error) {
            console.error('Failed to switch mode:', error);
            alert('切换模式失败');
        }
    }

    if (modeDailyBtn) {
        modeDailyBtn.addEventListener('click', () => switchMode('default'));
    }
    if (modeWorkBtn) {
        modeWorkBtn.addEventListener('click', () => switchMode('work_mode'));
    }

    // New Chat Button
    newChatBtn.addEventListener('click', () => {
        currentSessionId = null;
        showWelcomeMessage();
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
    const currentTableNameDisplay = document.getElementById('current-table-name');
    
    // New DB Config Integration
    const toggleDbConfigBtn = document.getElementById('toggle-db-config');
    const dbConfigPanel = document.getElementById('db-config-panel');
    const saveConnectDbBtn = document.getElementById('save-connect-db-btn');
    const refreshDbsBtn = document.getElementById('refresh-dbs-btn');
    const testConnectionBtn = document.getElementById('test-connection-btn');
    
    // --- Settings Modal Logic ---
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsModal = settingsModal.querySelector('.close-modal');
    const allowReadToggle = document.getElementById('allow-read-toggle');
    const allowedPathsInput = document.getElementById('allowed-paths-input');
    const saveSettingsBtn = document.getElementById('save-settings-btn');

    // Default Settings
    const DEFAULT_FILE_CONFIG = {
        allow_read: true,
        allowed_paths: []
    };

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.style.display = 'block';
            loadSettings();
        });
    }

    if (closeSettingsModal) {
        closeSettingsModal.addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });
    }

    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', async () => {
            await saveSettings();
            settingsModal.style.display = 'none';
            alert('设置已保存');
        });
    }

    function loadSettings() {
        const saved = localStorage.getItem('file_config');
        let config = DEFAULT_FILE_CONFIG;
        if (saved) {
            try {
                config = JSON.parse(saved);
            } catch (e) {
                console.error('Failed to parse file settings', e);
            }
        }
        
        // Ensure defaults if keys are missing
        if (config.allow_read === undefined) config.allow_read = true;
        if (!config.allowed_paths) config.allowed_paths = [];

        allowReadToggle.checked = config.allow_read;
        allowedPathsInput.value = (config.allowed_paths || []).join('\n');
    }

    async function saveSettings() {
        // 1. 保存文件权限设置 (本地)
        const allowRead = allowReadToggle.checked;
        const pathsText = allowedPathsInput.value.trim();
        const allowedPaths = pathsText 
            ? pathsText.split('\n').map(p => p.trim()).filter(p => p.length > 0)
            : [];
            
        const config = {
            allow_read: allowRead,
            allowed_paths: allowedPaths
        };
        
        localStorage.setItem('file_config', JSON.stringify(config));

        // 2. 保存 API 配置 (服务端)
        const apiBaseUrl = document.getElementById('api-base-url').value.trim();
        const apiKey = document.getElementById('api-key').value.trim();
        const apiModel = document.getElementById('api-model').value.trim();

        const visionBaseUrl = document.getElementById('vision-base-url').value.trim();
        const visionApiKey = document.getElementById('vision-api-key').value.trim();
        const visionModel = document.getElementById('vision-model').value.trim();

        if (apiBaseUrl || apiKey || apiModel || visionBaseUrl || visionApiKey || visionModel) {
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        logic_base_url: apiBaseUrl || null,
                        logic_api_key: apiKey || null,
                        logic_model: apiModel || null,
                        vision_base_url: visionBaseUrl || null,
                        vision_api_key: visionApiKey || null,
                        vision_model: visionModel || null
                    })
                });
                
                if (!res.ok) {
                    const err = await res.json();
                    console.error('Failed to update API config:', err);
                    alert('文件设置已保存，但 API 配置更新失败: ' + (err.detail || '未知错误'));
                }
            } catch (e) {
                console.error('Error updating API config:', e);
                alert('文件设置已保存，但 API 配置请求出错');
            }
        }
    }

    function getFileConfig() {
         const saved = localStorage.getItem('file_config');
         if (saved) {
             try {
                 return JSON.parse(saved);
             } catch (e) {
                 return DEFAULT_FILE_CONFIG;
             }
         }
         return DEFAULT_FILE_CONFIG;
    }

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

    // Test Connection
    if (testConnectionBtn) {
        testConnectionBtn.addEventListener('click', async () => {
            const originalText = testConnectionBtn.innerHTML;
            testConnectionBtn.innerHTML = '<span class="loading-dots">连接中</span>';
            testConnectionBtn.disabled = true;

            const config = {
                host: document.getElementById('db-host').value,
                port: parseInt(document.getElementById('db-port').value) || 3306,
                user: document.getElementById('db-user').value,
                password: document.getElementById('db-password').value,
                database: null
            };

            try {
                const res = await fetch('/api/db/test-connection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                if (res.ok) {
                    const data = await res.json();
                    alert('连接成功！');
                } else {
                    const err = await res.json();
                    alert('连接失败: ' + (err.detail || 'Unknown error'));
                }
            } catch (e) {
                alert('连接错误: ' + e.message);
            } finally {
                testConnectionBtn.innerHTML = originalText;
                testConnectionBtn.disabled = false;
            }
        });
    }

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
                        ${p.id !== 'default' ? `<button class="delete-btn" style="color: #ff4a4a;"><svg class="icon"><use href="#icon-trash"></use></svg></button>` : ''}
                    </div>
                `;

                // Bind events
                if (!p.is_active) {
                    div.querySelector('.activate-btn').addEventListener('click', async () => {
                        await fetch(`/api/personas/${p.id}/activate`, { method: 'PUT' });
                        loadPersonas();
                        updateBrandName();
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
        if (e.target === settingsModal) settingsModal.style.display = 'none';
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
    });

    // Handle Enter key
    userInput.addEventListener('keydown', (e) => {
        if (e.isComposing) return; // Ignore if using IME
        
        // Send on Ctrl+Enter or Cmd+Enter
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // --- Voice Interaction Logic ---
    // Check Browser Support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isRecording = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN'; // Default to Chinese
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            if (micBtn) {
                micBtn.classList.add('recording'); 
                micBtn.style.color = '#ff4a4a';
                // Pulse animation could be added via CSS
            }
        };

        recognition.onend = () => {
            isRecording = false;
            if (micBtn) {
                micBtn.classList.remove('recording');
                micBtn.style.color = '';
            }
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value += transcript;
            userInput.focus();
            // Trigger auto-resize
            userInput.style.height = 'auto';
            userInput.style.height = (userInput.scrollHeight) + 'px';
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            isRecording = false;
            if (micBtn) {
                micBtn.classList.remove('recording');
                micBtn.style.color = '';
            }
        };

        if (micBtn) {
            micBtn.addEventListener('click', () => {
                if (isRecording) {
                    recognition.stop();
                } else {
                    recognition.start();
                }
            });
        }
    } else {
        if (micBtn) {
            micBtn.style.display = 'none'; // Hide if not supported
            console.warn('Speech Recognition not supported in this browser.');
        }
    }

    function speakText(text) {
        if (!window.speechSynthesis) return;
        
        // Cancel any current speaking
        window.speechSynthesis.cancel();

        // Strip markdown symbols for better speech
        // Simple regex to remove common markdown like **, ##, etc.
        const cleanText = text.replace(/[*#`_]/g, '');

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'zh-CN'; // Default to Chinese
        
        window.speechSynthesis.speak(utterance);
    }

    // Handle Image/File Upload
    imageUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            currentImage = file;
            
            if (file.type.startsWith('image/')) {
                // Image handling
                const reader = new FileReader();
                reader.onload = (e) => {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                    if (filePreview) filePreview.style.display = 'none';
                };
                reader.readAsDataURL(file);
            } else {
                // Document handling
                imagePreview.style.display = 'none';
                if (filePreview) {
                    filePreview.style.display = 'flex';
                    filePreview.innerHTML = `
                        <svg class="icon"><use href="#icon-paperclip"></use></svg>
                        <span>${file.name}</span>
                        <span style="font-size: 0.8em; color: var(--text-muted); margin-left: 5px;">(${(file.size/1024).toFixed(1)} KB)</span>
                    `;
                }
            }
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
                    <span><svg class="icon" style="margin-right:8px; opacity:0.7;"><use href="#icon-chat"></use></svg>${session.title}</span>
                    <button class="delete-btn" title="删除对话"><svg class="icon"><use href="#icon-trash"></use></svg></button>
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
                 showWelcomeMessage();
            }
            scrollToBottom();
        } catch (error) {
            removeLoading(loadingId);
            appendMessage('agent', '无法加载历史记录。');
        }
    }

    let abortController = null;

    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            if (abortController) {
                abortController.abort();
                abortController = null;
                // UI reset will happen in the catch block or finally
            }
        });
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text && !currentImage) return;

        // Clear input
        userInput.value = '';
        userInput.style.height = '24px';
        
        // Determine display for local message
        let displayImage = null;
        let displayText = text;

        if (currentImage) {
            if (currentImage.type.startsWith('image/')) {
                displayImage = imagePreview.src;
            } else {
                displayText = (text ? text + '\n' : '') + `[文件: ${currentImage.name}]`;
            }
        }

        // Add User Message locally
        removeWelcomeMessage();
        appendMessage('user', displayText, displayImage);
        
        // Hide preview
        imagePreview.style.display = 'none';
        if (filePreview) filePreview.style.display = 'none';
        
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

        // Get File Config
        const fileConfig = getFileConfig();
        if (fileConfig) {
            formData.append('file_config', JSON.stringify(fileConfig));
        }
        
        if (currentImage) {
            formData.append('file', currentImage);
        }

        const endpoint = currentImage ? '/api/vision' : '/api/chat';
        let options = {};

        // Setup AbortController
        if (abortController) abortController.abort(); // Cancel previous if any
        abortController = new AbortController();

        // UI State: Show Stop, Hide Send
        sendBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'flex';
        startTimer();

        if (currentImage) {
            options = {
                method: 'POST',
                body: formData,
                signal: abortController.signal
            };
        } else {
            // For JSON endpoint
            const payload = { text: text };
            if (currentSessionId) payload.session_id = currentSessionId;
            if (dbConfig) payload.db_config = JSON.parse(dbConfig);
            if (fileConfig) payload.file_config = fileConfig;
            
            options = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: abortController.signal
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

            if (data.finish_reason === 'length') {
                setTimeout(() => {
                    if (confirm("任务执行步骤已达上限，是否继续执行剩余计划？")) {
                        handleContinue(data.session_id);
                    }
                }, 500);
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
            removeLoading(loadingId);
            if (error.name === 'AbortError') {
                console.log('Request aborted by user');
                // Optional: Append a small note saying "Cancelled"
                // appendMessage('system', '已停止生成');
            } else {
                console.error('Error:', error);
                appendMessage('agent', '错误: 无法连接到代理系统。');
            }
        } finally {
            // Reset UI
            sendBtn.style.display = 'flex';
            if (stopBtn) stopBtn.style.display = 'none';
            stopTimer();
            abortController = null;
        }
    }

    async function handleContinue(sessionId) {
        const loadingId = appendLoading();
        
        // UI State
        sendBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'flex';
        startTimer();
        
        const dbConfigRaw = localStorage.getItem('db_config');
        const fileConfig = getFileConfig();
        
        const payload = {
           text: "请继续执行剩余的计划步骤",
           session_id: sessionId,
           max_steps: 20 // Increase limit for continuation
        };
        if (dbConfigRaw) payload.db_config = JSON.parse(dbConfigRaw);
        if (fileConfig) payload.file_config = fileConfig;
        
        try {
           const response = await fetch('/api/chat', {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify(payload)
           });
           const data = await response.json();
           
           removeLoading(loadingId);
           
           if (data.response) {
               appendMessage('agent', data.response, null, true);
           }
           
           if (data.finish_reason === 'length') {
                setTimeout(() => {
                   if (confirm("任务仍未完成，是否继续？")) {
                       handleContinue(sessionId);
                   }
               }, 500);
           }
           
        } catch (e) {
            removeLoading(loadingId);
            appendMessage('agent', 'Error: ' + e.message);
        } finally {
           sendBtn.style.display = 'flex';
           if (stopBtn) stopBtn.style.display = 'none';
           stopTimer();
        }
    }

    function showWelcomeMessage() {
        chatContainer.innerHTML = '';
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-container';
        welcomeDiv.innerHTML = `<div class="welcome-text">我是${currentAgentName}，很高兴为你服务。</div>`;
        chatContainer.appendChild(welcomeDiv);
    }

    function removeWelcomeMessage() {
        const welcome = chatContainer.querySelector('.welcome-container');
        if (welcome) welcome.remove();
    }

    function processAutoEmbeds(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // Find links to .html files in static/files
        const anchors = tempDiv.querySelectorAll('a[href^="/static/files/"][href$=".html"]');
        
        anchors.forEach(a => {
            const iframeContainer = document.createElement('div');
            iframeContainer.style.cssText = 'margin-top: 10px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;';
            
            const iframe = document.createElement('iframe');
            iframe.src = a.getAttribute('href');
            iframe.style.cssText = 'width: 100%; height: 500px; border: none;';
            
            iframeContainer.appendChild(iframe);
            
            // Insert after the anchor's parent block element if possible, or just after the anchor
            if (a.parentElement.tagName === 'P') {
                 a.parentElement.after(iframeContainer);
            } else {
                 a.after(iframeContainer);
            }
        });
        
        return tempDiv.innerHTML;
    }

    function appendMessage(role, text, imageUrl = null, animate = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        let contentHtml = '';
        if (role === 'agent') {
            const logoSrc = isLightMode ? LOGO_LIGHT : LOGO_DARK;
            contentHtml = `
                <div class="msg-header">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <img src="${logoSrc}" class="agent-avatar"> ${currentAgentName}
                    </div>
                    <button class="copy-btn" title="复制内容">
                        <svg class="icon" style="width:14px; height:14px;"><use href="#icon-copy"></use></svg>
                    </button>
                </div>`;
        } else {
            contentHtml = `
                <div class="msg-header">
                    <button class="copy-btn" title="复制内容" style="margin-right:auto;">
                        <svg class="icon" style="width:14px; height:14px;"><use href="#icon-copy"></use></svg>
                    </button>
                    <div style="display:flex; align-items:center; gap:8px;">
                        User <svg class="icon"><use href="#icon-user"></use></svg>
                    </div>
                </div>`;
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

        // Copy functionality
        const copyBtn = msgDiv.querySelector('.copy-btn');
        if (copyBtn && text) {
            copyBtn.addEventListener('click', () => {
                // Function to perform fallback copy (must be synchronous for execCommand)
                const performFallbackCopy = () => {
                    try {
                        const textArea = document.createElement("textarea");
                        textArea.value = text;
                        
                        // Ensure element is part of layout but invisible
                        textArea.style.position = "fixed";
                        textArea.style.left = "-9999px";
                        textArea.style.top = "0";
                        textArea.setAttribute("readonly", ""); // Prevent keyboard on mobile
                        
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        textArea.setSelectionRange(0, 99999); // For mobile devices
                        
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (successful) {
                            showCopySuccess(copyBtn);
                        } else {
                            console.error('Fallback copy failed');
                            // User reported it works even if execCommand returns false, so we suppress the alert
                            // and optimistically show success
                            showCopySuccess(copyBtn);
                        }
                    } catch (fallbackErr) {
                        console.error('Copy failed:', fallbackErr);
                        // Suppress alert
                    }
                };

                // Check for secure context and clipboard API support
                // If not secure or no clipboard API, go straight to fallback to preserve user gesture
                if (!navigator.clipboard || !window.isSecureContext) {
                    performFallbackCopy();
                    return;
                }

                // Try Clipboard API
                navigator.clipboard.writeText(text)
                    .then(() => {
                        showCopySuccess(copyBtn);
                    })
                    .catch((err) => {
                        console.warn('Clipboard API failed, trying fallback...', err);
                        // Note: Fallback might fail here if the browser requires user gesture
                        // and the promise microtask lost it. But it's worth a try.
                        performFallbackCopy();
                    });
            });
        }

        if (text) {
            if (animate && role === 'agent') {
                // Typewriter effect for agent
                typeText(contentDiv, text);
            } else {
                // Instant render
                contentDiv.innerHTML = processAutoEmbeds(marked.parse(text));
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
                element.innerHTML = processAutoEmbeds(marked.parse(text));
                // Highlight code blocks if we had a highlighter (optional)
                scrollToBottom();
                
                // --- TTS Trigger ---
                // Only speak if auto-tts is enabled
                const autoTtsToggle = document.getElementById('auto-tts-toggle');
                if (autoTtsToggle && autoTtsToggle.checked) {
                    speakText(text);
                }
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
            <div class="msg-header"><img src="${logoSrc}" class="agent-avatar"> ${currentAgentName}</div>
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

    function showCopySuccess(btn) {
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<span style="font-size:12px;">已复制</span>';
        setTimeout(() => {
            btn.innerHTML = originalHtml;
        }, 2000);
    }

    async function updateBrandName() {
        try {
            const res = await fetch('/api/personas');
            const personas = await res.json();
            const activePersona = personas.find(p => p.is_active);
            const nameDisplay = document.getElementById('agent-name-display');
            
            if (activePersona) {
                currentAgentName = activePersona.name;
                updateModeSwitcherUI(activePersona.id);
                
                // Update Sidebar
                if (nameDisplay) {
                    nameDisplay.textContent = `智能助理 ${activePersona.name}`;
                }

                // Update Welcome Message if visible
                const welcomeText = document.querySelector('.welcome-text');
                if (welcomeText) {
                    welcomeText.textContent = `我是${currentAgentName}，很高兴为你服务。`;
                }

                // Update Existing Messages in Chat Window
                const agentHeaders = document.querySelectorAll('.message.agent .msg-header');
                agentHeaders.forEach(header => {
                    // Try to find the wrapper div first (new structure with copy button)
                    const wrapper = header.querySelector('div');
                    if (wrapper) {
                        const img = wrapper.querySelector('img');
                        if (img) {
                            wrapper.innerHTML = '';
                            wrapper.appendChild(img);
                            wrapper.append(' ' + currentAgentName);
                        }
                    } else {
                        // Fallback for legacy structure
                        const img = header.querySelector('img');
                        if (img) {
                            // Preserve the avatar, update the name
                            const avatarSrc = img.src;
                            const avatarClass = img.className;
                            header.innerHTML = `<img src="${avatarSrc}" class="${avatarClass}"> ${currentAgentName}`;
                        }
                    }
                });
            }
        } catch (e) {
            console.error('Failed to update brand name:', e);
        }
    }

    // Initialization
    updateBrandName();
});
