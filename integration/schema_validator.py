"""
Schema validation for Trading 212 API responses.

This module ensures that mock data exactly matches the expected API response format
to prevent hallucination issues in integration tests.
"""

from typing import Dict, Any, List, Union
from decimal import Decimal
import json


class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


class Trading212ApiSchemaValidator:
    """Validates Trading 212 API response schemas."""
    
    @staticmethod
    def validate_account_metadata(data: Dict[str, Any]) -> None:
        """Validate account metadata response schema."""
        if "error" in data:
            # Error response schema
            required_fields = ["error", "status_code"]
            for field in required_fields:
                if field not in data:
                    raise SchemaValidationError(f"Error response missing required field: {field}")
            return
        
        # Success response schema
        required_fields = ["currencyCode", "id", "type"]
        for field in required_fields:
            if field not in data:
                raise SchemaValidationError(f"Account metadata missing required field: {field}")
        
        # Validate field types
        if not isinstance(data["currencyCode"], str):
            raise SchemaValidationError(f"currencyCode should be str, got {type(data['currencyCode'])}")
        
        if not isinstance(data["id"], int):
            raise SchemaValidationError(f"id should be int, got {type(data['id'])}")
        
        if not isinstance(data["type"], str):
            raise SchemaValidationError(f"type should be str, got {type(data['type'])}")
        
        # Validate field values
        valid_currencies = ["USD", "GBP", "EUR"]
        if data["currencyCode"] not in valid_currencies:
            raise SchemaValidationError(f"currencyCode should be one of {valid_currencies}, got {data['currencyCode']}")
        
        valid_types = ["LIVE", "ISA", "DEMO"]
        if data["type"] not in valid_types:
            raise SchemaValidationError(f"type should be one of {valid_types}, got {data['type']}")
    
    @staticmethod
    def validate_account_cash(data: Dict[str, Any]) -> None:
        """Validate account cash response schema."""
        if "error" in data:
            # Error response schema
            required_fields = ["error", "status_code"]
            for field in required_fields:
                if field not in data:
                    raise SchemaValidationError(f"Error response missing required field: {field}")
            return
        
        # Success response schema
        required_fields = ["free", "total", "result", "interest"]
        for field in required_fields:
            if field not in data:
                raise SchemaValidationError(f"Account cash missing required field: {field}")
        
        # Validate field types (should be numbers)
        for field in required_fields:
            if not isinstance(data[field], (int, float)):
                raise SchemaValidationError(f"{field} should be numeric, got {type(data[field])}")
        
        # Validate logical constraints
        if data["free"] < 0:
            raise SchemaValidationError(f"free should be non-negative, got {data['free']}")
        
        if data["total"] < 0:
            raise SchemaValidationError(f"total should be non-negative, got {data['total']}")
    
    @staticmethod
    def validate_portfolio_positions(data: List[Dict[str, Any]]) -> None:
        """Validate portfolio positions response schema."""
        if not isinstance(data, list):
            raise SchemaValidationError(f"Portfolio positions should be list, got {type(data)}")
        
        for i, position in enumerate(data):
            if not isinstance(position, dict):
                raise SchemaValidationError(f"Position {i} should be dict, got {type(position)}")
            
            # Validate required fields
            required_fields = ["ticker", "quantity", "averagePrice", "currentPrice", "currencyCode"]
            for field in required_fields:
                if field not in position:
                    raise SchemaValidationError(f"Position {i} missing required field: {field}")
            
            # Validate field types
            if not isinstance(position["ticker"], str):
                raise SchemaValidationError(f"Position {i} ticker should be str, got {type(position['ticker'])}")
            
            if not isinstance(position["quantity"], (int, float)):
                raise SchemaValidationError(f"Position {i} quantity should be numeric, got {type(position['quantity'])}")
            
            if not isinstance(position["averagePrice"], (int, float)):
                raise SchemaValidationError(f"Position {i} averagePrice should be numeric, got {type(position['averagePrice'])}")
            
            if not isinstance(position["currentPrice"], (int, float)):
                raise SchemaValidationError(f"Position {i} currentPrice should be numeric, got {type(position['currentPrice'])}")
            
            if not isinstance(position["currencyCode"], str):
                raise SchemaValidationError(f"Position {i} currencyCode should be str, got {type(position['currencyCode'])}")
            
            # Validate logical constraints
            if position["quantity"] <= 0:
                raise SchemaValidationError(f"Position {i} quantity should be positive, got {position['quantity']}")
            
            if position["averagePrice"] <= 0:
                raise SchemaValidationError(f"Position {i} averagePrice should be positive, got {position['averagePrice']}")
            
            if position["currentPrice"] <= 0:
                raise SchemaValidationError(f"Position {i} currentPrice should be positive, got {position['currentPrice']}")
            
            # Validate currency code
            valid_currencies = ["USD", "GBP", "EUR"]
            if position["currencyCode"] not in valid_currencies:
                raise SchemaValidationError(f"Position {i} currencyCode should be one of {valid_currencies}, got {position['currencyCode']}")
            
            # Validate ticker format
            ticker = position["ticker"]
            if not ticker or len(ticker) < 1:
                raise SchemaValidationError(f"Position {i} ticker should not be empty")
            
            # Basic ticker format validation
            if not ticker.replace(".", "").replace("-", "").isalnum():
                raise SchemaValidationError(f"Position {i} ticker contains invalid characters: {ticker}")
    
    @staticmethod
    def validate_position_details(ticker: str, data: Dict[str, Any]) -> None:
        """Validate position details response schema."""
        if "error" in data:
            # Error response schema
            required_fields = ["error", "status_code"]
            for field in required_fields:
                if field not in data:
                    raise SchemaValidationError(f"Position details error response missing required field: {field}")
            return
        
        # Success response schema
        required_fields = ["ticker", "name", "type", "currencyCode"]
        for field in required_fields:
            if field not in data:
                # Allow minimal response with just ticker and name
                if field in ["ticker", "name"]:
                    continue
                raise SchemaValidationError(f"Position details missing required field: {field}")
        
        # Validate field types
        if "ticker" in data and not isinstance(data["ticker"], str):
            raise SchemaValidationError(f"Position details ticker should be str, got {type(data['ticker'])}")
        
        if "name" in data and not isinstance(data["name"], str):
            raise SchemaValidationError(f"Position details name should be str, got {type(data['name'])}")
        
        if "type" in data and not isinstance(data["type"], str):
            raise SchemaValidationError(f"Position details type should be str, got {type(data['type'])}")
        
        if "currencyCode" in data and not isinstance(data["currencyCode"], str):
            raise SchemaValidationError(f"Position details currencyCode should be str, got {type(data['currencyCode'])}")
        
        # Validate ticker consistency
        if "ticker" in data and data["ticker"] != ticker:
            raise SchemaValidationError(f"Position details ticker mismatch: expected {ticker}, got {data['ticker']}")
        
        # Validate currency code if present
        if "currencyCode" in data:
            valid_currencies = ["USD", "GBP", "EUR"]
            if data["currencyCode"] not in valid_currencies:
                raise SchemaValidationError(f"Position details currencyCode should be one of {valid_currencies}, got {data['currencyCode']}")
        
        # Validate type if present
        if "type" in data:
            valid_types = ["STOCK", "ETF", "FUND"]
            if data["type"] not in valid_types:
                raise SchemaValidationError(f"Position details type should be one of {valid_types}, got {data['type']}")
    
    @staticmethod
    def validate_complete_test_data(test_data) -> None:
        """Validate complete test data structure."""
        # Validate account metadata
        Trading212ApiSchemaValidator.validate_account_metadata(test_data.account_metadata)
        
        # Validate account cash
        Trading212ApiSchemaValidator.validate_account_cash(test_data.account_cash)
        
        # Validate portfolio positions
        Trading212ApiSchemaValidator.validate_portfolio_positions(test_data.portfolio_positions)
        
        # Validate position details
        for ticker, details in test_data.position_details.items():
            Trading212ApiSchemaValidator.validate_position_details(ticker, details)
        
        # Validate expected calculations structure
        required_calc_fields = [
            "total_positions", "total_market_value", "total_cost_basis", 
            "total_profit_loss", "account_currency", "free_funds"
        ]
        
        for field in required_calc_fields:
            if field not in test_data.expected_calculations:
                raise SchemaValidationError(f"Expected calculations missing required field: {field}")
        
        # Validate calculation types
        if not isinstance(test_data.expected_calculations["total_positions"], int):
            raise SchemaValidationError("total_positions should be int")
        
        decimal_fields = ["total_market_value", "total_cost_basis", "total_profit_loss", "free_funds"]
        for field in decimal_fields:
            if not isinstance(test_data.expected_calculations[field], Decimal):
                raise SchemaValidationError(f"{field} should be Decimal")
        
        if not isinstance(test_data.expected_calculations["account_currency"], str):
            raise SchemaValidationError("account_currency should be str")
        
        # Validate consistency between data and calculations
        actual_position_count = len(test_data.portfolio_positions)
        expected_position_count = test_data.expected_calculations["total_positions"]
        
        if actual_position_count != expected_position_count:
            raise SchemaValidationError(
                f"Position count mismatch: portfolio has {actual_position_count}, "
                f"expected calculations specify {expected_position_count}"
            )
        
        # Validate currency consistency
        metadata_currency = test_data.account_metadata.get("currencyCode")
        expected_currency = test_data.expected_calculations["account_currency"]
        
        if metadata_currency and metadata_currency != expected_currency:
            raise SchemaValidationError(
                f"Currency mismatch: metadata has {metadata_currency}, "
                f"expected calculations specify {expected_currency}"
            )
    
    @staticmethod
    def validate_fixture_file(filepath: str) -> None:
        """Validate a JSON fixture file against appropriate schema."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise SchemaValidationError(f"Failed to load fixture file {filepath}: {e}")
        
        filename = filepath.split('/')[-1].split('\\')[-1]  # Handle both Unix and Windows paths
        
        if filename == "account_metadata.json":
            for key, metadata in data.items():
                Trading212ApiSchemaValidator.validate_account_metadata(metadata)
        
        elif filename == "account_cash.json":
            for key, cash in data.items():
                Trading212ApiSchemaValidator.validate_account_cash(cash)
        
        elif filename == "portfolio_positions.json":
            for key, positions in data.items():
                Trading212ApiSchemaValidator.validate_portfolio_positions(positions)
        
        elif filename == "position_details.json":
            for ticker, details in data.items():
                Trading212ApiSchemaValidator.validate_position_details(ticker, details)
        
        else:
            raise SchemaValidationError(f"Unknown fixture file type: {filename}")


def validate_all_test_data():
    """Validate all test data classes against schemas."""
    from .isolated_test_data import SingleAccountTestData, MultiAccountTestData, EdgeCaseTestData
    
    validator = Trading212ApiSchemaValidator()
    
    # Validate single account test data
    try:
        usd_data = SingleAccountTestData.create_usd_account()
        validator.validate_complete_test_data(usd_data)
        print("[PASS] SingleAccountTestData.create_usd_account() passed validation")
    except SchemaValidationError as e:
        print(f"[FAIL] SingleAccountTestData.create_usd_account() failed validation: {e}")
    
    try:
        gbp_data = SingleAccountTestData.create_gbp_account()  
        validator.validate_complete_test_data(gbp_data)
        print("[PASS] SingleAccountTestData.create_gbp_account() passed validation")
    except SchemaValidationError as e:
        print(f"[FAIL] SingleAccountTestData.create_gbp_account() failed validation: {e}")
    
    # Validate multi account test data
    try:
        multi_data = MultiAccountTestData.create_isa_and_invest_accounts()
        for account_name, test_data in multi_data.items():
            validator.validate_complete_test_data(test_data)
        print("[PASS] MultiAccountTestData.create_isa_and_invest_accounts() passed validation")
    except SchemaValidationError as e:
        print(f"[FAIL] MultiAccountTestData.create_isa_and_invest_accounts() failed validation: {e}")
    
    # Validate edge case test data
    try:
        empty_data = EdgeCaseTestData.create_empty_portfolio()
        validator.validate_complete_test_data(empty_data)
        print("[PASS] EdgeCaseTestData.create_empty_portfolio() passed validation")
    except SchemaValidationError as e:
        print(f"[FAIL] EdgeCaseTestData.create_empty_portfolio() failed validation: {e}")
    
    try:
        fractional_data = EdgeCaseTestData.create_fractional_shares()
        validator.validate_complete_test_data(fractional_data)
        print("[PASS] EdgeCaseTestData.create_fractional_shares() passed validation")
    except SchemaValidationError as e:
        print(f"[FAIL] EdgeCaseTestData.create_fractional_shares() failed validation: {e}")


if __name__ == "__main__":
    validate_all_test_data()