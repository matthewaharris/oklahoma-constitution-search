# Configuration template for Supabase connection
# Copy this to config.py and fill in your actual values

# Supabase Configuration
SUPABASE_URL = "https://your-project-id.supabase.co"  # Replace with your Supabase project URL
SUPABASE_KEY = "your-anon-key-here"  # Replace with your Supabase anon key (or service role key)

# Optional: Database connection string for direct PostgreSQL access
# Only needed if you want to use raw SQL instead of Supabase client
DATABASE_URL = "postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres"

# Scraper settings
SCRAPER_VERSION = "1.0"
DEFAULT_DELAY_SECONDS = 1  # Delay between requests to be respectful