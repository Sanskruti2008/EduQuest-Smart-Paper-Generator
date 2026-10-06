import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  hover?: boolean;
}

export function PremiumCard({ children, className = '', delay = 0, hover = true }: PremiumCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`relative overflow-hidden rounded-2xl border border-gray-200 bg-white/90 backdrop-blur-xl shadow-xl p-8 ${
        hover ? 'hover:shadow-2xl transition-shadow duration-300' : ''
      } ${className}`}
    >
      {children}
    </motion.div>
  );
}
