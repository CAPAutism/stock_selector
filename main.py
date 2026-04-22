"""
Main pipeline orchestration for A股选股系统

This module orchestrates the stock selection pipeline by running agents in sequence:
DataCollectorAgent -> SectorAnalyzerAgent -> ChainAnalyzerAgent -> StockScreenerAgent -> ObsidianReportAgent

Usage:
    python main.py [--date YYYYMMDD]
"""
import argparse
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import agents
from stock_selector.agents.data_collector import DataCollectorAgent
from stock_selector.agents.sector_analyzer import SectorAnalyzerAgent
from stock_selector.agents.chain_analyzer import ChainAnalyzerAgent
from stock_selector.agents.stock_screener import StockScreenerAgent
from stock_selector.agents.obsidian_report import ObsidianReportAgent

# Import settings
from stock_selector.config.settings import Settings

# Import queue utilities
from stock_selector.queue.memory_queue import clear_all_queues


def run_pipeline(trade_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the complete stock selection pipeline.

    Args:
        trade_date: Optional trade date in YYYYMMDD format.
                   If not provided, uses current date.

    Returns:
        Dict containing:
        - success: bool - Whether pipeline completed successfully
        - error: Optional[str] - Error message if failed
        - summary: Dict with agent results and timing info
    """
    start_time = time.time()
    settings = Settings()

    # Default to current date if not provided
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y%m%d")

    logger.info(f"Starting pipeline for trade date: {trade_date}")

    # Clear all queues before starting
    logger.info("Clearing all queues...")
    clear_all_queues()

    # Initialize result tracking
    result = {
        'success': False,
        'trade_date': trade_date,
        'summary': {
            'agents_completed': 0,
            'agent_results': []
        },
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'duration_seconds': None
    }

    # Track current agent name for error reporting
    current_agent = None

    # Collect all data for final report
    report_data = {
        'trade_date': trade_date,
        'top_stocks': [],
        'sectors': [],
        'supply_chains': [],
        'industry_distribution': {},
        'data_sources': {
            'fund_flow': {'source': 'AKShare', 'update_time': trade_date},
            'internet_heat': {'source': '待实现', 'update_time': trade_date},
            'stock_price': {'source': 'AKShare', 'update_time': trade_date}
        }
    }

    try:
        # Step 1: DataCollectorAgent (no input queue, produces raw data)
        current_agent = "DataCollectorAgent"
        logger.info(f"Running {current_agent}...")
        collector = DataCollectorAgent()
        collector_result = collector.process()
        sectors_fund_flow = collector_result.get('sectors_fund_flow', [])
        report_data['sectors'] = sectors_fund_flow
        logger.info(f"{current_agent} completed: {len(sectors_fund_flow)} sectors collected")
        result['summary']['agent_results'].append({
            'agent': current_agent,
            'success': True,
            'data_keys': list(collector_result.keys())
        })
        result['summary']['agents_completed'] += 1

        # Step 2: SectorAnalyzerAgent (consumes raw_market_data, produces sector_analysis)
        current_agent = "SectorAnalyzerAgent"
        logger.info(f"Running {current_agent}...")
        sector_analyzer = SectorAnalyzerAgent()
        sector_result = sector_analyzer.process()
        top_sectors = sector_result.get('top_sectors', [])
        report_data['sectors'] = top_sectors
        logger.info(f"{current_agent} completed: {len(top_sectors)} top sectors")
        result['summary']['agent_results'].append({
            'agent': current_agent,
            'success': True,
            'top_sectors_count': len(top_sectors)
        })
        result['summary']['agents_completed'] += 1

        # Step 3: ChainAnalyzerAgent (consumes sector_analysis, produces chain_analysis)
        current_agent = "ChainAnalyzerAgent"
        logger.info(f"Running {current_agent}...")
        chain_analyzer = ChainAnalyzerAgent()
        chain_result = chain_analyzer.process()
        chain_structures = chain_result.get('chain_structures', [])
        report_data['supply_chains'] = chain_structures
        logger.info(f"{current_agent} completed: {len(chain_structures)} chain structures")
        result['summary']['agent_results'].append({
            'agent': current_agent,
            'success': True,
            'chain_structures_count': len(chain_structures)
        })
        result['summary']['agents_completed'] += 1

        # Step 4: StockScreenerAgent (consumes chain_analysis, produces final_stocks)
        current_agent = "StockScreenerAgent"
        logger.info(f"Running {current_agent}...")
        screener = StockScreenerAgent()
        screener_result = screener.process()
        top_stocks = screener_result.get('top_stocks', [])
        report_data['top_stocks'] = top_stocks
        logger.info(f"{current_agent} completed: {len(top_stocks)} top stocks")
        result['summary']['agent_results'].append({
            'agent': current_agent,
            'success': True,
            'top_stocks_count': len(top_stocks)
        })
        result['summary']['agents_completed'] += 1

        # Step 5: ObsidianReportAgent (consumes final_stocks, produces file)
        current_agent = "ObsidianReportAgent"
        logger.info(f"Running {current_agent}...")
        report_agent = ObsidianReportAgent()
        report_result = report_agent.process(report_data)
        logger.info(f"{current_agent} completed: report_path={report_result.get('report_path')}")
        result['summary']['agent_results'].append({
            'agent': current_agent,
            'success': report_result.get('success', False),
            'report_path': report_result.get('report_path')
        })
        result['summary']['agents_completed'] += 1

        # Pipeline completed successfully
        result['success'] = True
        logger.info("Pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        result['success'] = False
        result['error'] = f"{current_agent}: {str(e)}"

    finally:
        end_time = time.time()
        result['end_time'] = datetime.now().isoformat()
        result['duration_seconds'] = round(end_time - start_time, 2)

    return result


def main() -> int:
    """
    Main entry point for the pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description='A股选股系统 - Main Pipeline'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Trade date in YYYYMMDD format (default: today)'
    )

    args = parser.parse_args()

    try:
        result = run_pipeline(trade_date=args.date)

        if result['success']:
            print("\nPipeline completed successfully!")
            print(f"Trade date: {result['trade_date']}")
            print(f"Duration: {result['duration_seconds']}s")
            print(f"Agents completed: {result['summary']['agents_completed']}")
            return 0
        else:
            print(f"\nPipeline failed: {result.get('error', 'Unknown error')}")
            print(f"Agents completed before failure: {result['summary']['agents_completed']}")
            return 1

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
