import React, { useState, useEffect } from 'react';
import { getUserGallery, getCollections, createCollection, addToCollection, deleteImage } from '../../services/ImageService';
import ImageMessage from './ImageMessage';
import { useTheme } from '../../contexts/ThemeContext';

const ImageGallery = ({ className = "" }) => {
  const { isDarkMode } = useTheme();
  const [images, setImages] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterCollection, setFilterCollection] = useState('all');
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadGallery();
    loadCollections();
  }, [currentPage, sortBy, sortOrder, filterCollection]);

  const loadGallery = async () => {
    try {
      setLoading(true);
      const params = {
        page: currentPage,
        limit: 20,
        sort_by: sortBy,
        sort_order: sortOrder
      };
      
      if (filterCollection !== 'all') {
        params.collection_id = filterCollection;
      }

      const response = await getUserGallery(params.page, params.limit);
      setImages(response.images || []);
      setTotalPages(response.pagination?.pages || response.total_pages || 1);
      setStats(response.stats);
    } catch (error) {
      setError('Failed to load gallery');
      console.error('Gallery load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCollections = async () => {
    try {
      const response = await getCollections();
      setCollections(response.collections || []);
    } catch (error) {
      console.error('Collections load error:', error);
    }
  };

  const handleImageClick = (image) => {
    setSelectedImage(image);
  };

  const handleDeleteImage = async (imageId) => {
    if (!window.confirm('Are you sure you want to delete this image?')) {
      return;
    }

    try {
      await deleteImage(imageId);
      setImages(images.filter(img => img.id !== imageId));
      if (selectedImage && selectedImage.id === imageId) {
        setSelectedImage(null);
      }
    } catch (error) {
      alert('Failed to delete image');
      console.error('Delete error:', error);
    }
  };

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) return;

    try {
      await createCollection(newCollectionName.trim());
      setNewCollectionName('');
      setShowCollectionModal(false);
      loadCollections();
    } catch (error) {
      alert('Failed to create collection');
      console.error('Collection creation error:', error);
    }
  };

  const handleAddToCollection = async (collectionId, imageId) => {
    try {
      await addToCollection(collectionId, imageId);
      alert('Image added to collection');
    } catch (error) {
      alert('Failed to add image to collection');
      console.error('Add to collection error:', error);
    }
  };

  const renderImageGrid = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {images.map((image) => (
        <div key={image.id} className="relative group">
          <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
            {(image.image_base64 || image.image_data) ? (
              <img
                src={`data:image/png;base64,${image.image_base64 || image.image_data}`}
                alt={image.revised_prompt || image.prompt}
                className="w-full h-full object-cover cursor-pointer hover:scale-105 transition-transform duration-200"
                onClick={() => handleImageClick(image)}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <svg className="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            )}
          </div>
          
          {/* Image Actions Overlay */}
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div className="flex gap-2">
              <button
                onClick={() => handleImageClick(image)}
                className="bg-white text-gray-800 p-2 rounded-full hover:bg-gray-100 transition-colors"
                title="View Image"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              
              <button
                onClick={() => handleDeleteImage(image.id)}
                className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                title="Delete Image"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
          
          {/* Image Info */}
          <div className="mt-2">
            <p className={`text-sm truncate ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`} title={image.prompt || image.original_prompt}>
              {image.prompt || image.original_prompt}
            </p>
            <div className="flex items-center justify-between mt-1">
              <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {new Date(image.created_at).toLocaleDateString()}
              </span>
              <span className={`text-xs ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {image.size}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderImageList = () => (
    <div className="space-y-4">
      {images.map((image) => (
        <div key={image.id} className={`rounded-lg border p-4 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <ImageMessage
            image={image}
            showMetadata={true}
            onImageClick={handleImageClick}
            className="border-0"
          />
          <div className="flex justify-end gap-2 mt-3">
            <select
              onChange={(e) => e.target.value && handleAddToCollection(e.target.value, image.id)}
              className={`text-sm border rounded px-2 py-1 ${isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-200' : 'bg-white border-gray-300 text-gray-900'}`}
              defaultValue=""
            >
              <option value="">Add to Collection...</option>
              {collections.map((collection) => (
                <option key={collection.id} value={collection.id}>
                  {collection.name}
                </option>
              ))}
            </select>
            
            <button
              onClick={() => handleDeleteImage(image.id)}
              className="text-sm text-red-600 hover:text-red-800 px-2 py-1"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className={`image-gallery ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-2xl font-bold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Image Gallery</h2>
          <button
            onClick={() => setShowCollectionModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            + New Collection
          </button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <div className="text-2xl font-bold text-blue-600">{stats.total_images}</div>
              <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Images</div>
            </div>
            <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <div className="text-2xl font-bold text-green-600">${stats.total_cost?.toFixed(2) || '0.00'}</div>
              <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Total Cost</div>
            </div>
            <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <div className="text-2xl font-bold text-purple-600">{stats.collections_count || 0}</div>
              <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Collections</div>
            </div>
            <div className={`p-3 rounded-lg border ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <div className="text-2xl font-bold text-orange-600">{stats.avg_generation_time?.toFixed(1) || '0.0'}s</div>
              <div className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Avg Time</div>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4">
          {/* View Mode */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
          </div>

          {/* Sort Controls */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className={`border rounded px-3 py-1 text-sm ${isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-200' : 'bg-white border-gray-300 text-gray-900'}`}
          >
            <option value="created_at">Date Created</option>
            <option value="generation_cost">Cost</option>
            <option value="generation_time">Generation Time</option>
          </select>

          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value)}
            className={`border rounded px-3 py-1 text-sm ${isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-200' : 'bg-white border-gray-300 text-gray-900'}`}
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>

          {/* Collection Filter */}
          <select
            value={filterCollection}
            onChange={(e) => setFilterCollection(e.target.value)}
            className={`border rounded px-3 py-1 text-sm ${isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-200' : 'bg-white border-gray-300 text-gray-900'}`}
          >
            <option value="all">All Images</option>
            {collections.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name} ({collection.image_count || 0})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className={`mb-4 p-4 border rounded-lg ${isDarkMode ? 'bg-red-900/20 border-red-800' : 'bg-red-50 border-red-200'}`}>
          <p className={`${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      )}

      {/* Images Display */}
      {!loading && images.length > 0 && (
        <>
          {viewMode === 'grid' ? renderImageGrid() : renderImageList()}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className={`px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed ${
                  isDarkMode 
                    ? 'border-gray-600 text-gray-200 hover:bg-gray-700' 
                    : 'border-gray-300 text-gray-900 hover:bg-gray-50'
                }`}
              >
                Previous
              </button>
              
              <span className={`px-3 py-1 text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className={`px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed ${
                  isDarkMode 
                    ? 'border-gray-600 text-gray-200 hover:bg-gray-700' 
                    : 'border-gray-300 text-gray-900 hover:bg-gray-50'
                }`}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && images.length === 0 && (
        <div className="text-center py-12">
          <svg className={`mx-auto h-24 w-24 mb-4 ${isDarkMode ? 'text-gray-600' : 'text-gray-300'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 className={`text-lg font-medium mb-2 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>No images found</h3>
          <p className={isDarkMode ? 'text-gray-400' : 'text-gray-600'}>Generate your first image to see it here!</p>
        </div>
      )}

      {/* Image Modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`rounded-lg max-w-4xl max-h-full overflow-auto ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Image Details</h3>
                <button
                  onClick={() => setSelectedImage(null)}
                  className={`${isDarkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-700'}`}
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <ImageMessage
                image={selectedImage}
                showMetadata={true}
                className="border-0"
              />
            </div>
          </div>
        </div>
      )}

      {/* Collection Creation Modal */}
      {showCollectionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className={`rounded-lg p-6 w-full max-w-md ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <h3 className={`text-lg font-medium mb-4 ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>Create New Collection</h3>
            
            <input
              type="text"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              placeholder="Collection name..."
              className={`w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                isDarkMode 
                  ? 'bg-gray-700 border-gray-600 text-gray-100 placeholder-gray-400' 
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
              onKeyPress={(e) => e.key === 'Enter' && handleCreateCollection()}
            />
            
            <div className="flex gap-3">
              <button
                onClick={handleCreateCollection}
                disabled={!newCollectionName.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create
              </button>
              <button
                onClick={() => {
                  setShowCollectionModal(false);
                  setNewCollectionName('');
                }}
                className={`flex-1 py-2 px-4 rounded-lg ${
                  isDarkMode 
                    ? 'bg-gray-700 text-gray-200 hover:bg-gray-600' 
                    : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                }`}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageGallery;