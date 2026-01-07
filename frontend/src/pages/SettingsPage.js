import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import { ArrowLeft, Save, Crown, Palette } from "lucide-react";
import { themes } from "../config/themes";
import versionData from "../version.json";

import PremiumModal from '../components/PremiumModal';

export default function SettingsPage({ user, setUser }) {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [availableModels, setAvailableModels] = useState([]);
    const [modelToPull, setModelToPull] = useState("");
    const [pullingModel, setPullingModel] = useState(false);
    const [downloadStatus, setDownloadStatus] = useState({});
    const [showPremiumModal, setShowPremiumModal] = useState(false);

    // API Keys state (separate to avoid showing existing keys)
    const [apiKeys, setApiKeys] = useState({
        openai: "",
        anthropic: ""
    });

    // Local state for form settings
    const [settings, setSettings] = useState({
        ui_color_primary: user?.settings?.ui_color_primary || "",
        ui_color_primary: user?.settings?.ui_color_primary || "",
        ui_color_accent: user?.settings?.ui_color_accent || "",
        background_url: user?.settings?.background_url || "",
        theme: user?.settings?.theme || "default",
        preferred_model: user?.settings?.preferred_model || ""
    });

    useEffect(() => {
        if (user && user.settings) {
            setSettings({
                ui_color_primary: user.settings.ui_color_primary || "",
                ui_color_accent: user.settings.ui_color_accent || "",
                background_url: user.settings.background_url || "",
                theme: user.settings.theme || "default",
                preferred_model: user.settings.preferred_model || ""
            });
        }

        // Fetch available models
        const fetchModels = async () => {
            try {
                const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/models/available`);
                if (res.ok) {
                    const data = await res.json();
                    setAvailableModels(data || []);

                    // If user has no preferred model set, default the dropdown to the currently active one
                    const active = data.find(m => m.active);
                    if (active && (!user.settings || !user.settings.preferred_model)) {
                        setSettings(prev => ({ ...prev, preferred_model: active.name }));
                    }
                }
            } catch (error) {
                console.error("Failed to fetch models", error);
            }
        };
        fetchModels();
    }, [user]);

    // Poll for download status
    useEffect(() => {
        let interval;
        if (pullingModel) {
            interval = setInterval(async () => {
                try {
                    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/models/download-status`);
                    const data = await res.json();
                    setDownloadStatus(data);

                    // Check if current download completed
                    if (modelToPull) {
                        // Extract filename logic similar to backend
                        let filename = modelToPull.split("/").pop().split("?")[0];
                        if (!filename.endsWith(".gguf")) filename += ".gguf";

                        const status = data[filename];
                        if (status && status.status === 'completed') {
                            setPullingModel(false);
                            toast.success(`Download complete: ${filename}`);
                            setModelToPull("");
                            // Refresh models
                            const modelsRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/models/available`);
                            if (modelsRes.ok) {
                                setAvailableModels(await modelsRes.json());
                            }
                        } else if (status && status.status === 'error') {
                            setPullingModel(false);
                            toast.error(`Download failed: ${status.error}`);
                        }
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [pullingModel, modelToPull]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setSettings(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleKeyChange = (e) => {
        const { name, value } = e.target;
        setApiKeys(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const applyTheme = (themeKey) => {
        const theme = themes[themeKey];
        if (theme.premium && !user.premium) {
            toast.error("This theme requires Premium access!");
            return;
        }

        setSettings(prev => ({
            ...prev,
            ui_color_primary: theme.colors.primary,
            ui_color_accent: theme.colors.accent,
            background_url: theme.background_url,
            theme: themeKey
        }));
        toast.success(`Applied ${theme.name} theme preset`);
    };

    const handlePullModel = async () => {
        if (!modelToPull) return;
        setPullingModel(true);
        // toast.info(`Starting pull for ${modelToPull}... this may take a while.`); // Removed to prevent double toast
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/models/pull`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ model_name: modelToPull })
            });
            if (res.ok) {
                // Toast handled by completion or start, strictly one
                toast.info(`Started downloading ${modelToPull}...`);
                // setModelToPull(""); // Keep it to track progress key
            } else {
                toast.error("Failed to trigger model pull");
            }
        } catch (e) {
            toast.error("Network error pulling model");
        }
        // Do not setPullingModel(false) here, wait for polling to finish or error
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const token = localStorage.getItem('token');
            // Prepare payload
            const payload = {
                ...settings,
                api_keys: apiKeys
            };

            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/user/settings`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                // Handle potential 403 for premium themes if someone bypasses frontend check
                if (response.status === 403) {
                    throw new Error("Premium required for this configuration");
                }
                throw new Error("Failed to update settings");
            }

            const data = await response.json();
            toast.success("Settings saved successfully!");

            // Update global user state
            setUser(prev => ({
                ...prev,
                settings: {
                    ...prev.settings,
                    ...settings
                }
            }));

        } catch (error) {
            console.error(error);
            toast.error(error.message || "Failed to save settings");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen app-background p-4 md:p-8 flex flex-col items-center">
            <div className="w-full max-w-2xl mb-6 flex items-center justify-between">
                <Button variant="ghost" className="bg-transparent text-white hover:bg-white/10" onClick={() => navigate('/game')}>
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back to Game
                </Button>
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                    Settings
                </h1>
                <div className="flex items-center gap-2">
                    {!user?.premium && (
                        <Button
                            onClick={() => setShowPremiumModal(true)}
                            className="bg-gradient-to-r from-yellow-500 to-amber-600 text-white hover:from-yellow-600 hover:to-amber-700"
                        >
                            <Crown className="w-4 h-4 mr-2" />
                            Go Premium
                        </Button>
                    )}
                </div>
            </div>

            {/* Theme Selector */}
            <Card className="w-full max-w-2xl bg-black/40 border-white/10 backdrop-blur-md text-white shadow-2xl mb-8">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Palette className="w-5 h-5 text-purple-400" />
                        <CardTitle className="text-xl">Choose a Theme</CardTitle>
                    </div>
                    <CardDescription className="text-gray-400">
                        Select a preset theme to instantly transform Roddle.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {Object.entries(themes).map(([key, theme]) => {
                            const isActive = settings.theme === key;
                            return (
                                <div
                                    key={key}
                                    onClick={() => applyTheme(key)}
                                    className={`
                                        relative p-4 rounded-xl border transition-all cursor-pointer group
                                        ${isActive
                                            ? 'bg-white/10 border-blue-500 ring-1 ring-blue-500'
                                            : 'bg-black/20 border-white/10 hover:bg-white/5 hover:border-white/20'
                                        }
                                    `}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="font-semibold text-white group-hover:text-blue-200 transition-colors">
                                            {theme.name}
                                        </h3>
                                        {theme.premium && !user.premium && (
                                            <Crown className="w-4 h-4 text-yellow-400" />
                                        )}
                                    </div>
                                    <p className="text-xs text-slate-400 mb-3">{theme.description}</p>

                                    <div className="flex gap-2">
                                        <div className="w-6 h-6 rounded-full border border-white/20" style={{ background: theme.colors.primary }} title="Primary" />
                                        <div className="w-6 h-6 rounded-full border border-white/20" style={{ background: theme.colors.accent }} title="Accent" />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </CardContent>
            </Card>

            <Card className="w-full max-w-2xl bg-black/40 border-white/10 backdrop-blur-md text-white shadow-2xl">
                <CardHeader>
                    <CardTitle className="text-xl">Fine-tune Customization</CardTitle>
                    <CardDescription className="text-gray-400">
                        Personalize your Roddle experience with custom colors and backgrounds.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSave} className="space-y-6">

                        <div className="space-y-2">
                            <Label htmlFor="ui_color_primary">Primary Color (Hex)</Label>
                            <div className="flex gap-2">
                                <Input
                                    id="ui_color_primary"
                                    name="ui_color_primary"
                                    placeholder="#0F172A"
                                    value={settings.ui_color_primary}
                                    onChange={handleChange}
                                    className="bg-black/50 border-white/20 text-white"
                                />
                                <input
                                    type="color"
                                    value={settings.ui_color_primary || "#0F172A"}
                                    onChange={(e) => handleChange({ target: { name: 'ui_color_primary', value: e.target.value } })}
                                    className="h-10 w-12 cursor-pointer bg-transparent border-none"
                                />
                            </div>
                            <p className="text-xs text-gray-400">Used for navigation bars and main backgrounds.</p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="ui_color_accent">Accent Color (Hex)</Label>
                            <div className="flex gap-2">
                                <Input
                                    id="ui_color_accent"
                                    name="ui_color_accent"
                                    placeholder="#8B5CF6"
                                    value={settings.ui_color_accent}
                                    onChange={handleChange}
                                    className="bg-black/50 border-white/20 text-white"
                                />
                                <input
                                    type="color"
                                    value={settings.ui_color_accent || "#8B5CF6"}
                                    onChange={(e) => handleChange({ target: { name: 'ui_color_accent', value: e.target.value } })}
                                    className="h-10 w-12 cursor-pointer bg-transparent border-none"
                                />
                            </div>
                            <p className="text-xs text-gray-400">Used for buttons, highlights, and important elements.</p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="background_url">Custom Background URL</Label>
                            <Input
                                id="background_url"
                                name="background_url"
                                placeholder="https://example.com/image.jpg"
                                value={settings.background_url}
                                onChange={handleChange}
                                className="bg-black/50 border-white/20 text-white"
                            />
                            <p className="text-xs text-gray-400">Paste a direct link to an image to replace the default gradient.</p>
                        </div>

                        {settings.background_url && (
                            <div className="mt-4 p-2 border border-white/10 rounded-md bg-black/20">
                                <p className="text-xs text-gray-400 mb-2">Preview:</p>
                                <div
                                    className="h-32 w-full rounded-md bg-cover bg-center"
                                    style={{ backgroundImage: `url(${settings.background_url})` }}
                                />
                            </div>
                        )}

                        <div className="space-y-2 pt-4 border-t border-white/10">
                            <Label>AI Model Configuration (Advanced)</Label>
                            <div className="space-y-4">
                                <div>
                                    <Label htmlFor="preferred_model" className="text-xs text-slate-400">Preferred Generation Model</Label>
                                    <select
                                        id="preferred_model"
                                        name="preferred_model"
                                        value={settings.preferred_model}
                                        onChange={handleChange}
                                        className="w-full mt-1 bg-black/50 border border-white/20 text-white rounded-md p-2"
                                    >
                                        <option value="">
                                            Use Server Default {availableModels.find(m => m.active) ? `(Active: ${availableModels.find(m => m.active).name})` : ""}
                                        </option>
                                        {availableModels.map((m, i) => (
                                            <option key={i} value={m.name || m}>
                                                {m.name || m} {m.active ? "(Currently Loaded)" : ""}
                                            </option>
                                        ))}
                                    </select>
                                    {availableModels.find(m => m.active) && settings.preferred_model === "" && (
                                        <p className="text-xs text-slate-400 mt-1">
                                            Currently using: <span className="font-mono text-blue-400">{availableModels.find(m => m.active).name}</span>
                                        </p>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="pull_model" className="text-xs text-slate-400">Download New Model (Ollama)</Label>
                                    <div className="flex gap-2 items-center">
                                        <Input
                                            id="pull_model"
                                            placeholder="e.g. llama3, mistral"
                                            value={modelToPull}
                                            onChange={(e) => setModelToPull(e.target.value)}
                                            className="bg-black/50 border-white/20 text-white"
                                            disabled={pullingModel}
                                        />
                                        <Button type="button" onClick={handlePullModel} disabled={pullingModel} variant="secondary">
                                            {pullingModel ? "Downloading..." : "Pull"}
                                        </Button>
                                    </div>
                                    {pullingModel && modelToPull && (
                                        <div className="mt-2 text-xs text-blue-400 flex items-center gap-2">
                                            {(() => {
                                                let filename = modelToPull.split("/").pop().split("?")[0];
                                                if (!filename.endsWith(".gguf")) filename += ".gguf";
                                                const status = downloadStatus[filename];
                                                if (status) {
                                                    const mb = (status.progress / (1024 * 1024)).toFixed(1);
                                                    const total = (status.total / (1024 * 1024)).toFixed(1);
                                                    const pct = status.total > 0 ? Math.round((status.progress / status.total) * 100) : 0;
                                                    return (
                                                        <div className="w-full space-y-1 mt-2">
                                                            <div className="flex justify-between text-xs text-blue-400">
                                                                <span className="flex items-center gap-2">
                                                                    <div className="w-3 h-3 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                                                                    Downloading...
                                                                </span>
                                                                <span>{pct}% ({mb}MB / {total}MB)</span>
                                                            </div>
                                                            <Progress value={pct} className="h-1.5" />
                                                        </div>
                                                    );
                                                }
                                                return <span>Initializing...</span>;
                                            })()}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Online Integration */}
                        <div className="space-y-2 pt-4 border-t border-white/10">
                            <Label>Online Integrations</Label>
                            <p className="text-xs text-gray-400 mb-4">
                                Provide API keys to use cloud-based models. Keys are stored securely encrypted.
                            </p>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="openai_key" className="text-xs text-slate-400">OpenAI API Key (gpt-* models)</Label>
                                    <Input
                                        id="openai_key"
                                        name="openai"
                                        type="password"
                                        placeholder={user?.settings?.api_keys?.openai ? "Key is set (enter new to update)" : "sk-..."}
                                        value={apiKeys.openai}
                                        onChange={handleKeyChange}
                                        className="bg-black/50 border-white/20 text-white font-mono"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="anthropic_key" className="text-xs text-slate-400">Anthropic API Key (claude-* models)</Label>
                                    <Input
                                        id="anthropic_key"
                                        name="anthropic"
                                        type="password"
                                        placeholder={user?.settings?.api_keys?.anthropic ? "Key is set (enter new to update)" : "sk-ant-..."}
                                        value={apiKeys.anthropic}
                                        onChange={handleKeyChange}
                                        className="bg-black/50 border-white/20 text-white font-mono"
                                    />
                                </div>
                            </div>
                        </div>

                        <Button type="submit" className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-2" disabled={loading}>
                            {loading ? (
                                <span className="flex items-center gap-2">Saving...</span>
                            ) : (
                                <span className="flex items-center gap-2"><Save className="w-4 h-4" /> Save Changes</span>
                            )}
                        </Button>

                    </form>
                </CardContent>
            </Card>



            <Card className="w-full max-w-2xl bg-black/40 border-white/10 backdrop-blur-md text-white shadow-2xl mt-8">
                <CardHeader>
                    <CardTitle className="text-xl">About Perplexed</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex justify-between items-center border-b border-white/10 pb-2">
                        <span className="text-slate-400">Version</span>
                        <span className="font-mono text-sm bg-white/10 px-2 py-1 rounded">{versionData.version}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2">
                        <span className="text-slate-400">Links</span>
                        <div className="flex gap-4">
                            <a
                                href="https://github.com/Saikojin/Perplexed"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1"
                            >
                                GitHub
                            </a>
                            <a
                                href="https://opensource.org/licenses/MIT"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1"
                            >
                                MIT License
                            </a>
                        </div>
                    </div>
                </CardContent>
            </Card>
            <PremiumModal
                isOpen={showPremiumModal}
                onClose={() => setShowPremiumModal(false)}
                user={user}
                setUser={setUser}
            />
        </div>
    );
}
