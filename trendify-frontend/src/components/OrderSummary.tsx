import { Link } from "@tanstack/react-router";
import type { Order } from "@/lib/orders";
import { formatPrice } from "@/lib/products";

export function OrderSummary({ order }: { order: Order }) {
  return (
    <>
      <div className="space-y-3">
        {order.items.map((i) => (
          <div key={`${i.product_id}-${i.size}`} className="flex items-center gap-4">
            <img src={i.image_url ?? ""} alt="" className="h-16 w-16 rounded-2xl object-cover" />
            <div className="flex-1">
              {i.product_slug ? (
                <Link to="/product/$id" params={{ id: i.product_slug }} className="font-semibold">
                  {i.product_name}
                </Link>
              ) : (
                <span className="font-semibold">{i.product_name}</span>
              )}
              <p className="text-sm text-muted-foreground">
                {i.size && `Size ${i.size} · `}
                {i.quantity} × {formatPrice(i.price)}
              </p>
            </div>
            <span className="font-semibold">{formatPrice(i.line_total)}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex justify-between border-t pt-4 text-lg font-bold">
        <span>Total</span>
        <span>
          {formatPrice(order.total_amount)} {order.currency}
        </span>
      </div>
    </>
  );
}
