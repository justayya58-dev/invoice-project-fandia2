export type TaxRate = 0 | 11 | 12;
export type TaxStatus = "draft" | "review" | "ready" | "reported" | "needs_correction";

export interface TaxRateProfile {
  rate: TaxRate;
  label: string;
  description: string;
}

export interface TaxStatusEvent {
  status: TaxStatus;
  actor: string;
  timestamp: string;
  note: string;
}

export interface TaxDocumentUpdate {
  npwp: string;
  tax_invoice_number: string;
  document_date: string;
  dpp: number;
  tax_rate: TaxRate;
}

export interface TaxActionRequest {
  action: "submit_review" | "mark_ready" | "mark_reported" | "request_correction";
  actor: string;
  note: string;
}

export interface TaxDocument {
  id: string;
  source_type: "invoice" | "transaction";
  source_id: string;
  direction: "input" | "output";
  counterparty: string;
  npwp: string;
  source_reference: string;
  tax_invoice_number: string;
  document_date: string;
  tax_period: string;
  dpp: number;
  tax_rate: TaxRate;
  vat: number;
  status: TaxStatus;
  completeness_score: number;
  missing_fields: string[];
  validation_notes: string[];
  created_at: string;
  updated_at: string;
  status_history: TaxStatusEvent[];
}

export interface TaxRateSummary {
  rate: number;
  dpp: number;
  vat: number;
  document_count: number;
}

export interface TaxSummary {
  period: string;
  output_dpp: number;
  output_vat: number;
  input_dpp: number;
  input_vat: number;
  net_vat: number;
  ready_count: number;
  issue_count: number;
  status_counts: Record<string, number>;
  by_rate: TaxRateSummary[];
}

export interface TaxSyncResult {
  created: number;
  total: number;
}