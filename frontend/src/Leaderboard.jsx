import React from 'react';

function useTelegramTheme() {
  React.useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;
    const apply = () => {
      const p = tg.themeParams || {};
      document.documentElement.style.setProperty('--bg', p.bg_color || '#f4f7fb');
      document.documentElement.style.setProperty('--card', p.secondary_bg_color || '#ffffff');
      document.documentElement.style.setProperty('--text', p.text_color || '#1f2937');
      document.documentElement.style.setProperty('--muted', p.hint_color || '#6b7280');
    };
    tg.ready?.();
    tg.expand?.();
    apply();
    tg.onEvent?.('themeChanged', apply);
    return () => tg.offEvent?.('themeChanged', apply);
  }, []);
}

export default function Leaderboard() {
  useTelegramTheme();
  const [rows, setRows] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [dark, setDark] = React.useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/leaderboard?limit=50', { headers: { 'Accept': 'application/json' } });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      const items = Array.isArray(json.items) ? json.items : [];
      setRows(items);
    } catch (e) {
      console.error('Leaderboard fetch failed', e);
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { fetchData(); }, []);

  React.useEffect(() => {
    document.documentElement.style.setProperty('--bg', dark ? '#0f172a' : '#f4f7fb');
    document.documentElement.style.setProperty('--card', dark ? '#111827' : '#ffffff');
    document.documentElement.style.setProperty('--text', dark ? '#e5e7eb' : '#1f2937');
    document.documentElement.style.setProperty('--muted', dark ? '#9ca3af' : '#6b7280');
  }, [dark]);

  return (
    <div className="container">
      <div className="header">
        <div className="logo">LB</div>
        <div className="title">luckybet Bingo</div>
      </div>

      <div className="card">
        <div className="tab">
          <span>Rank</span>
          <span>Player</span>
          <span>Points</span>
          <span>Prize</span>
        </div>

        <div className="rows">
          {loading && <div className="row"><div className="name">Loading...</div></div>}
          {!loading && rows.map((it) => (
            <div key={it.rank} className="row">
              <div className="rank">{it.rank}</div>
              <div className="name">{it.player}</div>
              <div className="points">{it.points}</div>
              <div className="prize">{it.prize}</div>
            </div>
          ))}
        </div>

        <div className="center">
          <button className="btn" onClick={fetchData}>↻ Refresh Data</button>
        </div>
      </div>

      <div className="footer">
        <div>Copyright © Luckybet Bingo 2025</div>
        <div className="moon" onClick={() => setDark(!dark)} title="Toggle theme">☽</div>
      </div>
    </div>
  );
}
