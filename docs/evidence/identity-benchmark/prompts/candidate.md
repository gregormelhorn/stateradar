For each deferred callback, handle or stored reference, trace identity from
creation to use. Distinguish a copied value, a captured object and a lookup
through a mutable wrapper or key. Identify which reference is read at invocation.
Where the public boundary permits it, compare copying, replacement or reassignment
between creation and invocation with the unchanged case. Follow the result to
the actual recipient, including admission, counters, generation checks and cleanup.
Do not treat a generation number alone as proof of object identity. State the
starting objects, ordered operations and observable outcome; cite capture and
use sites. Probe material claims through the public seam. A general mention of
copying or replacement does not cover an untraced effect. If a documented contract
excludes an ordering, cite that contract; if intent is silent, retain an open
question. Do not infer that copying is supported, or invent a defect when the
captured value or an identity check prevents redirection.
