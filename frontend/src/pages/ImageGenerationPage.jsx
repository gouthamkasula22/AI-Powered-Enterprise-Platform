import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ImageGenerator from '../components/image/ImageGenerator';
import ImageMessage from '../components/image/ImageMessage';
import DashboardLayout from '../components/layout/DashboardLayout';

const ImageGenerationPage = () => {
  const { user } = useAuth();
  const [recentImages, setRecentImages] = useState([]);

  const handleImageGenerated = (imageData) => {
    setRecentImages(prev => [imageData, ...prev.slice(0, 4)]); // Keep only 5 most recent
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Image Generation</h1>
          <p className="mt-2 text-gray-600">
            Create stunning images with DALL-E 3. Describe what you want to see and let AI bring it to life.
          </p>
        </div>

        {/* Image Generator */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <ImageGenerator 
            onImageGenerated={handleImageGenerated}
            className="shadow-sm"
          />
        </div>

        {/* Usage Tips */}
        <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-3">💡 Tips for Better Images</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <h4 className="font-medium mb-2">Be Descriptive</h4>
              <ul className="space-y-1 text-blue-700">
                <li>• Include details about style, colors, lighting</li>
                <li>• Mention specific objects, people, or scenes</li>
                <li>• Add context about mood or atmosphere</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">Use Keywords</h4>
              <ul className="space-y-1 text-blue-700">
                <li>• "photorealistic", "oil painting", "digital art"</li>
                <li>• "cinematic lighting", "golden hour", "dramatic"</li>
                <li>• "high resolution", "detailed", "masterpiece"</li>
              </ul>
            </div>
          </div>
          <div className="mt-4 p-3 bg-white rounded border">
            <strong className="text-blue-900">Example:</strong>
            <span className="text-blue-800 italic">
              "A majestic snow-covered mountain peak at sunset, with golden light reflecting on the snow, photorealistic style, cinematic composition"
            </span>
          </div>
        </div>

        {/* Recent Images */}
        {recentImages.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Generations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {recentImages.map((image, index) => (
                <ImageMessage
                  key={`${image.id}-${index}`}
                  image={image}
                  showMetadata={true}
                  className="shadow-sm"
                />
              ))}
            </div>
          </div>
        )}

        {/* Getting Started */}
        {recentImages.length === 0 && (
          <div className="text-center py-12">
            <svg className="mx-auto h-24 w-24 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Create?</h3>
            <p className="text-gray-600">
              Describe your vision in the generator above and watch AI create amazing images for you!
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ImageGenerationPage;