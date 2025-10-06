import React, { useState, useEffect } from 'react';
import { generateImage, getTaskStatus } from '../../services/ImageService';

const ImageGenerator = ({ threadId, onImageGenerated, className = "" }) => {
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState('');
  const [taskId, setTaskId] = useState(null);
  
  // Advanced options
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [size, setSize] = useState('1024x1024');
  const [quality, setQuality] = useState('standard');
  const [style, setStyle] = useState('vivid');

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a description for the image');
      return;
    }

    setIsGenerating(true);
    setError('');
    setProgress(0);
    setCurrentStep('Starting image generation...');

    try {
      const task = await generateImage({
        prompt: prompt.trim(),
        size,
        quality,
        style,
        thread_id: threadId
      });

      setTaskId(task.task_id);
      
      // Poll for progress updates
      const pollProgress = setInterval(async () => {
        try {
          const status = await getTaskStatus(task.task_id);
          
          setProgress(status.progress || 0);
          setCurrentStep(status.current_step || 'Processing...');
          
          if (status.status === 'completed') {
            clearInterval(pollProgress);
            setIsGenerating(false);
            setProgress(100);
            setCurrentStep('Image generated successfully!');
            
            if (onImageGenerated && status.image_data) {
              onImageGenerated({
                ...status.image_data,
                task_id: task.task_id
              });
            }
            
            // Clear the form
            setPrompt('');
            setTaskId(null);
          } else if (status.status === 'failed') {
            clearInterval(pollProgress);
            setIsGenerating(false);
            setError(status.error || 'Image generation failed');
            setTaskId(null);
          }
        } catch (err) {
          console.error('Error checking task status:', err);
        }
      }, 1000);

      // Cleanup interval after 5 minutes
      setTimeout(() => {
        clearInterval(pollProgress);
        if (isGenerating) {
          setIsGenerating(false);
          setError('Generation timed out');
        }
      }, 300000);
      
    } catch (error) {
      setIsGenerating(false);
      setError(error.message || 'Failed to start image generation');
      console.error('Image generation failed:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className={`image-generator bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          🎨 Image Description
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe the image you want to generate... (e.g., 'A sunset over mountains with a lake reflection')"
          className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={3}
          disabled={isGenerating}
          maxLength={1000}
        />
        <div className="text-xs text-gray-500 mt-1">
          {prompt.length}/1000 characters
        </div>
      </div>

      {/* Advanced Options */}
      <div className="mb-4">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-blue-600 hover:text-blue-800 focus:outline-none"
          disabled={isGenerating}
        >
          {showAdvanced ? '▼' : '▶'} Advanced Options
        </button>
        
        {showAdvanced && (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Size
              </label>
              <select
                value={size}
                onChange={(e) => setSize(e.target.value)}
                disabled={isGenerating}
                className="w-full p-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              >
                <option value="1024x1024">Square (1024×1024)</option>
                <option value="1792x1024">Landscape (1792×1024)</option>
                <option value="1024x1792">Portrait (1024×1792)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Quality
              </label>
              <select
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
                disabled={isGenerating}
                className="w-full p-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              >
                <option value="standard">Standard</option>
                <option value="hd">HD (Higher Cost)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Style
              </label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                disabled={isGenerating}
                className="w-full p-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              >
                <option value="vivid">Vivid</option>
                <option value="natural">Natural</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Progress Display */}
      {isGenerating && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>{currentStep}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          {taskId && (
            <div className="text-xs text-gray-500 mt-1">
              Task ID: {taskId}
            </div>
          )}
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <span className="text-red-600 text-sm">⚠️ {error}</span>
          </div>
        </div>
      )}

      {/* Generate Button */}
      <div className="flex justify-between items-center">
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className={`
            px-6 py-2 rounded-lg font-medium text-white transition-all duration-200
            ${isGenerating || !prompt.trim() 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500'
            }
          `}
        >
          {isGenerating ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating...
            </span>
          ) : (
            '🎨 Generate Image'
          )}
        </button>
        
        <div className="text-xs text-gray-500">
          ~10-30 seconds
        </div>
      </div>
    </div>
  );
};

export default ImageGenerator;