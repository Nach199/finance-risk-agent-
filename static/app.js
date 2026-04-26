document.addEventListener('DOMContentLoaded', () => {
    const apiInput = document.getElementById('api-key-input');
    const savedKey = localStorage.getItem('gemini_api_key');
    if (savedKey) apiInput.value = savedKey;
    apiInput.addEventListener('input', (e) => localStorage.setItem('gemini_api_key', e.target.value));

    const uploadForm = document.getElementById('upload-form');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const btnText = analyzeBtn.querySelector('.btn-text');
    const loader = analyzeBtn.querySelector('.loader');
    
    const resultsPlaceholder = document.getElementById('results-placeholder');
    const resultsContent = document.getElementById('results-content');
    
    const fileInput = document.getElementById('financialDoc');
    const fileVisual = document.querySelector('.file-upload-visual span');
    
    // Ajout de la logique pour minimiser le chatbot
    const chatHeader = document.getElementById('chat-header');
    const chatWidget = document.getElementById('chat-widget');
    const chatToggle = document.getElementById('chat-toggle');
    
    chatHeader.addEventListener('click', () => {
        chatWidget.classList.toggle('collapsed');
        // Change l'icone de la flèche
        if (chatWidget.classList.contains('collapsed')) {
            chatToggle.textContent = '▲';
        } else {
            chatToggle.textContent = '▼';
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileVisual.textContent = "📄 " + e.target.files[0].name;
            fileVisual.style.color = "var(--brand-primary)";
        } else {
            fileVisual.textContent = "📄 Glisser-déposer un document ou cliquer";
            fileVisual.style.color = "";
        }
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        resultsPlaceholder.textContent = "L'Agent IA étudie minutieusement les rapports...";
        resultsContent.classList.add('hidden');
        resultsPlaceholder.classList.remove('hidden');
        
        const formData = new FormData(uploadForm);
        
        try {
            const response = await fetch('/api/analyze', { method: 'POST', body: formData });
            const data = await response.json();
            renderResults(data);
        } catch (error) {
            console.error(error);
            resultsPlaceholder.textContent = "Une erreur est survenue lors de l'analyse.";
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });

    function renderResults(data) {
        resultsPlaceholder.classList.add('hidden');
        resultsContent.classList.remove('hidden');
        
        const scoreElement = document.getElementById('risk-score');
        const scorePath = document.getElementById('score-circle-path');
        const riskLevel = document.getElementById('risk-level');
        
        let currentScore = 0;
        const targetScore = data.overall_risk_score;
        const duration = 1000;
        const steps = 30;
        const stepTime = duration / steps;
        
        const counter = setInterval(() => {
            currentScore += (targetScore / steps);
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(counter);
            }
            scoreElement.textContent = Math.round(currentScore);
        }, stepTime);
        
        setTimeout(() => {
            scorePath.setAttribute('stroke-dasharray', `${targetScore}, 100`);
            let colorClass = 'stroke-good'; let bgClass = 'good';
            if (targetScore > 40) { colorClass = 'stroke-warning'; bgClass = 'warning'; }
            if (targetScore > 70) { colorClass = 'stroke-danger'; bgClass = 'danger'; }
            
            scorePath.className.baseVal = `circle ${colorClass}`;
            riskLevel.className = `risk-level-badge ${bgClass}`;
            riskLevel.textContent = data.risk_level;
        }, 100);

        document.getElementById('agent-summary').textContent = data.agent_summary;
        
        const grid = document.getElementById('ratios-grid');
        grid.innerHTML = '';
        
        for (const [key, ratio] of Object.entries(data.ratios)) {
            const title = key.replace(/_/g, ' ');
            const card = document.createElement('div');
            card.className = 'ratio-card';
            card.innerHTML = `
                <div class="ratio-title">${title}</div>
                <div class="ratio-value" style="color: var(--accent-${ratio.status === 'danger' ? 'red' : (ratio.status === 'warning' ? 'yellow' : 'green')})">${ratio.value}</div>
                <div class="ratio-desc">${ratio.description}</div>
            `;
            grid.appendChild(card);
        }
        
        // Auto-open chatbot when results are rendered
        if(chatWidget.classList.contains('collapsed')) {
            chatWidget.classList.remove('collapsed');
            chatToggle.textContent = '▼';
        }
        
        addChatMessage(`Je viens de terminer l'analyse financière. Avez-vous des questions supplémentaires ?`, 'ai');
    }

    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-message');
    const chatBody = document.getElementById('chat-body');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = chatInput.value.trim();
        if (!msg) return;
        
        addChatMessage(msg, 'user');
        chatInput.value = '';
        
        const typingId = 'typing-' + Date.now();
        addChatMessage('...', 'ai', typingId);
        
        const formData = new FormData();
        formData.append('message', msg);
        formData.append('api_key', document.getElementById('api-key-input').value);
        
        try {
            const response = await fetch('/api/chat', { method: 'POST', body: formData });
            const data = await response.json();
            document.getElementById(typingId).remove();
            addChatMessage(data.reply, 'ai');
        } catch (error) {
            document.getElementById(typingId).remove();
            addChatMessage("Désolé, problème de connexion au serveur IA.", 'ai');
        }
    });

    function addChatMessage(text, sender, id = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        msgDiv.textContent = text;
        if (id) msgDiv.id = id;
        
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
});
