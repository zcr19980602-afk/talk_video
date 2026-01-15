/**
 * UI Controller for managing user interface updates
 */
class UIController {
    constructor() {
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.transcriptDisplay = document.getElementById('transcriptDisplay');
        this.sessionIdDisplay = document.getElementById('sessionId');
        this.stateDisplay = document.getElementById('stateDisplay');
        this.errorModal = document.getElementById('errorModal');
        this.errorMessage = document.getElementById('errorMessage');
        this.videoOverlay = document.getElementById('videoOverlay');
        
        // Setup modal close handlers
        const closeBtn = document.querySelector('.close');
        const errorOkBtn = document.getElementById('errorOkBtn');
        
        closeBtn.onclick = () => this.hideError();
        errorOkBtn.onclick = () => this.hideError();
        
        window.onclick = (event) => {
            if (event.target === this.errorModal) {
                this.hideError();
            }
        };
    }
    
    /**
     * Initialize UI
     */
    init() {
        this.showState('idle');
        this.clearTranscript();
    }
    
    /**
     * Show conversation state
     * @param {string} state - State: 'idle', 'listening', 'processing', 'speaking'
     */
    showState(state) {
        // Update status dot
        this.statusDot.className = 'status-dot ' + state;
        
        // Update status text
        const stateTexts = {
            'idle': '空闲',
            'listening': '监听中...',
            'processing': '思考中...',
            'speaking': '说话中...'
        };
        
        this.statusText.textContent = stateTexts[state] || state;
        this.stateDisplay.textContent = stateTexts[state] || state;
    }
    
    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorModal.style.display = 'block';
    }
    
    /**
     * Hide error modal
     */
    hideError() {
        this.errorModal.style.display = 'none';
    }
    
    /**
     * Update transcript display
     * @param {string} text - Text to add
     * @param {string} role - Role: 'user' or 'assistant'
     */
    updateTranscript(text, role = 'assistant') {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + role;
        
        const roleDiv = document.createElement('div');
        roleDiv.className = 'role';
        roleDiv.textContent = role === 'user' ? '用户' : 'AI助手';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(roleDiv);
        messageDiv.appendChild(contentDiv);
        
        this.transcriptDisplay.appendChild(messageDiv);
        
        // Scroll to bottom
        this.transcriptDisplay.scrollTop = this.transcriptDisplay.scrollHeight;
    }
    
    /**
     * Append text to last message
     * @param {string} text - Text to append
     */
    appendToLastMessage(text) {
        const messages = this.transcriptDisplay.querySelectorAll('.message');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            const content = lastMessage.querySelector('.content');
            content.textContent += text;
            
            // Scroll to bottom
            this.transcriptDisplay.scrollTop = this.transcriptDisplay.scrollHeight;
        }
    }
    
    /**
     * Clear transcript
     */
    clearTranscript() {
        this.transcriptDisplay.innerHTML = '';
    }
    
    /**
     * Set session ID
     * @param {string} sessionId - Session ID
     */
    setSessionId(sessionId) {
        this.sessionIdDisplay.textContent = sessionId;
    }
    
    /**
     * Hide video overlay
     */
    hideVideoOverlay() {
        this.videoOverlay.classList.add('hidden');
    }
    
    /**
     * Show video overlay
     */
    showVideoOverlay() {
        this.videoOverlay.classList.remove('hidden');
    }
    
    /**
     * Enable/disable buttons
     * @param {boolean} started - Whether conversation is started
     */
    updateButtons(started) {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const recordBtn = document.getElementById('recordBtn');
        
        startBtn.disabled = started;
        stopBtn.disabled = !started;
        recordBtn.disabled = !started;
    }
}
