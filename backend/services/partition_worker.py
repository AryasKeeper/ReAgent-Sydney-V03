"""Partition management worker with scheduling."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class PartitionManager:
    """Manages database partitions with automatic creation and cleanup."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def create_future_partitions(self, months_ahead: int = 2) -> dict:
        """Create partitions for future months."""
        async with AsyncSessionLocal() as session:
            try:
                results = {}
                table_names = ['agent_interactions', 'vector_embeddings', 'property_listings', 'api_usage']
                
                for i in range(months_ahead):
                    target_date = datetime.now().replace(day=1) + timedelta(days=32 * (i + 1))
                    month_str = target_date.strftime('%Y-%m-01')
                    
                    for table_name in table_names:
                        try:
                            await session.execute(
                                text("SELECT create_monthly_partition(:table_name, :start_date)"),
                                {"table_name": table_name, "start_date": month_str}
                            )
                            partition_key = f"{table_name}_{target_date.strftime('%Y_%m')}"
                            results[partition_key] = "created"
                            logger.info(f"Created partition: {partition_key}")
                        except Exception as e:
                            logger.warning(f"Failed to create partition {table_name}_{target_date.strftime('%Y_%m')}: {e}")
                            results[f"{table_name}_{target_date.strftime('%Y_%m')}"] = f"error: {str(e)}"
                
                await session.commit()
                return results
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating future partitions: {e}")
                raise
    
    async def cleanup_old_partitions(self, retention_months: int = 6) -> dict:
        """Clean up old partitions beyond retention period."""
        async with AsyncSessionLocal() as session:
            try:
                results = {}
                table_names = ['agent_interactions', 'vector_embeddings', 'property_listings', 'api_usage']
                
                for table_name in table_names:
                    try:
                        result = await session.execute(
                            text("SELECT cleanup_old_partitions(:table_name, :retention_months)"),
                            {"table_name": table_name, "retention_months": retention_months}
                        )
                        dropped_count = result.scalar()
                        results[table_name] = f"dropped {dropped_count} partitions"
                        logger.info(f"Cleaned up {dropped_count} old partitions for {table_name}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup partitions for {table_name}: {e}")
                        results[table_name] = f"error: {str(e)}"
                
                await session.commit()
                return results
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error cleaning up old partitions: {e}")
                raise
    
    async def ensure_current_partitions(self) -> dict:
        """Ensure current and next month partitions exist."""
        async with AsyncSessionLocal() as session:
            try:
                await session.execute(text("SELECT ensure_current_partitions()"))
                await session.commit()
                
                # Verify partitions were created
                result = await session.execute(text("""
                    SELECT tablename, 
                           split_part(tablename, '_', -2) as year,
                           split_part(tablename, '_', -1) as month
                    FROM pg_tables 
                    WHERE tablename ~ '^(agent_interactions|vector_embeddings|property_listings|api_usage)_\\d{4}_\\d{2}$'
                    AND schemaname = 'public'
                    ORDER BY tablename
                """))
                
                partitions = result.fetchall()
                partition_info = {}
                for partition in partitions:
                    table_base = '_'.join(partition.tablename.split('_')[:-2])
                    if table_base not in partition_info:
                        partition_info[table_base] = []
                    partition_info[table_base].append(f"{partition.year}_{partition.month}")
                
                logger.info(f"Current partitions: {partition_info}")
                return {"status": "success", "partitions": partition_info}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error ensuring current partitions: {e}")
                raise
    
    async def get_partition_stats(self) -> dict:
        """Get statistics about current partitions."""
        async with AsyncSessionLocal() as session:
            try:
                # Get partition counts and sizes
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        (SELECT count(*) FROM information_schema.tables WHERE table_name = t.tablename) as row_estimate
                    FROM pg_tables t
                    WHERE tablename ~ '^(agent_interactions|vector_embeddings|property_listings|api_usage)_\\d{4}_\\d{2}$'
                    AND schemaname = 'public'
                    ORDER BY tablename
                """))
                
                partitions = result.fetchall()
                stats = {
                    "total_partitions": len(partitions),
                    "partitions": []
                }
                
                for partition in partitions:
                    stats["partitions"].append({
                        "name": partition.tablename,
                        "size": partition.size,
                        "estimated_rows": partition.row_estimate
                    })
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting partition stats: {e}")
                raise
    
    def start_scheduler(self):
        """Start the partition management scheduler."""
        if self.is_running:
            logger.warning("Partition scheduler is already running")
            return
        
        # Schedule partition creation for the 1st of each month at 2 AM
        self.scheduler.add_job(
            self.create_future_partitions,
            CronTrigger(day=1, hour=2, minute=0),
            id='create_partitions',
            name='Create future partitions',
            kwargs={'months_ahead': 2},
            replace_existing=True
        )
        
        # Schedule partition cleanup weekly on Sunday at 3 AM
        self.scheduler.add_job(
            self.cleanup_old_partitions,
            CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='cleanup_partitions',
            name='Cleanup old partitions',
            kwargs={'retention_months': 6},
            replace_existing=True
        )
        
        # Schedule daily partition verification at 1 AM
        self.scheduler.add_job(
            self.ensure_current_partitions,
            CronTrigger(hour=1, minute=0),
            id='verify_partitions',
            name='Verify current partitions',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        logger.info("Partition management scheduler started")
    
    def stop_scheduler(self):
        """Stop the partition management scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("Partition management scheduler stopped")
    
    async def run_manual_maintenance(self) -> dict:
        """Run manual partition maintenance (for testing/troubleshooting)."""
        logger.info("Running manual partition maintenance")
        
        results = {}
        try:
            # Ensure current partitions
            current_result = await self.ensure_current_partitions()
            results['current_partitions'] = current_result
            
            # Create future partitions
            future_result = await self.create_future_partitions(months_ahead=2)
            results['future_partitions'] = future_result
            
            # Get stats
            stats_result = await self.get_partition_stats()
            results['stats'] = stats_result
            
            logger.info("Manual partition maintenance completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Manual partition maintenance failed: {e}")
            results['error'] = str(e)
            return results


# Global partition manager instance
partition_manager = PartitionManager()


async def start_partition_worker():
    """Start the partition management worker."""
    try:
        # Run initial setup
        logger.info("Starting partition worker - running initial maintenance")
        await partition_manager.run_manual_maintenance()
        
        # Start scheduler
        partition_manager.start_scheduler()
        logger.info("Partition worker started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start partition worker: {e}")
        raise


async def stop_partition_worker():
    """Stop the partition management worker."""
    try:
        partition_manager.stop_scheduler()
        logger.info("Partition worker stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop partition worker: {e}")
        raise


async def get_partition_health() -> dict:
    """Get partition health status for monitoring."""
    try:
        stats = await partition_manager.get_partition_stats()
        
        # Add health checks
        current_month = datetime.now().strftime('%Y_%m')
        next_month = (datetime.now().replace(day=1) + timedelta(days=32)).strftime('%Y_%m')
        
        health = {
            "status": "healthy",
            "stats": stats,
            "scheduler_running": partition_manager.is_running,
            "current_month_partitions": [],
            "next_month_partitions": [],
            "warnings": []
        }
        
        # Check if current and next month partitions exist
        for partition in stats["partitions"]:
            if current_month in partition["name"]:
                health["current_month_partitions"].append(partition["name"])
            elif next_month in partition["name"]:
                health["next_month_partitions"].append(partition["name"])
        
        # Add warnings if partitions are missing
        expected_tables = ['agent_interactions', 'vector_embeddings', 'property_listings', 'api_usage']
        current_missing = [t for t in expected_tables 
                          if not any(current_month in p["name"] and t in p["name"] 
                                   for p in stats["partitions"])]
        if current_missing:
            health["warnings"].append(f"Missing current month partitions: {current_missing}")
            health["status"] = "warning"
        
        next_missing = [t for t in expected_tables 
                       if not any(next_month in p["name"] and t in p["name"] 
                                for p in stats["partitions"])]
        if next_missing:
            health["warnings"].append(f"Missing next month partitions: {next_missing}")
            health["status"] = "warning"
        
        return health
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "scheduler_running": partition_manager.is_running
        }