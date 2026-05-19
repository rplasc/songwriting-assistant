"""Puerto Rican / Reggaetón slang supplementary frequency map.

Words are assigned synthetic frequencies in the 1e-7..3e-5 band:
  - 1e-5..3e-5  : broadly known, mainstream usage (guagua, chavos, flow)
  - 1e-6..9e-6  : common within the genre / community (perreo, bregar, janguear)
  - 1e-7..9e-7  : niche or very recent coinage (tiraera, bellaqueo)

Frequencies are floors: if wordfreq already knows the word at a higher value,
the max() in SpanishEngine.frequency() keeps the real value.  Words already in
the top-150k wordfreq corpus are skipped during corpus build (they're indexed
from wordfreq at a better frequency), but the floor ensures ranking never
demotes them below common Spanish words when they do appear.
"""

PR_SLANG: dict[str, float] = {
    # --- Everyday PR vocabulary ---
    "guagua": 2e-5,      # bus (PR/Cuba)
    "chavos": 1e-5,      # money/cents
    "bregar": 8e-6,      # to deal with / work hard
    "mai": 1e-5,         # mom
    "pai": 1e-5,         # dad
    "pana": 1e-5,        # friend/buddy
    "bicho": 8e-6,       # bug / PR slang for cool guy
    "bichote": 1e-6,     # top dog / boss in the game
    "cangri": 1e-6,      # cool / fly
    "brutal": 3e-5,      # awesome / intense (widely used)
    "jevo": 2e-6,        # boyfriend / dude
    "jeva": 2e-6,        # girlfriend / girl
    "pichear": 1e-6,     # to ignore / blow off
    "vacilón": 3e-6,     # fun / joke (also general Spanish but very PR)
    "bichiyal": 5e-7,    # variant of bichote
    "corillo": 2e-6,     # crew / group of friends
    "palante": 5e-6,     # forward / let's go (also written pa'lante)
    "chambear": 2e-6,    # to work a gig
    "llave": 8e-6,       # key / close friend (also Colombia)
    "mero": 6e-6,        # the main one / the real deal
    "tiraera": 1e-6,     # diss track / rap battle shot
    "tirador": 1e-6,     # one who throws diss tracks
    # --- Reggaetón / perreo specific ---
    "perreo": 5e-6,      # grinding dance style
    "perreito": 1e-6,    # diminutive of perreo
    "perrea": 3e-6,      # to dance perreo (conjugated form)
    "gata": 8e-6,        # cat / attractive woman in slang
    "janguear": 2e-6,    # to hang out (from "hang")
    "jangueo": 2e-6,     # the act of hanging out
    "flow": 5e-5,        # flow / style (loanword, very high usage)
    "swag": 2e-5,        # style/attitude loanword
    "dembow": 3e-6,      # the dembow rhythm / the genre root
    "bellaqueo": 1e-6,   # provocative dancing / flirting
    "bellaquear": 8e-7,  # to be provocative / flirt
    "bellaco": 2e-6,     # horny / rascal (context-dependent)
    "bellaca": 2e-6,     # feminine form
    "dura": 6e-6,        # tough / badass woman
    "duro": 6e-6,        # tough / hard / badass
    "prrrap": 5e-7,      # onomatopoeia vocal adlib
    "reggaetonero": 1e-6, # reggaeton artist
    "reggaetonera": 1e-6, # feminine form
    # --- Party / nightlife ---
    "after": 3e-6,       # after-party (loanword)
    "antro": 4e-6,       # club / dive bar (also Mexico)
    "palo": 5e-6,        # drink / stick / slang hit
    "cabaré": 2e-6,      # cabaret / nightclub scene
    "vacilando": 3e-6,   # having a good time
    # --- Money / street ---
    "billete": 6e-6,     # bill / money
    "pisto": 4e-6,       # money (also Central America)
    "real": 8e-5,        # real / genuine (also common Spanish, floor only)
    "trucha": 2e-6,      # careful / sharp (watch out)
    "trampa": 5e-6,      # trap / trick (also general Spanish)
    # --- Affect / interjections ---
    "wepa": 3e-6,        # exclamation of joy/approval (PR)
    "eso": 2e-4,         # that's it / yes (general, high freq — floor only)
    "dale": 3e-5,        # go ahead / do it (also Cuba, widely spread)
    "oye": 4e-5,         # hey / listen (general Spanish, floor only)
    "nene": 8e-6,        # kid / babe (PR term of endearment)
    "nena": 8e-6,        # girl / babe
    "mira": 3e-5,        # look / hey (also common Spanish)
    # --- Compound / lyrical fillers ---
    "tiradera": 8e-7,    # diss / diss track (variant spelling)
    "calle": 4e-5,       # street (general Spanish, floor)
    "barrio": 2e-5,      # neighbourhood (general Spanish, floor)
    "orgullo": 6e-6,     # pride
    "pegao": 2e-6,       # stuck on / in love (Puerto Rican form of pegado)
    "enamorao": 1e-6,    # enamorado contracted form
    "loco": 3e-5,        # crazy / dude (general, floor)
    "loca": 3e-5,        # crazy / girl (general, floor)
}
