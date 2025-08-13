"""Initial schema with rolling partitions

Revision ID: 001
Revises: 
Create Date: 2025-01-13 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply initial schema with rolling partitions."""
    
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create rolling partition function
    op.execute("""
    CREATE OR REPLACE FUNCTION create_monthly_partition(
        table_name TEXT,
        start_date DATE
    ) RETURNS VOID AS $$
    DECLARE
        partition_name TEXT;
        start_month TEXT;
        end_date DATE;
    BEGIN
        -- Format partition name as tablename_YYYY_MM
        start_month := to_char(start_date, 'YYYY_MM');
        partition_name := table_name || '_' || start_month;
        
        -- Calculate end date (first day of next month)
        end_date := (start_date + INTERVAL '1 month')::DATE;
        
        -- Create partition table
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, table_name, start_date, end_date
        );
        
        -- Create indexes on partition
        CASE table_name
            WHEN 'agent_interactions' THEN
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (org_id, created_at)', 
                    partition_name || '_org_created_idx', partition_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (session_id, created_at)', 
                    partition_name || '_session_created_idx', partition_name);
                    
            WHEN 'vector_embeddings' THEN
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (org_id, content_id)', 
                    partition_name || '_org_content_idx', partition_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)', 
                    partition_name || '_embedding_idx', partition_name);
                    
            WHEN 'property_listings' THEN
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (org_id, suburb)', 
                    partition_name || '_org_suburb_idx', partition_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (postcode)', 
                    partition_name || '_postcode_idx', partition_name);
                    
            WHEN 'api_usage' THEN
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (org_id, endpoint)', 
                    partition_name || '_org_endpoint_idx', partition_name);
                EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (status_code)', 
                    partition_name || '_status_idx', partition_name);
        END CASE;
        
        RAISE NOTICE 'Created partition %', partition_name;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Create partition cleanup function
    op.execute("""
    CREATE OR REPLACE FUNCTION cleanup_old_partitions(
        table_name TEXT,
        retention_months INTEGER DEFAULT 6
    ) RETURNS INTEGER AS $$
    DECLARE
        partition_record RECORD;
        partition_date DATE;
        cutoff_date DATE;
        dropped_count INTEGER := 0;
    BEGIN
        cutoff_date := (CURRENT_DATE - INTERVAL '1 month' * retention_months)::DATE;
        
        -- Find partitions older than retention period
        FOR partition_record IN
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE tablename LIKE table_name || '_%'
            AND schemaname = 'public'
        LOOP
            -- Extract date from partition name (table_YYYY_MM format)
            BEGIN
                partition_date := to_date(
                    substring(partition_record.tablename from '(\d{4}_\d{2})$'),
                    'YYYY_MM'
                );
                
                IF partition_date < cutoff_date THEN
                    EXECUTE format('DROP TABLE IF EXISTS %I', partition_record.tablename);
                    dropped_count := dropped_count + 1;
                    RAISE NOTICE 'Dropped old partition: %', partition_record.tablename;
                END IF;
            EXCEPTION
                WHEN OTHERS THEN
                    RAISE WARNING 'Could not parse date from partition name: %', partition_record.tablename;
            END;
        END LOOP;
        
        RETURN dropped_count;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Create automatic partition creation function
    op.execute("""
    CREATE OR REPLACE FUNCTION ensure_current_partitions() RETURNS VOID AS $$
    DECLARE
        current_month DATE;
        next_month DATE;
        table_names TEXT[] := ARRAY['agent_interactions', 'vector_embeddings', 'property_listings', 'api_usage'];
        table_name TEXT;
    BEGIN
        current_month := date_trunc('month', CURRENT_DATE)::DATE;
        next_month := (current_month + INTERVAL '1 month')::DATE;
        
        -- Create partitions for current and next month
        FOREACH table_name IN ARRAY table_names
        LOOP
            PERFORM create_monthly_partition(table_name, current_month);
            PERFORM create_monthly_partition(table_name, next_month);
        END LOOP;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # Create main tables with partitioning
    op.execute("""
    CREATE TABLE agent_interactions (
        id VARCHAR(26) PRIMARY KEY,
        org_id VARCHAR(26) NOT NULL,
        session_id VARCHAR(64) NOT NULL,
        user_message TEXT NOT NULL,
        agent_response TEXT,
        query_type VARCHAR(50),
        metadata JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    ) PARTITION BY RANGE (created_at);
    """)
    
    op.execute("""
    CREATE TABLE vector_embeddings (
        id VARCHAR(26) PRIMARY KEY,
        org_id VARCHAR(26) NOT NULL,
        content_id VARCHAR(26) NOT NULL,
        content_text TEXT NOT NULL,
        embedding vector(1536) NOT NULL,
        embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
        metadata JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    ) PARTITION BY RANGE (created_at);
    """)
    
    op.execute("""
    CREATE TABLE property_listings (
        id VARCHAR(26) PRIMARY KEY,
        org_id VARCHAR(26) NOT NULL,
        external_id VARCHAR(100),
        address TEXT NOT NULL,
        suburb VARCHAR(100) NOT NULL,
        state VARCHAR(10) NOT NULL,
        postcode VARCHAR(10) NOT NULL,
        property_type VARCHAR(50),
        bedrooms INTEGER,
        bathrooms INTEGER,
        car_spaces INTEGER,
        price VARCHAR(100),
        description TEXT,
        features JSONB,
        source_url TEXT,
        scraped_at TIMESTAMPTZ DEFAULT NOW(),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    ) PARTITION BY RANGE (created_at);
    """)
    
    op.execute("""
    CREATE TABLE api_usage (
        id VARCHAR(26) PRIMARY KEY,
        org_id VARCHAR(26) NOT NULL,
        endpoint VARCHAR(200) NOT NULL,
        method VARCHAR(10) NOT NULL,
        status_code INTEGER NOT NULL,
        response_time_ms INTEGER,
        tokens_used INTEGER,
        model_used VARCHAR(100),
        user_agent TEXT,
        ip_address VARCHAR(45),
        metadata JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    ) PARTITION BY RANGE (created_at);
    """)
    
    # Create initial partitions for current and next month
    op.execute("SELECT ensure_current_partitions();")
    
    # Create base indexes on parent tables
    op.create_index('ix_agent_interactions_org_id', 'agent_interactions', ['org_id'])
    op.create_index('ix_agent_interactions_session_id', 'agent_interactions', ['session_id'])
    op.create_index('ix_vector_embeddings_org_id', 'vector_embeddings', ['org_id'])
    op.create_index('ix_vector_embeddings_content_id', 'vector_embeddings', ['content_id'])
    op.create_index('ix_property_listings_org_id', 'property_listings', ['org_id'])
    op.create_index('ix_property_listings_suburb', 'property_listings', ['suburb'])
    op.create_index('ix_property_listings_postcode', 'property_listings', ['postcode'])
    op.create_index('ix_api_usage_org_id', 'api_usage', ['org_id'])


def downgrade() -> None:
    """Remove schema and partition functions."""
    
    # Drop partition tables first
    op.execute("""
    DO $$
    DECLARE
        partition_record RECORD;
    BEGIN
        FOR partition_record IN
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE tablename ~ '^(agent_interactions|vector_embeddings|property_listings|api_usage)_\d{4}_\d{2}$'
            AND schemaname = 'public'
        LOOP
            EXECUTE format('DROP TABLE IF EXISTS %I', partition_record.tablename);
        END LOOP;
    END $$;
    """)
    
    # Drop main tables
    op.drop_table('api_usage')
    op.drop_table('property_listings')
    op.drop_table('vector_embeddings')
    op.drop_table('agent_interactions')
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS ensure_current_partitions()")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_partitions(TEXT, INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS create_monthly_partition(TEXT, DATE)")
    
    # Drop extension (only if no other tables use it)
    op.execute("DROP EXTENSION IF EXISTS vector")