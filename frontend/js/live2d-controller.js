/**
 * Live2D Controller
 * Manage PixiJS application and Live2D model rendering
 */
class Live2DController {
    constructor() {
        this.app = null;
        this.model = null;
        this.canvas = document.getElementById('live2d');
        this.audioPlayer = null; // Reference to audio player
    }

    /**
     * Initialize Live2D
     * @param {AudioStreamPlayer} audioPlayer 
     */
    async init(audioPlayer) {
        this.audioPlayer = audioPlayer;

        // Initialize PixiJS Application
        this.app = new PIXI.Application({
            view: this.canvas,
            autoStart: true,
            backgroundAlpha: 0, // Transparent background
            resizeTo: this.canvas.parentElement // Responsive
        });

        await this.loadModel();

        // Start animation loop
        this.app.ticker.add(this.update.bind(this));

        console.log('Live2D Controller initialized');
    }

    /**
     * Load Live2D model
     */
    async loadModel() {
        try {
            // Load model from local path
            // Note: The path depends on how static files are served. 
            // Assuming 'frontend' is root or 'kei_basic_free' is accessible.
            // Using relative path assuming accessing from /
            // path: frontend/2d/simple/runtime/simple.model3.json
            // Served at: /static/2d/simple/runtime/simple.model3.json
            const modelPath = '/static/2d/simple/runtime/simple.model3.json';

            this.model = await PIXI.live2d.Live2DModel.from(modelPath);

            // Center the model
            this.model.x = this.app.screen.width / 2;
            this.model.y = this.app.screen.height / 2;

            // Scale Model
            // Scale Model
            // Simple model size adjustment - Increased again (0.6) per user request
            this.model.scale.set(0.6);
            this.model.anchor.set(0.5, 0.5);

            // Enable default mouse interaction (looking at mouse)
            // This allows the head/neck to track the mouse position
            this.model.autoInteract = true;

            // Enable explicit interaction key if needed
            this.model.interactive = true;
            this.model.on('pointertap', () => {
                this.playRandomMotion('Tap');
            });

            // Add to stage
            this.app.stage.addChild(this.model);

            console.log('Live2D model loaded successfully');

        } catch (error) {
            console.error('Failed to load Live2D model:', error);
        }
    }

    /**
     * Play a random motion from a group
     * @param {string} group - Motion group name (e.g., 'Tap', 'Idle')
     */
    playRandomMotion(group) {
        if (this.model) {
            this.model.motion(group);
            console.log(`Playing motion: ${group}`);
        }
    }

    /**
     * Update loop (called every frame)
     */
    update() {
        if (!this.model || !this.audioPlayer) return;

        // Lip Sync Logic
        // Map audio level (0.0 - 1.0) to MouthOpenY (0.0 - 1.0)

        // Get current audio level
        const audioLevel = this.audioPlayer.getAudioLevel();

        // Sensitivity factor - amplify the mouth movement
        const sensitivity = 8.0;
        let openValue = Math.min(1.0, audioLevel * sensitivity);

        // Smooth transition (Simple Low-pass filter)
        // If we want smoother movement, we can store previous value.
        // Direct mapping is responsive.

        // Set parameter
        // CoreModel.setParameterValueById(id, value)

        // Live2D Cubism 4 SDK uses internalModel.coreModel.setParameterValueById
        // Pixi-live2d-display simplifies this?
        // Let's us standard 'ParamMouthOpenY'

        if (this.model.internalModel && this.model.internalModel.coreModel) {

            // Linear Interpolation for smoothing
            if (typeof this.currentMouthValue === 'undefined') {
                this.currentMouthValue = 0;
            }

            // Target value based on audio
            const targetValue = openValue; // openValue already applied sensitivity

            // Smooth factors
            const openSpeed = 0.4;  // Opening is fast
            const closeSpeed = 0.15; // Closing is slower (decay)

            if (targetValue > this.currentMouthValue) {
                this.currentMouthValue += (targetValue - this.currentMouthValue) * openSpeed;
            } else {
                this.currentMouthValue += (targetValue - this.currentMouthValue) * closeSpeed;
            }

            // Clamp small values to 0 to avoid "micro-open"
            if (this.currentMouthValue < 0.05) this.currentMouthValue = 0;

            // Brute-force: Try setting all common mouth open parameter names
            // Epsilon usually uses PARAM_MOUTH_OPEN_Y, standard is ParamMouthOpenY
            try {
                this.model.internalModel.coreModel.setParameterValueById('PARAM_MOUTH_OPEN_Y', this.currentMouthValue);
                this.model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', this.currentMouthValue);
            } catch (e) {
                // Ignore errors if parameter doesn't exist
            }

            // DEBUG: Log audio level periodically (every ~60 frames = 1 sec)
            if (!this.frameCount) this.frameCount = 0;
            this.frameCount++;
            if (this.frameCount % 60 === 0 && this.currentMouthValue > 0.1) {
                console.log(`Audio Level: ${audioLevel.toFixed(3)}, Smoothed Mouth: ${this.currentMouthValue.toFixed(3)}`);
            }
        }
    }
}
