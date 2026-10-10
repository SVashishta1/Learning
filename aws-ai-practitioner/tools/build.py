"""Builds ../data.js from the content files in this folder."""
import json, os, re
H = os.path.dirname(os.path.abspath(__file__))
p = lambda f: os.path.join(H, f)
raw = {q['src']: q for q in json.load(open(p('source_questions.json')))}
REWRITE = {'P3': 'A retail company wants to determine whether customer reviews are positive or negative. Which AWS service is best suited for this task?'}
Q = []
for line in open(p('notes.txt')):
    line = line.strip()
    if not line or line.startswith('#'): continue
    src, d, ans, x = line.split('|', 3)
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
out = dict(questions=Q, concepts=C, warmups=W, tf=TF)
open(p('../data.js'), 'w').write('window.DATA=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
from collections import Counter
print(len(Q), 'questions', Counter(q['d'] for q in Q), Counter(q['t'] for q in Q), len(C), 'concepts', len(W), 'warmups', len(TF), 'tf')
