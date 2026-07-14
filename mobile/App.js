import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  SafeAreaView, View, Text, TextInput, TouchableOpacity, ScrollView,
  ActivityIndicator, StyleSheet, Platform, Keyboard,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

// ⚙️ Config — change l'URL si ton backend Render a un autre nom, et l'user si besoin.
const API_URL = 'https://coach-fitness-ai.onrender.com';
const USER = 'app:yehouda';

async function api(path, options) {
  const res = await fetch(`${API_URL}${path}`, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [kbHeight, setKbHeight] = useState(0);
  const scrollRef = useRef(null);

  // On mesure la hauteur du clavier et on remonte la zone de saisie d'autant.
  useEffect(() => {
    const showEvt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvt = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const s = Keyboard.addListener(showEvt, (e) => setKbHeight(e.endCoordinates?.height ?? 0));
    const h = Keyboard.addListener(hideEvt, () => setKbHeight(0));
    return () => { s.remove(); h.remove(); };
  }, []);

  const load = useCallback(async () => {
    try {
      const data = await api(`/api/${encodeURIComponent(USER)}/messages?limit=100`);
      const server = data.messages || [];
      // Ne JAMAIS rétrécir l'affichage (évite le "chat qui s'efface" si le poll
      // arrive avant que le serveur ait enregistré le dernier échange).
      setMessages((prev) => (server.length < prev.length ? prev : server));
    } catch (e) { /* réseau : on garde l'affichage courant */ }
  }, []);

  useEffect(() => { load(); }, [load]);
  // Poll léger pour récupérer d'éventuels messages proactifs du coach.
  useEffect(() => { const t = setInterval(load, 8000); return () => clearInterval(t); }, [load]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setSending(true);
    try {
      const data = await api('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: USER, message: text }),
      });
      setMessages((m) => [...m, { role: 'assistant', content: data.reply }]);
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', content: '(erreur réseau — réessaie)' }]);
    } finally { setSending(false); }
  };

  return (
    <View style={{ flex: 1, marginBottom: kbHeight }}>
      <ScrollView
        ref={scrollRef}
        style={styles.chat}
        contentContainerStyle={{ paddingVertical: 12 }}
        keyboardShouldPersistTaps="handled"
        onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}
      >
        {messages.map((m, i) => (
          <View key={i} style={[styles.bubble, m.role === 'user' ? styles.user : styles.coach]}>
            <Text style={m.role === 'user' ? styles.userText : styles.coachText}>{m.content}</Text>
          </View>
        ))}
        {sending && <ActivityIndicator style={{ margin: 10 }} color="#4a5d23" />}
      </ScrollView>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Écris au Sergent…"
          placeholderTextColor="#999"
          onSubmitEditing={send}
          returnKeyType="send"
        />
        <TouchableOpacity style={styles.sendBtn} onPress={send}>
          <Text style={styles.sendTxt}>▶</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

function ClockBar() {
  // Heure du backend (virtuelle si accéléré) qu'on fait avancer localement chaque
  // seconde, + un bouton pour basculer accéléré ⇄ normal à chaud.
  const [base, setBase] = useState(null);
  const [now, setNow] = useState(null);
  const [accel, setAccel] = useState(null);

  const sync = useCallback(async () => {
    try {
      const d = await api('/api/clock');
      setBase({ serverMs: new Date(d.now).getTime(), fetchedAt: Date.now(), factor: d.factor || 1 });
      setAccel(!!d.accelerated);
    } catch (e) { /* backend pas encore à jour */ }
  }, []);

  useEffect(() => { sync(); const t = setInterval(sync, 15000); return () => clearInterval(t); }, [sync]);
  useEffect(() => {
    const t = setInterval(() => {
      setBase((b) => {
        if (b) setNow(new Date(b.serverMs + (Date.now() - b.fetchedAt) * b.factor));
        return b;
      });
    }, 1000);
    return () => clearInterval(t);
  }, []);

  const toggle = async () => {
    const next = !accel;
    setAccel(next);
    try {
      await api('/api/clock/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accelerated: next }),
      });
      sync();
    } catch (e) { setAccel(!next); /* échec : on revient */ }
  };

  const jour = now ? now.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' }) : '—';
  const heure = now ? now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';

  return (
    <View style={styles.clockBar}>
      <Text style={styles.clock}>{accel ? '⏩ ' : '🕐 '}{jour} · {heure}</Text>
      {accel !== null && (
        <TouchableOpacity onPress={toggle} style={[styles.warpBtn, accel && styles.warpOn]}>
          <Text style={[styles.warpTxt, accel && styles.warpTxtOn]}>{accel ? `Accéléré ×${base?.factor ?? ''}` : 'Passer en accéléré'}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

function Card({ title, children }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api(`/api/${encodeURIComponent(USER)}/dashboard`)
      .then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color="#4a5d23" />;
  if (!data) return <Text style={styles.muted}>Impossible de charger (le service Render se réveille peut-être, réessaie dans 1 min).</Text>;
  const adh = data.adherence || {};

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
      <TouchableOpacity onPress={load} style={styles.refresh}><Text style={styles.refreshTxt}>↻ Rafraîchir</Text></TouchableOpacity>

      <Card title="🎯 Objectifs & motivations">
        {(data.goals || []).map((g, i) => <Text key={i} style={styles.line}>• [{g.type}] {g.content}</Text>)}
        {!(data.goals || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="💪 Cette semaine">
        <Text style={styles.big}>{adh.seances_cette_semaine ?? 0}{adh.objectif_semaine ? ` / ${adh.objectif_semaine}` : ''} séances</Text>
        {adh.jours_depuis_derniere != null && <Text style={styles.muted}>Dernière séance il y a {adh.jours_depuis_derniere} j</Text>}
      </Card>

      <Card title="⏰ Prochaine séance">
        <Text style={styles.line}>{data.prochaine_seance ? data.prochaine_seance.scheduled_at.replace('T', ' à ') : 'aucune prévue'}</Text>
      </Card>

      <Card title="🏋️ Programme">
        {data.programme ? (
          <>
            <Text style={styles.bold}>{data.programme.name} — {data.programme.frequence}x/sem</Text>
            {(data.programme.seances || []).map((s, i) => (
              <View key={i} style={{ marginTop: 6 }}>
                <Text style={styles.bold}>{s.jour ? s.jour + ' — ' : ''}{s.nom}</Text>
                {(s.exos || []).map((e, j) => <Text key={j} style={styles.muted}>   · {e.exo} {e.series}x{e.reps}</Text>)}
              </View>
            ))}
          </>
        ) : <Text style={styles.muted}>pas encore de programme</Text>}
      </Card>

      <Card title="🏁 Jalons">
        {(data.jalons || []).map((m, i) => <Text key={i} style={styles.line}>• {m.label} : dans {m.jours} j</Text>)}
        {!(data.jalons || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="📏 Mesures">
        {(data.mesures || []).map((m, i) => <Text key={i} style={styles.line}>• {m.metric} : {m.value}{m.unit || ''}</Text>)}
        {!(data.mesures || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="🩹 En ce moment">
        {(data.events || []).map((e, i) => <Text key={i} style={styles.line}>• [{e.kind}] {e.content} ({e.status})</Text>)}
        {!(data.events || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function Seances() {
  const [seances, setSeances] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api(`/api/${encodeURIComponent(USER)}/workouts?limit=40`)
      .then((d) => setSeances(d.seances || [])).catch(() => setSeances(null)).finally(() => setLoading(false));
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={OLIVE} />;
  if (!seances) return <Text style={styles.muted}>Impossible de charger (le service Render se réveille peut-être, réessaie).</Text>;

  const MAX_H = 120;
  const barColor = (n) => (n >= 8 ? '#c0392b' : n >= 5 ? '#e08e0b' : '#4a7c1f');
  const d2 = (n) => String(n).padStart(2, '0');
  const fmtDay = (iso) => { const d = new Date(iso); return `${d2(d.getDate())}/${d2(d.getMonth() + 1)}`; };
  const fmtFull = (iso) => new Date(iso).toLocaleString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16 }}>
      <TouchableOpacity onPress={load} style={styles.refresh}><Text style={styles.refreshTxt}>↻ Rafraîchir</Text></TouchableOpacity>

      <Text style={styles.cardTitle}>📈 Intensité ressentie (/10)</Text>
      {seances.length === 0 ? (
        <Text style={styles.muted}>Aucune séance pour l'instant. Parle de tes séances au Sergent (faite ou pas, comment c'était) — ça se remplit tout seul.</Text>
      ) : (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chart}>
          <View style={styles.chartRow}>
            {seances.map((s, i) => {
              const h = s.done && s.intensity ? (s.intensity / 10) * MAX_H : 0;
              return (
                <View key={i} style={styles.col}>
                  <Text style={styles.barVal}>{s.done ? (s.intensity ?? '✓') : ''}</Text>
                  <View style={[styles.barTrack, { height: MAX_H }]}>
                    {s.done ? (
                      <View style={[styles.bar, { height: Math.max(h, 8), backgroundColor: s.intensity ? barColor(s.intensity) : '#bbb' }]} />
                    ) : (
                      <Text style={styles.missedMark}>✗</Text>
                    )}
                  </View>
                  <Text style={styles.barDate}>{fmtDay(s.performed_at)}</Text>
                </View>
              );
            })}
          </View>
        </ScrollView>
      )}
      <Text style={styles.legend}>Vert = léger · Orange = soutenu · Rouge = très dur · ✗ = séance manquée</Text>

      <Text style={[styles.cardTitle, { marginTop: 20 }]}>🗒️ Historique des séances</Text>
      {[...seances].reverse().map((s, i) => (
        <View key={i} style={styles.seanceCard}>
          <View style={styles.seanceHead}>
            <Text style={styles.seanceDate}>{fmtFull(s.performed_at)}</Text>
            <Text style={s.done ? styles.badgeOk : styles.badgeKo}>{s.done ? '✅ Faite' : '❌ Manquée'}</Text>
          </View>
          {s.done && s.intensity != null && <Text style={styles.seanceInt}>Intensité : {s.intensity}/10</Text>}
          {(s.session_name || s.feeling) ? (
            <Text style={styles.muted}>{s.session_name || 'séance'}{s.feeling ? ` — « ${s.feeling} »` : ''}</Text>
          ) : null}
        </View>
      ))}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

export default function App() {
  const [tab, setTab] = useState('chat');
  const [kbd, setKbd] = useState(false);

  useEffect(() => {
    const showEvt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvt = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const s = Keyboard.addListener(showEvt, () => setKbd(true));
    const h = Keyboard.addListener(hideEvt, () => setKbd(false));
    return () => { s.remove(); h.remove(); };
  }, []);

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="light" />
      <View style={styles.header}>
        <Text style={styles.headerTxt}>🎖️ Le Sergent</Text>
        <ClockBar />
      </View>
      <View style={{ flex: 1 }}>
        {tab === 'chat' ? <Chat /> : tab === 'seances' ? <Seances /> : <Dashboard />}
      </View>
      {!(kbd && tab === 'chat') && (
        <View style={styles.tabs}>
          <TouchableOpacity style={[styles.tab, tab === 'chat' && styles.tabActive]} onPress={() => setTab('chat')}>
            <Text style={[styles.tabTxt, tab === 'chat' && styles.tabTxtActive]}>💬 Chat</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.tab, tab === 'seances' && styles.tabActive]} onPress={() => setTab('seances')}>
            <Text style={[styles.tabTxt, tab === 'seances' && styles.tabTxtActive]}>📈 Séances</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.tab, tab === 'dashboard' && styles.tabActive]} onPress={() => setTab('dashboard')}>
            <Text style={[styles.tabTxt, tab === 'dashboard' && styles.tabTxtActive]}>📊 Suivi</Text>
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const OLIVE = '#4a5d23';
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f5f5f0' },
  header: { backgroundColor: OLIVE, paddingVertical: 14, alignItems: 'center' },
  headerTxt: { color: '#fff', fontSize: 18, fontWeight: '700' },
  clockBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 4, gap: 8 },
  clock: { color: '#dfe6c8', fontSize: 12, fontVariant: ['tabular-nums'] },
  warpBtn: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12, borderWidth: 1, borderColor: '#dfe6c8' },
  warpOn: { backgroundColor: '#dfe6c8', borderColor: '#dfe6c8' },
  warpTxt: { color: '#dfe6c8', fontSize: 11, fontWeight: '700' },
  warpTxtOn: { color: OLIVE },
  chat: { flex: 1, paddingHorizontal: 12 },
  bubble: { maxWidth: '82%', padding: 10, borderRadius: 14, marginVertical: 4 },
  user: { alignSelf: 'flex-end', backgroundColor: OLIVE },
  coach: { alignSelf: 'flex-start', backgroundColor: '#e6e6dc' },
  userText: { color: '#fff', fontSize: 15 },
  coachText: { color: '#222', fontSize: 15 },
  inputRow: { flexDirection: 'row', padding: 8, backgroundColor: '#fff', alignItems: 'center' },
  input: { flex: 1, backgroundColor: '#f0f0e8', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 15 },
  sendBtn: { marginLeft: 8, backgroundColor: OLIVE, width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  sendTxt: { color: '#fff', fontSize: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 14, marginBottom: 12 },
  cardTitle: { fontWeight: '700', fontSize: 15, marginBottom: 8, color: OLIVE },
  line: { fontSize: 14, color: '#333', marginVertical: 2 },
  bold: { fontSize: 14, color: '#222', fontWeight: '600' },
  muted: { fontSize: 13, color: '#888', marginVertical: 2 },
  big: { fontSize: 26, fontWeight: '800', color: OLIVE },
  tabs: { flexDirection: 'row', backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#e0e0d5' },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center' },
  tabActive: { borderTopWidth: 3, borderTopColor: OLIVE },
  tabTxt: { fontSize: 14, color: '#888' },
  tabTxtActive: { color: OLIVE, fontWeight: '700' },
  refresh: { alignSelf: 'flex-end', marginBottom: 8 },
  refreshTxt: { color: OLIVE, fontWeight: '600' },
  // Suivi des séances (chart + historique)
  chart: { backgroundColor: '#fff', borderRadius: 12, paddingVertical: 12, marginTop: 8 },
  chartRow: { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 10 },
  col: { alignItems: 'center', width: 34 },
  barVal: { fontSize: 11, color: '#555', height: 14, fontWeight: '700' },
  barTrack: { width: '100%', justifyContent: 'flex-end', alignItems: 'center' },
  bar: { width: 16, borderRadius: 4 },
  missedMark: { color: '#c0392b', fontSize: 16, fontWeight: '800' },
  barDate: { fontSize: 9, color: '#999', marginTop: 4 },
  legend: { fontSize: 11, color: '#888', marginTop: 8, fontStyle: 'italic' },
  seanceCard: { backgroundColor: '#fff', borderRadius: 10, padding: 12, marginTop: 8 },
  seanceHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  seanceDate: { fontSize: 13, color: '#333', fontWeight: '600', textTransform: 'capitalize' },
  badgeOk: { fontSize: 12, color: '#2e7d32', fontWeight: '700' },
  badgeKo: { fontSize: 12, color: '#c0392b', fontWeight: '700' },
  seanceInt: { fontSize: 13, color: OLIVE, fontWeight: '700', marginTop: 4 },
});
