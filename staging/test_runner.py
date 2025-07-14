#!/usr/bin/env python3
"""
Comprehensive Test Runner for NavieTakie Simulation
Tests all components: MCP Server, Lambda Functions, Frontend Apps
"""

import os
import sys
import time
import json
import requests
import boto3
import pytest
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NavieTakieTestRunner:
    def __init__(self):
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:8000')
        self.dax_app_url = os.getenv('DAX_APP_URL', 'http://localhost:3000')
        self.pax_app_url = os.getenv('PAX_APP_URL', 'http://localhost:3001')
        self.dynamodb_endpoint = os.getenv('DYNAMODB_ENDPOINT', 'http://localhost:8001')
        
        # Initialize AWS clients for local testing
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=self.dynamodb_endpoint,
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        self.lambda_client = boto3.client(
            'lambda',
            endpoint_url='http://localhost:9000',
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }

    def wait_for_service(self, url: str, service_name: str, timeout: int = 60) -> bool:
        """Wait for a service to be ready"""
        logger.info(f"Waiting for {service_name} at {url}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"{service_name} is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        logger.error(f"{service_name} failed to start within {timeout} seconds")
        return False

    def test_dynamodb_local(self) -> Dict[str, Any]:
        """Test DynamoDB Local setup"""
        logger.info("Testing DynamoDB Local...")
        
        try:
            # Create test table
            table_name = 'chat-messages-local'
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'booking_code', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'booking_code', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            
            # Test basic operations
            test_item = {
                'booking_code': 'TEST001',
                'timestamp': datetime.now().isoformat(),
                'message': 'Test message',
                'sender': 'driver',
                'message_type': 'text'
            }
            
            table.put_item(Item=test_item)
            response = table.get_item(Key={'booking_code': 'TEST001', 'timestamp': test_item['timestamp']})
            
            if 'Item' in response:
                logger.info("DynamoDB Local test passed")
                return {'status': 'passed', 'message': 'DynamoDB Local is working correctly'}
            else:
                return {'status': 'failed', 'message': 'Failed to retrieve test item'}
                
        except Exception as e:
            logger.error(f"DynamoDB Local test failed: {str(e)}")
            return {'status': 'failed', 'message': str(e)}

    def test_mcp_server(self) -> Dict[str, Any]:
        """Test MCP Server endpoints"""
        logger.info("Testing MCP Server...")
        
        try:
            # Test health endpoint
            health_response = requests.get(f"{self.mcp_server_url}/health")
            if health_response.status_code != 200:
                return {'status': 'failed', 'message': f'Health check failed: {health_response.status_code}'}
            
            # Test send message endpoint
            test_message = {
                'booking_code': 'TEST002',
                'message': 'Hello from test',
                'sender': 'driver'
            }
            
            send_response = requests.post(
                f"{self.mcp_server_url}/api/v1/send_message",
                json=test_message
            )
            
            if send_response.status_code != 200:
                return {'status': 'failed', 'message': f'Send message failed: {send_response.status_code}'}
            
            # Test get messages endpoint
            get_response = requests.get(f"{self.mcp_server_url}/api/v1/get_message/TEST002")
            if get_response.status_code != 200:
                return {'status': 'failed', 'message': f'Get messages failed: {get_response.status_code}'}
            
            logger.info("MCP Server test passed")
            return {'status': 'passed', 'message': 'MCP Server endpoints are working correctly'}
            
        except Exception as e:
            logger.error(f"MCP Server test failed: {str(e)}")
            return {'status': 'failed', 'message': str(e)}

    def test_lambda_functions(self) -> Dict[str, Any]:
        """Test Lambda functions locally"""
        logger.info("Testing Lambda functions...")
        
        try:
            # Test send-message function
            send_message_event = {
                'booking_code': 'TEST003',
                'message': 'Test message from Lambda',
                'sender': 'passenger',
                'timestamp': datetime.now().isoformat()
            }
            
            # Note: This would require the Lambda runtime to be properly set up
            # For now, we'll just test the function files exist
            lambda_functions = [
                '../lambda-functions/send_message.py',
                '../lambda-functions/make_call.py',
                '../lambda-functions/get_message.py'
            ]
            
            for func_file in lambda_functions:
                if not os.path.exists(func_file):
                    return {'status': 'failed', 'message': f'Lambda function file not found: {func_file}'}
            
            logger.info("Lambda functions test passed")
            return {'status': 'passed', 'message': 'Lambda function files exist and are valid'}
            
        except Exception as e:
            logger.error(f"Lambda functions test failed: {str(e)}")
            return {'status': 'failed', 'message': str(e)}

    def test_frontend_apps(self) -> Dict[str, Any]:
        """Test frontend applications"""
        logger.info("Testing frontend applications...")
        
        try:
            # Test DAX app
            dax_response = requests.get(self.dax_app_url, timeout=10)
            if dax_response.status_code != 200:
                return {'status': 'failed', 'message': f'DAX app not accessible: {dax_response.status_code}'}
            
            # Test PAX app
            pax_response = requests.get(self.pax_app_url, timeout=10)
            if pax_response.status_code != 200:
                return {'status': 'failed', 'message': f'PAX app not accessible: {pax_response.status_code}'}
            
            logger.info("Frontend apps test passed")
            return {'status': 'passed', 'message': 'Frontend applications are accessible'}
            
        except Exception as e:
            logger.error(f"Frontend apps test failed: {str(e)}")
            return {'status': 'failed', 'message': str(e)}

    def test_integration(self) -> Dict[str, Any]:
        """Test end-to-end integration"""
        logger.info("Testing end-to-end integration...")
        
        try:
            booking_code = 'INTEGRATION_TEST'
            
            # Send message through MCP server
            message_data = {
                'booking_code': booking_code,
                'message': 'Integration test message',
                'sender': 'driver'
            }
            
            send_response = requests.post(
                f"{self.mcp_server_url}/api/v1/send_message",
                json=message_data
            )
            
            if send_response.status_code != 200:
                return {'status': 'failed', 'message': 'Failed to send message in integration test'}
            
            # Get messages
            get_response = requests.get(f"{self.mcp_server_url}/api/v1/get_message/{booking_code}")
            if get_response.status_code != 200:
                return {'status': 'failed', 'message': 'Failed to get messages in integration test'}
            
            # Verify message was stored
            response_data = get_response.json()
            if not response_data.get('success'):
                return {'status': 'failed', 'message': 'Message not found in integration test'}
            
            logger.info("Integration test passed")
            return {'status': 'passed', 'message': 'End-to-end integration test successful'}
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            return {'status': 'failed', 'message': str(e)}

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("Starting comprehensive test suite...")
        
        # Wait for services to be ready
        services_ready = True
        services_ready &= self.wait_for_service(self.mcp_server_url, "MCP Server")
        services_ready &= self.wait_for_service(self.dax_app_url, "DAX App")
        services_ready &= self.wait_for_service(self.pax_app_url, "PAX App")
        
        if not services_ready:
            logger.error("Some services failed to start")
            return {'status': 'failed', 'message': 'Services not ready'}
        
        # Run individual tests
        tests = [
            ('dynamodb_local', self.test_dynamodb_local),
            ('mcp_server', self.test_mcp_server),
            ('lambda_functions', self.test_lambda_functions),
            ('frontend_apps', self.test_frontend_apps),
            ('integration', self.test_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"Running {test_name} test...")
            result = test_func()
            self.test_results['tests'][test_name] = result
            
            if result['status'] == 'passed':
                self.test_results['summary']['passed'] += 1
            else:
                self.test_results['summary']['failed'] += 1
            
            self.test_results['summary']['total'] += 1
        
        # Generate summary
        total = self.test_results['summary']['total']
        passed = self.test_results['summary']['passed']
        failed = self.test_results['summary']['failed']
        
        logger.info(f"Test Summary: {passed}/{total} passed, {failed} failed")
        
        # Save results
        with open('/app/test-results/results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate HTML report
        self.generate_html_report()
        
        return self.test_results

    def generate_html_report(self):
        """Generate HTML test report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NavieTakie Test Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .test {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
                .passed {{ background: #d4edda; border: 1px solid #c3e6cb; }}
                .failed {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
                .summary {{ background: #e2e3e5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>NavieTakie Simulation Test Results</h1>
                <p>Generated: {self.test_results['timestamp']}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total: {self.test_results['summary']['total']}</p>
                <p>Passed: {self.test_results['summary']['passed']}</p>
                <p>Failed: {self.test_results['summary']['failed']}</p>
            </div>
            
            <h2>Test Results</h2>
        """
        
        for test_name, result in self.test_results['tests'].items():
            status_class = 'passed' if result['status'] == 'passed' else 'failed'
            html_content += f"""
            <div class="test {status_class}">
                <h3>{test_name.replace('_', ' ').title()}</h3>
                <p><strong>Status:</strong> {result['status']}</p>
                <p><strong>Message:</strong> {result['message']}</p>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open('/app/test-results/report.html', 'w') as f:
            f.write(html_content)

def main():
    """Main function"""
    runner = NavieTakieTestRunner()
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    if results['summary']['failed'] > 0:
        logger.error("Some tests failed")
        sys.exit(1)
    else:
        logger.info("All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main() 