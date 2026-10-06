import { LucideIcon } from 'lucide-react';
import { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

interface BaseInputProps {
  label: string;
  icon?: LucideIcon;
  error?: string;
}

interface TextInputProps extends BaseInputProps, InputHTMLAttributes<HTMLInputElement> {
  type?: 'text' | 'number' | 'email' | 'password';
}

interface SelectInputProps extends BaseInputProps, SelectHTMLAttributes<HTMLSelectElement> {
  options: { value: string; label: string }[];
}

interface TextAreaInputProps extends BaseInputProps, TextareaHTMLAttributes<HTMLTextAreaElement> {}

export function TextInput({ label, icon: Icon, error, className = '', ...props }: TextInputProps) {
  return (
    <div>
      <label className="flex items-center gap-2 font-semibold mb-3 text-gray-900">
        {Icon && <Icon className="w-4 h-4 text-blue-500" />}
        {label}
      </label>
      <input
        className={`w-full px-4 py-3 rounded-xl border-2 ${
          error ? 'border-red-500' : 'border-gray-200'
        } focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all bg-white ${className}`}
        {...props}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
}

export function SelectInput({ label, icon: Icon, options, error, className = '', ...props }: SelectInputProps) {
  return (
    <div>
      <label className="flex items-center gap-2 font-semibold mb-3 text-gray-900">
        {Icon && <Icon className="w-4 h-4 text-purple-500" />}
        {label}
      </label>
      <select
        className={`w-full px-4 py-3 rounded-xl border-2 ${
          error ? 'border-red-500' : 'border-gray-200'
        } focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none transition-all bg-white appearance-none ${className}`}
        {...props}
      >
        {options.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
}

export function TextAreaInput({ label, icon: Icon, error, className = '', ...props }: TextAreaInputProps) {
  return (
    <div>
      <label className="flex items-center gap-2 font-semibold mb-3 text-gray-900">
        {Icon && <Icon className="w-4 h-4 text-green-500" />}
        {label}
      </label>
      <textarea
        className={`w-full px-4 py-3 rounded-xl border-2 ${
          error ? 'border-red-500' : 'border-gray-200'
        } focus:border-green-500 focus:ring-2 focus:ring-green-500/20 outline-none transition-all bg-white resize-y ${className}`}
        {...props}
      />
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  );
}
