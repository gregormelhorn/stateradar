# Structured cell rationale

Opt in with `rationaleVersion: 1` in `analysis.json`. Every cell then carries
`rationale`: `kind`, an explicit `claim`, scenario `scope`, and nonempty
`evidence`. Historical sidecars remain readable without opting in.

| Kind | Meaning | Required evidence |
|---|---|---|
| `required-behavior` | The stated behavior applies in this scenario | Accepted decision or cited callee contract |
| `documented-no-action` | Intentional ignore within its stated scope | Accepted decision; disposition must be `ignore (documented)` |
| `upstream-guarantee` | A named callee supplies the stated guarantee | Original callee identity and fragment citation |
| `outside-contract` | The owner explicitly limits the contract | Accepted decision |

An evidence entry has `kind: decision` with `dr: DR-nnn`, or
`kind: upstream-contract` with `source` identifying the callee. Both require
`citation: {file, line, fragment}` relative to the repository passed to
`dsc_check.py --repo`. Decision evidence must cite that named accepted decision
file. Fragments are verified within three lines, including prose citations.
The schema and checker validate structure, references and consistency. They
do not prove that a quotation entails the claim or extends to its scenario.
The human decision and requirement-scope rules still apply.

Keep `cell-rationale.json` beside the matrix, with `formatVersion: 1` and a
`cells` array. Each entry binds `state`, `event`, `disposition`, optional
`target` and `rationale`. The sidecar generator preserves these fields; an
outcome change requires review of the binding. It refuses regeneration when
an already adopted rationale file is missing, instead of silently dropping
rationale. The checker also detects disagreement between bindings and sidecar.

The weighted-semaphore evaluation binds all 38 cells to the thirteen accepted
DRs. Its four contract-limit cells remain explicitly untestable via the seam.
The repeated standard CancelFunc case additionally cites the retained callee
contract; that guarantee does not extend to arbitrary broken Context objects.

Run `python tools/selftest/test_cell_rationale.py` for positive, negative and
regeneration checks. The initial failures and component evidence are retained
in `docs/evidence/mutation-rationale-cost/`.
