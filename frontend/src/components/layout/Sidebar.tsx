import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Database, 
  FileCheck, 
  Settings, 
  BarChart3, 
  Award,
  FlaskConical,
  CheckSquare,
  History
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Home', href: '/', icon: Home },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Models', href: '/models', icon: Award },
  { name: 'Experiments', href: '/experiments', icon: FlaskConical },
  { name: 'Detection', href: '/detection', icon: FileCheck },
  { name: 'Correction', href: '/correction', icon: CheckSquare },
  { name: 'Feedback', href: '/feedback', icon: History }, // NEW
  { name: 'Evaluation', href: '/evaluation', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 border-r bg-gray-50">
      <nav className="flex flex-col gap-1 p-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}