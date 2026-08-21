/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export default function App() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 font-sans">
      <div className="bg-white p-8 rounded-xl shadow-lg text-center max-w-md w-full">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">🤖 Telegram Bot is Running</h1>
        <p className="text-gray-600 mb-6">
          The bot backend has been started automatically. You can interact with your bot on Telegram.
        </p>
        <div className="inline-flex items-center justify-center p-3 bg-blue-50 rounded-full">
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-ping absolute"></div>
          <div className="w-3 h-3 bg-blue-600 rounded-full relative z-10"></div>
          <span className="ml-3 text-blue-700 font-medium text-sm">Status: Active</span>
        </div>
      </div>
    </div>
  );
}
