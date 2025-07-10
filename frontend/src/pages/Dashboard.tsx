import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Dashboard content will go here */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-2">Welcome to Mobius</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Your Context Engineering Platform
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;