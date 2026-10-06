import { Link } from 'react-router-dom';

interface HeaderProps {
  title?: string;
  showActions?: boolean;
  actions?: React.ReactNode;
}

const Header = ({ title = 'AI-Powered Question Paper Generator', showActions = false, actions = null }: HeaderProps) => {
  return (
    <header className="bg-white/95 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <div className="flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3 no-underline group">
            <div className="text-3xl transition-transform group-hover:scale-105">📚 EduQuest.ai</div>
            <div>
              <h2 className="text-xl font-bold m-0 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent tracking-tight">EduQuest.ai</h2>
              <p className="text-xs text-gray-500 m-0 font-medium">{title}</p>
            </div>
          </Link>
          
          {showActions && (
            <div className="flex gap-3">
              {actions}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
