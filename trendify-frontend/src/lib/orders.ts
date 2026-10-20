export type OrderStatus =
  "pending_payment" | "paid" | "shipped" | "delivered" | "cancelled" | "refunded";

export interface OrderItem {
  product_id: number;
  product_slug: string | null;
  product_name: string | null;
  image_url: string | null;
  quantity: number;
  size: string | null;
  price: number;
  line_total: number;
}

export interface Order {
  order_id: number;
  reference: string;
  status: OrderStatus;
  total_amount: number;
  currency: string;
  shipping_address: string;
  phone_number: string | null;
  payment_status: string | null;
  payment_method: string | null;
  paid_at: string | null;
  created_at: string | null;
  can_cancel: boolean;
  can_pay: boolean;
  items: OrderItem[];
}

export interface AdminOrder extends Order {
  user_id: number;
  user_email: string | null;
  payment_provider: string | null;
  payment_tracking_id: string | null;
  allowed_transitions: OrderStatus[];
}

export const statusLabel: Record<OrderStatus, string> = {
  pending_payment: "Awaiting payment",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
  refunded: "Refunded",
};

export const formatDate = (iso: string | null) =>
  iso ? new Date(iso + (iso.endsWith("Z") ? "" : "Z")).toLocaleString() : "";

/** Send the browser to the payment page (Pesapal is a different site; the simulator is ours). */
export function goToPayment(url: string, navigateInternal: (path: string) => void) {
  const target = new URL(url, window.location.origin);
  if (target.origin === window.location.origin) navigateInternal(target.pathname + target.search);
  else window.location.assign(target.toString());
}
