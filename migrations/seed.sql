-- TranslateFlow Database Seed Data
-- This file contains initial data for development/testing
--
-- Usage:
--   ./scripts/db-migrate.sh seed
--
-- Note: This file is automatically executed by the migration system
-- when you run ./scripts/db-migrate.sh seed

-- Insert default subscription plans
INSERT INTO subscription_plans (name, description, price_monthly, price_yearly, max_members, max_projects, features, stripe_price_id_monthly, stripe_price_id_yearly, is_active) VALUES
('Free', 'Perfect for trying out TranslateFlow', 0, 0, 5, 1, '["Basic translation", "Community support"]', NULL, NULL, true),
('Starter', 'For individuals and small projects', 9, 90, 10, 5, '["Basic translation", "Email support", "5 team members"]', NULL, NULL, true),
('Pro', 'For growing teams and businesses', 29, 290, 50, 50, '["Advanced translation", "Priority support", "50 team members", "API access"]', NULL, NULL, true),
('Enterprise', 'For large organizations with custom needs', 99, 990, -1, -1, '["Unlimited everything", "Dedicated support", "Custom integrations", "SLA guarantee"]', NULL, NULL, true)
ON CONFLICT (name) DO NOTHING;

-- Note: The default admin user (username: admin, password: admin)
-- is automatically created by the application on startup
-- See: Tools/WebServer/web_server.py startup event

-- Insert sample language preferences (optional)
-- This is just an example - the application manages language preferences dynamically

-- Insert system settings (optional)
-- INSERT INTO settings (key, value, description) VALUES
-- ('maintenance_mode', 'false', 'Enable maintenance mode'),
-- ('max_upload_size', '10485760', 'Maximum file upload size in bytes (10MB)')
-- ON CONFLICT (key) DO NOTHING;

-- Seed complete
-- You can add more seed data as needed for your application
