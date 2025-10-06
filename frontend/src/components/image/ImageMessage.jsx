import React, { useState } from 'react';
import { downloadImage } from '../../services/ImageService';

const ImageMessage = ({ 
  image, 
  message, 
  showMetadata = true, 
  className = "",
  onImageClick = null 
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showFullMetadata, setShowFullMetadata] = useState(false);

  const handleDownload = async () => {
    if (!image.id) return;
    
    setIsLoading(true);
    try {
      await downloadImage(image.id, `generated-image-${image.id}.png`);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download image');
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageClick = () => {
    if (onImageClick) {
      onImageClick(image);
    }
  };

  const formatCost = (cost) => {
    return cost ? `$${cost.toFixed(4)}` : 'Free';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getQualityBadge = (quality) => {
    return quality === 'hd' ? (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
        HD
      </span>
    ) : (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        Standard
      </span>
    );
  };

  const getStyleBadge = (style) => {
    return style === 'vivid' ? (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
        Vivid
      </span>
    ) : (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Natural
      </span>
    );
  };

  return (
    <div className={`image-message bg-white rounded-lg border border-gray-200 overflow-hidden ${className}`}>
      {/* Message Text (if any) */}
      {message && (
        <div className="p-4 border-b border-gray-100">
          <p className="text-gray-800">{message}</p>
        </div>
      )}

      {/* Image Display */}
      <div className="relative">
        {image.image_data ? (
          <img
            src={`data:image/png;base64,${image.image_data}`}
            alt={image.revised_prompt || image.original_prompt || 'Generated image'}
            className={`w-full h-auto max-w-full ${onImageClick ? 'cursor-pointer hover:opacity-90' : ''}`}
            onClick={handleImageClick}
            loading="lazy"
          />
        ) : (
          <div className="w-full h-64 bg-gray-100 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <svg className="mx-auto h-12 w-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p>Image not available</p>
            </div>
          </div>
        )}

        {/* Image Actions Overlay */}
        <div className="absolute top-2 right-2 flex gap-2">
          <button
            onClick={handleDownload}
            disabled={isLoading || !image.image_data}
            className="bg-black bg-opacity-50 hover:bg-opacity-70 text-white p-2 rounded-full transition-all duration-200 disabled:opacity-50"
            title="Download Image"
          >
            {isLoading ? (
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Metadata */}
      {showMetadata && (
        <div className="p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-900">Image Details</h4>
            <button
              onClick={() => setShowFullMetadata(!showFullMetadata)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              {showFullMetadata ? 'Show Less' : 'Show More'}
            </button>
          </div>

          {/* Basic Metadata */}
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Size:</span>
              <span className="font-medium">{image.size || 'Unknown'}</span>
              {getQualityBadge(image.quality)}
              {getStyleBadge(image.style)}
            </div>

            {image.generation_cost > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Cost:</span>
                <span className="font-medium text-green-600">{formatCost(image.generation_cost)}</span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <span className="text-gray-600">Generated:</span>
              <span className="text-gray-800">{formatDate(image.created_at)}</span>
            </div>
          </div>

          {/* Full Metadata */}
          {showFullMetadata && (
            <div className="mt-4 space-y-3 text-sm border-t border-gray-200 pt-3">
              {image.original_prompt !== image.revised_prompt && image.revised_prompt && (
                <div>
                  <span className="text-gray-600 block mb-1">Revised Prompt:</span>
                  <p className="text-gray-800 bg-white p-2 rounded border text-xs">
                    {image.revised_prompt}
                  </p>
                </div>
              )}
              
              <div>
                <span className="text-gray-600 block mb-1">Original Prompt:</span>
                <p className="text-gray-800 bg-white p-2 rounded border text-xs">
                  {image.original_prompt}
                </p>
              </div>

              {image.generation_time && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">Generation Time:</span>
                  <span className="text-gray-800">{image.generation_time.toFixed(2)}s</span>
                </div>
              )}

              {image.id && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">Image ID:</span>
                  <span className="text-gray-800 font-mono text-xs">{image.id}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ImageMessage;