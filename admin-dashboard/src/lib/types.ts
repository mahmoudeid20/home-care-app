export type UserRole = "PATIENT" | "NURSE" | "ADMIN";

export interface AuthUser {
  id: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  is_email_verified: boolean;
  is_phone_verified: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: AuthUser;
  tokens: TokenPair;
}

export interface UserAdmin {
  id: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
}

export type DocumentType =
  | "NATIONAL_ID"
  | "NURSING_CERTIFICATE"
  | "GRADUATION_CERTIFICATE"
  | "EXPERIENCE_CERTIFICATE"
  | "OTHER";

export type DocumentStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface NurseDocument {
  id: string;
  document_type: DocumentType;
  status: DocumentStatus;
  rejection_reason: string | null;
}

export interface Location {
  id: string;
  governorate: string;
  city: string;
  area: string | null;
  address_line: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface Specialty {
  id: string;
  name_en: string;
  name_ar: string;
  is_active: boolean;
}

export interface ServiceItem {
  id: string;
  name_en: string;
  name_ar: string;
  is_active: boolean;
}

export interface NurseAdmin {
  id: string;
  user_id: string;
  full_name: string;
  professional_title: string | null;
  bio: string | null;
  gender: "MALE" | "FEMALE";
  experience_years: number;
  education: string | null;
  photo_url: string | null;
  location: Location | null;
  identity_verified: boolean;
  qualification_verified: boolean;
  experience_verified: boolean;
  is_approved: boolean;
  is_suspended: boolean;
  average_rating: number;
  review_count: number;
  specialties: Specialty[];
  services: { service: ServiceItem; price: number; price_unit: string }[];
  availability: unknown[];
}

export interface MatchingWeights {
  skills_weight: number;
  experience_weight: number;
  location_weight: number;
  availability_weight: number;
  price_weight: number;
  rating_weight: number;
  verification_weight: number;
}

export interface PlatformSettings {
  commission_percentage: number;
}

export interface PlatformStats {
  total_patients: number;
  total_nurses: number;
  verified_nurses: number;
  pending_verifications: number;
  active_bookings: number;
  completed_bookings: number;
  cancelled_bookings: number;
  total_revenue: number;
  platform_commission_earned: number;
  average_rating: number;
  most_requested_services: { service: string; count: number }[];
}

export type PaymentStatus = "PENDING" | "PAID" | "FAILED" | "REFUNDED" | "CANCELLED";

export interface Payment {
  id: string;
  booking_id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_method: string | null;
  transaction_id: string | null;
  platform_commission: number;
  nurse_earnings: number;
  created_at: string;
}

export type ComplaintStatus = "OPEN" | "IN_REVIEW" | "RESOLVED" | "CLOSED";

export interface Complaint {
  id: string;
  user_id: string;
  booking_id: string | null;
  category: string;
  description: string;
  attachments: string[];
  status: ComplaintStatus;
  admin_response: string | null;
  created_at: string;
}

export interface ApiError {
  error: { code: string; message: string; details?: unknown };
}
