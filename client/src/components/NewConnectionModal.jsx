import React, { useContext, useState, useEffect } from 'react';
import { DBClientContext } from '../contexts/DBClientContext';

const ENGINE_DEFAULTS = {
  PostgreSQL: 5432,
  MongoDB: 27017,
  MySQL: 3306,
  Redis: 6379,
};

export function NewConnectionModal() {
  const {
    showConnectionModal,
    setShowConnectionModal,
    isLoadingConnection,
    connectionError,
    editingConnection,
    setEditingConnection,
    addConnection,
  } = useContext(DBClientContext);

  const [formData, setFormData] = useState({
    name: '',
    engine: 'PostgreSQL',
    host: 'localhost',
    port: 5432,
    username: '',
    password: '',
    database: '',
  });

  // Reset form when modal opens
  useEffect(() => {
    if (showConnectionModal) {
      if (editingConnection) {
        setFormData(editingConnection);
      } else {
        setFormData({
          name: '',
          engine: 'PostgreSQL',
          host: 'localhost',
          port: 5432,
          username: '',
          password: '',
          database: '',
        });
      }
    }
  }, [showConnectionModal, editingConnection]);

  const handleEngineChange = (e) => {
    const newEngine = e.target.value;
    const newPort = ENGINE_DEFAULTS[newEngine] || formData.port;
    setFormData({
      ...formData,
      engine: newEngine,
      port: newPort,
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'port' ? parseInt(value) || '' : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate required fields
    if (!formData.name.trim()) {
      alert('Connection name is required');
      return;
    }
    if (!formData.engine) {
      alert('Engine type is required');
      return;
    }
    if (!formData.host.trim()) {
      alert('Host is required');
      return;
    }
    if (!formData.port || formData.port <= 0) {
      alert('Valid port number is required');
      return;
    }

    // Prepare connection data for backend
    const connectionData = {
      name: formData.name,
      engine: formData.engine,
      host: formData.host,
      port: formData.port,
      username: formData.username || null,
      password: formData.password || null,
      database: formData.database || null,
    };

    await addConnection(connectionData);
  };

  const handleCancel = () => {
    setShowConnectionModal(false);
    setEditingConnection(null);
  };

  if (!showConnectionModal) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md mx-4 p-6">
        {/* Header */}
        <h2 className="text-xl font-bold text-gray-800 mb-4">
          {editingConnection ? 'Editar Conexión' : 'Nueva Conexión'}
        </h2>

        {/* Error Message */}
        {connectionError && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {connectionError}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Connection Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre de la Conexión *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Mi Base de Datos"
            />
          </div>

          {/* Engine Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de Motor *
            </label>
            <select
              name="engine"
              value={formData.engine}
              onChange={handleEngineChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="PostgreSQL">PostgreSQL</option>
              <option value="MongoDB">MongoDB</option>
              <option value="MySQL">MySQL</option>
              <option value="Redis">Redis</option>
            </select>
          </div>

          {/* Host */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Host *
            </label>
            <input
              type="text"
              name="host"
              value={formData.host}
              onChange={handleInputChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="localhost"
            />
          </div>

          {/* Port */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Puerto *
            </label>
            <input
              type="number"
              name="port"
              value={formData.port}
              onChange={handleInputChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="5432"
            />
          </div>

          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Usuario
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="postgres"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="••••••••"
            />
          </div>

          {/* Database */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Base de Datos
            </label>
            <input
              type="text"
              name="database"
              value={formData.database}
              onChange={handleInputChange}
              disabled={isLoadingConnection}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="postgres"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={isLoadingConnection}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md font-medium hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
            >
              {isLoadingConnection ? 'Conectando...' : 'Conectar'}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={isLoadingConnection}
              className="flex-1 bg-gray-300 text-gray-800 py-2 px-4 rounded-md font-medium hover:bg-gray-400 disabled:bg-gray-200 disabled:cursor-not-allowed transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
