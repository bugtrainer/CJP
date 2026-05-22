"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Activity, 
  Clock, 
  Search, 
  ExternalLink, 
  Radio, 
  CheckCircle,
  Database,
  RefreshCw,
  FileText
} from "lucide-react";
import ObservatoryTelemetry from "@/components/ObservatoryTelemetry";

const fadeIn = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.4, ease: "easeOut" },
  }),
};

export default function Home() {
  const [activeTab, setActiveTab] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [isLive, setIsLive] = useState(false);
  const [isCollecting, setIsCollecting] = useState(false);

  // Dynamic state
  const [posts, setPosts] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [dbStats, setDbStats] = useState({
    totalArticles: 0,
    lastUpdate: "Just now",
    status: "Syncing..."
  });

  // Dynamic fetching hook connecting UI to backend API database
  const fetchTelemetryData = async () => {
    const getApiUrl = () => {
      if (typeof window !== "undefined") {
        const hostname = window.location.hostname;
        if (hostname === "localhost" || hostname === "127.0.0.1") {
          return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        }
      }
      return "";
    };

    const API_URL = getApiUrl();

    try {
      const testRes = await fetch(`${API_URL}/api/v1/health`);
      if (!testRes.ok) throw new Error("FastAPI Backend Offline");
      setIsLive(true);
      setDbStats(prev => ({ ...prev, status: "Connected & Active" }));

      // Load Posts Feed
      const feedRes = await fetch(`${API_URL}/api/v1/feed?limit=100`);
      if (feedRes.ok) {
        const feedData = await feedRes.json();
        if (feedData.length > 0) {
          setDbStats(prev => ({ ...prev, totalArticles: feedData.length })); // Using feed length for now
          
          setPosts(feedData.map((p: any) => {
            const minsDiff = Math.round((new Date().getTime() - new Date(p.published_at || p.created_at).getTime()) / 60000);
            let timeStr = "1h ago";
            if (minsDiff < 60) timeStr = `${minsDiff}m ago`;
            else if (minsDiff < 1440) timeStr = `${Math.round(minsDiff / 60)}h ago`;
            else timeStr = `${Math.round(minsDiff / 1440)}d ago`;

            return {
              id: p.id,
              platform: p.source_platform.charAt(0).toUpperCase() + p.source_platform.slice(1),
              author: p.author || "anonymous",
              content: p.content,
              contentType: p.content_type || "reaction",
              credibility: p.credibility_score,
              botProbability: p.bot_probability,
              time: timeStr,
              title: p.title || "",
              externalLink: p.post_url || p.external_id
            };
          }));
        }
      }

      // Load daily brief
      const summaryRes = await fetch(`${API_URL}/api/v1/summaries/latest?timeframe=daily`);
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary({
          summary_text: summaryData.summary_text,
          bullet_points: summaryData.bullet_points || [],
          sentiment_distribution: summaryData.sentiment_distribution || { supportive: 33, ironic: 33, critical: 33 }
        });
      }
    } catch (err) {
      console.warn("FastAPI backend unreachable.", err);
      setIsLive(false);
      setDbStats(prev => ({ ...prev, status: "Offline" }));
    }
  };

  useEffect(() => {
    fetchTelemetryData();
    // Auto-refresh data every 5 minutes
    const refreshInterval = setInterval(fetchTelemetryData, 5 * 60 * 1000);
    return () => clearInterval(refreshInterval);
  }, []);

  const handleManualCollect = async () => {
    setIsCollecting(true);
    try {
      const res = await fetch("/api/v1/collect");
      if (res.ok) {
        console.log("Collection triggered");
        // Re-fetch after 15 seconds to give backend time to finish
        setTimeout(() => {
          fetchTelemetryData();
          setIsCollecting(false);
        }, 15000);
      } else {
        setIsCollecting(false);
      }
    } catch (err) {
      setIsCollecting(false);
    }
  };

  const filteredPosts = posts.filter(post => {
    if (activeTab !== "all" && post.contentType !== activeTab) return false;
    if (searchTerm.trim() !== "") {
      const term = searchTerm.toLowerCase();
      return (
        (post.content && post.content.toLowerCase().includes(term)) ||
        (post.author && post.author.toLowerCase().includes(term)) ||
        (post.title && post.title.toLowerCase().includes(term))
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-[#0b0f0e] text-slate-200 font-sans selection:bg-amber-500/30 selection:text-amber-200">
      {/* Dynamic AI Summary Header */}
      <ObservatoryTelemetry summaryData={summary} isLive={isLive} />

      {/* Main Content Area - Centered Feed Layout */}
      <main className="max-w-4xl mx-auto px-4 md:px-8 py-8 space-y-8">
        
        {/* Dynamic Telemetry Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[#121615] border border-slate-800/60 p-4 rounded-xl shadow-lg flex flex-col justify-center items-center">
            <Database className="text-amber-500 mb-2" size={20} />
            <span className="text-2xl font-bold font-mono tracking-tight text-slate-100">{dbStats.totalArticles}</span>
            <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">Articles Indexed</span>
          </div>
          <div className="bg-[#121615] border border-slate-800/60 p-4 rounded-xl shadow-lg flex flex-col justify-center items-center">
            <Activity className="text-emerald-500 mb-2" size={20} />
            <span className="text-sm font-bold text-slate-100 mt-2 text-center">{dbStats.status}</span>
            <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1 text-center">System Health</span>
          </div>
          <div className="bg-[#121615] border border-slate-800/60 p-4 rounded-xl shadow-lg flex flex-col justify-center items-center">
            <Clock className="text-blue-500 mb-2" size={20} />
            <span className="text-sm font-bold text-slate-100 mt-2 text-center">{dbStats.lastUpdate}</span>
            <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1 text-center">Last Sync</span>
          </div>
          <div 
            onClick={handleManualCollect}
            className={`bg-[#121615] border border-slate-800/60 p-4 rounded-xl shadow-lg flex flex-col justify-center items-center cursor-pointer transition-colors ${isCollecting ? 'opacity-50' : 'hover:border-amber-500/50 hover:bg-[#161a19]'}`}
          >
            <RefreshCw className={`text-slate-400 mb-2 ${isCollecting ? 'animate-spin text-amber-500' : ''}`} size={20} />
            <span className="text-sm font-bold text-slate-100 mt-2 text-center">{isCollecting ? "Scraping..." : "Force Sync"}</span>
            <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1 text-center">Manual Collect</span>
          </div>
        </div>

        {/* Community Slicing Stream */}
        <section className="bg-[#121615] border border-slate-800/60 rounded-xl shadow-2xl overflow-hidden">
          <div className="p-4 md:p-6 border-b border-slate-800/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Radio className="text-amber-500 animate-pulse" size={18} />
              <h2 className="text-lg font-semibold tracking-wide text-slate-100">Live Observatory Feed</h2>
            </div>
            
            {/* Search inputs */}
            <div className="relative w-full md:w-64">
              <Search className="absolute left-3 top-2.5 text-slate-500" size={16} />
              <input 
                type="text" 
                placeholder="Search narratives..." 
                className="w-full pl-9 pr-4 py-2 bg-[#0b0f0e] border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-amber-500/50 transition-colors"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          {/* Feed classification tabs */}
          <div className="flex flex-wrap gap-2 px-4 md:px-6 pt-4 pb-2 border-b border-slate-800/30">
            {["all", "news", "reaction", "meme", "opinion"].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-md transition-all capitalize font-medium text-xs tracking-wide ${
                  activeTab === tab 
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" 
                    : "bg-transparent text-slate-500 hover:text-slate-300 hover:bg-slate-800/30 border border-transparent"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Feed Items */}
          <div className="p-4 md:p-6 space-y-4 max-h-[800px] overflow-y-auto scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
            <AnimatePresence>
              {filteredPosts.length === 0 ? (
                <div className="py-12 text-center text-slate-500">
                  <Activity className="mx-auto mb-3 opacity-20" size={32} />
                  <p>No telemetry matched your filters.</p>
                </div>
              ) : (
                filteredPosts.map((post, i) => (
                  <motion.div
                    custom={i}
                    initial="hidden"
                    animate="visible"
                    variants={fadeIn}
                    key={post.id}
                    className="group relative p-4 rounded-xl bg-[#161a19]/50 border border-slate-800/40 hover:border-amber-500/30 transition-all shadow-sm hover:shadow-md hover:bg-[#161a19]"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="font-semibold text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded uppercase tracking-wider">
                          {post.platform}
                        </span>
                        <span className="text-slate-400 font-medium">{post.author}</span>
                        <span className="text-slate-600 font-mono flex items-center gap-1">
                          <Clock size={10} /> {post.time}
                        </span>
                      </div>
                      
                      {post.externalLink && (
                        <a href={post.externalLink} target="_blank" rel="noopener noreferrer" className="text-slate-600 hover:text-amber-400 transition-colors p-1">
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                    
                    {post.title && (
                      <h3 className="text-slate-100 font-medium mb-1.5 leading-snug">
                        {post.title}
                      </h3>
                    )}
                    
                    <div 
                      className="text-sm text-slate-300 leading-relaxed font-light [&>a]:text-amber-400 [&>a]:underline [&>a]:underline-offset-2 hover:[&>a]:text-amber-300" 
                      dangerouslySetInnerHTML={{ __html: post.content }} 
                    />

                    <div className="mt-4 pt-3 border-t border-slate-800/40 flex items-center gap-4 text-[10px] font-mono uppercase tracking-widest">
                      <div className="flex items-center gap-1.5 text-slate-400" title="Credibility Index (based on source and verifiability)">
                        <CheckCircle size={12} className={post.credibility > 0.8 ? "text-emerald-500" : "text-amber-500"} />
                        <span>Confidence: {Math.round(post.credibility * 100)}%</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <FileText size={12} />
                        <span>{post.contentType}</span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </section>
      </main>
    </div>
  );
}
