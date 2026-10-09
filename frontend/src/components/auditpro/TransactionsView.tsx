import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AlertTriangle, ArrowDownLeft, ArrowUpRight, Check, ChevronRight, Clock3, FileClock, Plus, Send, X } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiGet, apiPost } from "@/lib/api";
import type { Transaction, TransactionAction, TransactionActionRequest, TransactionCreate, TransactionStatus } from "@/types/finance";

const formatIDR = (value: number) => new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", maximumFractionDigits: 0 }).format(value);
const statusCopy: Record<TransactionStatus, string> = { draft: "Draft", review: "Perlu review", approved: "Disetujui", rejected: "Ditolak" };

function WorkflowBadge({ status }: { status: TransactionStatus }) {
  const tone = status === "approved" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300" : status === "rejected" ? "border-red-500/20 bg-red-500/10 text-red-300" : status === "review" ? "border-amber-500/20 bg-amber-500/10 text-amber-300" : "border-slate-500/20 bg-slate-500/10 text-slate-300";
  return <Badge data-testid={`transaction-status-${status}`} className={`border ${tone}`}>{statusCopy[status]}</Badge>;
}

export default function TransactionsView() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [type, setType] = useState<"income" | "expense">("expense");
  const [date, setDate] = useState("");
  const [counterparty, setCounterparty] = useState("");
  const [reference, setReference] = useState("");
  const [category, setCategory] = useState("Operasional");
  const [description, setDescription] = useState("");
  const [subtotal, setSubtotal] = useState("");
  const [tax, setTax] = useState("0");
  const transactionsQuery = useQuery({ queryKey: ["transactions"], queryFn: () => apiGet<Transaction[]>("/auditpro/transactions"), retry: false });
  const transactions = transactionsQuery.data ?? [];
  const selected = transactions.find((item) => item.id === selectedId) ?? null;
  const calculatedTotal = (Number(subtotal) || 0) + (Number(tax) || 0);
  const invalidateFinance = () => {
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["reports"] });
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  };
  const createMutation = useMutation({
    mutationFn: (payload: TransactionCreate) => apiPost<Transaction>("/auditpro/transactions", payload),
    onSuccess: (transaction) => {
      invalidateFinance();
      setSelectedId(transaction.id);
      setShowForm(false);
      setCounterparty(""); setReference(""); setDescription(""); setSubtotal(""); setTax("0");
      toast.success(transaction.duplicate_suspected ? "Transaksi tersimpan dengan peringatan duplikat" : "Transaksi draft berhasil disimpan");
    },
    onError: () => toast.error("Transaksi belum dapat disimpan"),
  });
  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: TransactionAction }) => apiPost<Transaction>(`/auditpro/transactions/${id}/action`, { action, actor: "Raka Adinata", note: action === "reject" ? "Ditolak saat review transaksi" : "" } satisfies TransactionActionRequest),
    onSuccess: (transaction) => { invalidateFinance(); setSelectedId(transaction.id); toast.success(`Status transaksi: ${statusCopy[transaction.status]}`); },
    onError: () => toast.error("Perubahan status tidak dapat diproses"),
  });
  const submitForm = () => createMutation.mutate({ type, transaction_date: date || null, counterparty, reference_number: reference, description, category, subtotal: Number(subtotal), tax: Number(tax), total: calculatedTotal });

  return <div className="animate-rise-in space-y-6">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p data-testid="transactions-eyebrow" className="text-[11px] font-semibold uppercase tracking-[.2em] text-cyan-300">TRANSACTION CONTROL · 03</p><h1 data-testid="transactions-title" className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-white sm:text-3xl">Database transaksi</h1><p data-testid="transactions-subtitle" className="mt-2 text-sm text-slate-500">Satukan input manual dan OCR dalam approval workflow yang dapat diaudit.</p></div><Button data-testid="add-transaction-button" onClick={() => setShowForm((value) => !value)} className="w-fit gap-2 bg-emerald-400 text-xs font-semibold text-[#03251b] hover:bg-emerald-300"><Plus size={15} /> Input transaksi</Button></div>
    {showForm && <Card data-testid="transaction-create-form" className="border-cyan-400/15 bg-[#101b2a] shadow-none"><CardHeader className="border-b border-white/[0.06] px-5 py-4"><CardTitle data-testid="transaction-form-title" className="font-heading text-base font-bold text-white">Transaksi manual baru</CardTitle></CardHeader><CardContent className="grid gap-4 p-5 sm:grid-cols-2 xl:grid-cols-4">
      <label data-testid="transaction-type-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Tipe</span><select data-testid="transaction-type-select" value={type} onChange={(event) => setType(event.target.value as "income" | "expense")} className="h-8 w-full rounded-lg border border-white/10 bg-[#111827] px-2.5 text-xs text-slate-200 outline-none focus:border-emerald-400"><option value="expense">Pengeluaran</option><option value="income">Pemasukan</option></select></label>
      <label data-testid="transaction-date-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Tanggal</span><Input data-testid="transaction-date-input" type="date" value={date} onChange={(event) => setDate(event.target.value)} className="border-white/10 bg-white/[0.03] text-xs" /></label>
      <label data-testid="transaction-counterparty-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Customer / vendor</span><Input data-testid="transaction-counterparty-input" value={counterparty} onChange={(event) => setCounterparty(event.target.value)} placeholder="PT Contoh Indonesia" className="border-white/10 bg-white/[0.03] text-xs" /></label>
      <label data-testid="transaction-reference-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Nomor referensi</span><Input data-testid="transaction-reference-input" value={reference} onChange={(event) => setReference(event.target.value)} placeholder="INV-2026-001" className="border-white/10 bg-white/[0.03] text-xs" /></label>
      <label data-testid="transaction-category-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Kategori</span><Input data-testid="transaction-category-input" value={category} onChange={(event) => setCategory(event.target.value)} className="border-white/10 bg-white/[0.03] text-xs" /></label>
      <label data-testid="transaction-subtotal-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Subtotal</span><Input data-testid="transaction-subtotal-input" type="number" min="0" value={subtotal} onChange={(event) => setSubtotal(event.target.value)} placeholder="0" className="border-white/10 bg-white/[0.03] text-xs" /></label>
      <label data-testid="transaction-tax-field" className="space-y-2"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Pajak</span><Input data-testid="transaction-tax-input" type="number" min="0" value={tax} onChange={(event) => setTax(event.target.value)} className="border-white/10 bg-white/[0.03] text-xs" /></label>
      <div data-testid="transaction-total-preview" className="rounded-lg border border-emerald-400/10 bg-emerald-400/[0.05] p-3"><p className="text-[10px] uppercase tracking-wider text-slate-500">Total real-time</p><p data-testid="transaction-total-value" className="mt-1 font-heading text-base font-bold text-emerald-300">{formatIDR(calculatedTotal)}</p></div>
      <label data-testid="transaction-description-field" className="space-y-2 sm:col-span-2 xl:col-span-3"><span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Deskripsi</span><Textarea data-testid="transaction-description-input" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Keterangan transaksi" className="min-h-20 border-white/10 bg-white/[0.03] text-xs" /></label>
      <div className="flex items-end"><Button data-testid="transaction-create-submit" onClick={submitForm} disabled={!counterparty.trim() || !reference.trim() || calculatedTotal <= 0 || createMutation.isPending} className="w-full gap-2 bg-emerald-400 text-xs text-[#03251b] hover:bg-emerald-300"><Check size={14} /> {createMutation.isPending ? "Menyimpan..." : "Simpan sebagai draft"}</Button></div>
    </CardContent></Card>}
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_340px]"><Card data-testid="transactions-database-card" className="border-white/[0.07] bg-[#111827]/80 shadow-none"><CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/[0.06] px-5 py-4"><div><p data-testid="transactions-table-eyebrow" className="text-[10px] font-semibold uppercase tracking-[.16em] text-slate-500">Unified ledger</p><CardTitle data-testid="transactions-table-title" className="mt-1 font-heading text-base font-bold text-white">Semua transaksi</CardTitle></div><span data-testid="transactions-count" className="text-xs text-slate-500">{transactions.length} transaksi</span></CardHeader><CardContent className="p-0"><div className="overflow-x-auto"><table data-testid="transactions-table" className="w-full min-w-[760px] text-left"><thead className="border-b border-white/[0.06] text-[10px] uppercase tracking-[.14em] text-slate-600"><tr><th className="px-5 py-3 font-semibold">Transaksi</th><th className="px-3 py-3 font-semibold">Pihak</th><th className="px-3 py-3 font-semibold">Total</th><th className="px-3 py-3 font-semibold">Status</th><th className="px-5 py-3 text-right font-semibold">Aksi</th></tr></thead><tbody>{transactions.map((transaction) => <tr data-testid={`transaction-row-${transaction.id}`} key={transaction.id} onClick={() => setSelectedId(transaction.id)} className="cursor-pointer border-b border-white/[0.04] last:border-0 hover:bg-white/[0.025]"><td className="px-5 py-3.5"><div className="flex items-center gap-2.5"><span className={`grid size-7 place-items-center rounded-lg ${transaction.type === "income" ? "bg-emerald-400/10 text-emerald-300" : "bg-amber-400/10 text-amber-300"}`}>{transaction.type === "income" ? <ArrowDownLeft size={14} /> : <ArrowUpRight size={14} />}</span><div><p data-testid={`transaction-reference-${transaction.id}`} className="text-xs font-semibold text-slate-200">{transaction.reference_number}</p><p data-testid={`transaction-date-${transaction.id}`} className="mt-0.5 text-[10px] text-slate-600">{transaction.transaction_date} · {transaction.source.toUpperCase()}</p></div>{transaction.duplicate_suspected && <span data-testid={`transaction-duplicate-${transaction.id}`} title={`Mirip dengan ${transaction.duplicate_of ?? "transaksi lain"}`} className="text-amber-300"><AlertTriangle size={14} /></span>}</div></td><td data-testid={`transaction-counterparty-${transaction.id}`} className="px-3 py-3.5 text-xs text-slate-400">{transaction.counterparty}</td><td data-testid={`transaction-total-${transaction.id}`} className="px-3 py-3.5 text-xs font-medium text-slate-300">{formatIDR(transaction.total)}</td><td className="px-3 py-3.5"><WorkflowBadge status={transaction.status} /></td><td className="px-5 py-3.5"><div className="flex justify-end gap-1.5" onClick={(event) => event.stopPropagation()}>{transaction.status === "draft" && <Button data-testid={`transaction-submit-${transaction.id}`} onClick={() => actionMutation.mutate({ id: transaction.id, action: "submit" })} size="xs" variant="outline" className="border-white/10 bg-transparent text-slate-300"><Send size={12} /> Review</Button>}{transaction.status === "review" && <><Button data-testid={`transaction-approve-${transaction.id}`} onClick={() => actionMutation.mutate({ id: transaction.id, action: "approve" })} size="xs" className="bg-emerald-400 text-[#03251b] hover:bg-emerald-300"><Check size={12} /> Setujui</Button><Button data-testid={`transaction-reject-${transaction.id}`} onClick={() => actionMutation.mutate({ id: transaction.id, action: "reject" })} size="icon-xs" variant="destructive"><X size={12} /></Button></>}{transaction.status !== "draft" && transaction.status !== "review" && <button data-testid={`transaction-detail-${transaction.id}`} onClick={() => setSelectedId(transaction.id)} className="rounded-md p-1.5 text-slate-600 hover:bg-white/5 hover:text-white"><ChevronRight size={14} /></button>}</div></td></tr>)}</tbody></table></div></CardContent></Card>
      <Card data-testid="transaction-audit-card" className="h-fit border-white/[0.07] bg-[#111827]/80 shadow-none"><CardHeader className="border-b border-white/[0.06] px-5 py-4"><div className="flex items-center gap-2"><FileClock size={16} className="text-cyan-300" /><CardTitle data-testid="transaction-audit-title" className="font-heading text-base font-bold text-white">Audit trail</CardTitle></div></CardHeader><CardContent className="p-5">{selected ? <div data-testid="transaction-audit-content"><div className="border-b border-white/[0.06] pb-4"><p data-testid="audit-selected-reference" className="text-sm font-semibold text-slate-200">{selected.reference_number}</p><p data-testid="audit-selected-party" className="mt-1 text-xs text-slate-500">{selected.counterparty} · {formatIDR(selected.total)}</p></div><div className="mt-5 space-y-4">{[...selected.audit_trail].reverse().map((item, index) => <div data-testid={`audit-event-${index}`} key={`${item.timestamp}-${index}`} className="flex gap-3"><span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-cyan-400/10 text-cyan-300"><Clock3 size={12} /></span><div><p data-testid={`audit-event-action-${index}`} className="text-xs font-semibold capitalize text-slate-300">{item.action.replace("_", " ")}</p><p data-testid={`audit-event-note-${index}`} className="mt-1 text-[11px] leading-relaxed text-slate-500">{item.note || "Status diperbarui"}</p><p data-testid={`audit-event-meta-${index}`} className="mt-1 text-[10px] text-slate-700">{item.actor} · {new Date(item.timestamp).toLocaleString("id-ID")}</p></div></div>)}</div></div> : <div data-testid="transaction-audit-empty" className="py-10 text-center"><FileClock className="mx-auto text-slate-700" size={24} /><p className="mt-3 text-xs text-slate-500">Pilih transaksi untuk melihat riwayat lengkap.</p></div>}</CardContent></Card>
    </div>
  </div>;
}