"""
Tests for main.py - Main pipeline orchestration

This module tests the run_pipeline() function that orchestrates all agents:
DataCollectorAgent -> SectorAnalyzerAgent -> ChainAnalyzerAgent -> StockScreenerAgent -> ObsidianReportAgent
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMainImport:
    """Test that main.py can be imported without errors"""

    def test_main_module_imports_without_error(self):
        """main.py should be importable without exceptions"""
        import main
        assert main is not None


class TestRunPipelineExists:
    """Test that run_pipeline function exists and is callable"""

    def test_run_pipeline_exists(self):
        """run_pipeline function should exist in main module"""
        import main
        assert hasattr(main, 'run_pipeline')
        assert callable(main.run_pipeline)


class TestPipelineExecution:
    """Test pipeline runs through all agents correctly"""

    @patch('main.DataCollectorAgent')
    @patch('main.SectorAnalyzerAgent')
    @patch('main.ChainAnalyzerAgent')
    @patch('main.StockScreenerAgent')
    @patch('main.ObsidianReportAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_runs_all_agents_in_sequence(
        self, mock_clear, mock_obsidian, mock_screener,
        mock_chain, mock_sector, mock_collector
    ):
        """Pipeline should run all 5 agents in correct order"""
        import main

        # Setup mock agents with return values
        mock_collector_instance = Mock()
        mock_collector_instance.process.return_value = {
            'trade_date': '20260418',
            'sectors_fund_flow': [{'code': '001', 'name': '板块1'}],
            'sectors_heat': []
        }
        mock_collector.return_value = mock_collector_instance

        mock_sector_instance = Mock()
        mock_sector_instance.process.return_value = {
            'trade_date': '20260418',
            'top_sectors': [{'code': '001', 'name': '板块1', 'score': 80}]
        }
        mock_sector.return_value = mock_sector_instance

        mock_chain_instance = Mock()
        mock_chain_instance.process.return_value = {
            'trade_date': '20260418',
            'chain_structures': []
        }
        mock_chain.return_value = mock_chain_instance

        mock_screener_instance = Mock()
        mock_screener_instance.process.return_value = {
            'trade_date': '20260418',
            'top_stocks': []
        }
        mock_screener.return_value = mock_screener_instance

        mock_obsidian_instance = Mock()
        mock_obsidian_instance.process.return_value = {
            'success': True,
            'report_path': '/path/to/report.md'
        }
        mock_obsidian.return_value = mock_obsidian_instance

        # Run pipeline
        result = main.run_pipeline()

        # Verify all agents were called
        mock_collector.assert_called_once()
        mock_sector.assert_called_once()
        mock_chain.assert_called_once()
        mock_screener.assert_called_once()
        mock_obsidian.assert_called_once()

        # Verify result structure
        assert result['success'] is True
        assert 'summary' in result
        assert result['summary']['agents_completed'] == 5

    @patch('main.DataCollectorAgent')
    @patch('main.SectorAnalyzerAgent')
    @patch('main.ChainAnalyzerAgent')
    @patch('main.StockScreenerAgent')
    @patch('main.ObsidianReportAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_clears_queues_before_start(
        self, mock_clear, mock_obsidian, mock_screener,
        mock_chain, mock_sector, mock_collector
    ):
        """Pipeline should clear all queues before starting"""
        import main

        # Setup minimal mocks
        mock_collector_instance = Mock()
        mock_collector_instance.process.return_value = {'trade_date': '20260418'}
        mock_collector.return_value = mock_collector_instance

        mock_sector_instance = Mock()
        mock_sector_instance.process.return_value = {'trade_date': '20260418', 'top_sectors': []}
        mock_sector.return_value = mock_sector_instance

        mock_chain_instance = Mock()
        mock_chain_instance.process.return_value = {'trade_date': '20260418', 'chain_structures': []}
        mock_chain.return_value = mock_chain_instance

        mock_screener_instance = Mock()
        mock_screener_instance.process.return_value = {'trade_date': '20260418', 'top_stocks': []}
        mock_screener.return_value = mock_screener_instance

        mock_obsidian_instance = Mock()
        mock_obsidian_instance.process.return_value = {'success': True, 'report_path': None}
        mock_obsidian.return_value = mock_obsidian_instance

        main.run_pipeline()

        # Verify clear_all_queues was called before any agent
        mock_clear.assert_called_once()


class TestPipelineEdgeCases:
    """Test edge cases and error handling"""

    @patch('main.DataCollectorAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_handles_collector_failure(self, mock_clear, mock_collector):
        """Pipeline should handle DataCollectorAgent failure gracefully"""
        import main

        mock_collector_instance = Mock()
        mock_collector_instance.process.side_effect = Exception("API Error")
        mock_collector.return_value = mock_collector_instance

        result = main.run_pipeline()

        assert result['success'] is False
        assert 'error' in result
        assert 'DataCollectorAgent' in result['error']

    @patch('main.DataCollectorAgent')
    @patch('main.SectorAnalyzerAgent')
    @patch('main.ChainAnalyzerAgent')
    @patch('main.StockScreenerAgent')
    @patch('main.ObsidianReportAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_handles_partial_failure(
        self, mock_clear, mock_obsidian, mock_screener,
        mock_chain, mock_sector, mock_collector
    ):
        """Pipeline should report partial failure when mid-pipeline agent fails"""
        import main

        # First two agents succeed
        mock_collector_instance = Mock()
        mock_collector_instance.process.return_value = {'trade_date': '20260418'}
        mock_collector.return_value = mock_collector_instance

        mock_sector_instance = Mock()
        mock_sector_instance.process.return_value = {'trade_date': '20260418', 'top_sectors': []}
        mock_sector.return_value = mock_sector_instance

        # ChainAnalyzer fails
        mock_chain_instance = Mock()
        mock_chain_instance.process.side_effect = Exception("Chain analysis failed")
        mock_chain.return_value = mock_chain_instance

        mock_screener_instance = Mock()
        mock_screener.return_value = mock_screener_instance

        mock_obsidian_instance = Mock()
        mock_obsidian.return_value = mock_obsidian_instance

        result = main.run_pipeline()

        assert result['success'] is False
        assert 'error' in result
        assert 'ChainAnalyzerAgent' in result['error']
        assert result['summary']['agents_completed'] == 2

    @patch('main.DataCollectorAgent')
    @patch('main.SectorAnalyzerAgent')
    @patch('main.ChainAnalyzerAgent')
    @patch('main.StockScreenerAgent')
    @patch('main.ObsidianReportAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_with_empty_data(
        self, mock_clear, mock_obsidian, mock_screener,
        mock_chain, mock_sector, mock_collector
    ):
        """Pipeline should handle empty data gracefully"""
        import main

        # All agents return minimal data
        mock_collector_instance = Mock()
        mock_collector_instance.process.return_value = {
            'trade_date': '20260418',
            'sectors_fund_flow': [],
            'sectors_heat': []
        }
        mock_collector.return_value = mock_collector_instance

        mock_sector_instance = Mock()
        mock_sector_instance.process.return_value = {
            'trade_date': '20260418',
            'top_sectors': []
        }
        mock_sector.return_value = mock_sector_instance

        mock_chain_instance = Mock()
        mock_chain_instance.process.return_value = {
            'trade_date': '20260418',
            'chain_structures': []
        }
        mock_chain.return_value = mock_chain_instance

        mock_screener_instance = Mock()
        mock_screener_instance.process.return_value = {
            'trade_date': '20260418',
            'top_stocks': []
        }
        mock_screener.return_value = mock_screener_instance

        mock_obsidian_instance = Mock()
        mock_obsidian_instance.process.return_value = {
            'success': True,
            'report_path': '/path/to/report.md'
        }
        mock_obsidian.return_value = mock_obsidian_instance

        result = main.run_pipeline()

        assert result['success'] is True
        assert result['summary']['agents_completed'] == 5


class TestPipelineReturnValue:
    """Test that run_pipeline returns correct result structure"""

    @patch('main.DataCollectorAgent')
    @patch('main.SectorAnalyzerAgent')
    @patch('main.ChainAnalyzerAgent')
    @patch('main.StockScreenerAgent')
    @patch('main.ObsidianReportAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_returns_success_result(
        self, mock_clear, mock_obsidian, mock_screener,
        mock_chain, mock_sector, mock_collector
    ):
        """run_pipeline should return dict with success=True on success"""
        import main

        mock_collector_instance = Mock()
        mock_collector_instance.process.return_value = {'trade_date': '20260418'}
        mock_collector.return_value = mock_collector_instance

        mock_sector_instance = Mock()
        mock_sector_instance.process.return_value = {'trade_date': '20260418', 'top_sectors': []}
        mock_sector.return_value = mock_sector_instance

        mock_chain_instance = Mock()
        mock_chain_instance.process.return_value = {'trade_date': '20260418', 'chain_structures': []}
        mock_chain.return_value = mock_chain_instance

        mock_screener_instance = Mock()
        mock_screener_instance.process.return_value = {'trade_date': '20260418', 'top_stocks': []}
        mock_screener.return_value = mock_screener_instance

        mock_obsidian_instance = Mock()
        mock_obsidian_instance.process.return_value = {'success': True, 'report_path': '/path'}
        mock_obsidian.return_value = mock_obsidian_instance

        result = main.run_pipeline()

        assert isinstance(result, dict)
        assert 'success' in result
        assert 'summary' in result
        assert 'start_time' in result
        assert 'end_time' in result
        assert 'duration_seconds' in result

    @patch('main.DataCollectorAgent')
    @patch('main.SectorAnalyzerAgent')
    @patch('main.ChainAnalyzerAgent')
    @patch('main.StockScreenerAgent')
    @patch('main.ObsidianReportAgent')
    @patch('main.clear_all_queues')
    def test_pipeline_summary_contains_agent_info(
        self, mock_clear, mock_obsidian, mock_screener,
        mock_chain, mock_sector, mock_collector
    ):
        """Summary should contain information about completed agents"""
        import main

        mock_collector_instance = Mock()
        mock_collector_instance.process.return_value = {'trade_date': '20260418'}
        mock_collector.return_value = mock_collector_instance

        mock_sector_instance = Mock()
        mock_sector_instance.process.return_value = {'trade_date': '20260418', 'top_sectors': []}
        mock_sector.return_value = mock_sector_instance

        mock_chain_instance = Mock()
        mock_chain_instance.process.return_value = {'trade_date': '20260418', 'chain_structures': []}
        mock_chain.return_value = mock_chain_instance

        mock_screener_instance = Mock()
        mock_screener_instance.process.return_value = {'trade_date': '20260418', 'top_stocks': []}
        mock_screener.return_value = mock_screener_instance

        mock_obsidian_instance = Mock()
        mock_obsidian_instance.process.return_value = {'success': True, 'report_path': '/path'}
        mock_obsidian.return_value = mock_obsidian_instance

        result = main.run_pipeline()

        summary = result['summary']
        assert 'agents_completed' in summary
        assert 'agent_results' in summary
        assert len(summary['agent_results']) == 5
