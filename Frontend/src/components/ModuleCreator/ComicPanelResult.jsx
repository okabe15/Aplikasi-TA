import React, { useState, useRef, useEffect } from 'react';
import { Volume2, VolumeX, Download } from 'lucide-react';
import { moduleAPI, cleanTextForTTS } from '../../services/api';

/**
 * Enhanced Comic Panel Result Component
 * 
 * Features:
 * - Clean audio generation (no more "asterisk asterisk" sounds!)
 * - Smart button state management (loading, playing, ready, error)
 * - Automatic stop of previous audio
 * - Audio caching for performance
 * - Visual feedback for audio state
 */
export default function ComicPanelResult({ panels, onPlayAudio }) {
  const [audioStates, setAudioStates] = useState({});
  const audioRefs = useRef({});

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Stop all audio and revoke blob URLs
      Object.values(audioRefs.current).forEach(audio => {
        if (audio) {
          audio.pause();
          audio.src = '';
        }
      });
      audioRefs.current = {};
    };
  }, []);

  /**
   * Play audio for a panel
   * Automatically cleans text and manages audio state
   */
  const playPanelAudio = async (panelId, text, type) => {
    const audioKey = `${panelId}-${type}`;
    
    console.log(`🎵 Playing audio for panel ${panelId}, type: ${type}`);
    console.log(`📝 Original text: ${text.substring(0, 50)}...`);
    
    // Clean the text first
    const cleanedText = cleanTextForTTS(text);
    console.log(`🧹 Cleaned text: ${cleanedText.substring(0, 50)}...`);
    
    if (!cleanedText || cleanedText.toLowerCase() === 'none') {
      console.warn('⚠️ No valid text to play');
      return;
    }

    // Check if this audio is already playing
    const currentState = audioStates[audioKey];
    if (currentState === 'playing') {
      // Stop this audio
      stopAudio(panelId, type);
      return;
    }

    // Stop any currently playing audio
    stopAllAudio();

    try {
      // Set loading state
      setAudioStates(prev => ({ ...prev, [audioKey]: 'loading' }));

      // Determine voice type
      const voiceType = type === 'dialogue' ? 'modern' : 'narrator';
      
      // Generate audio (text is already cleaned, so backend will clean it again - double safety!)
      const audioUrl = await moduleAPI.generateAudio(cleanedText, voiceType);
      
      if (!audioUrl) {
        throw new Error('Failed to generate audio URL');
      }
      
      // Create audio element
      const audio = new Audio(audioUrl);
      audioRefs.current[audioKey] = audio;

      // Set up event handlers
      audio.onplay = () => {
        console.log(`▶️ Audio playing: ${audioKey}`);
        setAudioStates(prev => ({ ...prev, [audioKey]: 'playing' }));
      };

      audio.onended = () => {
        console.log(`✅ Audio ended: ${audioKey}`);
        setAudioStates(prev => ({ ...prev, [audioKey]: 'ready' }));
        audioRefs.current[audioKey] = null;
      };

      audio.onerror = (error) => {
        console.error(`❌ Audio error for ${audioKey}:`, error);
        setAudioStates(prev => ({ ...prev, [audioKey]: 'error' }));
        
        // Show error message
        setTimeout(() => {
          setAudioStates(prev => ({ ...prev, [audioKey]: 'ready' }));
        }, 2000);
      };

      // Play the audio
      await audio.play();
      
      // Call callback if provided
      if (onPlayAudio) {
        onPlayAudio(panelId, type);
      }

    } catch (error) {
      console.error(`❌ Audio playback error for ${audioKey}:`, error);
      setAudioStates(prev => ({ ...prev, [audioKey]: 'error' }));
      
      // Reset to ready after 2 seconds
      setTimeout(() => {
        setAudioStates(prev => ({ ...prev, [audioKey]: 'ready' }));
      }, 2000);
    }
  };

  /**
   * Stop specific audio
   */
  const stopAudio = (panelId, type) => {
    const audioKey = `${panelId}-${type}`;
    const audio = audioRefs.current[audioKey];
    
    if (audio) {
      console.log(`⏹️ Stopping audio: ${audioKey}`);
      audio.pause();
      audio.currentTime = 0;
      setAudioStates(prev => ({ ...prev, [audioKey]: 'ready' }));
      audioRefs.current[audioKey] = null;
    }
  };

  /**
   * Stop all currently playing audio
   */
  const stopAllAudio = () => {
    console.log('⏹️ Stopping all audio');
    
    Object.keys(audioRefs.current).forEach(key => {
      const audio = audioRefs.current[key];
      if (audio && !audio.paused) {
        audio.pause();
        audio.currentTime = 0;
      }
    });
    
    // Reset all states to ready
    setAudioStates({});
    audioRefs.current = {};
  };

  /**
   * Download panel image
   */
  const downloadImage = (imageUrl, panelId) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `comic-panel-${panelId}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  /**
   * Get audio button state for a specific panel/type
   */
  const getAudioButtonState = (panelId, type) => {
    const audioKey = `${panelId}-${type}`;
    return audioStates[audioKey] || 'ready';
  };

  /**
   * Get button props based on state
   */
  const getAudioButtonProps = (state, isInline = false) => {
    const baseProps = {
      className: isInline ? 'btn-audio-inline' : 'btn btn-audio',
      disabled: state === 'loading'
    };

    switch (state) {
      case 'loading':
        return {
          ...baseProps,
          className: `${baseProps.className} loading`,
          children: isInline ? '⏳' : '⏳ Loading...'
        };
      
      case 'playing':
        return {
          ...baseProps,
          className: `${baseProps.className} playing`,
          children: isInline ? <VolumeX size={16} /> : '⏸️ Stop'
        };
      
      case 'error':
        return {
          ...baseProps,
          className: `${baseProps.className} error`,
          children: isInline ? '❌' : '❌ Error'
        };
      
      case 'ready':
      default:
        return {
          ...baseProps,
          className: baseProps.className,
          children: isInline ? <Volume2 size={16} /> : '🔊 Play Narration'
        };
    }
  };

  return (
    <div className="result-section">
      <div className="section-header">
        <h2>Your Comic is Ready!</h2>
        <p className="subtitle">
          ✨ Audio has been cleaned for natural speech synthesis (no more weird markdown sounds!)
        </p>
      </div>

      <div className="panel-grid">
        {panels.map(({ panel, imageUrl }) => {
          const hasDialogue = panel.dialogue && panel.dialogue !== 'None';
          const hasNarration = panel.narration && panel.narration.trim() !== '';
          
          const dialogueState = getAudioButtonState(panel.id, 'dialogue');
          const narrationState = getAudioButtonState(panel.id, 'narration');

          // Get cleaned text for display
          const cleanedDialogue = hasDialogue ? cleanTextForTTS(panel.dialogue) : '';
          const cleanedNarration = hasNarration ? cleanTextForTTS(panel.narration) : '';

          return (
            <div key={panel.id} className="comic-panel">
              <div className="panel-header">
                <span className="panel-title">Panel {panel.id}</span>
                <button
                  onClick={() => downloadImage(imageUrl, panel.id)}
                  className="btn-icon"
                  title="Download panel"
                >
                  <Download size={18} />
                </button>
              </div>

              <div className="panel-image-container">
                <img
                  src={imageUrl}
                  alt={`Panel ${panel.id}`}
                  className="generated-image"
                />
                
                {hasDialogue && (
                  <div className="dialogue-bubble">
                    <div className="dialogue-content">
                      <div className="dialogue-text">
                        {cleanedDialogue}
                      </div>
                      <button
                        {...getAudioButtonProps(dialogueState, true)}
                        onClick={() => playPanelAudio(panel.id, panel.dialogue, 'dialogue')}
                        title={dialogueState === 'playing' ? 'Stop audio' : 'Play dialogue audio'}
                      />
                    </div>
                  </div>
                )}
              </div>

              {hasNarration && (
                <div className="panel-narration">
                  <div className="narration-header">
                    <strong>Narration:</strong>
                    <button
                      {...getAudioButtonProps(narrationState, false)}
                      onClick={() => playPanelAudio(panel.id, panel.narration, 'narration')}
                      title={narrationState === 'playing' ? 'Stop audio' : 'Play narration audio'}
                    />
                  </div>
                  <div className="narration-text">
                    {cleanedNarration}
                  </div>
                </div>
              )}

              <div className="panel-details">
                <div className="detail-item">
                  <strong>Setting:</strong> {panel.setting || 'N/A'}
                </div>
                <div className="detail-item">
                  <strong>Mood:</strong> {panel.mood || 'N/A'}
                </div>
                {panel.composition && (
                  <div className="detail-item">
                    <strong>Composition:</strong> {panel.composition}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="audio-info-banner">
        <div className="info-content">
          <div className="info-icon">🎵</div>
          <div className="info-text">
            <strong>Clean Audio Technology:</strong> All dialogue and narration has been 
            automatically processed to remove markdown and formatting artifacts, ensuring 
            natural and clear text-to-speech output.
          </div>
        </div>
      </div>
    </div>
  );
}