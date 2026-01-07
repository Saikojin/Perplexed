import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Crown, Check } from 'lucide-react';
import { toast } from 'sonner';
import { useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PremiumModal({ isOpen, onClose, user, setUser }) {
  const [loading, setLoading] = useState(false);

  const handleUnlock = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/premium/unlock`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        setUser({ ...user, premium: true });
        toast.success('Premium unlocked! 🎉');
        onClose();
      } else {
        toast.error('Failed to unlock premium');
      }
    } catch (error) {
      toast.error('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-gradient-to-br from-slate-900 to-blue-900 border-white/20 text-white" data-testid="premium-modal">
        <DialogHeader>
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-2xl flex items-center justify-center">
              <Crown className="w-10 h-10 text-white" />
            </div>
          </div>
          <DialogTitle className="text-3xl text-center" style={{ fontFamily: 'Space Grotesk' }}>
            Unlock Premium
          </DialogTitle>
          <DialogDescription className="text-slate-300 text-center">
            Access the hardest riddles and prove your mastery
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-6">
          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-green-400 mt-1" />
            <div>
              <h4 className="font-semibold text-white">Very Hard Difficulty</h4>
              <p className="text-sm text-slate-400">Cryptic riddles with 2 guesses</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-green-400 mt-1" />
            <div>
              <h4 className="font-semibold text-white">Insane Difficulty</h4>
              <p className="text-sm text-slate-400">Mind-bending challenges with only 1 guess</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-green-400 mt-1" />
            <div>
              <h4 className="font-semibold text-white">Exclusive Themes</h4>
              <p className="text-sm text-slate-400">Unlock Cyberpunk, Fantasy, and more</p>
            </div>
          </div>
        </div>

        <div className="bg-white/10 rounded-lg p-4 text-center mb-4">
          <div className="text-4xl font-bold text-white mb-1">$10.00</div>
          <div className="text-slate-400 text-sm">One-time payment • Lifetime access</div>
        </div>

        <Button
          data-testid="unlock-premium-button"
          onClick={handleUnlock}
          className="w-full bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white font-bold py-6 text-lg"
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Unlock Now'}
        </Button>

        <p className="text-xs text-slate-400 text-center">
          Secure payment processing
        </p>
      </DialogContent>
    </Dialog>
  );
}