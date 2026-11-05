// Contrato de respuesta del backend: { ok, message, data }
export interface ApiResponse<T> {
  ok: boolean;
  message: string;
  data: T;
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export type Role = 'ADMIN' | 'OPERADOR' | 'CONSULTA';

export interface SessionUser {
  id: number;
  identification: string;
  full_name: string;
  email: string;
  role: Role;
  is_active: boolean;
}

export interface LoginData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: SessionUser;
}

export interface Ref {
  id: number;
  name: string;
}

export interface Campus {
  id: number;
  name: string;
  is_active: boolean;
  inactivation_reason: string | null;
}

export interface Block extends Campus {
  campus_id: number;
  campus_name: string;
}

export interface Department extends Campus {}

export interface Category extends Campus {}

export interface ObjectType extends Campus {
  category_id: number;
  category_name: string;
}

export interface Person {
  id: number;
  identification: string;
  full_name: string;
  affiliation_type: string;
  department_id: number | null;
  department_name: string | null;
  email: string | null;
  phone: string | null;
  is_active: boolean;
  inactivation_reason: string | null;
}

export interface ReturnSummary {
  id: number;
  receipt_reference: string;
  returned_at: string;
  delivered_by: Ref;
  owner: { id: number; full_name: string; identification: string };
  claim_id: number;
}

// Objeto completo (OPERADOR y ADMIN). Para CONSULTA llegan solo algunos campos.
export interface ObjectLost {
  id: number;
  code: string;
  object_type: Ref;
  category: Ref;
  description?: string;
  campus?: Ref;
  found_campus?: Ref;
  found_block?: Ref;
  found_location?: string;
  found_at?: string;
  custody_campus?: Ref;
  custody_block?: Ref;
  custody_location?: string;
  finder_person?: { id: number; identification: string; full_name: string; affiliation_type: string };
  finder_department?: Ref | null;
  received_by?: Ref;
  received_at: string;
  status: 'DISPONIBLE' | 'DEVUELTO';
  is_active?: boolean;
  version?: number;
  correction_reason?: string | null;
  inactivated_at?: string | null;
  inactivation_reason?: string | null;
  active_photos?: number;
  cover_photo_id?: number | null;
  return?: ReturnSummary | null;
}

export interface Photo {
  id: number;
  object_lost_id: number;
  mime_type: string;
  size_bytes: number;
  uploaded_by: Ref;
  uploaded_at: string;
  is_active: boolean;
  inactivation_reason: string | null;
}

export interface Claim {
  id: number;
  object_lost: { id: number; code: string; status: string };
  claimant: { id: number; identification: string; full_name: string };
  evidence: string;
  identity_verified: boolean;
  verification_notes: string | null;
  status: 'PENDIENTE' | 'ACEPTADA' | 'RECHAZADA';
  reviewed_by: Ref | null;
  reviewed_at: string | null;
  decision_reason: string | null;
  is_active: boolean;
  created_at: string;
  inactivation_reason: string | null;
}

export interface ReturnRecord {
  id: number;
  object_lost: { id: number; code: string; status: string };
  claim_id: number;
  owner: { id: number; identification: string; full_name: string };
  delivered_by: Ref;
  returned_at: string;
  receipt_reference: string;
  receipt_method: string;
  verification_summary: string;
  notes: string | null;
}

export interface AuditLog {
  id: number;
  entity: string;
  entity_id: number;
  action: string;
  actor: Ref | null;
  occurred_at: string;
  reason: string | null;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
}

export interface UserAccount {
  id: number;
  identification: string;
  full_name: string;
  email: string;
  role_id: number;
  role: Role;
  is_active: boolean;
  inactivation_reason: string | null;
}

export interface RoleItem {
  id: number;
  name: Role;
  description: string;
}

export interface CountItem {
  id: number;
  name: string;
  total: number;
}

export interface InventorySummary {
  total_available: number;
  by_campus: CountItem[];
  by_type: CountItem[];
  by_status: { status: string; total: number }[];
}

export interface DashboardSummary {
  total: number;
  available: number;
  returned: number;
  inactive: number;
  pending_claims: number;
}
