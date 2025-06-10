#!/usr/bin/env python3
"""
Test script for DoclingParser - runs locally without AWS Lambda
Mimics the lambda function behavior but allows local testing
"""

import requests
import time
import json
import logging
import traceback
import sys
import os
from pathlib import Path

# Add the docling directory to Python path so we can import the parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'docling'))

from docling_parser import DoclingParser, DocumentFormatError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DoclingParserTester:
    """Test class for DoclingParser with various document types and configurations"""
    
    def __init__(self):
        self.test_results = []
    
    def test_document_from_url(self, url: str, is_image_present: bool = False, 
                              is_md_response: bool = True, test_name: str = None):
        """
        Test parsing a document from a URL
        
        Args:
            url: URL to download document from
            is_image_present: Whether to enable OCR for image processing
            is_md_response: Whether to return markdown (True) or dict (False)
            test_name: Optional name for the test
        """
        test_name = test_name or f"URL_Test_{len(self.test_results) + 1}"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {test_name}")
        logger.info(f"URL: {url}")
        logger.info(f"Image processing: {is_image_present}")
        logger.info(f"Markdown response: {is_md_response}")
        logger.info(f"{'='*60}")
        
        result = {
            'test_name': test_name,
            'url': url,
            'is_image_present': is_image_present,
            'is_md_response': is_md_response,
            'success': False,
            'error': None,
            'processing_time': 0,
            'document_type': None,
            'result_length': 0,
            'result_preview': None
        }
        
        try:
            # Download document
            logger.info("Downloading document...")
            download_start = time.time()
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            file_bytes = response.content
            download_time = time.time() - download_start
            
            logger.info(f"Downloaded {len(file_bytes)} bytes in {download_time:.2f} seconds")
            
            # Initialize parser
            logger.info("Initializing DoclingParser...")
            parser = DoclingParser(
                bytes_content=file_bytes,
                is_image_present=is_image_present,
                is_md_response=is_md_response
            )
            
            result['document_type'] = parser.doc_type
            logger.info(f"Detected document type: {parser.doc_type}")
            
            # Parse document
            logger.info("Starting document parsing...")
            parse_start = time.time()
            parsed_result = parser.parse_documents()
            parse_time = time.time() - parse_start
            
            result['processing_time'] = parse_time
            result['success'] = True
            
            # Handle result based on type
            if isinstance(parsed_result, str):
                result['result_length'] = len(parsed_result)
                result['result_preview'] = parsed_result[:500] + "..." if len(parsed_result) > 500 else parsed_result
            elif isinstance(parsed_result, dict):
                result['result_length'] = len(str(parsed_result))
                result['result_preview'] = str(parsed_result)[:500] + "..." if len(str(parsed_result)) > 500 else str(parsed_result)
            
            logger.info(f"✅ Parsing completed successfully in {parse_time:.2f} seconds")
            logger.info(f"Result length: {result['result_length']} characters")
            
            # Save full result to file for inspection
            output_file = f"test_output_{test_name.replace(' ', '_')}.{'md' if is_md_response else 'json'}"
            with open(output_file, 'w', encoding='utf-8') as f:
                if isinstance(parsed_result, dict):
                    json.dump(parsed_result, f, indent=2, ensure_ascii=False)
                else:
                    f.write(parsed_result)
            logger.info(f"Full result saved to: {output_file}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Download error: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            
        except DocumentFormatError as e:
            error_msg = f"Document format error: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
            
        except Exception as e:
            error_msg = f"Parsing error: {str(e)}"
            stack_trace = traceback.format_exc()
            logger.error(f"{error_msg}\nStack trace: {stack_trace}")
            result['error'] = error_msg
        
        self.test_results.append(result)
        return result
    
    def run_comprehensive_tests(self):
        """Run a comprehensive test suite with various document types and configurations"""
        
        # Test URLs - you can replace these with your own test documents
        test_cases = [
            {
                'url': 'https://documents.pelles.ai/level-app-staging/1949fed8-2d02-4a2a-a696-43ca1cf46d08/bc688860-8f5c-40ef-828f-f0312174d6ae/5?se=2025-06-11T09%3A21%3A09Z&sp=r&sv=2023-11-03&sr=b&sig=1KSA6U8t7rpIs4MeHr9CK0GpQpcJO6EOXWRtgKdl8so%3D',
                'is_image_present': False,
                'is_md_response': True,
                'test_name': 'PDF_No_OCR_Markdown'
            },
            {
                'url': 'https://documents.pelles.ai/level-app-staging/1949fed8-2d02-4a2a-a696-43ca1cf46d08/bc688860-8f5c-40ef-828f-f0312174d6ae/5?se=2025-06-11T09%3A21%3A09Z&sp=r&sv=2023-11-03&sr=b&sig=1KSA6U8t7rpIs4MeHr9CK0GpQpcJO6EOXWRtgKdl8so%3D',
                'is_image_present': True,
                'is_md_response': True,
                'test_name': 'PDF_With_OCR_Markdown'
            },
            {
                'url': 'https://documents.pelles.ai/level-app-staging/1949fed8-2d02-4a2a-a696-43ca1cf46d08/bc688860-8f5c-40ef-828f-f0312174d6ae/5?se=2025-06-11T09%3A21%3A09Z&sp=r&sv=2023-11-03&sr=b&sig=1KSA6U8t7rpIs4MeHr9CK0GpQpcJO6EOXWRtgKdl8so%3D',
                'is_image_present': False,
                'is_md_response': False,
                'test_name': 'PDF_No_OCR_Dict'
            },
            {
                'url': 'https://documents.pelles.ai/level-app-staging/1949fed8-2d02-4a2a-a696-43ca1cf46d08/bc688860-8f5c-40ef-828f-f0312174d6ae/5?se=2025-06-11T09%3A21%3A09Z&sp=r&sv=2023-11-03&sr=b&sig=1KSA6U8t7rpIs4MeHr9CK0GpQpcJO6EOXWRtgKdl8so%3D',
                'is_image_present': True,
                'is_md_response': False,
                'test_name': 'PDF_With_OCR_Dict'
            }
        ]
        
        logger.info("🚀 Starting comprehensive DoclingParser tests...")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n📝 Running test {i}/{len(test_cases)}: {test_case['test_name']}")
            self.test_document_from_url(**test_case)
            
            # Small delay between tests
            time.sleep(1)
    
    def print_summary(self):
        """Print a summary of all test results"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 TEST SUMMARY")
        logger.info(f"{'='*80}")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        
        logger.info(f"\n{'='*50}")
        logger.info("📋 DETAILED RESULTS")
        logger.info(f"{'='*50}")
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"\n\n{status} {result['test_name']}")
            logger.info(f"  Document type: {result.get('document_type', 'Unknown')}")
            logger.info(f"  Processing time: {result['processing_time']:.2f}s")
            
            if result['success']:
                logger.info(f"  Result length: {result['result_length']} characters")
            else:
                logger.info(f"  Error: {result['error']}")


def main():
    """Main function to run the tests"""
    
    # Test with the URL from the existing test_lambda.py
    tester = DoclingParserTester()
    
    # You can test individual documents
    logger.info("🔍 Testing individual document...")
    
    # Example from your test_lambda.py
    sample_url = "https://documents.pelles.ai/level-app-staging/1949fed8-2d02-4a2a-a696-43ca1cf46d08/bc688860-8f5c-40ef-828f-f0312174d6ae/5?se=2025-06-11T09%3A21%3A09Z&sp=r&sv=2023-11-03&sr=b&sig=1KSA6U8t7rpIs4MeHr9CK0GpQpcJO6EOXWRtgKdl8so%3D"
    
    # Test with different configurations
    tester.test_document_from_url(
        url=sample_url,
        is_image_present=True,
        is_md_response=True,
        test_name="Presigned_URL_Test"
    )
    
    # Run comprehensive tests with public documents
    logger.info("\n🧪 Running comprehensive test suite...")
    tester.run_comprehensive_tests()
    
    # Print summary
    tester.print_summary()
    
    # Example of testing a local file (uncomment if you have a local file)
    # tester.test_local_file("path/to/your/document.pdf", test_name="Local_PDF_Test")


if __name__ == "__main__":
    main()
