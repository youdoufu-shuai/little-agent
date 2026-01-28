document.addEventListener('DOMContentLoaded', () => {
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
    let isLightMode = false;
    themeBtn.addEventListener('click', () => {
        isLightMode = !isLightMode;
        if (isLightMode) {
            document.documentElement.setAttribute('data-theme', 'light');
            themeIcon.className = 'fas fa-moon';
        } else {
            document.documentElement.removeAttribute('data-theme');
            themeIcon.className = 'fas fa-sun';
        }
    });

    // New Chat Button
    newChatBtn.addEventListener('click', () => {
        currentSessionId = null;
        chatContainer.innerHTML = '<div class="message agent">系统初始化完成。双脑架构已上线。今天我能为您做些什么？</div>';
        // Clear active class from history
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    });

    // DB Config Modal Logic
    const dbConfigBtn = document.getElementById('db-config-btn');
    const dbModal = document.getElementById('db-modal');
    const closeDbModal = dbModal.querySelector('.close-modal');
    const saveDbBtn = document.getElementById('save-db-btn');

    // Load saved config
    const savedDbConfig = localStorage.getItem('db_config');
    if (savedDbConfig) {
        const config = JSON.parse(savedDbConfig);
        document.getElementById('db-host').value = config.host || 'localhost';
        document.getElementById('db-port').value = config.port || 3306;
        document.getElementById('db-user').value = config.user || 'root';
        document.getElementById('db-password').value = config.password || '';
        document.getElementById('db-name').value = config.database || '';
    }

    dbConfigBtn.addEventListener('click', () => {
        dbModal.style.display = 'block';
    });

    closeDbModal.addEventListener('click', () => {
        dbModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === dbModal) {
            dbModal.style.display = 'none';
        }
    });

    saveDbBtn.addEventListener('click', () => {
        const config = {
            host: document.getElementById('db-host').value,
            port: parseInt(document.getElementById('db-port').value),
            user: document.getElementById('db-user').value,
            password: document.getElementById('db-password').value,
            database: document.getElementById('db-name').value
        };
        localStorage.setItem('db_config', JSON.stringify(config));
        dbModal.style.display = 'none';
        alert('数据库配置已保存');
    });

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
                   appendMessage(msg.role === 'user' ? 'user' : 'agent', msg.content); 
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
                appendMessage('agent', data.response);
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

    function appendMessage(role, text, imageUrl = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        let contentHtml = '';
        if (role === 'agent') {
            contentHtml = `<div class="msg-header">Way Agent</div>`;
        } else {
            contentHtml = `<div class="msg-header">User</div>`;
        }

        if (imageUrl) {
            contentHtml += `<img src="${imageUrl}" style="max-width:100%; border-radius:10px; margin-bottom:10px;">`;
        }

        if (text) {
             // Parse Markdown
            const rawHtml = marked.parse(text);
            contentHtml += `<div class="message-content">${rawHtml}</div>`;
        }

        msgDiv.innerHTML = contentHtml;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendLoading() {
        const id = 'loading-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message agent';
        msgDiv.id = id;
        msgDiv.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> 思考中...';
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
