/**
 * Main Application Logic
 */
class VoiceConversationApp {
    constructor() {
        this.ui = new UIController();
        this.mediaCapture = new MediaCaptureManager();
        this.client = new ConversationClient();
        this.audioPlayer = new AudioStreamPlayer();

        this.isConversationActive = false;
        this.currentTranscriptRole = null;
        this.recordingTimeout = null;

        this.init();
    }

    /**
     * Initialize application
     */
    async init() {
        this.ui.init();
        this.setupEventListeners();

        console.log('Application initialized');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const recordBtn = document.getElementById('recordBtn');

        startBtn.addEventListener('click', () => this.startConversation());
        stopBtn.addEventListener('click', () => this.stopConversation());

        // Record button - press and hold to record
        recordBtn.addEventListener('mousedown', () => this.onRecordStart());
        recordBtn.addEventListener('mouseup', () => this.onRecordStop());
        recordBtn.addEventListener('mouseleave', () => this.onRecordStop());

        // Touch support for mobile
        recordBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.onRecordStart();
        });
        recordBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.onRecordStop();
        });
    }

    /**
     * Handle record button press
     */
    async onRecordStart() {
        const recordBtn = document.getElementById('recordBtn');
        if (recordBtn.disabled || this.mediaCapture.isCurrentlyRecording()) {
            return;
        }

        // Stop current audio playback immediately (Barge-in)
        this.audioPlayer.stop();

        recordBtn.classList.add('recording');
        recordBtn.textContent = '松开发送';

        await this.startRecording();
    }

    /**
     * Handle record button release
     */
    async onRecordStop() {
        const recordBtn = document.getElementById('recordBtn');
        recordBtn.classList.remove('recording');
        recordBtn.textContent = '按住说话';

        if (this.mediaCapture.isCurrentlyRecording()) {
            await this.stopRecording();
        }
    }

    /**
     * Start conversation
     */
    async startConversation() {
        try {
            this.ui.showState('processing');

            // Request permissions and start video
            await this.mediaCapture.requestPermissions();
            const videoElement = document.getElementById('userVideo');
            await this.mediaCapture.startVideoStream(videoElement);
            this.ui.hideVideoOverlay();

            // Start session
            const sessionId = await this.client.startSession();
            this.ui.setSessionId(sessionId);

            // Start listening to initial greeting
            this.client.startListening(
                'start',
                (type, data) => this.handleMessage(type, data),
                (error) => this.handleError(error)
            );

            this.isConversationActive = true;
            this.ui.updateButtons(true);

            console.log('Conversation started');
        } catch (error) {
            console.error('Error starting conversation:', error);
            this.ui.showError(error.message);
            this.ui.showState('idle');
        }
    }

    /**
     * Stop conversation
     */
    stopConversation() {
        this.isConversationActive = false;

        // Stop media
        this.mediaCapture.stopAllStreams();

        // Stop audio
        this.audioPlayer.stop();

        // Stop listening
        this.client.stopListening();

        // Update UI
        this.ui.showState('idle');
        this.ui.updateButtons(false);
        this.ui.showVideoOverlay();

        console.log('Conversation stopped');
    }

    /**
     * Handle SSE message
     * @param {string} type - Message type
     * @param {Object} data - Message data
     */
    async handleMessage(type, data) {
        console.log('Message:', type, data);

        switch (type) {
            case 'state_change':
                this.handleStateChange(data.state);
                break;

            case 'transcript':
                this.handleTranscript(data.text);
                break;

            case 'response':
                this.handleResponse(data.text);
                break;

            case 'audio':
                await this.handleAudio(data);
                break;

            case 'done':
                this.handleDone();
                break;
        }
    }

    /**
     * Handle state change
     * @param {string} state - New state
     */
    handleStateChange(state) {
        this.ui.showState(state);

        const recordBtn = document.getElementById('recordBtn');

        if (state === 'listening') {
            // Enable record button when in listening state
            recordBtn.disabled = false;
        } else {
            // Disable record button in other states
            recordBtn.disabled = true;
        }
    }

    /**
     * Handle transcript
     * @param {string} text - Transcript text
     */
    handleTranscript(text) {
        if (this.currentTranscriptRole !== 'user') {
            this.ui.updateTranscript(text, 'user');
            this.currentTranscriptRole = 'user';
        } else {
            this.ui.appendToLastMessage(text);
        }
    }

    /**
     * Handle response
     * @param {string} text - Response text
     */
    handleResponse(text) {
        if (this.currentTranscriptRole !== 'assistant') {
            this.ui.updateTranscript(text, 'assistant');
            this.currentTranscriptRole = 'assistant';
        } else {
            this.ui.appendToLastMessage(text);
        }
    }

    /**
     * Handle audio
     * @param {Object} data - Audio data
     */
    async handleAudio(data) {
        try {
            await this.audioPlayer.playChunk(data.audio, data.sample_rate);
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

    /**
     * Handle done
     */
    handleDone() {
        console.log('Processing done');
        this.currentTranscriptRole = null;
    }

    /**
     * Handle error
     * @param {Object} error - Error data
     */
    handleError(error) {
        console.error('Error:', error);
        this.ui.showError(error.message || '发生错误');
        this.ui.showState('idle');
    }

    /**
     * Start recording
     */
    async startRecording() {
        try {
            console.log('Attempting to start recording...');
            await this.mediaCapture.startAudioRecording();
            console.log('Recording started successfully');

            // Auto-stop after 10 seconds
            this.recordingTimeout = setTimeout(() => {
                console.log('Auto-stopping recording after timeout');
                this.stopRecording();
            }, 10000);

        } catch (error) {
            console.error('Error starting recording:', error);
            this.ui.showError('无法开始录音: ' + error.message);
            this.ui.showState('idle');
        }
    }

    /**
     * Stop recording and process
     */
    async stopRecording() {
        try {
            if (this.recordingTimeout) {
                clearTimeout(this.recordingTimeout);
                this.recordingTimeout = null;
            }

            if (!this.mediaCapture.isCurrentlyRecording()) {
                console.log('Not currently recording, skipping stop');
                return;
            }

            console.log('Stopping recording...');
            const audioBlob = await this.mediaCapture.stopAudioRecording();

            if (audioBlob.size === 0) {
                console.warn('Empty audio blob');
                this.ui.showError('录音为空，请重试');
                this.ui.showState('listening');
                return;
            }

            console.log('Stopped recording, processing audio, size:', audioBlob.size);
            this.ui.showState('processing');

            // Process audio with streaming response
            await this.client.processAudioStream(
                audioBlob,
                (type, data) => this.handleMessage(type, data),
                (error) => this.handleError(error)
            );

        } catch (error) {
            console.error('Error stopping recording:', error);
            this.ui.showError('录音处理失败: ' + error.message);
            this.ui.showState('idle');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VoiceConversationApp();
});
