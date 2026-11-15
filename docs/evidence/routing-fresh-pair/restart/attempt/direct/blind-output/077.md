| Convention | Interpretation |
|---|---|
| States | `assumed-state: New_Succeeded` means construction succeeded and the receiver is usable. `assumed-state: New_Succeeded_Empty` additionally means it contains no entries. No lifecycle, shutdown, replacement-generation, or callback-execution states are documented. |
| Ordinary operations | Unless stated otherwise, rows concern a successfully constructed receiver and supported keys. `handle` preserves usability while performing the stated operation. An absent key is a normal result, not a declared refusal. |
| Pair orderings | Ordered cache effects below assume no intervening mutation unless mentioned. Overlapping calls must remain thread-safe; the requirements do not prescribe which concurrent call takes effect first. Invocation order alone does not establish completion or effect order. |
| Callback limits | Registration promises notification when an entry is evicted. Reentrancy, callback ordering, overlap, failure recovery, and delivery guarantees after abnormal termination are unspecified. Whether every explicit removal constitutes a notified eviction is also unspecified. |
| Scope | No expiration policy is specified for this cache. Returned values and snapshots describe their observation; they do not promise continued membership. `as-is:` marks behaviour supported only by the supplied implementation observations. |

| ID | Situation | Expected disposition and behaviour |
|---|---|---|
| New | Construction with requested capacity and optional callback | **transition → assumed-state: New_Succeeded_Empty** on successful construction: create an empty fixed-size LRU with the requested capacity and callback registration. **UNSPECIFIED**: accepted capacity domain, allocation failure, error signalling, and usability of any receiver returned with an error. |
| Purge | Usable receiver, empty or populated | **handle**: completely clear entries; `Len` becomes zero without changing configured capacity. An empty cache remains empty. Callback classification and ordering for explicit clearing are unspecified. |
| Resize | Usable receiver; supported requested capacity | **handle**: change capacity; when shrinking below current length, evict enough least-recently-used entries to fit and return the number evicted. Growing preserves entries and relative recency. **UNSPECIFIED**: unsupported capacity values and failure signalling. |
| Add | Key present or absent | **handle**: insert an absent key or replace the present key's value; make the key most recently used. Evict the least-recently-used entry when necessary to respect capacity. Return whether an eviction occurred. |
| Get | Key present or absent | **handle**: on hit, return value/found and make the key most recently used; on miss, return not-found without adding anything. |
| Contains | Key present or absent | **handle**: return membership without changing recency or deleting an entry for staleness. |
| Peek | Key present or absent | **handle**: return value/found on hit or not-found on miss, without changing recency. The missing-value representation is not fully specified. |
| ContainsOrAdd | Key present or absent | **handle**: atomically test membership and conditionally insert. On hit, retain existing value and recency; report found with no insertion eviction. On miss, add supplied value as most recently used, enforce capacity, and report not-found plus whether eviction occurred. |
| PeekOrAdd | Key present or absent | **handle**: atomically read or insert. On hit, return existing value/found without replacing it or touching recency. On miss, insert supplied value as most recently used and report not-found plus eviction status. The value return on miss is unspecified. |
| Remove | Key present or absent | **handle**: remove the selected entry if present; otherwise leave contents unchanged. No tombstone or suppression of later reinsertion is required. Callback treatment of explicit removal is unspecified. |
| RemoveOldest | Receiver populated or empty | **handle**: remove the least-recently-used entry if present; otherwise leave the empty cache unchanged. Exact empty-result signalling and callback treatment of explicit removal are unspecified. |
| GetOldest | Receiver populated or empty | **handle**: return oldest key/value/found when populated, or not-found when empty. Preserve contents. Whether this read changes recency is not explicitly specified. |
| Keys | Any usable receiver | **handle**: return a coherent key snapshot ordered oldest to newest; an empty cache yields no keys. No deep-copy or future-membership guarantee is specified. |
| Values | Any usable receiver | **handle**: return a coherent value snapshot ordered oldest to newest; an empty cache yields no values. No deep-copy guarantee or atomic correspondence with a separately called `Keys` is specified. |
| Len | Any usable receiver | **handle**: return the current entry count without changing contents or recency. |
| Cap | Any usable receiver | **handle**: return configured capacity through a thread-safe observation, including when `Resize` competes with the read. |
| CaptureEviction | Internal capture associated with removal and registered adapter | as-is: **handle**: capture the removed key/value under the writer lock, owned by the initiating call. The requirements prescribe eviction notification, but do not prescribe this internal event, buffer arrangement, or retention duration. Spurious or duplicate capture handling is **UNSPECIFIED**. |
| DeliverEviction | Registered callback and an eviction to report | **handle**: invoke the registered callback with the evicted entry's key/value. Without a registered callback, no invocation is required. Delivery timing, cross-call ordering, explicit-removal coverage, and abnormal-failure guarantees are **UNSPECIFIED**. |
| CallbackReturn | An invoked callback returns normally | as-is: **handle**: return control to its invoking cache method; continue any remaining captured batch before that method finishes normally. Requirements do not independently specify batch continuation. An unsolicited or duplicate return has no documented event contract: **UNSPECIFIED**. |
| CallbackReenter | Active callback invokes a cache API | **UNSPECIFIED**: whether same-receiver reentrancy must complete without deadlock. If the nested invocation is supported and executes, **handle** it according to its API contract against current contents; callback origin supplies no documented priority, rollback, or generation protection. |
| UV-01 | Construction omitted, delayed, unsuccessful, or not yet published | **UNSPECIFIED**: use before successful construction, including use of a receiver returned with an error. No documented refusal signal or deferred-use mechanism exists. If the owner has not invoked construction or published a usable receiver, the component cannot perform those owner actions itself. |
| UV-02 | Invalid, unintended, or duplicate construction | **UNSPECIFIED**: zero/negative-size acceptance and failure signalling. For a supported positive size, **transition → assumed-state: New_Succeeded_Empty** using that supplied size; unintended intent is not encoded. A successful duplicate construction creates a separate cache, without replacing or clearing another instance. |
| UV-03 | Purge omitted, delayed, repeated, or stale after repopulation | If no call arrives, no clearing is required. For each actual call, **handle**: clear entries present when it takes effect. Repetition on an empty cache leaves it empty; a stale call after repopulation clears the new entries too. No generation guard or stale-call refusal is specified. |
| UV-04 | Invalid, extreme, repeated, unintended, or competing Resize | **UNSPECIFIED**: zero/negative capacities, extreme-value support, overflow protection, and failure signalling. For supported sizes, **handle** every call using its supplied size; repeated resizing acts on then-current contents. Competing sizes require thread-safe effects; final capacity follows the last effective resize, not necessarily invocation order. |
| UV-05 | Omitted operation, abandoned wait, or stale request | An omitted invocation causes no operation. Once invoked, **handle** a valid request against its actual receiver and current contents; lost caller interest does not specify cancellation. Stale keys/values/decisions receive ordinary API semantics, without freshness detection. Cancellation and publication-slot coordination are **UNSPECIFIED**. |
| UV-06 | Repeated or overlapping Gets, conditional adds, Adds, or Removes | **handle** each valid invocation independently and thread-safely. Each successful `Get` updates recency; a retained earlier value has no freshness guarantee. Conditional adds decide atomically against current membership; `Add` replaces; repeated removal of an absent key leaves contents unchanged. No request deduplication is specified. |
| UV-07 | Wrong receiver, wrong payload, stale generation, or contradictory same-key calls | For a usable supplied receiver and supported payload, **handle** its ordinary operation on that receiver; plausible owner mistakes are not detectable from these contracts. Contradictory calls have thread-safe ordered effects, without intent reconciliation. **UNSPECIFIED**: invalid receivers and external generation validation. |
| UV-08 | Comparable but non-reflexive key, such as NaN | **UNSPECIFIED**: whether such keys are supported, how membership/removal must behave, and whether refusal is required. The observed equality behaviour and duplicate-capture risk do not establish intended semantics; no declared `reject` signal is specified. |
| UV-09 | Interface key containing a non-comparable dynamic value | **UNSPECIFIED**: admissibility, validation, panic behaviour, or declared refusal. A panic or error cannot be inferred as the required response from the supplied contracts. |
| UV-10 | Callback panics, terminates its goroutine, waits indefinitely, or returns late | **UNSPECIFIED**: recovery, propagation, timeout, tail delivery, and completion of the invoking method. A normally late return resumes its invocation, but no deadline is promised. Thread safety still governs independent cache operations; whether they can progress during callback execution is not expressly guaranteed. |
| UV-11 | Overlapping callbacks or duplicate, stale, contradictory, or misdirected nested work | **UNSPECIFIED**: callback serialization, overlap guarantees, and same-receiver reentrancy. If nested operations execute, **handle** each according to its supplied receiver/payload and current contents; no automatic deduplication, stale-work suppression, or contradiction resolution is specified. Callback bodies must not be assumed thread-safe merely because the cache is. |
| UV-12 | Late or aborting callback around Purge/Resize, including captured tail | **handle** completed cache mutations according to their contracts; callback lateness alone supplies no rollback or cache-generation change. **UNSPECIFIED**: cancellation of old notifications, delivery order across lifecycle calls, tail delivery after abort, and progress while callbacks remain active. |

| ID | Situation | Expected disposition and behaviour |
|---|---|---|
| P-01a | Purge → Add | **handle**: clear existing entries, then insert the supplied key/value into the cleared cache as most recently used, enforcing capacity. |
| P-01b | Add → Purge | **handle**: perform insertion/replacement and any necessary eviction, then clear all entries, including the added entry. |
| P-02a | Purge → Get | **handle**: clear entries; subsequent `Get` misses unless another operation has repopulated the key. |
| P-02b | Get → Purge | **handle**: return the pre-purge value/found and update recency on hit; then clear entries. The earlier result remains an earlier observation. |
| P-03a | Purge → Contains | **handle**: clear entries; membership is false absent intervening insertion. |
| P-03b | Contains → Purge | **handle**: report pre-purge membership without recency change; then clear entries. |
| P-04a | Purge → Peek | **handle**: clear entries; subsequent `Peek` reports not-found absent intervening insertion. |
| P-04b | Peek → Purge | **handle**: return pre-purge value/found without recency change; then clear entries. |
| P-05a | Purge → ContainsOrAdd | **handle**: clear entries; conditional add finds the key absent, inserts the supplied value, and reports not-found plus actual eviction status. |
| P-05b | ContainsOrAdd → Purge | **handle**: atomically preserve an existing value or insert an absent one; return corresponding flags, then clear all entries. |
| P-06a | Purge → PeekOrAdd | **handle**: clear entries; conditional read/add takes the miss branch, inserts the supplied value, and reports not-found plus eviction status. |
| P-06b | PeekOrAdd → Purge | **handle**: return an existing value without recency change or insert on miss; then clear entries without retroactively changing the result. |
| P-07a | Purge → Remove | **handle**: clear entries; removing the now-absent key leaves contents unchanged. |
| P-07b | Remove → Purge | **handle**: remove the selected key if present, then clear remaining entries. The selected entry is not present for a second removal by `Purge`. |
| P-08a | Purge → RemoveOldest | **handle**: clear entries; subsequent oldest removal finds no entry and leaves contents empty. Empty-result signalling is unspecified. |
| P-08b | RemoveOldest → Purge | **handle**: remove the current oldest entry if any, then clear the remainder. |
| P-09a | Purge → GetOldest | **handle**: clear entries; return not-found for oldest entry. |
| P-09b | GetOldest → Purge | **handle**: return the pre-purge oldest entry/found or not-found, then clear entries. |
| P-10a | Purge → Keys | **handle**: clear entries; return a snapshot containing no keys. |
| P-10b | Keys → Purge | **handle**: return the pre-purge oldest-to-newest key snapshot, then clear entries. The returned snapshot need not reflect later membership. |
| P-11a | Purge → Values | **handle**: clear entries; return a snapshot containing no values. |
| P-11b | Values → Purge | **handle**: return the pre-purge oldest-to-newest value snapshot, then clear entries. |
| P-12a | Purge → Len | **handle**: clear entries; return zero. |
| P-12b | Len → Purge | **handle**: return pre-purge count, then clear entries; subsequent count is zero. |
| P-13a | Purge → Cap | **handle**: clear entries; return unchanged configured capacity. |
| P-13b | Cap → Purge | **handle**: return configured capacity, then clear entries while preserving that capacity. |
| P-14a | Resize → Add | **handle**: resize and perform required LRU evictions, then insert/replace under the new capacity, evicting again if necessary. Unsupported resize values are **UNSPECIFIED**. |
| P-14b | Add → Resize | **handle**: insert/replace under old capacity, then resize and evict oldest entries as needed. The added key is most recent after `Add`; its survival depends on the supported new capacity and subsequent mutations. |
| P-15a | Resize → Get | **handle**: resize; `Get` misses if its key was evicted, otherwise returns its value and makes it most recently used. |
| P-15b | Get → Resize | **handle**: on hit, return value and make key most recently used before selecting resize victims. A miss leaves recency unchanged. |
| P-16a | Resize → Contains | **handle**: resize; report whether the key survived, without changing recency. |
| P-16b | Contains → Resize | **handle**: report membership without recency change, then resize using unchanged relative recency. A true result does not ensure survival. |
| P-17a | Resize → Peek | **handle**: resize; return value/found only if the key remains, without recency change. |
| P-17b | Peek → Resize | **handle**: return pre-resize value/found without changing recency, then resize. The observed key may be evicted. |
| P-18a | Resize → ContainsOrAdd | **handle**: resize; atomically test remaining membership. Preserve a surviving hit without recency change, or insert on miss under the new capacity and report eviction status. |
| P-18b | ContainsOrAdd → Resize | **handle**: atomically test/add under old capacity; a hit preserves recency and a miss inserts most recently used. Then resize using that resulting order. |
| P-19a | Resize → PeekOrAdd | **handle**: resize; return a surviving hit without recency change, or insert on miss under new capacity and report flags. |
| P-19b | PeekOrAdd → Resize | **handle**: atomically read/add under old capacity, then resize using resulting contents and recency. Earlier results do not promise survival. |
| P-20a | Resize → Remove | **handle**: resize, then remove the selected key if it survived; if resize already evicted it, removal leaves contents unchanged. |
| P-20b | Remove → Resize | **handle**: remove selected key if present, then calculate resize evictions from remaining entries; do not count the earlier removal as a resize eviction. |
| P-21a | Resize → RemoveOldest | **handle**: resize, then remove the oldest surviving entry if any; this is an additional removal. |
| P-21b | RemoveOldest → Resize | **handle**: remove the original oldest entry if any, then resize remaining contents and report only resize-caused evictions in the resize count. |
| P-22a | Resize → GetOldest | **handle**: resize, then return the oldest surviving entry/found or not-found if empty. |
| P-22b | GetOldest → Resize | **handle**: return the pre-resize oldest entry/found, then resize. Survival is not guaranteed; whether `GetOldest` affects victim selection through recency is **UNSPECIFIED**. |
| P-23a | Resize → Keys | **handle**: resize, then return surviving keys ordered oldest to newest. |
| P-23b | Keys → Resize | **handle**: return pre-resize ordered key snapshot, then resize; some snapshot keys may cease to be members. |
| P-24a | Resize → Values | **handle**: resize, then return surviving values ordered oldest to newest. |
| P-24b | Values → Resize | **handle**: return pre-resize ordered value snapshot, then resize; the snapshot is not a future-membership promise. |
| P-25a | Resize → Len | **handle**: return the post-resize count, bounded by supported new capacity. |
| P-25b | Len → Resize | **handle**: return pre-resize count, then resize and reduce count if needed. |
| P-26a | Resize → Cap | **handle**: return the new capacity after successful resize. A concurrent observation must be thread-safe. |
| P-26b | Cap → Resize | **handle**: return old capacity, then change it through successful resize. The earlier return is not updated retroactively. |
| P-27a | Purge → CallbackReturn | **handle**: clear entries; later normal return of an already running callback does not restore them. **UNSPECIFIED**: ordering of remaining notifications and whether lifecycle progress is guaranteed before callback return. |
| P-27b | CallbackReturn → Purge | **handle**: accept normal callback completion, then clear then-current entries. **UNSPECIFIED**: ordering of any remaining callback batch relative to `Purge`. |
| P-28a | Purge → CallbackReenter | **handle**: clear entries. **UNSPECIFIED**: same-receiver reentrancy support; if the nested operation executes, apply it to post-purge contents, allowing nested insertion to repopulate the cache. |
| P-28b | CallbackReenter → Purge | **UNSPECIFIED**: reentrancy support. If the nested operation completes before purge effects, **handle** it normally, then clear its resulting entries too; nested results remain earlier observations. |
| P-29a | Purge → UV-10 | **handle**: completed clearing remains effective when a callback subsequently stalls or escapes. **UNSPECIFIED**: outer-call completion, recovery, and remaining notification delivery. |
| P-29b | UV-10 → Purge | **UNSPECIFIED**: whether purge can progress while the earlier callback stalls, and how escape propagates. If `Purge` executes, **handle** it by clearing current entries; callback failure supplies no documented rollback. |
| P-30a | Resize → CallbackReturn | **handle**: completed resize and evictions remain effective after the older callback returns. **UNSPECIFIED**: lifecycle progress before return and ordering of remaining notifications. |
| P-30b | CallbackReturn → Resize | **handle**: normal callback return does not undo eviction; resize then-current contents to requested supported capacity. Remaining notification interleaving is **UNSPECIFIED**. |
| P-31a | Resize → CallbackReenter | **handle**: resize. **UNSPECIFIED**: same-receiver reentrancy support; if nested work executes afterward, apply it under the new capacity to surviving contents. |
| P-31b | CallbackReenter → Resize | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** subsequent resize against its resulting contents and recency. |
| P-32a | Resize → UV-10 | **handle**: completed capacity change and evictions remain effective. **UNSPECIFIED**: recovery, outer-call completion, and remaining callbacks after a callback stalls or escapes. |
| P-32b | UV-10 → Resize | **UNSPECIFIED**: progress while an earlier callback stalls and consequences of escape. If resize executes, **handle** current contents under the requested supported capacity. |
| P-33a | Add → CallbackReenter | **handle**: perform `Add`. **UNSPECIFIED**: reentrancy support; if nested work executes afterward, it sees resulting membership and may overwrite/remove the added key or change recency. The earlier eviction flag describes the earlier `Add`. |
| P-33b | CallbackReenter → Add | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** subsequent `Add` against its results; replace any then-present matching key, make it most recent, and enforce capacity. |
| P-34a | Get → CallbackReenter | **handle**: return value/found and update recency on hit. **UNSPECIFIED**: reentrancy support; subsequent executed nested work may replace/remove that key without invalidating the earlier observation. |
| P-34b | CallbackReenter → Get | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** `Get` against resulting membership/value, updating recency only on hit. |
| P-35a | ContainsOrAdd → CallbackReenter | **handle**: finish atomic test/add with its flags. **UNSPECIFIED**: reentrancy support; subsequent executed nested work may overwrite or remove the entry but cannot retroactively change the earlier flags. |
| P-35b | CallbackReenter → ContainsOrAdd | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** atomic conditional add against resulting membership; a present key retains its existing value and recency. |
| P-36a | PeekOrAdd → CallbackReenter | **handle**: finish atomic read/add and return its observation/flags. **UNSPECIFIED**: reentrancy support; later executed nested changes do not revise those returns. |
| P-36b | CallbackReenter → PeekOrAdd | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** atomic read/add against resulting contents; preserve value/recency on hit and insert on miss. |
| P-37a | Remove → CallbackReenter | **handle**: remove key if present. **UNSPECIFIED**: reentrancy support; a subsequently executed nested add may reinsert the same key, without a removal tombstone preventing it. |
| P-37b | CallbackReenter → Remove | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** subsequent removal of the then-present selected key, including a newly inserted replacement. |
| P-38a | RemoveOldest → CallbackReenter | **handle**: remove the current oldest entry if present. **UNSPECIFIED**: reentrancy support; later executed nested work acts on remaining contents and may reinsert the removed key. |
| P-38b | CallbackReenter → RemoveOldest | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** removal of the oldest entry in the resulting recency order, which may differ from the original oldest. |
| P-39a | Cap → CallbackReenter | **handle**: return configured capacity. **UNSPECIFIED**: reentrancy support; a later executed nested resize may change capacity without revising the earlier result. |
| P-39b | CallbackReenter → Cap | **UNSPECIFIED**: reentrancy support. If nested work executes first, **handle** a thread-safe capacity read reflecting any completed nested resize. |
| P-40a | Add → UV-10 | **handle**: completed insertion/replacement and its evictions remain effective when an older callback later stalls or escapes. **UNSPECIFIED**: callback failure propagation, notification completion, and affected invocation completion. |
| P-40b | UV-10 → Add | **UNSPECIFIED**: progress while the older callback stalls and consequences of escape. If independent `Add` executes, **handle** it normally against current contents, preserving thread safety and capacity. |
| P-41a | New → UV-05 | **transition → assumed-state: New_Succeeded_Empty** for successful replacement construction. For a delayed valid invocation, **handle** the actual receiver it uses: an old receiver remains a separate cache, and a replacement receiver has its own contents. Publication, migration, and stale-generation rejection are **UNSPECIFIED**. |
| P-41b | UV-05 → New | **handle** a valid delayed invocation on its actual existing receiver; omission causes no operation. Subsequent successful construction **transition → assumed-state: New_Succeeded_Empty** for the new instance without migrating or undoing old-instance work. Invocation on an unconstructed receiver and publication coordination are **UNSPECIFIED**. |

- [x] New
- [x] Purge
- [x] Resize
- [x] Add
- [x] Get
- [x] Contains
- [x] Peek
- [x] ContainsOrAdd
- [x] PeekOrAdd
- [x] Remove
- [x] RemoveOldest
- [x] GetOldest
- [x] Keys
- [x] Values
- [x] Len
- [x] Cap
- [x] CaptureEviction
- [x] DeliverEviction
- [x] CallbackReturn
- [x] CallbackReenter
- [x] UV-01
- [x] UV-02
- [x] UV-03
- [x] UV-04
- [x] UV-05
- [x] UV-06
- [x] UV-07
- [x] UV-08
- [x] UV-09
- [x] UV-10
- [x] UV-11
- [x] UV-12
- [x] P-01a
- [x] P-01b
- [x] P-02a
- [x] P-02b
- [x] P-03a
- [x] P-03b
- [x] P-04a
- [x] P-04b
- [x] P-05a
- [x] P-05b
- [x] P-06a
- [x] P-06b
- [x] P-07a
- [x] P-07b
- [x] P-08a
- [x] P-08b
- [x] P-09a
- [x] P-09b
- [x] P-10a
- [x] P-10b
- [x] P-11a
- [x] P-11b
- [x] P-12a
- [x] P-12b
- [x] P-13a
- [x] P-13b
- [x] P-14a
- [x] P-14b
- [x] P-15a
- [x] P-15b
- [x] P-16a
- [x] P-16b
- [x] P-17a
- [x] P-17b
- [x] P-18a
- [x] P-18b
- [x] P-19a
- [x] P-19b
- [x] P-20a
- [x] P-20b
- [x] P-21a
- [x] P-21b
- [x] P-22a
- [x] P-22b
- [x] P-23a
- [x] P-23b
- [x] P-24a
- [x] P-24b
- [x] P-25a
- [x] P-25b
- [x] P-26a
- [x] P-26b
- [x] P-27a
- [x] P-27b
- [x] P-28a
- [x] P-28b
- [x] P-29a
- [x] P-29b
- [x] P-30a
- [x] P-30b
- [x] P-31a
- [x] P-31b
- [x] P-32a
- [x] P-32b
- [x] P-33a
- [x] P-33b
- [x] P-34a
- [x] P-34b
- [x] P-35a
- [x] P-35b
- [x] P-36a
- [x] P-36b
- [x] P-37a
- [x] P-37b
- [x] P-38a
- [x] P-38b
- [x] P-39a
- [x] P-39b
- [x] P-40a
- [x] P-40b
- [x] P-41a
- [x] P-41b