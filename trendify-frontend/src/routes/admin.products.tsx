import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Button, Card, Field, FormError, TextArea } from "@/components/Forms";
import { fieldError } from "@/lib/forms";
import { query, useAdminList } from "@/lib/admin";
import { api } from "@/lib/api";
import {
  categories,
  formatPrice,
  invalidateProducts,
  type ApiProduct,
  type Category,
} from "@/lib/products";

interface AdminProduct extends ApiProduct {
  is_active: boolean;
}

export const Route = createFileRoute("/admin/products")({ component: AdminProducts });

function AdminProducts() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [editing, setEditing] = useState<AdminProduct | "new" | null>(null);
  const { data, error, reload } = useAdminList<AdminProduct>(
    `/admin/products${query({ q: q.trim() || undefined, status, per_page: 100 })}`,
  );

  async function toggle(p: AdminProduct) {
    try {
      if (p.is_active) await api(`/admin/products/${p.product_id}`, { method: "DELETE" });
      else await api(`/admin/products/${p.product_id}/restore`, { method: "POST" });
      invalidateProducts();
      toast.success(p.is_active ? `${p.name} archived` : `${p.name} restored`);
      reload();
    } catch (err) {
      toast.error((err as Error).message);
    }
  }

  if (editing)
    return (
      <ProductForm
        product={editing === "new" ? null : editing}
        onDone={() => {
          setEditing(null);
          invalidateProducts();
          reload();
        }}
      />
    );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search products…"
          aria-label="Search products"
          maxLength={100}
          className="rounded-full border bg-card px-4 py-2 text-sm outline-none"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          aria-label="Status"
          className="rounded-full border bg-card px-4 py-2 text-sm"
        >
          <option value="all">All</option>
          <option value="active">On sale</option>
          <option value="archived">Archived</option>
        </select>
        <Button className="ml-auto" onClick={() => setEditing("new")}>
          Add product
        </Button>
      </div>
      <FormError error={error} />
      <div className="overflow-x-auto rounded-3xl border bg-card">
        <table className="w-full text-sm">
          <thead className="text-left text-muted-foreground">
            <tr>
              <th className="p-3">Product</th>
              <th className="p-3">Category</th>
              <th className="p-3">Price</th>
              <th className="p-3">Stock</th>
              <th className="p-3">Status</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {data?.items.map((p) => (
              <tr key={p.product_id} className="border-t">
                <td className="flex items-center gap-3 p-3">
                  <img
                    src={p.image_url ?? ""}
                    alt=""
                    className="h-10 w-10 rounded-xl object-cover"
                  />
                  <span className="font-semibold">{p.name}</span>
                </td>
                <td className="p-3">{p.category}</td>
                <td className="p-3">{formatPrice(p.price)}</td>
                <td
                  className={`p-3 ${p.stock_quantity < 5 ? "font-semibold text-destructive" : ""}`}
                >
                  {p.stock_quantity}
                </td>
                <td className="p-3">{p.is_active ? "On sale" : "Archived"}</td>
                <td className="space-x-2 whitespace-nowrap p-3 text-right">
                  <button className="underline" onClick={() => setEditing(p)}>
                    Edit
                  </button>
                  <button className="underline" onClick={() => void toggle(p)}>
                    {p.is_active ? "Archive" : "Restore"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.items.length === 0 && (
          <p className="p-6 text-center text-muted-foreground">No products.</p>
        )}
      </div>
    </div>
  );
}

function ProductForm({ product, onDone }: { product: AdminProduct | null; onDone: () => void }) {
  const [form, setForm] = useState({
    name: product?.name ?? "",
    slug: product?.slug ?? "",
    description: product?.description ?? "",
    price: product ? String(product.price) : "",
    old_price: product?.old_price != null ? String(product.old_price) : "",
    stock_quantity: product ? String(product.stock_quantity) : "0",
    category: (product?.category ?? "Home") as Category,
    badge: product?.badge ?? "",
    sizes: product?.sizes.join(", ") ?? "",
    image_url: product?.image_url ?? "",
  });
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);

  const set =
    (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm({ ...form, [k]: e.target.value });

  async function upload(file: File) {
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api<{ image_url: string }>("/admin/uploads/product-image", {
        method: "POST",
        form: fd,
      });
      setForm((f) => ({ ...f, image_url: res.image_url }));
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const body = {
      name: form.name,
      description: form.description,
      price: Number(form.price),
      old_price: form.old_price ? Number(form.old_price) : null,
      stock_quantity: Number.parseInt(form.stock_quantity, 10),
      category: form.category,
      badge: form.badge || null,
      sizes: form.sizes
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      image_url: form.image_url || null,
      ...(form.slug ? { slug: form.slug } : {}),
    };
    try {
      if (product) await api(`/admin/products/${product.product_id}`, { method: "PATCH", body });
      else await api("/admin/products", { method: "POST", body });
      toast.success(product ? "Product saved" : "Product created");
      onDone();
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  }

  return (
    <Card>
      <h2 className="mb-4 text-2xl">{product ? `Edit ${product.name}` : "New product"}</h2>
      <form onSubmit={save} className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <FormError error={error} />
        </div>
        <Field
          label="Name"
          name="name"
          required
          maxLength={255}
          value={form.name}
          onChange={set("name")}
          error={fieldError(error, "name")}
        />
        <Field
          label="URL slug"
          name="slug"
          maxLength={120}
          value={form.slug}
          onChange={set("slug")}
          hint="Leave empty to generate it from the name."
          error={fieldError(error, "slug")}
        />
        <div className="md:col-span-2">
          <TextArea
            label="Description"
            name="description"
            required
            rows={3}
            maxLength={5000}
            value={form.description}
            onChange={set("description")}
            error={fieldError(error, "description")}
          />
        </div>
        <Field
          label="Price"
          name="price"
          type="number"
          step="0.01"
          min="0.01"
          required
          value={form.price}
          onChange={set("price")}
          error={fieldError(error, "price")}
        />
        <Field
          label="Old price (optional, for sales)"
          name="old_price"
          type="number"
          step="0.01"
          min="0.01"
          value={form.old_price}
          onChange={set("old_price")}
          error={fieldError(error, "old_price")}
        />
        <Field
          label="Stock"
          name="stock_quantity"
          type="number"
          step="1"
          min="0"
          required
          value={form.stock_quantity}
          onChange={set("stock_quantity")}
          error={fieldError(error, "stock_quantity")}
        />
        <label className="block space-y-1.5">
          <span className="text-sm font-semibold">Category</span>
          <select
            value={form.category}
            onChange={set("category")}
            className="w-full rounded-2xl border bg-card px-4 py-3 text-sm"
          >
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <Field
          label="Badge (optional)"
          name="badge"
          maxLength={40}
          value={form.badge}
          onChange={set("badge")}
          hint='e.g. "New" or "-20%"'
        />
        <Field
          label="Sizes (optional)"
          name="sizes"
          value={form.sizes}
          onChange={set("sizes")}
          hint="Comma-separated, e.g. 38, 39, 40"
          error={fieldError(error, "sizes")}
        />
        <div className="space-y-2 md:col-span-2">
          <span className="text-sm font-semibold">Photo</span>
          <div className="flex items-center gap-4">
            {form.image_url && (
              <img src={form.image_url} alt="" className="h-24 w-24 rounded-2xl object-cover" />
            )}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              aria-label="Upload photo"
              onChange={(e) => e.target.files?.[0] && void upload(e.target.files[0])}
            />
            {uploading && <span className="text-sm text-muted-foreground">Uploading…</span>}
          </div>
          <p className="text-xs text-muted-foreground">
            JPEG, PNG or WebP. It's cropped to a square and re-saved as a clean JPEG.
          </p>
        </div>
        <div className="flex gap-2 md:col-span-2">
          <Button type="submit" busy={busy}>
            {product ? "Save changes" : "Create product"}
          </Button>
          <Button type="button" variant="outline" onClick={onDone}>
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  );
}
