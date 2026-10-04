export interface CustomerProfile {
  name: string;
  phone_masked: string;
  city: string;
  service_address_line: string;
  account_status: string;
}

export interface DemoCustomer {
  customer_id: string;
  name: string;
  phone_masked: string;
}

export interface SnapshotPlan {
  plan_name: string;
  plan_type: string;
  renewal_date: string;
  data_limit_gb: number;
  is_data_unlimited: boolean;
}

export interface SnapshotBill {
  bill_id: string;
  amount: number;
  due_date: string;
  status: string;
  plan_type: string;
}

export interface SnapshotPayment {
  status: string;
  failure_reason?: string | null;
}

export interface SnapshotPaymentProfile {
  autopay_enabled: boolean;
  payment_method_label: string;
}

export interface SnapshotSubscription {
  subscription_id: string;
  plan_name: string;
  plan_type: string;
  status: string;
  renewal_date: string;
  monthly_price: number;
}

export interface SnapshotAttentionItem {
  domain: string;
  severity: string;
  message: string;
  prompt?: string;
}

export interface SnapshotBillByLine {
  plan_type: string;
  plan_name: string;
  bill_id: string;
  amount: number;
  due_date: string;
  status: string;
}

export interface SnapshotProjectedBill {
  estimated_amount: number;
  plan_name: string;
  plan_type: string;
  as_of_date: string;
}

export interface AccountSnapshot {
  customer_id: string;
  name: string;
  phone_masked: string;
  city: string;
  service_address_line: string;
  account_status: string;
  plan: SnapshotPlan | null;
  usage_headline: string | null;
  bill: SnapshotBill | null;
  bills_by_line: SnapshotBillByLine[];
  payment: SnapshotPayment | null;
  payment_profile: SnapshotPaymentProfile | null;
  has_payment_profile: boolean;
  projected_bill: SnapshotProjectedBill | null;
  available_credits: number;
  active_subscriptions: SnapshotSubscription[];
  attention_items: SnapshotAttentionItem[];
  generated_at: string;
}
