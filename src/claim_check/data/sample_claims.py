"""Illustrative claim sets for the demo / web examples. Public-style, synthetic claims."""

SAMPLE_CLAIMS: dict[str, str] = {
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
