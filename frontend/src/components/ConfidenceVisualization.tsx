interface ConfidenceVisualizationProps {
  value: number;
  label: string;
  color?: 'blue' | 'green' | 'orange' | 'red' | 'purple';
  size?: 'sm' | 'md' | 'lg';
}

export function ConfidenceVisualization({
  value,
  label,
  color = 'blue',
  size = 'md',
}: ConfidenceVisualizationProps) {
  const percentage = value * 100;

  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    orange: 'bg-orange-600',
    red: 'bg-red-600',
    purple: 'bg-purple-600',
  };

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  const widthClasses = {
    sm: 'w-20',
    md: 'w-32',
    lg: 'w-48',
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`${widthClasses[size]} bg-gray-200 rounded-full ${sizeClasses[size]}`}>
        <div
          className={`${colorClasses[color]} ${sizeClasses[size]} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={`${size === 'sm' ? 'text-xs' : 'text-sm'} font-semibold`}>
        {percentage.toFixed(1)}%
      </span>
    </div>
  );
}