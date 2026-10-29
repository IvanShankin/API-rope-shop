// Keep the view model stable across the existing API and the new product API.
export function normalizeVariant(variant) {
  return { ...variant,
    diameter_mm: variant.size_value ?? variant.diameter_mm,
    price_per_meter: variant.price ?? variant.price_per_meter,
    weight_g_per_m: variant.weight_g ?? variant.weight_g_per_m,
  };
}

export function normalizeProduct(product) {
  return { ...product,
    product_id: product.product_id ?? product.id,
    apiVersion: product.slug != null || (product.variants || []).some(v => 'size_value' in v) ? 2 : 1,
    variants: (product.variants || []).filter(v => v.is_active !== false).map(normalizeVariant)
      .sort((a,b) => (Number(a.index) || 0) - (Number(b.index) || 0)),
  };
}
