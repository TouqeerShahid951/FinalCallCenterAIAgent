class VoiceAssistant {
    constructor() {
        this.ws = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.isRecording = false;
        this.isConnected = false;
        this.callStartTime = null;
        this.callTimerInterval = null;
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.animationId = null;
        
        // Audio processing nodes
        this.sourceNode = null;
        this.gainNode = null;
        this.scriptProcessor = null;
        this.actualSampleRate = null;
        
        // Settings
        this.settings = {
            sensitivity: 50,
            gain: 1.5,  // Reduced default gain
            autoScroll: true,
            soundEffects: true
        };
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.connect();
        
        // Initialize audio context for visualizations
        this.initializeAudioContext();
    }
    
    initializeElements() {
        // Status elements
        this.statusDot = document.getElementById('connectionStatus');
        this.statusText = document.getElementById('statusText');
        
        // Call interface elements
        this.callBtn = document.getElementById('callBtn');
        this.muteBtn = document.getElementById('muteBtn');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.callStatusText = document.getElementById('callStatusText');
        this.callTimer = document.getElementById('callTimer');
        this.avatarCore = document.querySelector('.avatar-core');
        this.waves = document.querySelectorAll('.wave');
        
        // Transcription elements
        this.transcriptionContent = document.getElementById('transcriptionContent');
        this.liveTranscription = document.getElementById('liveTranscription');
        this.liveText = document.getElementById('liveText');
        this.clearBtn = document.getElementById('clearBtn');
        this.exportBtn = document.getElementById('exportBtn');
        
        // Modal elements
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettings = document.getElementById('closeSettings');
        this.sensitivityRange = document.getElementById('sensitivityRange');
        this.gainRange = document.getElementById('gainRange');
        this.gainValue = document.getElementById('gainValue');
        this.autoScrollToggle = document.getElementById('autoScroll');
        this.soundEffectsToggle = document.getElementById('soundEffects');
        
        // Audio element
        this.responseAudio = document.getElementById('responseAudio');
    }
    
    bindEvents() {
        // Call controls
        this.callBtn.addEventListener('click', () => this.toggleCall());
        this.muteBtn.addEventListener('click', () => this.toggleMute());
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        
        // Transcription actions
        this.clearBtn.addEventListener('click', () => this.clearConversation());
        this.exportBtn.addEventListener('click', () => this.exportConversation());
        
        // Settings modal
        this.closeSettings.addEventListener('click', () => this.closeSettingsModal());
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) this.closeSettingsModal();
        });
        
        // Settings controls
        this.sensitivityRange.addEventListener('input', (e) => {
            this.settings.sensitivity = parseInt(e.target.value);
            this.saveSettings();
        });
        
        this.gainRange.addEventListener('input', (e) => {
            const gain = parseFloat(e.target.value);
            this.settings.gain = gain;
            this.gainValue.textContent = `${gain.toFixed(1)}x`;
            this.saveSettings();
            
            // Update audio gain in real-time
            if (this.gainNode) {
                this.gainNode.gain.value = gain;
            }
        });
        
        this.autoScrollToggle.addEventListener('change', (e) => {
            this.settings.autoScroll = e.target.checked;
            this.saveSettings();
        });
        
        this.soundEffectsToggle.addEventListener('change', (e) => {
            this.settings.soundEffects = e.target.checked;
            this.saveSettings();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.ctrlKey) {
                e.preventDefault();
                this.toggleCall();
            }
            if (e.code === 'KeyM' && e.ctrlKey) {
                e.preventDefault();
                this.toggleMute();
            }
        });
    }
    
    async initializeAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        } catch (error) {
            console.warn('Audio context initialization failed:', error);
        }
    }
    
    // FIXED: Proper audio resampling function
    resampleTo16kHz(inputBuffer, inputSampleRate) {
        if (inputSampleRate === 16000) {
            return inputBuffer; // No resampling needed
        }

        const resampleRatio = 16000 / inputSampleRate;
        const outputLength = Math.round(inputBuffer.length * resampleRatio);
        const outputBuffer = new Float32Array(outputLength);

        // Simple linear interpolation resampling
        for (let i = 0; i < outputLength; i++) {
            const inputIndex = i / resampleRatio;
            const inputIndexFloor = Math.floor(inputIndex);
            const inputIndexCeil = Math.min(inputIndexFloor + 1, inputBuffer.length - 1);
            const fraction = inputIndex - inputIndexFloor;

            outputBuffer[i] = inputBuffer[inputIndexFloor] * (1 - fraction) + 
                             inputBuffer[inputIndexCeil] * fraction;
        }

        return outputBuffer;
    }

    async setupAudioProcessing() {
        try {
            if (!this.audioContext || !this.audioStream) {
                console.error('setupAudioProcessing: Missing audioContext or audioStream');
                return;
            }
            
            console.log('🔧 Setting up FIXED audio processing...');
            
            // Store the actual sample rate
            this.actualSampleRate = this.audioContext.sampleRate;
            console.log(`📊 Actual browser sample rate: ${this.actualSampleRate}Hz`);
            console.log(`🎯 Target sample rate: 16000Hz`);
            console.log(`🔄 Resampling ratio: ${16000 / this.actualSampleRate}`);
            
            // Create audio source from microphone
            this.sourceNode = this.audioContext.createMediaStreamSource(this.audioStream);
            
            // Create gain node for amplification
            this.gainNode = this.audioContext.createGain();
            this.gainNode.gain.value = this.settings.gain;
            console.log(`🎚️ Gain node created with value: ${this.settings.gain}`);
            
            // Create ScriptProcessorNode for raw PCM data
            const bufferSize = 4096;
            this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
            
            this.scriptProcessor.onaudioprocess = (event) => {
                if (!this.isRecording || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    return;
                }
                
                // Get audio data
                const inputBuffer = event.inputBuffer;
                const inputData = inputBuffer.getChannelData(0);
                
                // FIXED: Resample to 16kHz BEFORE any other processing
                const resampledData = this.resampleTo16kHz(inputData, this.actualSampleRate);
                
                // Check audio levels for debugging (use resampled data)
                let sum = 0;
                let peak = 0;
                for (let i = 0; i < resampledData.length; i++) {
                    const abs = Math.abs(resampledData[i]);
                    sum += resampledData[i] * resampledData[i];
                    if (abs > peak) peak = abs;
                }
                const rms = Math.sqrt(sum / resampledData.length);
                
                // Log audio levels occasionally for debugging
                if (Math.random() < 0.1) { // 10% of the time
                    console.log(`🎤 Audio levels (16kHz): RMS=${rms.toFixed(4)}, Peak=${peak.toFixed(4)}, Samples=${resampledData.length}`);
                    console.log(`📏 Original length: ${inputData.length}, Resampled length: ${resampledData.length}`);
                    
                    // Update UI with audio levels if element exists
                    const audioLevelElement = document.getElementById('audio-level');
                    if (audioLevelElement) {
                        const levelPercent = Math.min(100, (rms * 100));
                        audioLevelElement.style.width = `${levelPercent}%`;
                        audioLevelElement.style.backgroundColor = levelPercent > 50 ? '#4CAF50' : levelPercent > 20 ? '#FF9800' : '#F44336';
                    }
                }
                
                // FIXED: Convert to 16-bit PCM without double-gain application
                const pcmData = new Int16Array(resampledData.length);
                
                for (let i = 0; i < resampledData.length; i++) {
                    // Apply gain and clamp to [-1, 1], then convert to 16-bit
                    let sample = resampledData[i] * this.settings.gain;
                    sample = Math.max(-1, Math.min(1, sample)); // Clamp to prevent clipping
                    pcmData[i] = Math.round(sample * 32767);
                }
                
                // Log PCM data details occasionally
                if (Math.random() < 0.05) { // 5% of the time
                    const pcmRms = Math.sqrt(pcmData.reduce((sum, val) => sum + (val/32767) * (val/32767), 0) / pcmData.length);
                    const pcmPeak = Math.max(...pcmData.map(val => Math.abs(val/32767)));
                    console.log(`📤 Sending PCM (16kHz): ${pcmData.length} samples, RMS=${pcmRms.toFixed(4)}, Peak=${pcmPeak.toFixed(4)}`);
                    console.log(`📦 Buffer size: ${pcmData.buffer.byteLength} bytes`);
                }
                
                // Send raw PCM data
                try {
                    this.ws.send(pcmData.buffer);
                } catch (error) {
                    console.error('❌ Error sending PCM data:', error);
                }
            };
            
            // FIXED: Connect the audio processing chain properly
            this.sourceNode.connect(this.gainNode);
            this.gainNode.connect(this.scriptProcessor);
            // Connect to destination for monitoring (optional, can be removed for production)
            this.scriptProcessor.connect(this.audioContext.destination);
            
            console.log('✅ FIXED Audio processing chain connected successfully');
            console.log(`🔗 Audio chain: Microphone(${this.actualSampleRate}Hz) → Gain → Resample(16kHz) → ScriptProcessor → WebSocket`);
            
        } catch (error) {
            console.error('❌ Failed to setup audio processing:', error);
            this.showNotification('Audio processing setup failed', 'error');
        }
    }
    
    connect() {
        this.updateStatus('connecting', 'Connecting...');
        
        try {
            this.ws = new WebSocket('ws://localhost:8000/ws/audio');
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateStatus('connected', 'Connected');
                this.playNotificationSound('connect');
                this.showNotification('Connected to voice assistant', 'success');
            };
            
            this.ws.onmessage = (event) => {
                console.log(`📨 WebSocket message received: ${event.data instanceof Blob ? 'Audio Blob' : 'Text'}`);
                
                if (event.data instanceof Blob) {
                    console.log(`🔊 Audio response received: ${event.data.size} bytes`);
                    this.handleAudioResponse(event.data);
                } else {
                    try {
                        const data = JSON.parse(event.data);
                        console.log(`📝 Text message received:`, data);
                        this.handleTextMessage(data);
                    } catch (error) {
                        console.error('❌ Error parsing message:', error);
                    }
                }
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateStatus('disconnected', 'Disconnected');
                this.playNotificationSound('disconnect');
                this.showNotification('Disconnected from voice assistant', 'error');
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connect();
                    }
                }, 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateStatus('error', 'Connection error');
                this.showNotification('Connection error occurred', 'error');
            };
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateStatus('error', 'Failed to connect');
        }
    }
    
    updateStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }
    
    async toggleCall() {
        if (!this.isConnected) {
            this.showNotification('Not connected to server', 'error');
            return;
        }
        
        if (this.isRecording) {
            await this.stopCall();
        } else {
            await this.startCall();
        }
    }
    
    // FIXED: Improved microphone setup with better constraints
    async startCall() {
        try {
            console.log('🚀 Starting call...');
            
            // Resume audio context if suspended (required by modern browsers)
            if (this.audioContext && this.audioContext.state === 'suspended') {
                console.log('⏸️ Resuming suspended audio context...');
                await this.audioContext.resume();
                console.log('✅ Audio context resumed');
            }
            
            // FIXED: Better microphone constraints
            console.log('🎤 Requesting microphone access...');
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    // Remove sampleRate constraint - let browser choose, we'll resample
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: false,  // FIXED: Disable AGC to prevent double gain
                    googEchoCancellation: true,
                    googNoiseSuppression: true,
                    googAutoGainControl: false,  // FIXED: Disable Google AGC too
                    googHighpassFilter: true
                } 
            });
            
            // Log the actual audio track settings
            const audioTrack = this.audioStream.getAudioTracks()[0];
            const settings = audioTrack.getSettings();
            console.log('🎵 Actual microphone settings:', settings);
            console.log(`📊 Microphone sample rate: ${settings.sampleRate || 'unknown'}Hz`);
            
            console.log('✅ Microphone access granted');
            
            // Set up audio analysis for visualizations
            if (this.audioContext && this.analyser) {
                console.log('📊 Setting up audio visualization...');
                const source = this.audioContext.createMediaStreamSource(this.audioStream);
                source.connect(this.analyser);
                this.startVisualization();
                console.log('✅ Audio visualization started');
            }
            
            // Set up audio processing for raw PCM data
            console.log('🔧 Setting up FIXED audio processing for PCM...');
            await this.setupAudioProcessing();
            
            // Legacy MediaRecorder fallback (not used for PCM)
            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            // We don't use MediaRecorder for PCM, but keep it for compatibility
            this.mediaRecorder.ondataavailable = (event) => {
                // PCM data is sent via AudioWorklet instead
            };
            
            this.mediaRecorder.start(250); // Keep running for compatibility
            this.isRecording = true;
            console.log('✅ Recording started');
            
            // Update UI
            this.callBtn.innerHTML = '<i class="fas fa-phone-slash"></i><span class="btn-text">End Call</span>';
            this.callBtn.classList.add('active');
            this.callStatusText.textContent = 'Listening...';
            this.avatarCore.classList.add('listening');
            
            // Start call timer
            this.callStartTime = Date.now();
            this.startCallTimer();
            
            // Show live transcription
            this.liveTranscription.style.display = 'block';
            this.liveText.textContent = 'Listening for your voice...';
            
            this.playNotificationSound('start');
            this.showNotification('Call started - speak now', 'success');
            
        } catch (error) {
            console.error('❌ Error starting call:', error);
            this.showNotification('Failed to access microphone', 'error');
        }
    }
    
    async stopCall() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        // Clean up audio processing
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
            this.audioStream = null;
        }
        
        this.isRecording = false;
        
        // Update UI
        this.callBtn.innerHTML = '<i class="fas fa-phone"></i><span class="btn-text">Start Call</span>';
        this.callBtn.classList.remove('active');
        this.callStatusText.textContent = 'Ready to start';
        this.avatarCore.classList.remove('listening');
        
        // Stop call timer
        this.stopCallTimer();
        
        // Hide live transcription
        this.liveTranscription.style.display = 'none';
        
        // Stop visualization
        this.stopVisualization();
        
        this.playNotificationSound('end');
        this.showNotification('Call ended', 'info');
    }
    
    toggleMute() {
        if (!this.isRecording) return;
        
        const audioTracks = this.audioStream?.getAudioTracks();
        if (audioTracks && audioTracks.length > 0) {
            const isMuted = !audioTracks[0].enabled;
            audioTracks[0].enabled = isMuted;
            
            this.muteBtn.classList.toggle('muted', !isMuted);
            this.muteBtn.innerHTML = isMuted ? 
                '<i class="fas fa-microphone"></i>' : 
                '<i class="fas fa-microphone-slash"></i>';
            
            this.showNotification(isMuted ? 'Unmuted' : 'Muted', 'info');
        }
    }
    
    startCallTimer() {
        this.callTimer.style.display = 'block';
        this.callTimerInterval = setInterval(() => {
            if (this.callStartTime) {
                const elapsed = Date.now() - this.callStartTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                this.callTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    stopCallTimer() {
        if (this.callTimerInterval) {
            clearInterval(this.callTimerInterval);
            this.callTimerInterval = null;
        }
        this.callTimer.style.display = 'none';
        this.callStartTime = null;
    }
    
    startVisualization() {
        const animate = () => {
            if (!this.isRecording || !this.analyser || !this.dataArray) return;
            
            this.analyser.getByteFrequencyData(this.dataArray);
            
            // Calculate average volume
            const average = this.dataArray.reduce((sum, value) => sum + value, 0) / this.dataArray.length;
            const normalizedVolume = average / 255;
            
            // Update wave visualization
            this.waves.forEach((wave, index) => {
                const intensity = Math.max(0.3, normalizedVolume * (1 + index * 0.2));
                wave.style.transform = `scaleY(${intensity})`;
                wave.classList.toggle('active', normalizedVolume > 0.1);
            });
            
            // Update avatar based on volume
            if (normalizedVolume > 0.2) {
                this.avatarCore.style.transform = `scale(${1 + normalizedVolume * 0.2})`;
                this.avatarCore.style.boxShadow = `0 0 ${30 + normalizedVolume * 20}px rgba(99, 102, 241, ${0.5 + normalizedVolume * 0.3})`;
            } else {
                this.avatarCore.style.transform = 'scale(1)';
                this.avatarCore.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';
            }
            
            this.animationId = requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        // Reset waves
        this.waves.forEach(wave => {
            wave.style.transform = 'scaleY(1)';
            wave.classList.remove('active');
        });
        
        // Reset avatar
        this.avatarCore.style.transform = 'scale(1)';
        this.avatarCore.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.2)';
    }
    
    handleAudioResponse(audioBlob) {
        // Convert blob to audio and play
        const audioUrl = URL.createObjectURL(audioBlob);
        this.responseAudio.src = audioUrl;
        
        this.responseAudio.onloadeddata = () => {
            this.responseAudio.play().catch(error => {
                console.error('Error playing audio:', error);
                this.showNotification('Error playing audio response', 'error');
            });
        };
        
        this.responseAudio.onended = () => {
            URL.revokeObjectURL(audioUrl);
        };
        
        // Visual feedback for response
        this.showResponseFeedback();
    }
    
    playBase64Audio(base64Audio, format = 'wav') {
        try {
            // Convert base64 to binary
            const binaryString = atob(base64Audio);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Create blob from binary data
            const mimeType = format === 'wav' ? 'audio/wav' : 'audio/mpeg';
            const audioBlob = new Blob([bytes], { type: mimeType });
            
            // Play the audio blob
            this.handleAudioResponse(audioBlob);
            
            console.log(`🔊 Playing base64 audio: ${bytes.length} bytes, format: ${format}`);
        } catch (error) {
            console.error('❌ Error playing base64 audio:', error);
            this.showNotification('Error playing audio response', 'error');
        }
    }
    
    handleTextMessage(data) {
        if (data.type === 'transcript') {
            this.updateLiveTranscription(data.text, data.final);
            
            if (data.final) {
                this.addMessage('user', data.text);
            }
        } else if (data.type === 'response') {
            this.addMessage('assistant', data.text);
        } else if (data.type === 'audio_response') {
            // Handle combined text and audio response
            if (data.text) {
                this.addMessage('assistant', data.text);
            }
            
            if (data.audio) {
                // Convert base64 audio to blob and play it
                this.playBase64Audio(data.audio, data.audio_format || 'wav');
            }
        } else if (data.type === 'status') {
            this.callStatusText.textContent = data.message;
        }
    }
    
    updateLiveTranscription(text, isFinal) {
        if (this.liveText) {
            this.liveText.textContent = text;
            this.liveText.style.fontStyle = isFinal ? 'normal' : 'italic';
            this.liveText.style.opacity = isFinal ? '1' : '0.8';
        }
    }
    
    addMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${sender}`;
        
        const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const avatar = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="${avatar}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(text)}</div>
                <div class="message-time">${currentTime}</div>
            </div>
        `;
        
        // Remove welcome message if it exists
        const welcomeMessage = this.transcriptionContent.querySelector('.welcome-message');
        if (welcomeMessage && sender === 'user') {
            welcomeMessage.remove();
        }
        
        this.transcriptionContent.appendChild(messageDiv);
        
        // Auto-scroll if enabled
        if (this.settings.autoScroll) {
            this.transcriptionContent.scrollTop = this.transcriptionContent.scrollHeight;
        }
        
        // Clear live transcription for user messages
        if (sender === 'user' && this.liveText) {
            this.liveText.textContent = 'Listening for your voice...';
        }
    }
    
    showResponseFeedback() {
        // Animate avatar for response
        this.avatarCore.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        this.avatarCore.style.transform = 'scale(1.1)';
        
        setTimeout(() => {
            this.avatarCore.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            this.avatarCore.style.transform = 'scale(1)';
        }, 1000);
    }
    
    clearConversation() {
        if (confirm('Clear all conversation history?')) {
            this.transcriptionContent.innerHTML = `
                <div class="welcome-message">
                    <div class="message-bubble assistant">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            <div class="message-text">
                                Hello! I'm your AI assistant. I can help you with company policies, returns, shipping, and more. How can I assist you today?
                            </div>
                            <div class="message-time">Ready</div>
                        </div>
                    </div>
                </div>
            `;
            this.showNotification('Conversation cleared', 'info');
        }
    }
    
    exportConversation() {
        const messages = Array.from(this.transcriptionContent.querySelectorAll('.message-bubble')).map(bubble => {
            const sender = bubble.classList.contains('user') ? 'User' : 'Assistant';
            const text = bubble.querySelector('.message-text').textContent;
            const time = bubble.querySelector('.message-time').textContent;
            return `[${time}] ${sender}: ${text}`;
        }).join('\n\n');
        
        const blob = new Blob([messages], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('Conversation exported', 'success');
    }
    
    openSettings() {
        this.settingsModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    closeSettingsModal() {
        this.settingsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
    
    loadSettings() {
        const saved = localStorage.getItem('voiceAssistantSettings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
        }
        
        // Update UI
        this.sensitivityRange.value = this.settings.sensitivity;
        this.gainRange.value = this.settings.gain;
        this.gainValue.textContent = `${this.settings.gain}x`;
        this.autoScrollToggle.checked = this.settings.autoScroll;
        this.soundEffectsToggle.checked = this.settings.soundEffects;
    }
    
    saveSettings() {
        localStorage.setItem('voiceAssistantSettings', JSON.stringify(this.settings));
    }
    
    playNotificationSound(type) {
        if (!this.settings.soundEffects) return;
        
        // Create audio context for sound effects
        if (this.audioContext) {
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            // Different sounds for different events
            switch (type) {
                case 'connect':
                    oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
                    oscillator.frequency.setValueAtTime(1000, this.audioContext.currentTime + 0.1);
                    break;
                case 'disconnect':
                    oscillator.frequency.setValueAtTime(600, this.audioContext.currentTime);
                    oscillator.frequency.setValueAtTime(400, this.audioContext.currentTime + 0.1);
                    break;
                case 'start':
                    oscillator.frequency.setValueAtTime(600, this.audioContext.currentTime);
                    break;
                case 'end':
                    oscillator.frequency.setValueAtTime(400, this.audioContext.currentTime);
                    break;
            }
            
            gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, this.audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.2);
            
            oscillator.start(this.audioContext.currentTime);
            oscillator.stop(this.audioContext.currentTime + 0.2);
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: 'rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '12px',
            padding: '16px 20px',
            color: 'white',
            fontSize: '14px',
            fontWeight: '500',
            zIndex: '10000',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease',
            maxWidth: '300px',
            boxShadow: '0 8px 16px rgba(0, 0, 0, 0.2)'
        });
        
        // Add color based on type
        const colors = {
            success: 'rgba(16, 185, 129, 0.2)',
            error: 'rgba(239, 68, 68, 0.2)',
            warning: 'rgba(245, 158, 11, 0.2)',
            info: 'rgba(59, 130, 246, 0.2)'
        };
        notification.style.background = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new VoiceAssistant();
});

// Add some helpful keyboard shortcuts info
document.addEventListener('keydown', (e) => {
    if (e.key === '?' && e.shiftKey) {
        alert(`Keyboard Shortcuts:
        
Ctrl + Space: Toggle call
Ctrl + M: Toggle mute
Shift + ?: Show this help

The voice assistant is ready to help with your questions!`);
    }
});
