import { useEffect, useState } from "react";
import { getNodeDraft, updateNode } from "../api";
import { GlassButton } from "./GlassButton";
import { NodeDraftFields, nodeDraftReady } from "./NodeDraftFields";
import { useI18n } from "../i18n";
import type { ManualNodeDraft, ProxyNode } from "../types";

/**
 * Parameter editor for a single stored node — the ⋮ menu "编辑节点" action.
 * Prefills via the backend's node → draft round-trip (the same conversion
 * the manual-node form uses) and saves through `update_node`, which keeps
 * the subscription link and migrates id-keyed references when the edit
 * changes the node's backend identity. Edits are ephemeral: the next
 * subscription refresh rebuilds the whole node list and discards them —
 * the warning banner says so before the user types anything.
 */
export function EditNodeModal({
  node,
  onClose,
  onSaved,
}: {
  node: ProxyNode;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const [draft, setDraft] = useState<ManualNodeDraft | null>(null);
  const [name, setName] = useState(node.name);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getNodeDraft(node.id)
      .then((d) => {
        if (cancelled) return;
        setDraft(d);
        if (d.name) setName(d.name);
      })
      .catch((e) => {
        if (!cancelled) setError(typeof e === "string" ? e : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [node.id]);

  const canSubmit = !!draft && !busy && name.trim().length > 0 && nodeDraftReady(draft);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!draft || !canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      await updateNode(node.id, { ...draft, name: name.trim() });
      onSaved();
    } catch (err) {
      setError(typeof err === "string" ? err : String(err));
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <div
        className="modal config-add-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="node-edit-title"
      >
        <header className="modal-header">
          <h2 id="node-edit-title">{t("nodes.editTitle")}</h2>
          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            disabled={busy}
            aria-label={t("common.close")}
          >
            ×
          </button>
        </header>
        <form className="modal-body" onSubmit={handleSubmit}>
          <div className="field-warning" role="status">
            {t("nodes.editOverwriteHint")}
          </div>
          <label className="field">
            <span>{t("modal.name")}</span>
            <input
              autoCapitalize="off"
              autoCorrect="off"
              spellCheck={false}
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={busy || !draft}
              autoFocus
            />
          </label>
          {draft ? (
            <NodeDraftFields value={draft} disabled={busy} onChange={setDraft} />
          ) : (
            !error && <div className="field-hint muted">{t("common.loading")}</div>
          )}
          {error && <div className="field-warning">{error}</div>}
          <footer className="modal-footer">
            <GlassButton onClick={onClose} disabled={busy}>
              {t("common.cancel")}
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={!canSubmit}>
              {busy ? t("common.saving") : t("common.save")}
            </GlassButton>
          </footer>
        </form>
      </div>
    </div>
  );
}
