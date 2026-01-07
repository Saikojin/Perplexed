import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Brain, Trophy, LogOut, Users, Sparkles, Crown, Loader2, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import PremiumModal from '../components/PremiumModal';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function GamePage({ user, setUser }) {
  const navigate = useNavigate();
  const [selectedDifficulty, setSelectedDifficulty] = useState(null);
  const [currentRiddle, setCurrentRiddle] = useState(null);
  const [currentGuess, setCurrentGuess] = useState('');
  const [guesses, setGuesses] = useState([]);
  const [timeRemaining, setTimeRemaining] = useState(120);
  const [gameStarted, setGameStarted] = useState(false);
  const [gameWon, setGameWon] = useState(false);
  const [loading, setLoading] = useState(false);
  const [correctAnswer, setCorrectAnswer] = useState('');
  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [dailyStatus, setDailyStatus] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState('');
  const gameRef = useRef(null);

  const [showModelAlert, setShowModelAlert] = useState(false);

  useEffect(() => {
    checkModels();
  }, []);

  const checkModels = async () => {
    try {
      const res = await fetch(`${API}/models/available`);
      const models = await res.json();
      // If list is empty or only contains legacy placeholders that aren't real
      const hasRealModel = models.some(m => m.type === 'local' && m.name !== 'legacy-model');
      if (!hasRealModel) {
        setShowModelAlert(true);
      }
    } catch (e) {
      console.error("Failed to check models", e);
    }
  };

  const difficulties = [
    { id: 'easy', name: 'Easy', guesses: 5, color: 'from-green-500 to-emerald-600', premium: false },
    { id: 'medium', name: 'Medium', guesses: 4, color: 'from-yellow-500 to-amber-600', premium: false },
    { id: 'hard', name: 'Hard', guesses: 3, color: 'from-orange-500 to-red-600', premium: false },
    { id: 'very_hard', name: 'Very Hard', guesses: 2, color: 'from-red-500 to-pink-600', premium: true },
    { id: 'insane', name: 'Insane', guesses: 1, color: 'from-purple-500 to-indigo-600', premium: true }
  ];

  // Fetch daily status on mount
  useEffect(() => {
    fetchDailyStatus();
  }, []);

  const fetchDailyStatus = async () => {
    try {
      console.log('Fetching daily status...');
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/riddles/daily-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setDailyStatus(data);

      if (data.needs_generation && !loading) {
        generateDailyRiddles();
      }
    } catch (error) {
      console.error('Failed to fetch daily status:', error);
    }
  };

  const generateDailyRiddles = async () => {
    console.log('Triggering daily riddle generation...');
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API}/riddle/generate-daily`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log('Generation request sent, refreshing status...');
      // Refresh status after generation
      const res = await fetch(`${API}/riddles/daily-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setDailyStatus(data);
    } catch (error) {
      toast.error("Failed to generate today's riddles");
    } finally {
      setLoading(false);
    }
  };

  // Hidden timer - tracks time but doesn't display
  useEffect(() => {
    if (gameStarted && !gameWon && guesses.length < currentRiddle?.max_guesses && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [gameStarted, gameWon, timeRemaining, guesses.length, currentRiddle]);

  // Handle keyboard input
  useEffect(() => {
    if (!gameStarted || gameWon || guesses.length >= currentRiddle?.max_guesses) return;

    const handleKeyPress = (e) => {
      if (e.key === 'Enter') {
        submitGuess();
      } else if (e.key === 'Backspace') {
        setCurrentGuess(prev => prev.slice(0, -1));
      } else if (/^[a-zA-Z]$/.test(e.key)) {
        if (currentGuess.length < currentRiddle.answer_length) {
          setCurrentGuess(prev => prev + e.key.toUpperCase());
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [gameStarted, gameWon, currentGuess, guesses.length, currentRiddle]);

  const startGame = async (difficulty) => {
    if (difficulty.premium && !user.premium) {
      setShowPremiumModal(true);
      return;
    }

    const isStarted = dailyStatus?.status?.[difficulty.id]?.started;
    setLoadingMessage(isStarted ? "Summoning your riddle!" : "Creating unique riddle for you!");
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/riddle/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          difficulty: difficulty.id,
          theme: user?.settings?.theme || "default"
        })
      });

      const data = await res.json();

      if (res.ok) {
        setCurrentRiddle(data);
        setSelectedDifficulty(difficulty);
        setGameStarted(true);
        setGuesses([]);
        setCurrentGuess('');
        setTimeRemaining(120);
        setGameWon(false);
        setCorrectAnswer('');
      } else {
        toast.error(data.detail || 'Failed to generate riddle');
      }
    } catch (error) {
      toast.error('Network error');
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const submitGuess = async () => {
    if (currentGuess.length !== currentRiddle.answer_length) {
      toast.error('Complete the word first');
      return;
    }

    if (guesses.includes(currentGuess)) {
      toast.error('Already guessed that word');
      return;
    }

    const newGuesses = [...guesses, currentGuess];
    setGuesses(newGuesses);

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/riddle/guess`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          riddle_id: currentRiddle.riddle_id,
          guess: currentGuess,
          time_remaining: timeRemaining,
          guesses_used: newGuesses.length
        })
      });

      const data = await res.json();

      if (data.correct) {
        setGameWon(true);
        setCorrectAnswer(data.answer);
        toast.success(`Correct! +${data.score} points 🎉`);
        setUser(prev => ({ ...prev, total_score: (prev.total_score || 0) + data.score }));
      } else {
        const remaining = currentRiddle.max_guesses - newGuesses.length;
        if (remaining > 0) {
          toast.error(`Wrong! ${remaining} ${remaining === 1 ? 'guess' : 'guesses'} left`);
        } else {
          // Game over - reveal answer
          setCorrectAnswer(data.answer || 'UNKNOWN');
          toast.error('No more guesses!');
        }
      }
    } catch (error) {
      toast.error('Network error');
    } finally {
      setLoading(false);
      setCurrentGuess('');
    }
  };

  const resetGame = () => {
    setCurrentRiddle(null);
    setSelectedDifficulty(null);
    setGameStarted(false);
    setGameWon(false);
    setGuesses([]);
    setCurrentGuess('');
    setTimeRemaining(120);
    setCorrectAnswer('');
    fetchDailyStatus(); // Refresh daily status
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/auth');
  };

  const isDifficultyCompleted = (diffId) => {
    return dailyStatus?.status?.[diffId]?.completed || false;
  };

  const renderTileRow = (rowIndex) => {
    const isCurrentRow = rowIndex === guesses.length && !gameWon && guesses.length < currentRiddle.max_guesses;
    const isPastRow = rowIndex < guesses.length;
    const isAnswerRow = gameWon && rowIndex === guesses.length;
    const showAnswer = correctAnswer && rowIndex === guesses.length && !gameWon && guesses.length >= currentRiddle.max_guesses;

    let displayWord = '';
    if (isPastRow) {
      displayWord = guesses[rowIndex];
    } else if (isCurrentRow) {
      displayWord = currentGuess;
    } else if (isAnswerRow || showAnswer) {
      displayWord = correctAnswer;
    }

    const isCorrect = isPastRow && displayWord === correctAnswer;

    return (
      <div key={rowIndex} className="flex justify-center gap-2 mb-3">
        {[...Array(currentRiddle.answer_length)].map((_, letterIndex) => {
          const letter = displayWord[letterIndex] || '';
          const isEmpty = !letter;
          const isActive = isCurrentRow && letterIndex === currentGuess.length;

          let tileClass = 'letter-tile empty';
          if (letter) {
            if (isCorrect || isAnswerRow || showAnswer) {
              tileClass = 'letter-tile correct';
            } else if (isPastRow) {
              tileClass = 'letter-tile filled';
            } else if (isCurrentRow) {
              tileClass = 'letter-tile filled';
            }
          }

          return (
            <div
              key={letterIndex}
              data-testid={`letter-tile-${rowIndex}-${letterIndex}`}
              className={`${tileClass} text-white ${isActive ? 'ring-2 ring-blue-400' : ''}`}
            >
              {letter}
            </div>
          );
        })}
      </div>
    );
  };

  if (!gameStarted) {
    return (
      <div className="app-background p-4">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-8 pt-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Space Grotesk' }}>Perplexed</h1>
                <p className="text-slate-400 text-sm">Welcome, {user.username}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="glass-card px-4 py-2 flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-400" />
                <span className="text-white font-semibold" data-testid="user-total-score">{user?.total_score || 0}</span>
              </div>
              {user.premium && (
                <div className="glass-card px-4 py-2 flex items-center gap-2">
                  <Crown className="w-5 h-5 text-yellow-400" />
                  <span className="text-yellow-400 font-semibold">Premium</span>
                </div>
              )}
              <Button
                data-testid="leaderboard-nav-button"
                onClick={() => navigate('/leaderboard')}
                className="bg-white/10 hover:bg-white/20 text-white"
              >
                <Users className="w-4 h-4 mr-2" />
                Leaderboard
              </Button>
              <Button
                data-testid="settings-button"
                onClick={() => navigate('/settings')}
                className="bg-white/10 hover:bg-white/20 text-white"
              >
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
              <Button
                data-testid="logout-button"
                onClick={handleLogout}
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Difficulty Selection */}
          <div className="text-center mb-12">
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4" style={{ fontFamily: 'Space Grotesk' }}>
              Choose Your Challenge
            </h2>
            <p className="text-lg text-slate-300 mb-2">Select a difficulty level to begin</p>
            {dailyStatus && (
              <p className="text-sm text-slate-400">
                Day {dailyStatus.day} • {dailyStatus.month}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {difficulties.map((diff) => {
              const isCompleted = isDifficultyCompleted(diff.id);
              const isLocked = (diff.premium && !user.premium) || (dailyStatus?.needs_generation);

              return (
                <Card
                  key={diff.id}
                  data-testid={`difficulty-${diff.id}`}
                  className={`glass-card p-6 cursor-pointer transition-all hover:scale-105 hover:shadow-2xl relative overflow-hidden ${isLocked && !diff.premium ? 'opacity-60' : ''
                    } ${(isLocked && diff.premium && !user.premium) ? 'border border-yellow-500/30' : ''} ${isCompleted ? 'border-2 border-green-500' : ''}`}
                  onClick={() => !isCompleted && !(isLocked && !diff.premium) && startGame(diff)}
                >
                  {isLocked && diff.premium && !user.premium && (
                    <div className="absolute top-2 right-2">
                      <Crown className="w-5 h-5 text-yellow-400" />
                    </div>
                  )}

                  {isCompleted && (
                    <div className="absolute top-2 right-2">
                      <Trophy className="w-5 h-5 text-green-400" />
                    </div>
                  )}

                  <div className={`w-16 h-16 bg-gradient-to-br ${diff.color} rounded-xl flex items-center justify-center mb-4 mx-auto`}>
                    <Sparkles className="w-8 h-8 text-white" />
                  </div>

                  <h3 className="text-2xl font-bold text-white mb-2 text-center" style={{ fontFamily: 'Space Grotesk' }}>
                    {diff.name}
                  </h3>

                  <div className="flex justify-center gap-2 mb-3">
                    {[...Array(diff.guesses)].map((_, i) => (
                      <div key={i} className="w-2 h-2 bg-white/30 rounded-full" />
                    ))}
                  </div>

                  <p className="text-slate-300 text-center text-sm">
                    {diff.guesses} {diff.guesses === 1 ? 'guess' : 'guesses'}
                  </p>

                  {isLocked && diff.premium && !user.premium && (
                    <div className="mt-3 text-center">
                      <span className="text-yellow-400 text-xs font-semibold">Premium Required</span>
                    </div>
                  )}

                  {isCompleted && (
                    <div className="mt-3 text-center">
                      <span className="text-green-400 text-xs font-semibold">Completed Today! ✓</span>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>

          {/* Loading Overlay */}
          {(loading || dailyStatus?.needs_generation) && (
            <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
              <div className="bg-slate-900/90 border border-slate-700 rounded-full px-6 py-3 flex items-center gap-3 shadow-2xl backdrop-blur-sm animate-in slide-in-from-bottom-5">
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                <span className="text-slate-200 font-medium">
                  {loadingMessage || (dailyStatus?.needs_generation ? "Generating riddles for today..." : "Loading...")}
                </span>
              </div>
            </div>
          )}
        </div>

        <PremiumModal
          isOpen={showPremiumModal}
          onClose={() => setShowPremiumModal(false)}
          user={user}
          setUser={setUser}
        />

        <AlertDialog open={showModelAlert} onOpenChange={setShowModelAlert}>
          <AlertDialogContent className="bg-slate-900 border-slate-700 text-slate-100">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-xl font-bold text-white">No AI Model Detected</AlertDialogTitle>
              <AlertDialogDescription className="text-slate-300">
                To play Perplexed, you need to have a local AI model downloaded.
                <br /><br />
                Please, go to the Settings page to download a model (like Qwen or TinyLlama) to get started!
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogAction
                onClick={() => navigate('/settings')}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Go to Settings
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    );
  }

  return (
    <div className="app-background p-4">
      <div className="max-w-4xl mx-auto pt-8" ref={gameRef}>
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <Button
            data-testid="back-to-menu-button"
            onClick={resetGame}
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10"
          >
            ← Back to Menu
          </Button>

          <div className="flex items-center gap-3">
            <div className="glass-card px-4 py-2">
              <span className="text-white font-semibold">{user.username}</span>
            </div>
            <div className="glass-card px-4 py-2 flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-400" />
              <span className="text-white font-semibold" data-testid="user-score-in-game">{user?.total_score || 0}</span>
            </div>
          </div>
        </div>

        {/* Game Info */}
        <div className="flex justify-center items-center mb-6">
          <div className={`difficulty-badge difficulty-${selectedDifficulty.id}`} data-testid="current-difficulty">
            {selectedDifficulty.name}
          </div>
        </div>

        {/* Riddle */}
        <Card className="riddle-box mb-8 fade-in" data-testid="riddle-display">
          <p className="text-xl text-white leading-relaxed text-center">
            {currentRiddle.riddle}
          </p>
        </Card>

        {/* Tile Grid - All Guess Rows */}
        <div className="mb-8" data-testid="tile-grid">
          {[...Array(currentRiddle.max_guesses)].map((_, rowIndex) => renderTileRow(rowIndex))}

          {/* Reveal answer if lost */}
          {!gameWon && guesses.length >= currentRiddle.max_guesses && (
            <div className="flex justify-center gap-2 mb-3 mt-4 animate-in fade-in slide-in-from-top-2">
              {[...correctAnswer].map((letter, i) => (
                <div key={i} className="letter-tile correct text-white ring-2 ring-red-500/50">
                  {letter}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="text-center mb-4">
          {!gameWon && guesses.length < currentRiddle.max_guesses ? (
            <p className="text-slate-300 text-sm">
              Type your answer and press Enter • {currentRiddle.max_guesses - guesses.length} {currentRiddle.max_guesses - guesses.length === 1 ? 'guess' : 'guesses'} remaining
            </p>
          ) : (
            <Button
              data-testid="play-again-button"
              onClick={resetGame}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 px-8 py-6 text-lg"
            >
              Play Again
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}