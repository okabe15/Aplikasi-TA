// api.js - Enhanced with Clean Text Support
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('🚀 API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.config.url, response.status);
    return response;
  },
  (error) => {
    console.error('❌ API Error:', error.response?.status, error.response?.data);
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Clean text for TTS - removes markdown, XML, and other artifacts
 * This matches the backend clean_text_for_tts() function
 * 
 * 🔥 KEY FUNCTION: This prevents "asterisk asterisk" from being spoken!
 */
export function cleanTextForTTS(text) {
  if (!text) return '';
  
  let cleaned = text.trim();
  
  // Step 1: Remove markdown formatting FIRST (crucial!)
  // **Watson:** -> Watson:
  cleaned = cleaned.replace(/\*\*([^*]+):\*\*/g, '$1:');
  // **text** -> text
  cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, '$1');
  // *text* -> text
  cleaned = cleaned.replace(/\*([^*]+)\*/g, '$1');
  // _text_ -> text
  cleaned = cleaned.replace(/_([^_]+)_/g, '$1');
  
  // Step 2: Remove HTML/XML tags
  cleaned = cleaned.replace(/<[^>]*>/g, '');
  
  // Step 3: Handle HTML entities
  cleaned = cleaned.replace(/&quot;/g, '"');
  cleaned = cleaned.replace(/&apos;/g, "'");
  cleaned = cleaned.replace(/&lt;/g, '<');
  cleaned = cleaned.replace(/&gt;/g, '>');
  cleaned = cleaned.replace(/&amp;/g, '&');
  
  // Step 4: Clean whitespace
  cleaned = cleaned.replace(/\s+/g, ' ').trim();
  
  // Step 5: Remove enclosing quotes if they wrap the whole text
  if (cleaned.startsWith('"') && cleaned.endsWith('"')) {
    cleaned = cleaned.slice(1, -1);
  }
  if (cleaned.startsWith("'") && cleaned.endsWith("'")) {
    cleaned = cleaned.slice(1, -1);
  }
  
  return cleaned;
}

// Audio cache for better performance
const audioCache = new Map();
const MAX_CACHE_SIZE = 100;

export const moduleAPI = {
  modernizeText: async (classicText) => {
    const response = await api.post('/api/modules/modernize-text', {
      text: classicText
    });
    return response.data;
  },

  generateComicScript: async (modernTextData) => {
    const response = await api.post('/api/modules/generate-comic-script', modernTextData);
    return response.data;
  },

  generatePanelImage: async (panelData) => {
    const response = await api.post('/api/modules/generate-panel-image', panelData, {
      responseType: 'blob'
    });
    return response.data;
  },

  blobToBase64: (blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  },

  /**
   * Generate audio with automatic text cleaning
   * 
   * @param {string} text - Text to synthesize (will be cleaned automatically)
   * @param {string} voiceType - Voice type: modern, classic, narrator, male, female
   * @param {string} rate - Speech rate: slow, medium, fast
   * @param {string} pitch - Voice pitch: low, medium, high
   * @param {boolean} useSSML - Use SSML formatting (not recommended for clean audio)
   * @param {boolean} useCache - Use cached audio if available
   * @returns {Promise<string>} - Blob URL for the audio
   */
  generateAudio: async (
    text, 
    voiceType = 'modern', 
    rate = 'medium', 
    pitch = 'medium', 
    useSSML = false,
    useCache = true
  ) => {
    // Clean the text BEFORE sending to backend
    // This ensures consistent behavior even if backend changes
    const cleanedText = cleanTextForTTS(text);
    
    console.log('🎵 Audio Generation:');
    console.log('  Original:', text.substring(0, 50) + '...');
    console.log('  Cleaned:', cleanedText.substring(0, 50) + '...');
    console.log('  Voice:', voiceType);
    
    if (!cleanedText || cleanedText.toLowerCase() === 'none') {
      console.warn('⚠️ No valid text to synthesize');
      return null;
    }
    
    // Check cache first
    const cacheKey = `${cleanedText}-${voiceType}-${rate}-${pitch}`;
    if (useCache && audioCache.has(cacheKey)) {
      console.log('💾 Audio found in cache');
      return audioCache.get(cacheKey);
    }
    
    try {
      const response = await api.get('/api/modules/generate-audio', {
        params: {
          text: cleanedText,  // Send cleaned text
          voice_type: voiceType,
          rate: rate,
          pitch: pitch,
          use_ssml: useSSML
        },
        responseType: 'blob'
      });
      
      const audioBlob = response.data;
      
      if (audioBlob.size === 0) {
        throw new Error('Received empty audio response');
      }
      
      console.log('✅ Audio generated:', audioBlob.size, 'bytes');
      
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Cache the audio URL
      if (useCache) {
        audioCache.set(cacheKey, audioUrl);
        
        // Limit cache size
        if (audioCache.size > MAX_CACHE_SIZE) {
          const firstKey = audioCache.keys().next().value;
          const oldUrl = audioCache.get(firstKey);
          URL.revokeObjectURL(oldUrl); // Clean up old blob URL
          audioCache.delete(firstKey);
          console.log('🗑️ Cache limit reached, removed oldest entry');
        }
      }
      
      return audioUrl;
      
    } catch (error) {
      console.error('❌ Audio generation failed:', error);
      throw error;
    }
  },

  // ============================================================================
// TAMBAHKAN INI DI api.js - di dalam export const moduleAPI = { ... }
// ============================================================================

// Letakkan setelah method generateAudio() yang sudah ada

/**
 * Generate audio and return as base64 for saving to database
 */
generateAudioBase64: async (text, voiceType = 'modern') => {
  try {
    const cleanedText = cleanTextForTTS(text);
    
    if (!cleanedText || cleanedText.toLowerCase() === 'none') {
      console.log('⚠️ No valid text for audio generation');
      return null;
    }
    
    console.log(`🎵 Generating base64 audio: ${cleanedText.substring(0, 30)}...`);
    
    const token = localStorage.getItem('token');
    const params = new URLSearchParams({
      text: cleanedText,
      voice_type: voiceType,
      rate: 'medium',
      pitch: 'medium',
      use_ssml: 'false'
    });
    
    const url = `${API_BASE_URL}/api/modules/generate-audio?${params.toString()}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const audioBlob = await response.blob();
    
    // Convert blob to base64
    const base64 = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(audioBlob);
    });
    
    console.log(`✅ Generated base64 audio: ${base64.length} characters`);
    return base64;
    
  } catch (error) {
    console.error('❌ Failed to generate audio base64:', error);
    return null;
  }
},

/**
 * Generate all audio for panels and return as array
 * This will be called when saving a module
 */
generateAllPanelAudio: async (panels) => {
  console.log(`🎵 Starting audio generation for ${panels.length} panels...`);
  
  const audioResults = [];
  let successCount = 0;
  
  for (let i = 0; i < panels.length; i++) {
    const panel = panels[i];
    console.log(`\n📍 Panel ${i + 1}/${panels.length} (ID: ${panel.id})`);
    
    const panelAudio = {
      panel_id: panel.id,
      dialogue_audio: null,
      narration_audio: null
    };
    
    // Generate dialogue audio if exists
    if (panel.dialogue && panel.dialogue !== 'None') {
      console.log(`  🗣️  Generating dialogue...`);
      panelAudio.dialogue_audio = await moduleAPI.generateAudioBase64(
        panel.dialogue, 
        'modern'
      );
      if (panelAudio.dialogue_audio) {
        console.log(`  ✅ Dialogue audio generated`);
        successCount++;
      }
    }
    
    // Generate narration audio if exists
    if (panel.narration && panel.narration.trim()) {
      console.log(`  📖 Generating narration...`);
      panelAudio.narration_audio = await moduleAPI.generateAudioBase64(
        panel.narration, 
        'narrator'
      );
      if (panelAudio.narration_audio) {
        console.log(`  ✅ Narration audio generated`);
        successCount++;
      }
    }
    
    audioResults.push(panelAudio);
    
    // Small delay to avoid overwhelming the server
    if (i < panels.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  
  console.log(`\n✅ Audio generation complete!`);
  console.log(`   Generated: ${successCount} audio files`);
  console.log(`   For: ${audioResults.length} panels`);
  
  return audioResults;
},

/**
 * Save panel audios to database
 */
savePanelAudios: async (moduleId, audios) => {
  console.log(`💾 Saving ${audios.length} panel audios to database...`);
  
  const response = await api.post('/api/modules/save-panel-audios', {
    module_id: moduleId,
    audios: audios
  });
  
  console.log(`✅ Audios saved:`, response.data);
  return response.data;
},

/**
 * Get URL for saved audio
 */
getPanelAudioUrl: (moduleId, panelId, audioType) => {
  return `${API_BASE_URL}/api/modules/panel-audio/${moduleId}/${panelId}?audio_type=${audioType}`;
},

/**
 * Check if saved audio exists for a panel
 */
checkPanelAudioExists: async (moduleId, panelId, audioType) => {
  try {
    const url = moduleAPI.getPanelAudioUrl(moduleId, panelId, audioType);
    const response = await fetch(url, { method: 'HEAD' });
    return response.ok;
  } catch (error) {
    return false;
  }
},

  /**
   * Preload audio for multiple texts
   * Useful for preloading all panel audio
   */
  preloadAudio: async (textArray, voiceType = 'modern') => {
    console.log(`🔄 Preloading ${textArray.length} audio files...`);
    
    const promises = textArray.map(text => 
      moduleAPI.generateAudio(text, voiceType, 'medium', 'medium', false, true)
        .catch(error => {
          console.error('Failed to preload audio:', error);
          return null;
        })
    );
    
    const results = await Promise.all(promises);
    const successful = results.filter(r => r !== null).length;
    
    console.log(`✅ Preloaded ${successful}/${textArray.length} audio files`);
    return results;
  },

  /**
   * Clear audio cache
   */
  clearAudioCache: () => {
    // Revoke all blob URLs to free memory
    audioCache.forEach(url => URL.revokeObjectURL(url));
    audioCache.clear();
    console.log('🗑️ Audio cache cleared');
  },

  /**
   * Get cache statistics
   */
  getAudioCacheStats: () => {
    return {
      size: audioCache.size,
      maxSize: MAX_CACHE_SIZE,
      entries: Array.from(audioCache.keys()).map(key => ({
        key: key.substring(0, 50) + '...',
        cached: true
      }))
    };
  },

  listModules: async (limit = 50) => {
    console.log('📚 Listing modules...');
    const response = await api.get('/api/modules', {
      params: { limit }
    });
    console.log('✅ Modules received:', response.data);
    return response.data;
  },

  getModule: async (moduleId) => {
    console.log('📖 Getting module:', moduleId);
    const response = await api.get(`/api/modules/${moduleId}`);
    console.log('✅ Module received:', response.data);
    return response.data;
  },

  deleteModule: async (moduleId) => {
    const response = await api.delete(`/api/modules/${moduleId}`);
    return response.data;
  },

   /**
   * Get all exercises for a module (for editing)
   */
  getModuleExercises: async (moduleId) => {
    console.log(`📝 Fetching exercises for module ${moduleId}...`);
    const response = await api.get(`/api/modules/${moduleId}/exercises`);
    console.log('✅ Exercises received:', response.data);
    return response.data;
  },
  
  /**
   * Update an existing exercise
   */
  updateExercise: async (exerciseId, exerciseData) => {
    console.log(`✏️ Updating exercise ${exerciseId}...`, exerciseData);
    const response = await api.put(`/api/modules/exercises/${exerciseId}`, exerciseData);
    console.log('✅ Exercise updated:', response.data);
    return response.data;
  },
  
  /**
   * Add a new exercise to a module
   */
  addExercise: async (moduleId, exerciseData) => {
    console.log(`➕ Adding exercise to module ${moduleId}...`, exerciseData);
    const response = await api.post(`/api/modules/${moduleId}/exercises`, exerciseData);
    console.log('✅ Exercise added:', response.data);
    return response.data;
  },
  
  /**
   * Delete an exercise (only if no students attempted it)
   */
  deleteExercise: async (exerciseId) => {
    console.log(`🗑️ Deleting exercise ${exerciseId}...`);
    const response = await api.delete(`/api/modules/exercises/${exerciseId}`);
    console.log('✅ Exercise deleted:', response.data);
    return response.data;
  }
  
};


export const userAPI = {
  listUsers: async (params = {}) => {
    console.log('👥 Fetching users...', params);
    const response = await api.get('/api/users/list', { params });
    console.log('✅ Users received:', response.data);
    return response.data;
  },

  getUserDetail: async (userId) => {
    console.log(`👤 Fetching user ${userId} details...`);
    const response = await api.get(`/api/users/${userId}`);
    console.log('✅ User detail received:', response.data);
    return response.data;
  },

  // ✅ NEW METHOD 1
  getUser: async (userId) => {
    console.log(`👤 Fetching user ${userId}...`);
    const response = await api.get(`/api/users/${userId}`);
    console.log('✅ User received:', response.data);
    return response.data;
  },

  updateUser: async (userId, updateData) => {
    console.log(`✏️ Updating user ${userId}...`, updateData);
    const response = await api.put(`/api/users/${userId}`, updateData);
    console.log('✅ User updated:', response.data);
    return response.data;
  },

  toggleUserStatus: async (userId) => {
    console.log(`🔄 Toggling status for user ${userId}...`);
    const response = await api.post(`/api/users/${userId}/toggle-status`);
    console.log('✅ User status toggled:', response.data);
    return response.data;
  },

  deleteUser: async (userId) => {
    console.log(`🗑️ Deleting user ${userId}...`);
    const response = await api.delete(`/api/users/${userId}`);
    console.log('✅ User deleted:', response.data);
    return response.data;
  },

  getUserStatistics: async () => {
    console.log('📊 Fetching user statistics...');
    const response = await api.get('/api/users/statistics/overview');
    console.log('✅ Statistics received:', response.data);
    return response.data;
  },

  resetUserProgress: async (userId) => {
    console.log(`🔄 Resetting progress for user ${userId}...`);
    const response = await api.post(`/api/users/${userId}/reset-progress`);
    console.log('✅ Progress reset:', response.data);
    return response.data;
  },

  // ✅ NEW METHOD 2
  getUserProgress: async (userId) => {
    console.log(`📊 Fetching progress for user ${userId}...`);
    const response = await api.get(`/api/users/${userId}/progress`);
    console.log('✅ Progress received:', response.data);
    return response.data;
  }
};



export const trainingAPI = {
  getTopics: async () => {
    console.log('🎯 Fetching topics...');
    const response = await api.get('/api/training/topics');
    console.log('📚 Topics received:', response.data);
    return response.data;
  },

  generateExercises: async (trainingRequest) => {
    console.log('🎓 Generating exercises...', trainingRequest);
    const response = await api.post('/api/training/generate-exercises', trainingRequest);
    console.log('✏️ Exercises generated:', response.data);
    return response.data;
  },

  saveAllResults: async (
    classicText, 
    modernText, 
    comicScript, 
    panels, 
    exercises, 
    userAnswers, 
    score, 
    panelImages, 
    panelAudios = []
  ) => {
    console.log('💾 Saving results...', { 
      score, 
      answers: userAnswers.length,
      images: panelImages.length,
      audios: panelAudios.length
    });
    const response = await api.post('/api/training/save-all-results', {
      classic_text: classicText,
      modern_text: modernText,
      comic_script: comicScript,
      panels: panels,
      exercises: exercises,
      user_answers: userAnswers,
      score: score,
      panel_images: panelImages,
      panel_audios: panelAudios
    });
    console.log('✅ Results saved:', response.data);
    return response.data;
  },

  // ✅ ADD THIS - TEACHER: Save module + exercises only
  saveModuleWithExercises: async (
    moduleName,
    classicText,
    modernText,
    comicScript,
    panels,
    exercises,
    base64Images,
    panelAudios = []
  ) => {
    console.log('💾 Saving module + exercises (teacher)...', {
      panels: panels.length,
      exercises: exercises.length,
      images: base64Images.length,
      audios: panelAudios.length
    });
    const response = await api.post('/api/training/save-module-exercises', {
      module_name: moduleName,
      classic_text: classicText,
      modern_text: modernText,
      comic_script: comicScript,
      panels: panels,
      exercises: exercises,
      panel_images: base64Images,
      panel_audios: panelAudios
    });
    console.log('✅ Module + exercises saved:', response.data);
    return response.data;
  },

  // ✅ ADD THIS - STUDENT: Save answers to existing module
  saveStudentAnswers: async (moduleId, userAnswers, totalScore) => {
    console.log('💾 Saving student answers...', {
      module_id: moduleId,
      answers: userAnswers.length,
      score: totalScore
    });
    const response = await api.post('/api/training/save-student-answers', {
      module_id: moduleId,
      user_answers: userAnswers,
      total_score: totalScore
    });
    console.log('✅ Student answers saved:', response.data);
    return response.data;
  },

  createModule: async (moduleData) => {
    console.log('📦 Creating module...', moduleData);
    const response = await api.post('/api/training/create-module', moduleData);
    console.log('✅ Module created:', response.data);
    return response.data;
  },

  getMyModules: async () => {
    console.log('📚 Fetching my modules...');
    const response = await api.get('/api/training/my-modules');
    console.log('✅ Modules received:', response.data);
    return response.data;
  },

  getStudentProgressOverview: async () => {
    console.log('👥 Fetching student progress...');
    const response = await api.get('/api/training/student-progress-overview');
    console.log('✅ Student progress received:', response.data);
    return response.data;
  },

  getStudentDetail: async (studentId) => {
    console.log(`👤 Fetching detail for student ${studentId}...`);
    const response = await api.get(`/api/training/student-detail/${studentId}`);
    console.log('✅ Student detail received:', response.data);
    return response.data;
  },

  getMyProgress: async () => {
    console.log('📊 Fetching my progress...');
    const response = await api.get('/api/training/progress');
    console.log('✅ Progress received:', response.data);
    return response.data;
  },

  /**
   * Get all available modules for student
   */
  getAvailableModules: async () => {
    console.log('📚 Fetching available modules...');
    const response = await api.get('/api/training/modules');
    console.log('✅ Modules received:', response.data);
    return response.data;
  },

  /**
   * Get module detail with exercises
   */
  getModuleDetail: async (moduleId) => {
    console.log(`📖 Fetching module ${moduleId}...`);
    const response = await api.get(`/api/training/modules/${moduleId}`);
    console.log('✅ Module detail received:', response.data);
    return response.data;
  },

  saveStudentAnswers: async (moduleId, userAnswers, score) => {
    console.log('💾 Saving student answers...');
    const response = await api.post('/api/training/save-student-answers', {
      module_id: moduleId,
      user_answers: userAnswers,
      score: score
    });
    console.log('✅ Student answers saved:', response.data);
    return response.data;
  },


  getLeaderboard: async (limit = 10, timePeriod = 'all_time') => {
    console.log(`🏆 Fetching leaderboard (limit: ${limit}, period: ${timePeriod})...`);
    try {
      const response = await api.get('/api/leaderboard/', {
        params: { 
          limit: limit,
          timeframe: timePeriod
        }
      });
      console.log('✅ Leaderboard received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch leaderboard:', error);
      throw error;
    }
  }
  
};

export const reportAPI = {
  /**
   * Get available report types
   */
  getReportTypes: async () => {
    console.log('📊 Fetching report types...');
    const response = await api.get('/api/reports/types');
    console.log('✅ Report types received:', response.data);
    return response.data;
  },

  /**
   * Get report preview data
   */
  getReportPreview: async (reportType, filters = {}) => {
    console.log(`🔍 Getting preview for ${reportType}...`);
    
    try {
      const response = await api.get(`/api/reports/preview/${reportType}`, {
        params: filters
      });
      console.log('✅ Preview data received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to get preview:', error);
      throw error;
    }
  },

  /**
 * Generate and download report
 *
 * @param {string} reportType - Type of report (student_progress, class_overview, etc)
 * @param {string} format - Output format (pdf, excel, json)
 * @param {object} filters - Report filters (student_id, date_from, date_to, etc)
 */
generateReport: async (reportType, format = 'pdf', filters = {}) => {
  console.log(`📄 Generating ${reportType} report in ${format} format...`);
  console.log('   Filters:', filters);

  try {
    const endpoint = `/api/reports/generate/${reportType}`;
    
    // Build query params
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);
    
    // Add all filters
    if (filters.student_id) queryParams.append('student_id', filters.student_id);
    if (filters.module_id) queryParams.append('module_id', filters.module_id);
    if (filters.date_from) queryParams.append('date_from', filters.date_from);
    if (filters.date_to) queryParams.append('date_to', filters.date_to);
    if (filters.comparison_type) queryParams.append('comparison_type', filters.comparison_type);
    if (filters.week_offset !== undefined) queryParams.append('week_offset', filters.week_offset);
    if (filters.start_date) queryParams.append('start_date', filters.start_date);
    if (filters.end_date) queryParams.append('end_date', filters.end_date);
    if (filters.week_start) queryParams.append('week_start', filters.week_start);
    
    const fullUrl = `${endpoint}?${queryParams.toString()}`;
    console.log('🚀 Full URL:', fullUrl);

    // POST with blob response
    const response = await api.post(
      fullUrl,
      {},
      { responseType: 'blob' }
    );

    // ✅ FIX: Check if response is actually JSON error (even with 200 status)
    const contentType = response.headers['content-type'];
    console.log('Response content-type:', contentType);
    
    if (contentType && contentType.includes('application/json')) {
      // This is an error response disguised as success
      const text = await response.data.text();
      console.log('JSON response text:', text);
      
      try {
        const errorData = JSON.parse(text);
        if (errorData.detail || errorData.error || errorData.message) {
          throw new Error(errorData.detail || errorData.error || errorData.message || 'Server error');
        }
      } catch (parseError) {
        console.error('Failed to parse error response:', parseError);
        throw new Error('Server returned invalid response');
      }
    }

    // ✅ Valid file response - trigger download
    const blob = response.data;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;

    // Get filename from Content-Disposition header or generate one
    let filename;
    const disposition = response.headers['content-disposition'];
    if (disposition && disposition.includes('filename=')) {
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
      if (matches != null && matches[1]) {
        filename = matches[1].replace(/['"]/g, '');
      }
    }
    
    // Fallback filename
    if (!filename) {
      const timestamp = new Date().toISOString().split('T')[0];
      const extension = format === 'pdf' ? 'pdf' : format === 'excel' ? 'xlsx' : 'json';
      filename = `${reportType}_${timestamp}.${extension}`;
    }
    
    link.download = filename;

    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    console.log(`✅ Report downloaded: ${filename}`);
    return { 
      success: true, 
      message: 'Report downloaded successfully',
      filename: filename
    };

  } catch (error) {
    console.error('❌ Failed to generate report:', error);
    
    // Try to extract error from blob response
    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text();
        const errorData = JSON.parse(text);
        const errorMsg = errorData.detail || errorData.error || errorData.message || 'Server error';
        throw new Error(errorMsg);
      } catch (e) {
        // If can't parse, use original error
        console.error('Could not parse error blob:', e);
      }
    }
    
    throw error;
  }
},

  /**
   * Get list of scheduled reports
   */
  getScheduledReports: async () => {
    console.log('📅 Fetching scheduled reports...');
    const response = await api.get('/api/reports/scheduled');
    console.log('✅ Scheduled reports received:', response.data);
    return response.data;
  },

  /**
   * Schedule a report for automatic generation
   */
  scheduleReport: async (reportType, schedule, recipients, parameters = {}) => {
    console.log(`📅 Scheduling ${reportType} report...`);
    
    const response = await api.post('/api/reports/schedule', {
      report_type: reportType,
      schedule,
      recipients,
      parameters
    });
    
    console.log('✅ Report scheduled:', response.data);
    return response.data;
  },

  /**
   * Generate student progress report
   */
  generateStudentProgressReport: async (studentId, format = 'pdf') => {
    return reportAPI.generateReport('student_progress', format, { student_id: studentId });
  },

  /**
   * Generate class overview report
   */
  generateClassOverviewReport: async (format = 'pdf') => {
    return reportAPI.generateReport('class_overview', format);
  },

  /**
   * Generate module performance report
   */
  generateModulePerformanceReport: async (moduleId = null, format = 'pdf') => {
    const filters = moduleId ? { module_id: moduleId } : {};
    return reportAPI.generateReport('module_performance', format, filters);
  },

  /**
   * Generate exercise analysis report
   */
  generateExerciseAnalysisReport: async (format = 'pdf') => {
    return reportAPI.generateReport('exercise_analysis', format);
  },

  /**
   * Generate engagement metrics report
   */
  generateEngagementReport: async (dateFrom, dateTo, format = 'pdf') => {
    const filters = {};
    if (dateFrom) filters.date_from = dateFrom;
    if (dateTo) filters.date_to = dateTo;
    return reportAPI.generateReport('engagement_metrics', format, filters);
  }
};

export const progressAPI = {
  async getMyProgress() {
    const response = await api.get('/api/progress/my-progress');
    return response.data;
  },
  
  async getLeaderboard(limit = 10) {
    // ✅ CORRECT: Parentheses with template literal
    const response = await api.get(`/api/progress/leaderboard?limit=${limit}`);
    return response.data;
  },
  
  async getAllStudentProgress() {
    const response = await api.get('/api/progress/all-students');
    return response.data;
  },
  
  async getStudentDetails(userId) {
    // ✅ CORRECT: Parentheses with template literal
    const response = await api.get(`/api/progress/student/${userId}/details`);
    return response.data;
  },
  
  async getModuleDetail(moduleId) {
    // ✅ CORRECT: Parentheses with template literal
    const response = await api.get(`/api/progress/module/${moduleId}/detail`);
    return response.data;
  }
};

// Export all APIs
export { api };

export default api;