"""Re-estimate frequencies for words missing from wordfreq (Zipf == 0).

Sources, in order: Norvig count_1w.txt (Google web corpus, https://norvig.com/ngrams/count_1w.txt),
then morphological base-word inference, then a length-based prior.
Words wordfreq already knows are left untouched. Usage:
  curl -o /tmp/count_1w.txt https://norvig.com/ngrams/count_1w.txt
  uv run python scripts/refine_frequencies.py /tmp/count_1w.txt
"""
import collections, json, math, sys
import wordfreq

PATH = 'data/words.json'
d = json.load(open(PATH))
norvig = {}
for line in open(sys.argv[1]):
    w, n = line.split()
    norvig[w] = int(n)
total = sum(norvig.values())

wf = lambda w: wordfreq.zipf_frequency(w, 'en')

def zipf(w):
    z = wf(w)
    if z > 0:
        return z
    if w in norvig:
        return max(0.5, math.log10(norvig[w] / total * 1e9) - 0.1)
    return 0

# calibrate Zipf -> 0-100 frequency using words already scored
pts = collections.defaultdict(list)
for w, f in d.items():
    z = wf(w)
    if z >= 1:
        pts[round(z * 5) / 5].append(f)
cal = sorted((z, sorted(v)[len(v) // 2]) for z, v in pts.items() if len(v) >= 5)

def tofreq(z):
    if z < cal[0][0]:
        return 5 + (cal[0][1] - 5) * max(z, 0) / cal[0][0]
    for (a, fa), (b, fb) in zip(cal, cal[1:]):
        if z <= b:
            return fa + (fb - fa) * (z - a) / (b - a)
    return cal[-1][1]

# (suffix, replacement, zipf penalty): inflections cost little, derivations more
RULES = [
    ('ies', 'y', .4), ('ied', 'y', .4), ('ing', '', .5), ('ing', 'e', .5), ('ings', '', .7),
    ('ings', 'e', .7), ('ed', '', .5), ('ed', 'e', .5), ('es', '', .4), ('s', '', .4),
    ('ers', '', .8), ('ers', 'e', .8), ('er', '', .7), ('er', 'e', .7), ('ier', 'y', .8),
    ('est', '', .9), ('est', 'e', .9), ('iest', 'y', .9), ('ly', '', .8), ('ily', 'y', .8),
    ('ally', 'al', .8), ('ically', 'ic', .8), ('ably', 'able', .8), ('ibly', 'ible', .8),
    ('ness', '', 1.0), ('iness', 'y', 1.0), ('ful', '', 1.0), ('less', '', 1.0),
    ('ment', '', 1.0), ('ments', '', 1.2), ('ism', '', 1.2), ('isms', '', 1.4), ('ist', '', 1.2),
    ('ists', '', 1.4), ('ity', '', 1.2), ('ities', '', 1.4), ('able', '', 1.0), ('able', 'e', 1.0),
    ('ize', 'e', 0.6), ('ise', 'e', 0.6), ('ized', 'ize', .5), ('ising', 'ise', .5), ('izing', 'ize', .5),
    ('ization', 'ize', 1.0), ('isation', 'ise', 1.0), ('ous', '', 1.0), ('ish', '', 1.0),
]
PREFIXES = ['un', 're', 'non', 'dis', 'mis', 'pre', 'anti', 'over', 'under', 'semi', 'sub', 'de']

def candidates(w):
    for suf, rep, pen in RULES:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            b = w[:-len(suf)] + rep
            yield b, pen
            if len(b) > 3 and b[-1] == b[-2]:
                yield b[:-1], pen
    for p in PREFIXES:
        if w.startswith(p) and len(w) - len(p) >= 4:
            yield w[len(p):], 1.0

def estimate(w):
    z = zipf(w)
    if z > 0:
        return z, 'corpus'
    best = 0
    for b, pen in candidates(w):
        if b in d:
            zb = zipf(b)
            if zb > 0:
                best = max(best, zb - pen)
    if best > 0.3:
        return min(best, 2.5), 'morph'
    # no evidence: longer words are rarer
    return max(0.0, 0.8 - 0.06 * max(0, len(w) - 5)), 'prior'

stats = collections.Counter()
for w in d:
    if wf(w) > 0:
        continue
    z, how = estimate(w)
    d[w] = round(tofreq(z), 1)
    stats[how] += 1
print(dict(stats))
json.dump(d, open(PATH, 'w'), separators=(',', ':'))
