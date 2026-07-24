"""Illustrative claim sets for the demo / web examples.

Synthetic claims, plus one REAL granted (and expired) claim set — claims 1-3 of US 6,285,999
(Google's PageRank patent, granted 2001). Patents are public documents; it is tagged as real
in the UI. Real claim language is the regression case for the drafting conventions the engine
models (dependent-claim preambles, gerund step references, "the one or more", participles).
"""

SAMPLE_CLAIMS: dict[str, str] = {
    "real-patent-pagerank": (
        "1. A computer implemented method of scoring a plurality of linked documents, "
        "comprising: obtaining a plurality of documents, at least some of the documents being "
        "linked documents, at least some of the documents being linking documents, and at least "
        "some of the documents being both linked documents and linking documents, each of the "
        "linked documents being pointed to by a link in one or more of the linking documents; "
        "assigning a score to each of the linked documents based on scores of the one or more "
        "linking documents and processing the linked documents according to their scores.\n"
        "2. The method of claim 1, wherein the assigning includes: identifying a weighting "
        "factor for each of the linking documents, the weighting factor being dependent on the "
        "number of links to the one or more linking documents, and adjusting the score of each "
        "of the one or more linking documents based on the identified weighting factor.\n"
        "3. The method of claim 1, wherein the assigning includes: identifying a weighting "
        "factor for each of the linking documents, the weighting factor being dependent on an "
        "estimation of a probability that a linking document will be accessed, and adjusting "
        "the score of each of the one or more linking documents based on the identified "
        "weighting factor."
    ),
    "clean-apparatus": (
        "1. An apparatus comprising: a processor; a memory storing instructions; and a network "
        "interface, wherein the memory further stores a plurality of records, and the processor is "
        "configured to transmit the records via the network interface.\n"
        "2. The apparatus of claim 1, wherein the processor comprises a first core and a second core.\n"
        "3. The apparatus of claim 2, wherein the first core and the second core share a cache."
    ),
    "missing-antecedent": (
        "1. A device comprising a housing, a processor within the housing, and a battery coupled to "
        "the controller.\n"
        "2. The device of claim 1, wherein the display is touch-sensitive."
    ),
    "bad-dependencies": (
        "1. A method comprising receiving a signal and filtering the signal.\n"
        "2. The method of claim 4, further comprising amplifying the signal.\n"
        "3. The method of claim 3, wherein the amplifying is substantially linear."
    ),
}

DEFAULT_SAMPLE = "missing-antecedent"

# Extra display metadata per sample (the web UI shows `tag` as a badge on the sample button).
SAMPLE_TAGS: dict[str, str] = {
    "real-patent-pagerank": "Real patent · US 6,285,999 (PageRank) · expired",
}
