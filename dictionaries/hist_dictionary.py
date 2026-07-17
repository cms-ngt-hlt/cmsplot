# dictionary for hist names for an easier handling during plotting
EFF = "effic"
DUP = "duplicatesRate"
PIL = "pileuprate"
FAK = "fakerate"

HIST_DICT = {
    "eff" : EFF,
    "effic" : EFF,
    "efficiency" : EFF,
    "pil" : PIL,
    "pileup" : PIL,
    "pileuprate" : PIL,
    "fak" : FAK,
    "fake" : FAK,
    "fakerate" : FAK,
    "dup" : DUP, 
    "duplicate" : DUP,
    "duplicates" : DUP,
    "duplicatesRate" : DUP,
    "duplicatesrate" : DUP,
}

BIN_DICT = {
    "eta" : {
        EFF : "", DUP : "", PIL : "", FAK : ""
    },
    "phi" : {
        EFF : "_vs_phi", DUP : "_phi", PIL : "_phi", FAK : "_vs_phi"
    },
    "pt" : {
        EFF : "Pt", DUP : "_Pt", PIL : "_Pt", FAK : "Pt"
    },
    "coll" : {
        EFF : "_vs_coll", DUP : "_coll", PIL : "_coll", FAK : "_vs_coll"
    },
    "hit" : {
        EFF : "_vs_hit", DUP : "_hit", PIL : "_hit", FAK : "_vs_hit"
    },
}

def HIST_NAME(count_quantity, bin_quantity):
    # first part of the hist name
    if count_quantity in HIST_DICT.keys():
        histname = HIST_DICT[count_quantity]
    else:
        histname = count_quantity

    # suffix of the hist name
    if bin_quantity in BIN_DICT.keys():
        if histname in BIN_DICT[bin_quantity].keys():
            return histname + BIN_DICT[bin_quantity][histname]
    return histname + bin_quantity
