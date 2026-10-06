import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  step?: number;
  totalSteps?: number;
  icon?: LucideIcon;
  title: string;
  description: string;
  badge?: string;
}

export function PageHeader({ step, totalSteps, icon: Icon, title, description, badge }: PageHeaderProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center mb-12 mt-8"
    >
      {(step || Icon || badge) && (
        <motion.div 
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 mb-6"
        >
          {Icon && <Icon className="w-4 h-4 text-blue-500" />}
          {step && totalSteps && (
            <span className="text-sm font-medium text-gray-700">
              Step {step} of {totalSteps}
            </span>
          )}
          {badge && <span className="text-sm font-medium text-gray-700">{badge}</span>}
        </motion.div>
      )}
      
      <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 via-blue-600 to-purple-600 bg-clip-text text-transparent">
        {title}
      </h1>
      <p className="text-xl text-gray-600 max-w-2xl mx-auto">
        {description}
      </p>
    </motion.div>
  );
}
