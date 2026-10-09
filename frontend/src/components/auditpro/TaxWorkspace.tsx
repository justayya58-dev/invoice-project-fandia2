import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AlertTriangle, Check, CircleDollarSign, Download, FileCheck2, FileSpreadsheet, Landmark, RefreshCw, Send, ShieldCheck, X } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiFileUrl, apiGet, apiPost, apiPut } from "@/lib/api";
import type { TaxActionRequest, TaxDocument, TaxDocumentUpdate, TaxRate, TaxRateProfile, TaxStatus, TaxSummary, TaxSyncResult } from "@/types/tax";

const formatIDR = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(value);
const statusCopy: Record<TaxStatus, string> = { draft: "Draft", review: "Perlu review", ready: "Siap e-Faktur", reported: "Dilaporkan", needs_correction: "Perlu perbaikan" };
const emptySummary: TaxSummary = { period: "—", output_dpp: 0, output_vat: 0, input_dpp: 0, input_vat: 0, net_vat: 0, ready_count: 0, issue_count: 0, status_counts: {}, by_rate: [] };

function TaxStatusBadge({ status }: { status: TaxStatus }) {
  const tone = status === "reported" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300" : status === "ready" ? "border-cyan-500/20 bg-cyan-500/10 text-cyan-300" : status === "needs_correction" ? "border-red-500/20 bg-red-500/10 text-red-300" : status === "review" ? "border-amber-500/20 bg-amber-500/10 text-amber-300" : "border-slate-500/20 bg-slate-500/10 text-slate-300";
  return <Badge data-testid={`tax-status-${status}`} className={`border ${tone}`}>{statusCopy[status]}</Badge>;
}

function SummaryCard({ testId, label, value, meta, icon: Icon, color }: { testId: string; label: string; value: string; meta: string; icon: typeof CircleDollarSign; color: string }) {
  return <Card data-testid={testId} className="border-white/[0.07] bg-[#111827]/80 shadow-none"><CardContent className="p-5"><div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-slate-500"><span>{label}</span><Icon size={16} className={color} /></div><p data-testid={`${testId}-value`} className={`mt-4 font-heading text-xl font-bold ${color}`}>{value}</p><p data-testid={`${testId}-meta`} className="mt-1 text-[10px] text-slate-600">{meta}</p></CardContent></Card>;
}

export default function TaxWorkspace() {
  const queryClient = useQueryClient();
  const [period, setPeriod] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<TaxDocumentUpdate | null>(null);
  const suffix = period ? `?period=${period}` : "";
  const summaryQuery = useQuery({ queryKey: ["tax-summary", period], queryFn: () => apiGet<TaxSummary>(`/auditpro/tax/summary${suffix}`), retry: false });
  const documentsQuery = useQuery({ queryKey: ["tax-documents", period], queryFn: () => apiGet<TaxDocument[]>(`/auditpro/tax/documents${suffix}`), retry: false });
  const profilesQuery = useQuery({ queryKey: ["tax-profiles"], queryFn: () => apiGet<TaxRateProfile[]>("/auditpro/tax/profiles"), retry: false });
  const summary = summaryQuery.data ?? emptySummary;
  const documents = documentsQuery.data ?? [];
  const profiles = profilesQuery.data ?? [];
  const selected = documents.find((item) => item.id === selectedId) ?? null;
  const displayedPeriod = period || summary.period;
  const vatPreview = draft ? Math.round(draft.dpp * draft.tax_rate / 100) : 0;
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["tax-summary"] });
    queryClient.invalidateQueries({ queryKey: ["tax-documents"] });
  };
  const chooseDocument = (document: TaxDocument) => {
    setSelectedId(document.id);
    setDraft({ npwp: document.npwp, tax_invoice_number: document.tax_invoice_number, document_date: document.document_date, dpp: document.dpp, tax_rate: document.tax_rate });
  };
  const syncMutation = useMutation({ mutationFn: () => apiPost<TaxSyncResult>("/auditpro/tax/sync", {}), onSuccess: (result) => { refresh(); toast.success(result.created ? `${result.created} dokumen pajak baru disinkronkan` : "Semua sumber sudah tersinkron"); }, onError: () => toast.error("Sinkronisasi pajak gagal") });
  const updateMutation = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: TaxDocumentUpdate }) => apiPut<TaxDocument>(`/auditpro/tax/documents/${id}`, payload), onSuccess: (document) => { refresh(); chooseDocument(document); toast.success("Data pajak diperbarui dan divalidasi ulang"); }, onError: () => toast.error("Data pajak belum dapat disimpan") });
  const actionMutation = useMutation({ mutationFn: ({ id, action }: { id: string; action: TaxActionRequest["action"] }) => apiPost<TaxDocument>(`/auditpro/tax/documents/${id}/action`, { action, actor: "Raka Adinata", note: action === "request_correction" ? "Dikembalikan untuk perbaikan data" : "" } satisfies TaxActionRequest), onSuccess: (document) => { refresh(); chooseDocument(document); toast.success(`Status pajak: ${statusCopy[document.status]}`); }, onError: () => toast.error("Pastikan semua field wajib lengkap dan valid") });
  const startDownload = (path: string) => { window.location.assign(apiFileUrl(path)); };

  return <div data-testid="tax-workspace" className="animate-rise-in space-y-6">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p data-testid="tax-eyebrow" className="text-[11px] font-semibold uppercase tracking-[.2em] text-cyan-300">TAX COMPLIANCE · TAHAP 3</p><h1 data-testid="tax-title" className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-white sm:text-3xl">Faktur pajak control center</h1><p data-testid="tax-subtitle" className="mt-2 text-sm text-slate-500">Rekonsiliasi PPN, validasi kelengkapan, dan persiapan data menuju e-Faktur.</p></div>
      <div className="flex flex-wrap gap-2"><Input data-testid="tax-period-input" type="month" value={displayedPeriod === "—" ? "" : displayedPeriod} onChange={(event) => setPeriod(event.target.value)} className="w-40 border-white/10 bg-white/[0.03] text-xs" /><Button data-testid="tax-sync-button" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending} variant="outline" className="gap-2 border-white/10 bg-white/[0.03] text-xs text-slate-300"><RefreshCw size={14} className={syncMutation.isPending ? "animate-spin" : ""} /> Sinkronkan</Button></div>
    </div>
    <div data-testid="tax-rate-profiles" className="flex flex-wrap gap-2">{profiles.map((profile) => <div data-testid={`tax-rate-profile-${profile.rate}`} key={profile.rate} title={profile.description} className="rounded-lg border border-white/[0.07] bg-white/[0.025] px-3 py-2"><span className="text-xs font-bold text-slate-200">{profile.label}</span><span className="ml-2 text-[10px] text-slate-600">aktif</span></div>)}</div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <SummaryCard testId="tax-output-card" label="PPN keluaran" value={formatIDR(summary.output_vat)} meta={`DPP ${formatIDR(summary.output_dpp)}`} icon={CircleDollarSign} color="text-emerald-300" />
      <SummaryCard testId="tax-input-card" label="PPN masukan" value={formatIDR(summary.input_vat)} meta={`DPP ${formatIDR(summary.input_dpp)}`} icon={FileSpreadsheet} color="text-cyan-300" />
      <SummaryCard testId="tax-net-card" label="PPN neto" value={formatIDR(summary.net_vat)} meta={`Masa ${summary.period}`} icon={Landmark} color="text-violet-300" />
      <SummaryCard testId="tax-readiness-card" label="Readiness" value={`${summary.ready_count} siap`} meta={`${summary.issue_count} perlu perhatian`} icon={ShieldCheck} color="text-amber-300" />
    </div>
    <div className="flex flex-wrap gap-2">
      <Button data-testid="tax-export-csv-button" onClick={() => startDownload(`/auditpro/tax/export.csv${suffix}`)} variant="outline" className="gap-2 border-white/10 bg-transparent text-xs text-slate-300"><Download size={14} /> CSV</Button>
      <Button data-testid="tax-export-excel-button" onClick={() => startDownload(`/auditpro/tax/export.xlsx${suffix}`)} variant="outline" className="gap-2 border-white/10 bg-transparent text-xs text-slate-300"><FileSpreadsheet size={14} /> Excel</Button>
      <Button data-testid="tax-export-efaktur-button" onClick={() => startDownload(`/auditpro/tax/efaktur-preview.csv${suffix}`)} variant="outline" className="gap-2 border-cyan-400/20 bg-cyan-400/[0.04] text-xs text-cyan-200"><FileCheck2 size={14} /> Preview e-Faktur</Button>
    </div>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_380px]">
      <Card data-testid="tax-documents-card" className="border-white/[0.07] bg-[#111827]/80 shadow-none">
        <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/[0.06] px-5 py-4"><div><p data-testid="tax-documents-eyebrow" className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Tax document ledger</p><CardTitle data-testid="tax-documents-title" className="mt-1 font-heading text-base font-bold text-white">Dokumen masa {summary.period}</CardTitle></div><span data-testid="tax-documents-count" className="text-xs text-slate-500">{documents.length} dokumen</span></CardHeader>
        <CardContent className="p-0"><div className="overflow-x-auto"><table data-testid="tax-documents-table" className="w-full min-w-[820px] text-left"><thead className="border-b border-white/[0.06] text-[10px] uppercase tracking-wider text-slate-600"><tr><th className="px-5 py-3">Referensi</th><th className="px-3 py-3">Pihak</th><th className="px-3 py-3">Arah</th><th className="px-3 py-3">DPP / PPN</th><th className="px-3 py-3">Kelengkapan</th><th className="px-5 py-3 text-right">Status</th></tr></thead><tbody>{documents.map((document) => <tr data-testid={`tax-document-row-${document.id}`} key={document.id} onClick={() => chooseDocument(document)} className="cursor-pointer border-b border-white/[0.04] last:border-0 hover:bg-white/[0.025]"><td className="px-5 py-4"><p data-testid={`tax-reference-${document.id}`} className="text-xs font-semibold text-slate-200">{document.source_reference}</p><p className="mt-0.5 text-[10px] text-slate-600">{document.document_date}</p></td><td data-testid={`tax-counterparty-${document.id}`} className="px-3 py-4 text-xs text-slate-400">{document.counterparty}</td><td className="px-3 py-4"><Badge className={document.direction === "output" ? "bg-emerald-400/10 text-emerald-300" : "bg-cyan-400/10 text-cyan-300"}>{document.direction === "output" ? "Keluaran" : "Masukan"}</Badge></td><td className="px-3 py-4"><p className="text-xs text-slate-300">{formatIDR(document.dpp)}</p><p className="mt-0.5 text-[10px] text-slate-600">PPN {document.tax_rate}% · {formatIDR(document.vat)}</p></td><td className="px-3 py-4"><div className="flex items-center gap-2"><div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-800"><div className={document.completeness_score === 100 ? "h-full rounded-full bg-emerald-400" : "h-full rounded-full bg-amber-400"} style={{ width: `${document.completeness_score}%` }} /></div><span data-testid={`tax-completeness-${document.id}`} className="text-[10px] text-slate-500">{document.completeness_score}%</span></div></td><td className="px-5 py-4 text-right"><TaxStatusBadge status={document.status} /></td></tr>)}</tbody></table></div></CardContent>
      </Card>
      <Card data-testid="tax-validation-panel" className="h-fit border-white/[0.07] bg-[#101b2a] shadow-none">
        <CardHeader className="border-b border-white/[0.06] px-5 py-4"><CardTitle data-testid="tax-validation-title" className="font-heading text-base font-bold text-white">Validasi dokumen</CardTitle></CardHeader>
        <CardContent className="p-5">{selected && draft ? <div data-testid="tax-validation-form" className="space-y-4">
          <div className="flex items-start justify-between"><div><p data-testid="tax-selected-reference" className="text-sm font-semibold text-slate-200">{selected.source_reference}</p><p data-testid="tax-selected-party" className="mt-1 text-xs text-slate-500">{selected.counterparty}</p></div><TaxStatusBadge status={selected.status} /></div>
          <label className="block space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">NPWP</span><Input data-testid="tax-npwp-input" value={draft.npwp} onChange={(event) => setDraft({ ...draft, npwp: event.target.value })} placeholder="00.000.000.0-000.000" className="border-white/10 bg-white/[0.03] text-xs" /></label>
          <label className="block space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Nomor faktur pajak</span><Input data-testid="tax-invoice-number-input" value={draft.tax_invoice_number} onChange={(event) => setDraft({ ...draft, tax_invoice_number: event.target.value })} placeholder="010.000-00.00000000" className="border-white/10 bg-white/[0.03] text-xs" /></label>
          <label className="block space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Tanggal dokumen</span><Input data-testid="tax-document-date-input" type="date" value={draft.document_date} onChange={(event) => setDraft({ ...draft, document_date: event.target.value })} className="border-white/10 bg-white/[0.03] text-xs" /></label>
          <div className="grid grid-cols-2 gap-3"><label className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">DPP</span><Input data-testid="tax-dpp-input" type="number" min="0" value={draft.dpp} onChange={(event) => setDraft({ ...draft, dpp: Number(event.target.value) })} className="border-white/10 bg-white/[0.03] text-xs" /></label><label className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Tarif</span><select data-testid="tax-rate-select" value={draft.tax_rate} onChange={(event) => setDraft({ ...draft, tax_rate: Number(event.target.value) as TaxRate })} className="h-8 w-full rounded-lg border border-white/10 bg-[#111827] px-2.5 text-xs text-slate-200"><option value="0">0%</option><option value="11">11%</option><option value="12">12%</option></select></label></div>
          <div data-testid="tax-vat-preview" className="flex items-center justify-between rounded-lg border border-emerald-400/10 bg-emerald-400/[0.04] p-3"><span className="text-xs text-slate-500">PPN otomatis</span><span className="text-sm font-bold text-emerald-300">{formatIDR(vatPreview)}</span></div>
          {selected.missing_fields.length > 0 && <div data-testid="tax-missing-fields" className="rounded-lg border border-amber-400/10 bg-amber-400/[0.04] p-3"><p className="flex items-center gap-2 text-xs font-semibold text-amber-300"><AlertTriangle size={14} /> Field belum lengkap</p><div className="mt-2 flex flex-wrap gap-1.5">{selected.missing_fields.map((field) => <span data-testid={`tax-missing-${field.toLowerCase().replaceAll(" ", "-")}`} key={field} className="rounded bg-amber-400/10 px-2 py-1 text-[10px] text-amber-200">{field}</span>)}</div></div>}
          <Button data-testid="tax-save-validation-button" onClick={() => updateMutation.mutate({ id: selected.id, payload: draft })} className="w-full gap-2 bg-emerald-400 text-xs text-[#03251b] hover:bg-emerald-300"><Check size={14} /> Simpan & validasi</Button>
          <div className="grid grid-cols-2 gap-2">{(selected.status === "draft" || selected.status === "needs_correction") && <Button data-testid="tax-submit-review-button" onClick={() => actionMutation.mutate({ id: selected.id, action: "submit_review" })} variant="outline" className="col-span-2 gap-2 border-white/10 bg-transparent text-xs text-slate-300"><Send size={14} /> Kirim review</Button>}{selected.status === "review" && <><Button data-testid="tax-mark-ready-button" onClick={() => actionMutation.mutate({ id: selected.id, action: "mark_ready" })} className="gap-2 bg-cyan-400 text-xs text-[#03251b]"><FileCheck2 size={14} /> Siap e-Faktur</Button><Button data-testid="tax-request-correction-button" onClick={() => actionMutation.mutate({ id: selected.id, action: "request_correction" })} variant="destructive" className="gap-2 text-xs"><X size={14} /> Perbaiki</Button></>}{selected.status === "ready" && <><Button data-testid="tax-mark-reported-button" onClick={() => actionMutation.mutate({ id: selected.id, action: "mark_reported" })} className="gap-2 bg-emerald-400 text-xs text-[#03251b]"><ShieldCheck size={14} /> Dilaporkan</Button><Button data-testid="tax-ready-correction-button" onClick={() => actionMutation.mutate({ id: selected.id, action: "request_correction" })} variant="destructive" className="gap-2 text-xs"><X size={14} /> Koreksi</Button></>}</div>
          <div data-testid="tax-status-history" className="border-t border-white/[0.06] pt-4"><p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600">Riwayat status</p>{[...selected.status_history].reverse().slice(0, 4).map((event, index) => <div data-testid={`tax-history-${index}`} key={`${event.timestamp}-${index}`} className="mt-3 border-l border-cyan-400/20 pl-3"><p className="text-[11px] font-semibold text-slate-300">{statusCopy[event.status]}</p><p className="mt-0.5 text-[10px] text-slate-600">{event.actor} · {event.note}</p></div>)}</div>
        </div> : <div data-testid="tax-validation-empty" className="py-12 text-center"><FileCheck2 className="mx-auto text-slate-700" size={26} /><p className="mt-3 text-xs text-slate-500">Pilih dokumen pajak untuk memeriksa kelengkapannya.</p></div>}</CardContent>
      </Card>
    </div>
  </div>;
}