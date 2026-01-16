/**
 * Media Capture Manager for handling camera and microphone
 */
class MediaCaptureManager {
    constructor() {
        this.videoStream = null;
        this.audioStream = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.mimeType = null;
        this.videoRecorder = null;
        this.videoChunks = [];
    }

    /**
     * Get supported MIME type for audio recording
     * @returns {string} Supported MIME type
     */
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4',
            'audio/wav'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                console.log('Using MIME type:', type);
                return type;
            }
        }

        console.warn('No preferred MIME type supported, using default');
        return '';
    }

    /**
     * Request permissions for camera and microphone
     * @returns {Promise<boolean>} Success status
     */
    async requestPermissions() {
        try {
            // Request video stream
            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            // Request separate audio stream for recording
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                video: false,
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });

            // Get supported MIME type
            this.mimeType = this.getSupportedMimeType();

            return true;
        } catch (error) {
            console.error('Permission denied:', error);
            throw new Error('无法访问摄像头和麦克风。请检查浏览器权限设置。');
        }
    }

    /**
     * Start video stream
     * @param {HTMLVideoElement} videoElement - Video element to display stream
     * @returns {Promise<void>}
     */
    async startVideoStream(videoElement) {
        if (!this.videoStream) {
            await this.requestPermissions();
        }

        videoElement.srcObject = this.videoStream;
    }

    /**
     * Start audio recording
     * @returns {Promise<void>}
     */
    async startAudioRecording() {
        if (!this.audioStream) {
            await this.requestPermissions();
        }

        // Check if audio stream has active tracks
        const audioTracks = this.audioStream.getAudioTracks();
        if (audioTracks.length === 0) {
            throw new Error('没有可用的音频轨道');
        }

        console.log('Audio tracks:', audioTracks.map(t => ({ label: t.label, enabled: t.enabled, readyState: t.readyState })));

        // Reset audio chunks
        this.audioChunks = [];

        // Create MediaRecorder with supported options
        const options = {};
        if (this.mimeType) {
            options.mimeType = this.mimeType;
        }

        try {
            this.mediaRecorder = new MediaRecorder(this.audioStream, options);
            console.log('MediaRecorder created with mimeType:', this.mediaRecorder.mimeType);
        } catch (error) {
            console.error('Failed to create MediaRecorder with options:', error);
            // Fallback without options
            this.mediaRecorder = new MediaRecorder(this.audioStream);
            console.log('MediaRecorder created with default settings');
        }

        // Handle data available
        this.mediaRecorder.ondataavailable = (event) => {
            console.log('Data available:', event.data.size, 'bytes');
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };

        // Handle errors
        this.mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
        };

        // Start recording with timeslice to get data periodically
        this.mediaRecorder.start(1000); // Get data every 1 second
        this.isRecording = true;

        console.log('Recording started, state:', this.mediaRecorder.state);
    }

    /**
     * Stop audio recording
     * @returns {Promise<Blob>} Audio blob
     */
    stopAudioRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder) {
                reject(new Error('MediaRecorder not initialized'));
                return;
            }

            if (this.mediaRecorder.state === 'inactive') {
                // Already stopped, return what we have
                const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(this.audioChunks, { type: mimeType });
                this.isRecording = false;
                console.log('Recording already stopped, blob size:', audioBlob.size);
                resolve(audioBlob);
                return;
            }

            this.mediaRecorder.onstop = () => {
                const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(this.audioChunks, { type: mimeType });
                this.isRecording = false;
                console.log('Recording stopped, blob size:', audioBlob.size, 'type:', mimeType);
                resolve(audioBlob);
            };

            this.mediaRecorder.stop();
        });
    }

    /**
     * Get audio blob
     * @returns {Blob} Audio blob
     */
    getAudioBlob() {
        return new Blob(this.audioChunks, { type: 'audio/webm' });
    }

    /**
     * Check if recording
     * @returns {boolean}
     */
    isCurrentlyRecording() {
        return this.isRecording;
    }

    /**
     * Stop all streams
     */
    stopAllStreams() {
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
        }

        if (this.audioStream && this.audioStream !== this.videoStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }

        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
        }

        if (this.videoRecorder && this.videoRecorder.state !== 'inactive') {
            this.videoRecorder.stop();
        }
    }

    /**
     * Start video recording
     */
    async startVideoRecording() {
        if (!this.videoStream) {
            console.warn('No video stream available for recording');
            return;
        }

        this.videoChunks = [];
        const mimeTypes = [
            'video/mp4',
            'video/webm;codecs=h264',
            'video/webm',
            'video/vp8'
        ];

        let selectedType = '';
        for (const type of mimeTypes) {
            if (MediaRecorder.isTypeSupported(type)) {
                selectedType = type;
                break;
            }
        }

        if (!selectedType) {
            console.error('No supported video mime type found');
            return;
        }

        try {
            // Create combined stream with video and audio
            const combinedStream = new MediaStream();

            // Add video tracks
            this.videoStream.getVideoTracks().forEach(track => {
                combinedStream.addTrack(track);
            });

            // Add audio tracks if available
            if (this.audioStream) {
                this.audioStream.getAudioTracks().forEach(track => {
                    combinedStream.addTrack(track);
                });
                console.log('Added audio tracks to video recording');
            }

            this.videoRecorder = new MediaRecorder(combinedStream, { mimeType: selectedType });

            this.videoRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.videoChunks.push(event.data);
                }
            };

            this.videoRecorder.onstop = () => {
                this.uploadVideo();
            };

            this.videoRecorder.start();
            console.log(`Video recording started with ${selectedType}`);
        } catch (error) {
            console.error('Failed to start video recording:', error);
        }
    }

    /**
     * Stop video recording
     */
    stopVideoRecording() {
        if (this.videoRecorder && this.videoRecorder.state !== 'inactive') {
            this.videoRecorder.stop();
            console.log('Video recording stopped');
        }
    }

    /**
     * Upload recorded video to server
     */
    async uploadVideo() {
        if (this.videoChunks.length === 0) return;

        const mimeType = this.videoRecorder ? this.videoRecorder.mimeType : 'video/webm';
        const blob = new Blob(this.videoChunks, { type: mimeType });

        console.log('Uploading video, size:', blob.size, 'type:', mimeType);

        // Create FormData
        const formData = new FormData();
        // Generate a filename
        const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
        const filename = `recording.${ext}`;
        formData.append('file', blob, filename);

        try {
            const response = await fetch('/upload-video', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Video uploaded successfully:', result);
            } else {
                console.error('Video upload failed:', response.statusText);
            }
        } catch (error) {
            console.error('Error uploading video:', error);
        }

        // Clear chunks
        this.videoChunks = [];
    }
}
