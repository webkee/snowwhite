-- 올리브영 스킨케어/메이크업 제품 테이블

CREATE TABLE IF NOT EXISTS olive_products (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_type varchar(20) NOT NULL CHECK (product_type IN ('skincare', 'makeup')),
  goods_no varchar(50) NOT NULL,
  brand text,
  product_name text,
  price integer,
  rating numeric(3, 2),
  review_count integer,
  category text,
  product_info_disclosure text,
  contents_volume_or_weight text,
  main_specifications text,
  expiration_date text,
  usage_method text,
  manufacturer_info text,
  country_of_origin text,
  ingredients text,
  functionality_approval text,
  precautions text,
  quality_standard text,
  consumer_phone text,
  source_url text,
  crawled_at timestamptz,
  UNIQUE(goods_no, product_type)
);

CREATE INDEX IF NOT EXISTS idx_olive_products_goods_no ON olive_products(goods_no);
CREATE INDEX IF NOT EXISTS idx_olive_products_brand ON olive_products(brand);
CREATE INDEX IF NOT EXISTS idx_olive_products_category ON olive_products(category);
CREATE INDEX IF NOT EXISTS idx_olive_products_product_type ON olive_products(product_type);
