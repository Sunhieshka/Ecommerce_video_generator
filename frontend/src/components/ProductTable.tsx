import type { ProductItem } from "@/lib/types";

import StatusPill from "@/components/StatusPill";

interface ProductTableProps {
  products: ProductItem[];
}

export default function ProductTable({ products }: ProductTableProps) {
  return (
    <div className="overflow-hidden rounded-card border border-border bg-surface shadow-card">
      <div className="grid gap-4 p-4 lg:hidden">
        {products.map((product) => (
          <article key={product.id} className="rounded-inner border border-border bg-bg p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">
                  Row {product.row_number}
                </p>
                <p className="mt-2 font-medium text-text-primary">{product.product_name}</p>
                <p className="mt-1 font-mono text-[11px] text-purple-muted">{product.sku}</p>
              </div>
              <StatusPill status={product.status} />
            </div>
            <p className="mt-3 text-[13px] leading-6 text-text-secondary">{product.product_description}</p>
            {product.error_message ? (
              <p className="mt-3 text-[12px] text-pink break-words">{product.error_message}</p>
            ) : null}
            <div className="mt-4 rounded-card border border-blue/30 bg-surface">
              <div className="border-b border-border px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">
                Prompt Preview
              </div>
              <p className="px-3 py-3 font-mono text-[12px] leading-6 text-text-secondary break-words">
                {product.generated_prompt ?? "Prompt pending..."}
              </p>
            </div>
          </article>
        ))}
        {products.length === 0 ? (
          <div className="rounded-inner border border-border bg-bg px-4 py-6 text-[13px] text-text-secondary">
            No products available yet.
          </div>
        ) : null}
      </div>
      <div className="hidden max-h-[640px] overflow-auto lg:block">
        <table className="min-w-full table-fixed text-left text-sm">
          <colgroup>
            <col className="w-[70px]" />
            <col className="w-[96px]" />
            <col className="w-[24%]" />
            <col className="w-[22%]" />
            <col className="w-[34%]" />
          </colgroup>
          <thead className="sticky top-0 bg-surface/95 backdrop-blur">
            <tr className="text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">
              <th className="px-5 py-4">Row</th>
              <th className="px-5 py-4">SKU</th>
              <th className="px-5 py-4">Product</th>
              <th className="px-5 py-4">Status</th>
              <th className="px-5 py-4">Prompt</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id} className="border-t border-border align-top hover:bg-blue/[0.02]">
                <td className="px-5 py-4 text-[13px] text-text-secondary">{product.row_number}</td>
                <td className="px-5 py-4 font-mono text-[11px] text-purple-muted">{product.sku}</td>
                <td className="px-5 py-4">
                  <p className="font-medium text-text-primary">{product.product_name}</p>
                  <p className="mt-2 line-clamp-3 max-w-sm text-[13px] leading-6 text-text-secondary">
                    {product.product_description}
                  </p>
                </td>
                <td className="px-5 py-4">
                  <StatusPill status={product.status} />
                  {product.error_message ? (
                    <p className="mt-2 max-w-xs text-[12px] text-pink">{product.error_message}</p>
                  ) : null}
                </td>
                <td className="px-5 py-4">
                  <div className="rounded-card border border-blue/30 bg-surface">
                    <div className="border-b border-border px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.10em] text-text-tertiary">
                      Prompt Preview
                    </div>
                    <p className="line-clamp-5 px-3 py-3 font-mono text-[12px] leading-6 text-text-secondary break-words">
                      {product.generated_prompt ?? "Prompt pending..."}
                    </p>
                  </div>
                </td>
              </tr>
            ))}
            {products.length === 0 ? (
              <tr>
                <td className="px-5 py-6 text-[13px] text-text-secondary" colSpan={5}>
                  No products available yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
