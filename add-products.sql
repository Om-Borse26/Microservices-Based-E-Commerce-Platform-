USE shopease_db;

-- Clear existing products (optional)
-- DELETE FROM products;

-- Add 25 products across different categories
INSERT INTO products (name, description, price, stock, category, image_url) VALUES
-- Electronics
('MacBook Pro 16"', 'Apple M3 Max, 36GB RAM, 1TB SSD', 2999.99, 15, 'Electronics', 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=300'),
('iPhone 15 Pro', '256GB Titanium Blue', 1199.99, 50, 'Electronics', 'https://images.unsplash.com/photo-1592286927505-b87b3e47eb89?w=300'),
('iPad Air', '11-inch, 256GB WiFi', 749.99, 30, 'Electronics', 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=300'),
('Samsung Galaxy S24 Ultra', '512GB Phantom Black', 1299.99, 25, 'Electronics', 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=300'),
('Dell XPS 15', 'Intel i9, 32GB RAM, RTX 4060', 2299.99, 10, 'Electronics', 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=300'),

-- Audio
('Sony WH-1000XM5', 'Wireless Noise-Cancelling Headphones', 399.99, 75, 'Audio', 'https://images.unsplash.com/photo-1545127398-14699f92334b?w=300'),
('AirPods Pro 2', 'USB-C with Spatial Audio', 249.99, 100, 'Audio', 'https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=300'),
('Bose QuietComfort 45', 'Bluetooth Headphones', 329.99, 60, 'Audio', 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=300'),
('JBL Flip 6', 'Portable Bluetooth Speaker', 129.99, 120, 'Audio', 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=300'),

-- Monitors
('Dell UltraSharp 27"', '4K USB-C Monitor', 649.99, 30, 'Monitors', 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=300'),
('LG 34" UltraWide', 'Curved Gaming Monitor 144Hz', 899.99, 20, 'Monitors', 'https://images.unsplash.com/photo-1585792180666-f7347c490ee2?w=300'),
('Samsung Odyssey G7', '32" 4K 240Hz Gaming', 1199.99, 15, 'Monitors', 'https://images.unsplash.com/photo-1527443195645-1133f7f28990?w=300'),

-- Accessories
('Logitech MX Master 3S', 'Wireless Performance Mouse', 99.99, 100, 'Accessories', 'https://images.unsplash.com/photo-1527814050087-3793815479db?w=300'),
('Keychron K8 Pro', 'Mechanical Keyboard RGB', 119.99, 80, 'Accessories', 'https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=300'),
('Apple Magic Trackpad', 'Multi-Touch Surface', 149.99, 50, 'Accessories', 'https://images.unsplash.com/photo-1625948515291-69613efd103f?w=300'),
('Anker PowerBank 20000mAh', 'Fast Charging USB-C', 59.99, 150, 'Accessories', 'https://images.unsplash.com/photo-1609592806955-a9c1c6f93ab6?w=300'),

-- Gaming
('PlayStation 5', '1TB Console with Controller', 499.99, 25, 'Gaming', 'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=300'),
('Xbox Series X', '1TB Console', 499.99, 20, 'Gaming', 'https://images.unsplash.com/photo-1621259182978-fbf93132d53d?w=300'),
('Nintendo Switch OLED', 'Neon Red/Blue', 349.99, 40, 'Gaming', 'https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?w=300'),
('Steam Deck', '512GB Handheld Gaming', 649.99, 15, 'Gaming', 'https://images.unsplash.com/photo-1635514569146-9a9607ecf303?w=300'),

-- Smart Home
('Amazon Echo Dot 5th Gen', 'Smart Speaker with Alexa', 49.99, 200, 'Smart Home', 'https://images.unsplash.com/photo-1543512214-318c7553f230?w=300'),
('Google Nest Hub', '7" Smart Display', 99.99, 100, 'Smart Home', 'https://images.unsplash.com/photo-1558089687-0bb9eadb4a3e?w=300'),
('Philips Hue Starter Kit', 'Smart LED Bulbs 4-Pack', 89.99, 75, 'Smart Home', 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=300'),
('Ring Video Doorbell', '1080p HD with Night Vision', 99.99, 60, 'Smart Home', 'https://images.unsplash.com/photo-1558002038-1055907df827?w=300'),

-- Wearables
('Apple Watch Series 9', 'GPS 45mm Starlight', 429.99, 45, 'Wearables', 'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=300');

SELECT COUNT(*) as total_products FROM products;
SELECT * FROM products ORDER BY id DESC LIMIT 10;