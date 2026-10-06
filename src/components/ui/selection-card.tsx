import { motion } from 'framer-motion';
import { CheckCircle2, LucideIcon } from 'lucide-react';
import { ReactNode } from 'react';

interface SelectionCardProps {
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
  badge?: ReactNode;
}

export function SelectionCard({
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
  delay = 0,
  badge
}: SelectionCardProps) {
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
      
      {/* Glass Effect */}
      <div className="relative bg-white/90 backdrop-blur-xl p-8">
        {/* Icon */}
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br ${gradient} mb-6 transform transition-transform group-hover:scale-110`}>
          <Icon className={`w-8 h-8 ${iconColor}`} />
        </div>

        {/* Selected Indicator */}
        {isSelected && (
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute top-6 right-6"
          >
            <CheckCircle2 className="w-8 h-8 text-green-500 fill-green-50" />
          </motion.div>
        )}

        {/* Title & Description */}
        <h2 className="text-2xl font-bold mb-3 text-gray-900">{title}</h2>
        <p className="text-gray-600 mb-6 leading-relaxed">{description}</p>
        
        {/* Features */}
        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-blue-500" />
            Key Features
          </h4>
          <ul className="space-y-3">
            {features.map((feature, idx) => (
              <motion.li 
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: delay + idx * 0.05 }}
                className="flex items-start gap-3 text-gray-600"
              >
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span>{feature}</span>
              </motion.li>
            ))}
          </ul>
        </div>

        {/* Badge */}
        {badge && <div className="mt-4">{badge}</div>}
      </div>
    </motion.div>
  );
}
