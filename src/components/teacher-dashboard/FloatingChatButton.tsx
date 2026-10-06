import { MessageCircle } from 'lucide-react';

export default function FloatingChatButton() {
  return (
    <button className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-xl flex items-center justify-center">
      <MessageCircle className="h-6 w-6" />
    </button>
  );
}
