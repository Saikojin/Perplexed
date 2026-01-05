import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { Trophy, Users, ArrowLeft, Crown, Medal } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LeaderboardPage({ user }) {
  const navigate = useNavigate();
  const [globalLeaderboard, setGlobalLeaderboard] = useState([]);
  const [friendsLeaderboard, setFriendsLeaderboard] = useState([]);
  const [friendUsername, setFriendUsername] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboards();
  }, []);

  const fetchLeaderboards = async () => {
    try {
      const token = localStorage.getItem('token');

      const [globalRes, friendsRes] = await Promise.all([
        fetch(`${API}/leaderboard/global`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API}/leaderboard/friends`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      const globalData = await globalRes.json();
      const friendsData = await friendsRes.json();

      setGlobalLeaderboard(globalData);
      setFriendsLeaderboard(friendsData);
    } catch (error) {
      toast.error('Failed to load leaderboards');
    } finally {
      setLoading(false);
    }
  };

  const addFriend = async () => {
    if (!friendUsername.trim()) {
      toast.error('Please enter a username');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/friends/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ friend_username: friendUsername })
      });

      if (res.ok) {
        toast.success('Friend added!');
        setFriendUsername('');
        fetchLeaderboards();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to add friend');
      }
    } catch (error) {
      toast.error('Network error');
    }
  };

  const getRankIcon = (index) => {
    if (index === 0) return <Crown className="w-6 h-6 text-yellow-400" />;
    if (index === 1) return <Medal className="w-6 h-6 text-gray-300" />;
    if (index === 2) return <Medal className="w-6 h-6 text-amber-600" />;
    return <span className="text-slate-400 font-semibold">{index + 1}</span>;
  };

  const LeaderboardList = ({ data, testIdPrefix }) => (
    <div className="space-y-3">
      {data.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          No players yet
        </div>
      ) : (
        data.map((player, index) => (
          <Card
            key={index}
            data-testid={`${testIdPrefix}-${index}`}
            className={`glass-card p-4 flex items-center justify-between transition-all hover:scale-102 ${player.username === user.username ? 'border-2 border-blue-500' : ''
              }`}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 flex items-center justify-center">
                {getRankIcon(index)}
              </div>
              <div>
                <div className="text-white font-semibold flex items-center gap-2">
                  {player.username}
                  {player.username === user.username && (
                    <span className="text-xs text-blue-400">(You)</span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-400" />
              <span className="text-white font-bold text-lg" data-testid={`${testIdPrefix}-score-${index}`}>
                {player.total_score}
              </span>
            </div>
          </Card>
        ))
      )}
    </div>
  );

  return (
    <div className="app-background p-4">
      <div className="max-w-4xl mx-auto pt-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <Button
            data-testid="back-to-game-button"
            onClick={() => navigate('/game')}
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Game
          </Button>
        </div>

        <div className="text-center mb-12">
          <div className="flex justify-center mb-4">
            <div className="w-20 h-20 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Trophy className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-2" style={{ fontFamily: 'Space Grotesk' }}>
            Leaderboard
          </h1>
          <p className="text-lg text-slate-300">Compete with the best</p>
        </div>

        <Tabs defaultValue="global" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-white/10 mb-6" data-testid="leaderboard-tabs">
            <TabsTrigger
              value="global"
              data-testid="global-tab"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 text-white"
            >
              <Users className="w-4 h-4 mr-2" />
              Global
            </TabsTrigger>
            <TabsTrigger
              value="friends"
              data-testid="friends-tab"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 text-white"
            >
              <Users className="w-4 h-4 mr-2" />
              Friends
            </TabsTrigger>
          </TabsList>

          <TabsContent value="global" data-testid="global-leaderboard">
            {loading ? (
              <div className="text-center py-12 text-white">Loading...</div>
            ) : (
              <LeaderboardList data={globalLeaderboard} testIdPrefix="global-player" />
            )}
          </TabsContent>

          <TabsContent value="friends" data-testid="friends-leaderboard">
            <Card className="glass-card p-4 mb-6">
              <h3 className="text-white font-semibold mb-3">Add Friend</h3>
              <div className="flex gap-2">
                <Input
                  data-testid="friend-username-input"
                  type="text"
                  placeholder="Enter username"
                  value={friendUsername}
                  onChange={(e) => setFriendUsername(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addFriend()}
                  className="bg-white/10 border-white/20 text-white placeholder:text-slate-400"
                />
                <Button
                  data-testid="add-friend-button"
                  onClick={addFriend}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                >
                  Add
                </Button>
              </div>
            </Card>

            {loading ? (
              <div className="text-center py-12 text-white">Loading...</div>
            ) : (
              <LeaderboardList data={friendsLeaderboard} testIdPrefix="friend-player" />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}