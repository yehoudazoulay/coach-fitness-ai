import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  SafeAreaView, View, Text, TextInput, TouchableOpacity, ScrollView,
  ActivityIndicator, StyleSheet, Platform, Keyboard, Modal, KeyboardAvoidingView,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';

// ⚙️ Config — change l'URL si ton backend Render a un autre nom, et l'user si besoin.
const API_URL = 'https://coach-fitness-ai.onrender.com';
const USER = 'app:yehouda';

// 🎨 Thème « dark tactique »
const C = {
  bg: '#14181c', card: '#1e2429', card2: '#252c32', border: '#2f383f',
  text: '#e8ece9', muted: '#8b969b', accent: '#b6ff3a', khaki: '#8a9a5b',
  danger: '#ff5a4d', warn: '#e0a020', ok: '#7bd66a',
};

async function api(path, options) {
  const res = await fetch(`${API_URL}${path}`, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
async function apiSend(path, method, body) {
  return api(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
}
const U = encodeURIComponent(USER);
const saveItem = (kind, id, fields) => id
  ? apiSend(`/api/${U}/items/${kind}/${id}`, 'PATCH', fields)
  : apiSend(`/api/${U}/items/${kind}`, 'POST', fields);
const deleteItem = (kind, id) => apiSend(`/api/${U}/items/${kind}/${id}`, 'DELETE');
const saveProgram = (prog) => apiSend(`/api/${U}/program`, 'POST', prog);

// ─────────────────────────────────────────────────────────────────────────
// Schémas d'édition : quels champs pour chaque type de donnée de suivi.
const SCHEMAS = {
  goal: [
    { key: 'type', label: 'Type', type: 'select', options: ['objectif', 'motivation'] },
    { key: 'content', label: 'Contenu', type: 'text', placeholder: 'ex. perdre 5 kg' },
  ],
  motivation: [ // alias visuel -> même table goal
    { key: 'type', label: 'Type', type: 'select', options: ['objectif', 'motivation'] },
    { key: 'content', label: 'Contenu', type: 'text' },
  ],
  fact: [
    { key: 'category', label: 'Catégorie', type: 'select', options: ['boulot', 'routine', 'social', 'contrainte', 'preference', 'sante_fond'] },
    { key: 'content', label: 'Info', type: 'text' },
  ],
  measurement: [
    { key: 'metric', label: 'Mesure', type: 'text', placeholder: 'poids, tour_bras, taux_gras...' },
    { key: 'value', label: 'Valeur', type: 'number' },
    { key: 'unit', label: 'Unité', type: 'text', placeholder: 'kg, cm, %' },
  ],
  milestone: [
    { key: 'label', label: 'Jalon', type: 'text', placeholder: 'ex. mariage' },
    { key: 'target_date', label: 'Date (AAAA-MM-JJ)', type: 'text', placeholder: '2026-09-01' },
  ],
  event: [
    { key: 'kind', label: 'Type', type: 'select', options: ['sante', 'blessure', 'moral', 'perso', 'social', 'boulot'] },
    { key: 'content', label: 'Détail', type: 'text' },
    { key: 'status', label: 'Statut', type: 'select', options: ['actif', 'amélioration', 'rémission', 'résolu', 'aggravation'] },
  ],
  workout: [
    { key: 'performed_at', label: 'Date/heure (AAAA-MM-JJTHH:MM)', type: 'text', placeholder: '2026-07-14T18:00' },
    { key: 'done', label: 'Statut', type: 'toggle', on: 'Faite', off: 'Manquée', default: true },
    { key: 'intensity', label: 'Intensité /10', type: 'number' },
    { key: 'session_name', label: 'Séance', type: 'text', placeholder: 'jambes, full body...' },
    { key: 'feeling', label: 'Ressenti', type: 'text', placeholder: 'bien, cramé...' },
  ],
};

// ─────────────────────────────────────────────────────────────────────────
// Modale générique d'édition / ajout / suppression.
function EditModal({ visible, title, kind, id, initial, onClose, onSaved }) {
  const schema = SCHEMAS[kind] || [];
  const [vals, setVals] = useState({});
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!visible) return;
    const seed = {};
    for (const f of schema) {
      const v = initial ? initial[f.key] : undefined;
      seed[f.key] = v != null ? v : (f.type === 'toggle' ? (f.default ?? true) : '');
    }
    setVals(seed);
  }, [visible, kind, id]);

  const realKind = kind === 'motivation' ? 'goal' : kind;

  const submit = async () => {
    const payload = {};
    for (const f of schema) {
      const v = vals[f.key];
      if (f.type === 'toggle') payload[f.key] = !!v;
      else if (f.type === 'number') { if (v !== '' && v != null) payload[f.key] = Number(v); }
      else if (v != null && String(v).trim() !== '') payload[f.key] = String(v).trim();
    }
    setBusy(true);
    try { await saveItem(realKind, id, payload); onSaved(); }
    catch (e) { /* garde ouvert */ } finally { setBusy(false); }
  };
  const remove = async () => {
    setBusy(true);
    try { await deleteItem(realKind, id); onSaved(); }
    catch (e) {} finally { setBusy(false); }
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalWrap}>
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>{title}</Text>
          <ScrollView style={{ maxHeight: 360 }} keyboardShouldPersistTaps="handled">
            {schema.map((f) => (
              <View key={f.key} style={{ marginBottom: 12 }}>
                <Text style={styles.fieldLabel}>{f.label}</Text>
                {f.type === 'select' ? (
                  <View style={styles.chipsRow}>
                    {f.options.map((o) => (
                      <TouchableOpacity key={o} onPress={() => setVals((s) => ({ ...s, [f.key]: o }))}
                        style={[styles.chip, vals[f.key] === o && styles.chipOn]}>
                        <Text style={[styles.chipTxt, vals[f.key] === o && styles.chipTxtOn]}>{o}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                ) : f.type === 'toggle' ? (
                  <View style={styles.chipsRow}>
                    {[[true, f.on], [false, f.off]].map(([bv, lbl]) => (
                      <TouchableOpacity key={String(bv)} onPress={() => setVals((s) => ({ ...s, [f.key]: bv }))}
                        style={[styles.chip, !!vals[f.key] === bv && styles.chipOn]}>
                        <Text style={[styles.chipTxt, !!vals[f.key] === bv && styles.chipTxtOn]}>{lbl}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                ) : (
                  <TextInput
                    style={styles.field}
                    value={vals[f.key] != null ? String(vals[f.key]) : ''}
                    onChangeText={(t) => setVals((s) => ({ ...s, [f.key]: t }))}
                    placeholder={f.placeholder || ''}
                    placeholderTextColor={C.muted}
                    keyboardType={f.type === 'number' ? 'numeric' : 'default'}
                  />
                )}
              </View>
            ))}
          </ScrollView>
          <View style={styles.modalBtns}>
            {id ? (
              <TouchableOpacity onPress={remove} style={[styles.mBtn, styles.mDel]} disabled={busy}>
                <Text style={styles.mDelTxt}>Supprimer</Text>
              </TouchableOpacity>
            ) : <View />}
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <TouchableOpacity onPress={onClose} style={[styles.mBtn, styles.mCancel]} disabled={busy}>
                <Text style={styles.mCancelTxt}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={submit} style={[styles.mBtn, styles.mSave]} disabled={busy}>
                <Text style={styles.mSaveTxt}>{busy ? '…' : 'Enregistrer'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}

// Éditeur de programme : nom, fréquence, séances et exercices (ajout/suppression).
function ProgramEditor({ visible, initial, onClose, onSaved }) {
  const [name, setName] = useState('');
  const [freq, setFreq] = useState('');
  const [seances, setSeances] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!visible) return;
    setName(initial?.name || '');
    setFreq(initial?.frequence != null ? String(initial.frequence) : '');
    setSeances((initial?.seances || []).map((s) => ({
      nom: s.nom || '', jour: s.jour || '',
      exos: (s.exos || []).map((e) => ({
        exo: e.exo || '', series: e.series != null ? String(e.series) : '', reps: e.reps != null ? String(e.reps) : '',
      })),
    })));
  }, [visible]);

  const edit = (mut) => setSeances((prev) => {
    const c = prev.map((s) => ({ ...s, exos: s.exos.map((e) => ({ ...e })) }));
    mut(c); return c;
  });
  const save = async () => {
    const prog = {
      name: name.trim() || 'Programme',
      frequence: freq ? Number(freq) : null,
      seances: seances.map((s) => ({
        nom: s.nom.trim(), jour: s.jour.trim() || null,
        exos: s.exos.filter((e) => e.exo.trim()).map((e) => ({
          exo: e.exo.trim(), series: e.series ? Number(e.series) : null, reps: e.reps.trim(),
        })),
      })),
    };
    setBusy(true);
    try { await saveProgram(prog); onSaved(); } catch (e) {} finally { setBusy(false); }
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.modalWrap}>
        <View style={[styles.modalCard, { maxHeight: '88%' }]}>
          <Text style={styles.modalTitle}>🏋️ Modifier le programme</Text>
          <ScrollView keyboardShouldPersistTaps="handled">
            <Text style={styles.fieldLabel}>Nom</Text>
            <TextInput style={styles.field} value={name} onChangeText={setName} placeholder="ex. Push / Pull / Legs" placeholderTextColor={C.muted} />
            <Text style={[styles.fieldLabel, { marginTop: 12 }]}>Séances / semaine</Text>
            <TextInput style={styles.field} value={freq} onChangeText={setFreq} keyboardType="numeric" placeholder="3" placeholderTextColor={C.muted} />

            {seances.map((s, i) => (
              <View key={i} style={styles.seanceEdit}>
                <View style={styles.rowBetween}>
                  <Text style={styles.seanceEditTitle}>Séance {i + 1}</Text>
                  <TouchableOpacity onPress={() => edit((c) => c.splice(i, 1))}><Text style={styles.delX}>✕</Text></TouchableOpacity>
                </View>
                <TextInput style={styles.field} value={s.nom} onChangeText={(t) => edit((c) => { c[i].nom = t; })} placeholder="Nom (ex. Push)" placeholderTextColor={C.muted} />
                <TextInput style={[styles.field, { marginTop: 6 }]} value={s.jour} onChangeText={(t) => edit((c) => { c[i].jour = t; })} placeholder="Jour (optionnel)" placeholderTextColor={C.muted} />
                {s.exos.map((e, j) => (
                  <View key={j} style={styles.exoRow}>
                    <TextInput style={[styles.field, styles.exoName]} value={e.exo} onChangeText={(t) => edit((c) => { c[i].exos[j].exo = t; })} placeholder="Exercice" placeholderTextColor={C.muted} />
                    <TextInput style={[styles.field, styles.exoNum]} value={e.series} onChangeText={(t) => edit((c) => { c[i].exos[j].series = t; })} keyboardType="numeric" placeholder="sér." placeholderTextColor={C.muted} />
                    <TextInput style={[styles.field, styles.exoNum]} value={e.reps} onChangeText={(t) => edit((c) => { c[i].exos[j].reps = t; })} placeholder="reps" placeholderTextColor={C.muted} />
                    <TouchableOpacity onPress={() => edit((c) => c[i].exos.splice(j, 1))}><Text style={styles.delX}>✕</Text></TouchableOpacity>
                  </View>
                ))}
                <TouchableOpacity onPress={() => edit((c) => c[i].exos.push({ exo: '', series: '', reps: '' }))} style={styles.miniAdd}>
                  <Text style={styles.miniAddTxt}>＋ exercice</Text>
                </TouchableOpacity>
              </View>
            ))}
            <TouchableOpacity onPress={() => setSeances((p) => [...p, { nom: '', jour: '', exos: [] }])} style={[styles.addPill, { alignSelf: 'flex-start', marginTop: 14 }]}>
              <Text style={styles.addPillTxt}>＋ Séance</Text>
            </TouchableOpacity>
            <View style={{ height: 10 }} />
          </ScrollView>
          <View style={styles.modalBtns}>
            <View />
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <TouchableOpacity onPress={onClose} style={[styles.mBtn, styles.mCancel]} disabled={busy}><Text style={styles.mCancelTxt}>Annuler</Text></TouchableOpacity>
              <TouchableOpacity onPress={save} style={[styles.mBtn, styles.mSave]} disabled={busy}><Text style={styles.mSaveTxt}>{busy ? '…' : 'Enregistrer'}</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}

// Petit hook : gère l'ouverture de la modale d'édition pour une vue.
function useEditor(reload) {
  const [ed, setEd] = useState(null); // {kind,title,id,initial}
  const open = (kind, title, item, pick) => {
    const id = item ? (kind === 'event' ? item.event_key : item.id) : null;
    const initial = item && pick ? pick(item) : (item || null);
    setEd({ kind, title, id, initial });
  };
  const node = ed ? (
    <EditModal visible title={ed.title} kind={ed.kind} id={ed.id} initial={ed.initial}
      onClose={() => setEd(null)} onSaved={() => { setEd(null); reload(); }} />
  ) : null;
  return { open, node };
}

function AddBtn({ onPress }) {
  return (
    <TouchableOpacity onPress={onPress} style={styles.addBtn}>
      <Text style={styles.addTxt}>＋</Text>
    </TouchableOpacity>
  );
}
function Card({ title, onAdd, children }) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHead}>
        <Text style={styles.cardTitle}>{title}</Text>
        {onAdd && <AddBtn onPress={onAdd} />}
      </View>
      {children}
    </View>
  );
}
function EditRow({ onPress, children }) {
  return (
    <TouchableOpacity onPress={onPress} style={styles.editRow} activeOpacity={0.6}>
      <View style={{ flex: 1 }}>{children}</View>
      <Text style={styles.pencil}>✎</Text>
    </TouchableOpacity>
  );
}

// ─────────────────────────────────────────────────────────────────────────
function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const data = await api(`/api/${U}/messages?limit=100`);
      const server = data.messages || [];
      setMessages((prev) => (server.length < prev.length ? prev : server));
    } catch (e) { /* réseau : on garde l'affichage */ }
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { const t = setInterval(load, 8000); return () => clearInterval(t); }, [load]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setSending(true);
    try {
      const data = await apiSend('/api/chat', 'POST', { user: USER, message: text });
      setMessages((m) => [...m, { role: 'assistant', content: data.reply }]);
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', content: '(erreur réseau — réessaie)' }]);
    } finally { setSending(false); }
  };

  return (
    <View style={{ flex: 1 }}>
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
        {sending && <ActivityIndicator style={{ margin: 10 }} color={C.accent} />}
      </ScrollView>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Écris au Sergent…"
          placeholderTextColor={C.muted}
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

// ─────────────────────────────────────────────────────────────────────────
function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(() => {
    setLoading(true);
    api(`/api/${U}/dashboard`).then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);
  useEffect(() => { load(); }, [load]);
  const { open, node } = useEditor(load);
  const [progOpen, setProgOpen] = useState(false);

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={C.accent} />;
  if (!data) return <Text style={styles.muted}>Impossible de charger (le service Render se réveille peut-être, réessaie dans 1 min).</Text>;
  const adh = data.adherence || {};

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 14 }}>
      <TouchableOpacity onPress={load} style={styles.refresh}><Text style={styles.refreshTxt}>↻ Rafraîchir</Text></TouchableOpacity>

      <View style={styles.statRow}>
        <View style={styles.stat}>
          <Text style={styles.statBig}>{adh.seances_cette_semaine ?? 0}{adh.objectif_semaine ? `/${adh.objectif_semaine}` : ''}</Text>
          <Text style={styles.statLbl}>séances / sem.</Text>
        </View>
        <View style={styles.stat}>
          <Text style={styles.statBig}>{adh.jours_depuis_derniere != null ? adh.jours_depuis_derniere : '—'}</Text>
          <Text style={styles.statLbl}>j. depuis la dernière</Text>
        </View>
      </View>

      <Card title="🎯 Objectifs & motivations" onAdd={() => open('goal', 'Nouvel objectif / motivation', null)}>
        {(data.goals || []).map((g, i) => (
          <EditRow key={i} onPress={() => open('goal', 'Modifier', g, (x) => ({ type: x.type, content: x.content }))}>
            <Text style={styles.line}><Text style={styles.tag}>{g.type}</Text>  {g.content}</Text>
          </EditRow>
        ))}
        {!(data.goals || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="⏰ Prochaine séance">
        <Text style={styles.line}>{data.prochaine_seance ? data.prochaine_seance.scheduled_at.replace('T', ' à ') : 'aucune prévue'}</Text>
      </Card>

      <View style={styles.card}>
        <View style={styles.cardHead}>
          <Text style={styles.cardTitle}>🏋️ Programme</Text>
          <TouchableOpacity onPress={() => setProgOpen(true)} style={styles.editPill}>
            <Text style={styles.editPillTxt}>{data.programme ? '✎ Modifier' : '＋ Créer'}</Text>
          </TouchableOpacity>
        </View>
        {data.programme ? (
          <>
            <Text style={styles.bold}>{data.programme.name} — {data.programme.frequence}x/sem</Text>
            {(data.programme.seances || []).map((s, i) => (
              <View key={i} style={{ marginTop: 6 }}>
                <Text style={styles.bold}>{s.jour ? s.jour + ' — ' : ''}{s.nom}</Text>
                {(s.exos || []).map((e, j) => <Text key={j} style={styles.muted}>   · {e.exo} {e.series ? `${e.series}x${e.reps}` : e.reps}</Text>)}
              </View>
            ))}
          </>
        ) : <Text style={styles.muted}>pas encore de programme</Text>}
      </View>

      <Card title="🏁 Jalons" onAdd={() => open('milestone', 'Nouveau jalon', null)}>
        {(data.jalons || []).map((m, i) => (
          <EditRow key={i} onPress={() => open('milestone', 'Modifier le jalon', m, (x) => ({ label: x.label, target_date: x.target_date }))}>
            <Text style={styles.line}>{m.label} : <Text style={styles.accentTxt}>dans {m.jours} j</Text></Text>
          </EditRow>
        ))}
        {!(data.jalons || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="📏 Mesures" onAdd={() => open('measurement', 'Nouvelle mesure', null)}>
        {(data.mesures || []).map((m, i) => (
          <EditRow key={i} onPress={() => open('measurement', 'Modifier la mesure', m, (x) => ({ metric: x.metric, value: x.value, unit: x.unit }))}>
            <Text style={styles.line}>{m.metric} : <Text style={styles.accentTxt}>{m.value}{m.unit || ''}</Text></Text>
          </EditRow>
        ))}
        {!(data.mesures || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="🩹 En ce moment" onAdd={() => open('event', 'Nouvel élément', null)}>
        {(data.events || []).map((e, i) => (
          <EditRow key={i} onPress={() => open('event', 'Modifier', e, (x) => ({ kind: x.kind, content: x.content, status: x.status }))}>
            <Text style={styles.line}><Text style={styles.tag}>{e.kind}</Text>  {e.content} <Text style={styles.muted}>({e.status})</Text></Text>
          </EditRow>
        ))}
        {!(data.events || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <Card title="🧠 Infos perso" onAdd={() => open('fact', 'Nouvelle info', null)}>
        {(data.facts || []).map((f, i) => (
          <EditRow key={i} onPress={() => open('fact', 'Modifier', f, (x) => ({ category: x.category, content: x.content }))}>
            <Text style={styles.line}><Text style={styles.tag}>{f.category}</Text>  {f.content}</Text>
          </EditRow>
        ))}
        {!(data.facts || []).length && <Text style={styles.muted}>—</Text>}
      </Card>

      <View style={{ height: 40 }} />
      {node}
      <ProgramEditor visible={progOpen} initial={data.programme}
        onClose={() => setProgOpen(false)} onSaved={() => { setProgOpen(false); load(); }} />
    </ScrollView>
  );
}

// ─────────────────────────────────────────────────────────────────────────
function Seances() {
  const [seances, setSeances] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = useCallback(() => {
    setLoading(true);
    api(`/api/${U}/workouts?limit=40`).then((d) => setSeances(d.seances || [])).catch(() => setSeances(null)).finally(() => setLoading(false));
  }, []);
  useEffect(() => { load(); }, [load]);
  const { open, node } = useEditor(load);

  if (loading) return <ActivityIndicator style={{ marginTop: 40 }} color={C.accent} />;
  if (!seances) return <Text style={styles.muted}>Impossible de charger (réessaie).</Text>;

  const MAX_H = 120;
  const barColor = (n) => (n >= 8 ? C.danger : n >= 5 ? C.warn : C.accent);
  const d2 = (n) => String(n).padStart(2, '0');
  const fmtDay = (iso) => { const d = new Date(iso); return `${d2(d.getDate())}/${d2(d.getMonth() + 1)}`; };
  const fmtFull = (iso) => new Date(iso).toLocaleString('fr-FR', { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  const pick = (x) => ({ performed_at: x.performed_at?.slice(0, 16), done: x.done, intensity: x.intensity, session_name: x.session_name, feeling: x.feeling });

  return (
    <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 14 }}>
      <View style={styles.rowBetween}>
        <TouchableOpacity onPress={load}><Text style={styles.refreshTxt}>↻ Rafraîchir</Text></TouchableOpacity>
        <TouchableOpacity onPress={() => open('workout', 'Ajouter une séance', null)} style={styles.addPill}>
          <Text style={styles.addPillTxt}>＋ Séance</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.cardTitle}>📈 Intensité ressentie (/10)</Text>
      {seances.length === 0 ? (
        <Text style={styles.muted}>Aucune séance. Parle de tes séances au Sergent (faite ou pas, comment c'était) — ça se remplit tout seul. Ou ajoute-les à la main avec ＋.</Text>
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
                      <View style={[styles.bar, { height: Math.max(h, 8), backgroundColor: s.intensity ? barColor(s.intensity) : C.muted }]} />
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
      <Text style={styles.legend}>Vert = léger · Orange = soutenu · Rouge = très dur · ✗ = manquée</Text>

      <Text style={[styles.cardTitle, { marginTop: 20 }]}>🗒️ Historique</Text>
      {[...seances].reverse().map((s, i) => (
        <TouchableOpacity key={i} onPress={() => open('workout', 'Modifier la séance', s, pick)} style={styles.seanceCard} activeOpacity={0.6}>
          <View style={styles.seanceHead}>
            <Text style={styles.seanceDate}>{fmtFull(s.performed_at)}</Text>
            <Text style={s.done ? styles.badgeOk : styles.badgeKo}>{s.done ? '✅ Faite' : '❌ Manquée'}</Text>
          </View>
          {s.done && s.intensity != null && <Text style={styles.seanceInt}>Intensité : {s.intensity}/10</Text>}
          {(s.session_name || s.feeling) ? (
            <Text style={styles.muted}>{s.session_name || 'séance'}{s.feeling ? ` — « ${s.feeling} »` : ''}</Text>
          ) : null}
        </TouchableOpacity>
      ))}
      <View style={{ height: 40 }} />
      {node}
    </ScrollView>
  );
}

// ─────────────────────────────────────────────────────────────────────────
function ClockBar() {
  const [base, setBase] = useState(null);
  const [now, setNow] = useState(null);
  const [accel, setAccel] = useState(null);

  const sync = useCallback(async () => {
    try {
      const d = await api('/api/clock');
      setBase({ serverMs: new Date(d.now).getTime(), fetchedAt: Date.now(), factor: d.factor || 1 });
      setAccel(!!d.accelerated);
    } catch (e) {}
  }, []);
  useEffect(() => { sync(); const t = setInterval(sync, 15000); return () => clearInterval(t); }, [sync]);
  useEffect(() => {
    const t = setInterval(() => {
      setBase((b) => { if (b) setNow(new Date(b.serverMs + (Date.now() - b.fetchedAt) * b.factor)); return b; });
    }, 1000);
    return () => clearInterval(t);
  }, []);

  const toggle = async () => {
    const next = !accel;
    setAccel(next);
    try { await apiSend('/api/clock/mode', 'POST', { accelerated: next }); sync(); }
    catch (e) { setAccel(!next); }
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

  const TABS = [['chat', '💬 Chat'], ['seances', '📈 Séances'], ['dashboard', '📊 Suivi']];
  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.header}>
          <Text style={styles.headerTxt}>🎖️ LE SERGENT</Text>
          <ClockBar />
        </View>
        <View style={{ flex: 1 }}>
          {tab === 'chat' ? <Chat /> : tab === 'seances' ? <Seances /> : <Dashboard />}
        </View>
        {!(kbd && tab === 'chat') && (
          <View style={styles.tabs}>
            {TABS.map(([k, lbl]) => (
              <TouchableOpacity key={k} style={[styles.tab, tab === k && styles.tabActive]} onPress={() => setTab(k)}>
                <Text style={[styles.tabTxt, tab === k && styles.tabTxtActive]}>{lbl}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  header: { backgroundColor: '#0f1317', paddingVertical: 12, alignItems: 'center', borderBottomWidth: 1, borderBottomColor: C.border },
  headerTxt: { color: C.accent, fontSize: 18, fontWeight: '800', letterSpacing: 2 },
  // Chat
  chat: { flex: 1, paddingHorizontal: 12 },
  bubble: { maxWidth: '84%', padding: 11, borderRadius: 14, marginVertical: 4 },
  user: { alignSelf: 'flex-end', backgroundColor: '#3d4a24' },
  coach: { alignSelf: 'flex-start', backgroundColor: C.card2, borderWidth: 1, borderColor: C.border },
  userText: { color: '#eaf5d8', fontSize: 15 },
  coachText: { color: C.text, fontSize: 15 },
  inputRow: { flexDirection: 'row', padding: 8, backgroundColor: '#0f1317', alignItems: 'center', borderTopWidth: 1, borderTopColor: C.border },
  input: { flex: 1, backgroundColor: C.card2, color: C.text, borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 15 },
  sendBtn: { marginLeft: 8, backgroundColor: C.accent, width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  sendTxt: { color: '#14181c', fontSize: 16, fontWeight: '800' },
  // Cards & rows
  card: { backgroundColor: C.card, borderRadius: 14, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  cardHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  cardTitle: { fontWeight: '800', fontSize: 15, color: C.text, letterSpacing: 0.5 },
  line: { fontSize: 14, color: C.text, marginVertical: 3, lineHeight: 20 },
  bold: { fontSize: 14, color: C.text, fontWeight: '700' },
  muted: { fontSize: 13, color: C.muted, marginVertical: 2 },
  accentTxt: { color: C.accent, fontWeight: '700' },
  tag: { color: C.khaki, fontWeight: '800', fontSize: 12, textTransform: 'uppercase' },
  editRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 2 },
  pencil: { color: C.muted, fontSize: 15, paddingLeft: 8 },
  addBtn: { width: 28, height: 28, borderRadius: 14, backgroundColor: C.card2, borderWidth: 1, borderColor: C.khaki, alignItems: 'center', justifyContent: 'center' },
  addTxt: { color: C.accent, fontSize: 18, fontWeight: '800', lineHeight: 20 },
  // Stats
  statRow: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  stat: { flex: 1, backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, padding: 14, alignItems: 'center' },
  statBig: { fontSize: 30, fontWeight: '900', color: C.accent },
  statLbl: { fontSize: 11, color: C.muted, marginTop: 2, textTransform: 'uppercase', letterSpacing: 0.5 },
  refresh: { alignSelf: 'flex-end', marginBottom: 6 },
  refreshTxt: { color: C.khaki, fontWeight: '700' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  addPill: { backgroundColor: C.accent, borderRadius: 16, paddingHorizontal: 12, paddingVertical: 6 },
  addPillTxt: { color: '#14181c', fontWeight: '800', fontSize: 13 },
  editPill: { borderRadius: 16, paddingHorizontal: 12, paddingVertical: 5, borderWidth: 1, borderColor: C.khaki },
  editPillTxt: { color: C.accent, fontWeight: '800', fontSize: 12 },
  // Éditeur de programme
  seanceEdit: { backgroundColor: C.card2, borderRadius: 12, padding: 12, marginTop: 14, borderWidth: 1, borderColor: C.border },
  seanceEditTitle: { color: C.accent, fontWeight: '800', fontSize: 14, marginBottom: 6 },
  delX: { color: C.danger, fontSize: 16, fontWeight: '800', paddingHorizontal: 6 },
  exoRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  exoName: { flex: 3 },
  exoNum: { flex: 1, textAlign: 'center', paddingHorizontal: 4 },
  miniAdd: { marginTop: 8, alignSelf: 'flex-start' },
  miniAddTxt: { color: C.khaki, fontWeight: '700', fontSize: 13 },
  // Chart
  chart: { backgroundColor: C.card, borderRadius: 14, paddingVertical: 12, marginTop: 8, borderWidth: 1, borderColor: C.border },
  chartRow: { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 10 },
  col: { alignItems: 'center', width: 34 },
  barVal: { fontSize: 11, color: C.muted, height: 14, fontWeight: '700' },
  barTrack: { width: '100%', justifyContent: 'flex-end', alignItems: 'center' },
  bar: { width: 16, borderRadius: 4 },
  missedMark: { color: C.danger, fontSize: 16, fontWeight: '800' },
  barDate: { fontSize: 9, color: C.muted, marginTop: 4 },
  legend: { fontSize: 11, color: C.muted, marginTop: 8, fontStyle: 'italic' },
  seanceCard: { backgroundColor: C.card, borderRadius: 12, padding: 12, marginTop: 8, borderWidth: 1, borderColor: C.border },
  seanceHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  seanceDate: { fontSize: 13, color: C.text, fontWeight: '700', textTransform: 'capitalize' },
  badgeOk: { fontSize: 12, color: C.ok, fontWeight: '800' },
  badgeKo: { fontSize: 12, color: C.danger, fontWeight: '800' },
  seanceInt: { fontSize: 13, color: C.accent, fontWeight: '800', marginTop: 4 },
  // Tabs
  tabs: { flexDirection: 'row', backgroundColor: '#0f1317', borderTopWidth: 1, borderTopColor: C.border },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center' },
  tabActive: { borderTopWidth: 3, borderTopColor: C.accent },
  tabTxt: { fontSize: 14, color: C.muted },
  tabTxtActive: { color: C.accent, fontWeight: '800' },
  // Clock
  clockBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 6, gap: 8 },
  clock: { color: C.muted, fontSize: 12, fontVariant: ['tabular-nums'] },
  warpBtn: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12, borderWidth: 1, borderColor: C.khaki },
  warpOn: { backgroundColor: C.accent, borderColor: C.accent },
  warpTxt: { color: C.khaki, fontSize: 11, fontWeight: '800' },
  warpTxtOn: { color: '#14181c' },
  // Modal
  modalWrap: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  modalCard: { backgroundColor: C.card, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, borderWidth: 1, borderColor: C.border },
  modalTitle: { color: C.text, fontSize: 17, fontWeight: '800', marginBottom: 16 },
  fieldLabel: { color: C.muted, fontSize: 12, marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  field: { backgroundColor: C.card2, color: C.text, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 15, borderWidth: 1, borderColor: C.border },
  chipsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 16, backgroundColor: C.card2, borderWidth: 1, borderColor: C.border },
  chipOn: { backgroundColor: C.accent, borderColor: C.accent },
  chipTxt: { color: C.muted, fontSize: 13, fontWeight: '600' },
  chipTxtOn: { color: '#14181c', fontWeight: '800' },
  modalBtns: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 },
  mBtn: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12 },
  mSave: { backgroundColor: C.accent }, mSaveTxt: { color: '#14181c', fontWeight: '800' },
  mCancel: { backgroundColor: C.card2, borderWidth: 1, borderColor: C.border }, mCancelTxt: { color: C.text, fontWeight: '600' },
  mDel: { backgroundColor: 'transparent', borderWidth: 1, borderColor: C.danger }, mDelTxt: { color: C.danger, fontWeight: '700' },
});
