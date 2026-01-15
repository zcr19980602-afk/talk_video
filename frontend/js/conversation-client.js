/**
 * Conversation Client for communicating with backend
 */
class ConversationClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.eventSource = null;
        this.sessionId = null;
    }

    /**
     * Start a new conversation session
     * @returns {Promise<string>} Session ID
     */
    async startSession() {
        try {
            const response = await fetch(`${this.baseURL}/api/conversation/start`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.sessionId = data.session_id;

            console.log('Session started:', this.sessionId);
            return this.sessionId;
        } catch (error) {
            console.error('Error starting session:', error);
            throw error;
        }
    }

    /**
     * Send audio to backend
     * @param {Blob} audioBlob - Audio blob
     * @returns {Promise<void>}
     */
    async sendAudio(audioBlob) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }

        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.webm');

        try {
            const response = await fetch(
                `${this.baseURL}/api/conversation/audio?session_id=${this.sessionId}`,
                {
                    method: 'POST',
                    body: formData
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('Audio sent successfully');
        } catch (error) {
            console.error('Error sending audio:', error);
            throw error;
        }
    }

    /**
     * Start listening to SSE stream
     * @param {string} action - Action: 'start' or 'process'
     * @param {Function} onMessage - Message handler
     * @param {Function} onError - Error handler
     */
    startListening(action, onMessage, onError) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }

        const url = `${this.baseURL}/api/conversation/stream?session_id=${this.sessionId}&action=${action}`;

        this.eventSource = new EventSource(url);

        // Handle different event types
        this.eventSource.addEventListener('transcript', (event) => {
            const data = JSON.parse(event.data);
            onMessage('transcript', data);
        });

        this.eventSource.addEventListener('response', (event) => {
            const data = JSON.parse(event.data);
            onMessage('response', data);
        });

        this.eventSource.addEventListener('audio', (event) => {
            const data = JSON.parse(event.data);
            onMessage('audio', data);
        });

        this.eventSource.addEventListener('state_change', (event) => {
            const data = JSON.parse(event.data);
            onMessage('state_change', data);
        });

        this.eventSource.addEventListener('done', (event) => {
            onMessage('done', {});
            // 收到 done 事件后关闭连接，避免触发 onerror 和重连
            this.eventSource.close();
            console.log('Conversation stream completed normally');
        });

        this.eventSource.addEventListener('error', (event) => {
            if (event.data) {
                try {
                    const data = JSON.parse(event.data);
                    onError(data);
                } catch (e) {
                    console.warn('Failed to parse error event data:', e);
                    onError({ message: '未知错误' });
                }
            } else {
                // 原生 EventSource 错误（如连接断开），通常由 onerror 处理
                console.log('Received generic error event');
            }
        });

        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            onError({ message: '连接错误' });
        };

        console.log('Started listening to SSE stream');
    }

    /**
     * Process audio with streaming response
     * @param {Blob} audioBlob - Audio blob
     * @param {Function} onMessage - Message handler
     * @param {Function} onError - Error handler
     * @returns {Promise<void>}
     */
    async processAudioStream(audioBlob, onMessage, onError) {
        if (!this.sessionId) {
            throw new Error('No active session');
        }

        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.webm');

        try {
            const response = await fetch(
                `${this.baseURL}/api/conversation/process?session_id=${this.sessionId}`,
                {
                    method: 'POST',
                    body: formData
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Read SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n\n');
                buffer = lines.pop(); // Keep incomplete message in buffer

                for (const line of lines) {
                    if (!line.trim()) continue;

                    const eventMatch = line.match(/^event: (.+)$/m);
                    const dataMatch = line.match(/^data: (.+)$/m);

                    if (eventMatch && dataMatch) {
                        const eventType = eventMatch[1];
                        const data = JSON.parse(dataMatch[1]);

                        if (eventType === 'error') {
                            onError(data);
                        } else {
                            onMessage(eventType, data);
                        }
                    }
                }
            }

            console.log('Audio processing complete');
        } catch (error) {
            console.error('Error processing audio:', error);
            onError({ message: error.message });
        }
    }

    /**
     * Stop listening
     */
    stopListening() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            console.log('Stopped listening');
        }
    }

    /**
     * Get conversation history
     * @returns {Promise<Array>} Message history
     */
    async getHistory() {
        if (!this.sessionId) {
            throw new Error('No active session');
        }

        try {
            const response = await fetch(
                `${this.baseURL}/api/conversation/history?session_id=${this.sessionId}`
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.messages;
        } catch (error) {
            console.error('Error getting history:', error);
            throw error;
        }
    }
}
