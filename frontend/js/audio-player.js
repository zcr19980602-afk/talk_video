/**
 * Audio Stream Player for playing TTS audio
 */
class AudioStreamPlayer {
    constructor() {
        this.audioContext = null;
        this.playQueue = [];
        this.isPlaying = false;
        this.currentSource = null;
    }
    
    /**
     * Initialize Audio Context
     * @returns {Promise<void>}
     */
    async init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Resume context if suspended
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }
    
    /**
     * Play audio chunk
     * @param {string} base64Audio - Base64 encoded PCM audio
     * @param {number} sampleRate - Sample rate (default: 24000)
     * @returns {Promise<void>}
     */
    async playChunk(base64Audio, sampleRate = 24000) {
        await this.init();
        
        try {
            // Decode base64 to array buffer
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Convert PCM to AudioBuffer
            const audioBuffer = await this.pcmToAudioBuffer(bytes.buffer, sampleRate);
            
            // Add to queue
            this.playQueue.push(audioBuffer);
            
            // Start playing if not already playing
            if (!this.isPlaying) {
                this.playNext();
            }
        } catch (error) {
            console.error('Error playing audio chunk:', error);
        }
    }
    
    /**
     * Convert PCM data to AudioBuffer
     * @param {ArrayBuffer} pcmData - PCM data
     * @param {number} sampleRate - Sample rate
     * @returns {Promise<AudioBuffer>}
     */
    async pcmToAudioBuffer(pcmData, sampleRate) {
        // PCM is 16-bit signed integer
        const int16Array = new Int16Array(pcmData);
        
        // Create audio buffer
        const audioBuffer = this.audioContext.createBuffer(
            1, // mono
            int16Array.length,
            sampleRate
        );
        
        // Convert int16 to float32 (-1.0 to 1.0)
        const channelData = audioBuffer.getChannelData(0);
        for (let i = 0; i < int16Array.length; i++) {
            channelData[i] = int16Array[i] / 32768.0;
        }
        
        return audioBuffer;
    }
    
    /**
     * Play next audio buffer in queue
     */
    playNext() {
        if (this.playQueue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        
        const audioBuffer = this.playQueue.shift();
        
        // Create source
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        
        // Play next when this finishes
        source.onended = () => {
            this.playNext();
        };
        
        source.start(0);
        this.currentSource = source;
    }
    
    /**
     * Stop playback
     */
    stop() {
        if (this.currentSource) {
            try {
                this.currentSource.stop();
            } catch (error) {
                // Already stopped
            }
            this.currentSource = null;
        }
        
        this.playQueue = [];
        this.isPlaying = false;
    }
    
    /**
     * Check if playing
     * @returns {boolean}
     */
    isCurrentlyPlaying() {
        return this.isPlaying;
    }
    
    /**
     * Get queue length
     * @returns {number}
     */
    getQueueLength() {
        return this.playQueue.length;
    }
}
