import json
import requests
import traceback
from docling_parser import DoclingParser, logger


def lambda_handler(event: dict, context):
    """ The lambda function that parses the document and returns the result """
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        # Validate presigned URL
        presigned_url = event.get('presignedUrl', '')
        if not presigned_url:
            logger.error("Missing presigned URL in event")
            return {
                'statusCode': 400,
                'body': 'Missing presigned URL parameter'
            }

        # Log the URL we're about to request (redacted for security)
        logger.info(f"Fetching content from presigned URL (first 20 chars): {presigned_url[:20]}...")

        # Get file content
        response = requests.get(presigned_url)
        response.raise_for_status()
        file_bytes = response.content

        # Log success and content length
        logger.info(f"Successfully downloaded content, size: {len(file_bytes)} bytes")

        # Process parameters
        is_image_present = event.get('isImagePresent', False)
        is_md_response = event.get('isMdResponse', True)

        # Initialize parser with bytes content directly
        parser = DoclingParser(
            bytes_content=file_bytes,
            is_image_present=is_image_present,
            is_md_response=is_md_response
        )

        logger.info(f"Detected document type: {parser.doc_type}")

        result = parser.parse_documents()
        return {
            'statusCode': 200,
            'body': result
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return {
            'statusCode': 502,
            'body': f'Error fetching document: {str(e)}'
        }
    except Exception as e:
        # Get full stack trace for debugging
        stack_trace = traceback.format_exc()
        logger.error(f"Error processing document: {str(e)}\nStack trace: {stack_trace}")
        return {
            'statusCode': 500,
            'body': f'Processing error: {str(e)}'
        }
