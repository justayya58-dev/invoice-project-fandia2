import type { InvoiceItem, InvoiceTemplate } from "@/types/invoice";

export interface AssistantSessionCreate { title: string }
export interface AssistantSession { id: string; workspace_id: string; title: string; created_at: string; updated_at: string }
export interface AssistantMessageCreate { message: string }
export interface AssistantMessage { id: string; session_id: string; role: "user" | "assistant"; content: string; proposal_id: string | null; created_at: string }

export interface DraftInvoiceProposalPayload {
  customer: string;
  customer_id: string | null;
  due_date: string;
  items: InvoiceItem[];
  template: InvoiceTemplate;
  notes: string;
  tax_rate: number;
}

export interface DraftReportProposalPayload { title: string; period_start: string; period_end: string; summary_focus: string }
export interface AssistantProposal {
  id: string;
  session_id: string;
  type: "draft_invoice" | "draft_report";
  title: string;
  status: "pending" | "confirmed" | "cancelled";
  payload: DraftInvoiceProposalPayload | DraftReportProposalPayload;
  created_at: string;
  decided_at: string | null;
  result_id: string | null;
}
export interface AssistantProposalDecision { confirm: boolean }
export interface AssistantSessionDetail { session: AssistantSession; messages: AssistantMessage[]; proposals: AssistantProposal[] }
export interface AssistantQuickPrompt { id: string; label: string; prompt: string }
export interface AssistantAuditEvent { id: string; session_id: string; action: "message" | "proposal_created" | "proposal_confirmed" | "proposal_cancelled"; actor: string; detail: string; timestamp: string }
export interface AssistantDraftReport { id: string; title: string; period_start: string; period_end: string; summary_focus: string; sales_total: number; expense_total: number; net_profit: number; receivables: number; created_by: string; created_at: string }