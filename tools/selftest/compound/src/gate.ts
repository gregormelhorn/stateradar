// Selftest fixture: a non-Python source file, so the sidecar generator's
// language-agnostic index and citation regex are exercised in CI.
export class Gate {
  private phase: "idle" | "busy" = "idle";
  private closed = false;
  private queue: string[] = [];

  arrive(id: string): void {
    if (this.closed) {
      throw new ClosedError("gate is closed");
    }
    if (this.phase === "busy") {
      this.queue.push(id);
      return;
    }
    this.phase = "busy"; // transition anchor: open idle x E1
  }

  finish(): void {
    if (this.closed) return;
    this.phase = "idle"; // transition anchor: open busy x E2
    const next = this.queue.shift();
    if (next !== undefined) this.arrive(next);
  }

  shutdown(): void {
    this.closed = true;
    throw new ClosedError("gate is closed"); // reject anchor: closed x E1
  }

  projection(): string {
    return this.closed ? "closed" : `open ${this.phase}`;
  }
}

export class ClosedError extends Error {}
