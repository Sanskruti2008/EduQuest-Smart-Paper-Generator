import { motion } from 'framer-motion';
import { CheckCircle2, LucideIcon } from 'lucide-react';

interface FormatCardProps {
  id: string;
  icon: LucideIcon;
  iconColor: string;
  title: string;
  description: string;
  features: string[];
  gradient: string;
  borderGradient: string;
  isSelected: boolean;
  onSelect: (id: string) => void;
  delay?: number;
}

export function FormatCard({
  id,
  icon: Icon,
  iconColor,
  title,
  description,
  features,
  gradient,
  borderGradient,
  isSelected,
  onSelect,
  delay = 0
}: FormatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      onClick={() => onSelect(id)}
      className={`group relative overflow-hidden rounded-2xl border-2 transition-all duration-300 cursor-pointer
        ${isSelected 
          ? 'border-transparent shadow-2xl shadow-blue-500/20 scale-[1.02]' 
          : 'border-gray-200 hover:border-gray-300 hover:shadow-xl'
        }`}
    >
      {/* Gradient Background */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-50`} />
      
      {/* Selected Border Gradient */}
      {isSelected && (
        <div className={`absolute inset-0 bg-gradient-to-r ${borderGradient} opacity-20`} />
      )}
      
      {/* Content */}
      <div className="relative bg-white/90 backdrop-blur-xl p-6">
        <div className="flex items-start gap-4 mb-4">
          <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br ${gradient}`}>
            <Icon className={`w-6 h-6 ${iconColor}`} />
          </div>
          
          {isSelected && (
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
            >
              <CheckCircle2 className="w-6 h-6 text-green-500 fill-green-50" />
            </motion.div>
          )}
        </div>
        
        <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 mb-4">{description}</p>
        
        <ul className="space-y-2">
          {features.map((feature, idx) => (
            <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
              <span>{feature}</span>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
