import { Database } from 'lucide-react';

export function Header() {
  return (
    <header className="border-b bg-white">
      <div className="flex h-16 items-center px-6">
        <div className="flex items-center gap-2">
          <Database className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900">SLDCE</h1>
        </div>
        <p className="ml-4 text-sm text-gray-500">
          Self-Learning Data Correction Engine
        </p>
      </div>
    </header>
  );
}