import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  SafeAreaView, View, Text, TextInput, TouchableOpacity, ScrollView,
  ActivityIndicator, StyleSheet, KeyboardAvoidingView, Platform, Keyboard,
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

function ClockBadge() {
  // On récupère l'heure du backend (virtuelle si temps accéléré) + le facteur,
  // puis on la fait avancer localement chaque seconde, avec resync toutes les 30s.
  const [base, setBase] = useState(null);
  const [now, setNow] = useState(null);

  const sync = useCallback(async () => {
    try {
      const d = await api('/api/clock');
      setBase({ serverMs: new Date(d.now).getTime(), fetchedAt: Date.now(), factor: d.factor || 1 });
    } catch (e) { /* backend pas encore à jour : badge masqué */ }
  }, []);

  useEffect(() => { sync(); const t = setInterval(sync, 30000); return () => clearInterval(t); }, [sync]);
  useEffect(() => {
    const t = setInterval(() => {
      setBase((b) => {
        if (b) setNow(new Date(b.serverMs + (Date.now() - b.fetchedAt) * b.factor));
        return b;
      });
    }, 1000);
    return () => clearInterval(t);
  }, []);

  if (!now) return null;
  const jour = now.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short' });
  const heure = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const warp = base && base.factor !== 1;
  return <Text style={styles.clock}>{warp ? '⏩ ' : '🕐 '}{jour} · {heure}{warp ? `  (x${base.factor})` : ''}</Text>;
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
        <ClockBadge />
      </View>
      <View style={{ flex: 1 }}>{tab === 'chat' ? <Chat /> : <Dashboard />}</View>
      {!(kbd && tab === 'chat') && (
        <View style={styles.tabs}>
          <TouchableOpacity style={[styles.tab, tab === 'chat' && styles.tabActive]} onPress={() => setTab('chat')}>
            <Text style={[styles.tabTxt, tab === 'chat' && styles.tabTxtActive]}>💬 Chat</Text>
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
  clock: { color: '#dfe6c8', fontSize: 12, marginTop: 2, fontVariant: ['tabular-nums'] },
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
});
