import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import ImageGallery from '../components/image/ImageGallery';
import DashboardLayout from '../components/layout/DashboardLayout';

const GalleryPage = () => {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gallery</h1>
          <p className="mt-2 text-gray-600">
            Browse and manage your generated images
          </p>
        </div>

        <ImageGallery />
      </div>
    </DashboardLayout>
  );
};

export default GalleryPage;