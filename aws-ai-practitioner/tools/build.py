"""Builds ../data.js from the content files in this folder."""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__))
p = lambda f: os.path.join(H, f)
raw = {q['src']: q for q in json.load(open(p('source_questions.json')))}
# Low-value items removed in the quality pass: trivia with throwaway distractors, or duplicates.
DROP = set('P4 P7 P9 P10 P12 P14 P15 P31 P34 P37 P38 P40 P42 P46 P49 P51 P52 P53 P54 P58 P61 P65 P67 P68 P71 P72 P73 P75 P76 P79 P82 P85 P87 P89 P93 P94'.split())
SCEN = re.compile(r'\b(company|team|organization|bank|hospital|startup|retailer|firm|institution|developer|practitioner|agency|manufacturer|analyst|platform)\b', re.I)
def level(q):
    if q.get('t') in ('match', 'order'): return 2
    t = q['q']
    if SCEN.search(t) and len(t) > 110: return 3
    return 1 if len(t) < 95 else 2
REWRITE = {'P3': 'A retail company wants to determine whether customer reviews are positive or negative. Which AWS service is best suited for this task?'}
Q = []
for line in open(p('notes.txt')):
    line = line.strip()
    if not line or line.startswith('#'): continue
    src, d, ans, x = line.split('|', 3)
    if src in DROP: continue
    r = raw[src]
    opts = [t for _, t in r['o']]
    a = [ord(c) - 65 for c in ans.split(',')]
    q = REWRITE.get(src, r['q'])
    if len(a) > 1 and 'Choose' not in q: q += ' (Choose %s.)' % ['', '', 'TWO', 'THREE'][len(a)]
    Q.append(dict(id=src, d=int(d), t='mr' if len(a) > 1 else 'mc', q=q, o=opts, a=a, x=x))
for i, line in enumerate(open(p('authored.jsonl'))):
    if not line.strip(): continue
    o = json.loads(line); o['id'] = 'N%d' % (i + 1)
    o.setdefault('t', 'mr' if len(o.get('a', [])) > 1 else 'mc')
    Q.append(o)
for i, line in enumerate(open(p('scenarios.jsonl'))):
    if not line.strip(): continue
    o = json.loads(line); o['id'] = 'X%d' % (i + 1); o['l'] = 3 if o.get('t') not in ('match', 'order') else 2
    o.setdefault('t', 'mr' if len(o.get('a', [])) > 1 else 'mc')
    Q.append(o)
for q in Q: q.setdefault('l', level(q))
# AWS service catalog -> service cards + generated service questions
import random
rnd = random.Random(7)
SV = [json.loads(l) for l in open(p('services.jsonl')) if l.strip()]
GROUP = {'ml': 'sm', 'q': 'genai', 'infra': 'data'}
for i, v in enumerate(SV): v['id'] = 'V%d' % i; v['g'] = GROUP.get(v['c'], v['c'])
def others(v, k=3):
    same = [o for o in SV if o['g'] == v['g'] and o['n'] != v['n']]
    if len(same) < k: same += [o for o in SV if o['d'] == v['d'] and o['n'] != v['n'] and o not in same]
    return rnd.sample(same, k)
clean = lambda t: re.sub(r'\s*\(use [^)]*\)|\s*\([A-Z][^)]*\)$', '', t).strip()
for v in SV:
    for j, u in enumerate(v['use']):
        ds = others(v)
        Q.append(dict(id='%su%d' % (v['id'], j), d=v['d'], l=2, t='mc', svc=1, q='A company wants to %s. Which AWS service or feature should it use?' % u,
                      o=[v['n']] + [o['n'] for o in ds], a=[0], x='%s: %s Exam cue: %s.' % (v['n'], v['what'], v['cue'])))
    ds = others(v)
    Q.append(dict(id='%sw' % v['id'], d=v['d'], l=1, t='mc', svc=1, q='Which statement BEST describes %s?' % v['n'],
                  o=[v['what']] + [o['what'] for o in ds], a=[0], x='The other options describe %s.' % ', '.join(o['n'] for o in ds)))
    if v['not'] and len(v['use']) >= 2:
        bad = v['not'][0]
        Q.append(dict(id='%sn' % v['id'], d=v['d'], l=2, t='mc', svc=1, q='Which use case is NOT a good fit for %s?' % v['n'],
                      o=[clean(bad)[0].upper() + clean(bad)[1:]] + [u[0].upper() + u[1:] for u in v['use'][:3]], a=[0], x='%s → %s' % (clean(bad), bad[len(clean(bad)):].strip(' ()') or 'use a different service') + '. %s is for: %s.' % (v['n'], '; '.join(v['use']))))
C = [dict(json.loads(l), id='K%d' % i) for i, l in enumerate(open(p('concepts.jsonl'))) if l.strip()]
W = []
for l in open(p('warmups.txt')):
    if l.strip() and not l.startswith('#'):
        c, d, k, a = l.rstrip('\n').split('|'); W.append(dict(id='W%d' % len(W), c=c, d=int(d), k=k, a=a))
TF = []
for l in open(p('tf.txt')):
    if l.strip() and not l.startswith('#'):
        d, v, s, w = l.rstrip('\n').split('|'); TF.append(dict(id='T%d' % len(TF), d=int(d), v=v == 'T', s=s, x=w))
for q in Q:
    assert q['t'] in ('match', 'order') or (q['o'] and all(0 <= i < len(q['o']) for i in q['a'])), q['id']
out = dict(questions=Q, concepts=C, warmups=W, tf=TF, services=SV)
open(p('../data.js'), 'w').write('window.DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
from collections import Counter
print(len(Q), 'questions', Counter(q['l'] for q in Q), sum(1 for q in Q if q.get('svc')), 'svc-generated', Counter(q['d'] for q in Q), Counter(q['t'] for q in Q), len(C), 'concepts', len(W), 'warmups', len(TF), 'tf')
