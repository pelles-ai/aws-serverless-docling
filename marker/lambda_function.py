import json
from pathlib import Path
import os
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
import marker.converters
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3', region_name='us-west-2')

# Setting up environment variables and directories
os.makedirs("/tmp/static/fonts/", exist_ok=True)
marker.util.settings.FONT_PATH = "/tmp/static/fonts/GoNotoCurrent-Regular.ttf"
os.environ["HOME"] = "/tmp"
os.environ["XDG_CACHE_HOME"] = "/tmp"
os.environ["SURYA_CACHE_DIR"] = "/tmp"
os.environ["TORCH_HOME"] = "/tmp/torch"
os.environ["TRANSFORMERS_CACHE"] = "/tmp"
marker.util.settings.FONT_PATH = "/tmp/static/fonts"
os.environ["WEASYPRINT_DLL_DIRECTORIES"] = "/tmp"
os.makedirs("/tmp/static/fonts", exist_ok=True)


def extract_document_to_markdown(input_doc_path: Path) -> str:
    """Convert document to markdown using Marker converter"""
    try:
        config = {
            "output_format": "markdown",
            "output_dir": str(input_doc_path.parent),
            "workers": 1

        }
        config_parser = ConfigParser(config)
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service()
        )

        rendered_content = converter(str(input_doc_path))
        return rendered_content.markdown

    except Exception as e:
        logger.error(str(e))
        raise Exception(f"Error converting document: {str(e)}")


def get_file_from_s3(bucket_name: str, object_key: str) -> Path:
    logger.info(f"Bucket:{bucket_name}, Key:{object_key}")
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception(f"Error fetching file from S3: {response['ResponseMetadata']['HTTPStatusCode']}")
    file_content = response['Body'].read()
    file_name = object_key.split("/")[-1]
    temp_dir = Path("/tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    filename = temp_dir / file_name
    with open(filename, "wb") as file:
        file.write(file_content)
    return filename


def lambda_handler(event, context):
    try:
        logger.info("Received event: " + json.dumps(event))
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_key = event['Records'][0]['s3']['object']['key']

        allowed_formats = ['pdf', 'png', 'jpeg', 'pptx', 'docx', 'xlsx', 'html', 'epub']
        file_extension = object_key.split('.')[-1].lower()
        if file_extension not in allowed_formats:
            raise Exception(f"Unsupported file format: {file_extension}. Supported formats are: {allowed_formats}")

        # Parse the input path and construct output path
        path_parts = object_key.split('/')
        if 'input' in path_parts:
            input_index = path_parts.index('input')
            path_parts[input_index] = 'output'
        output_key = '/'.join(path_parts).replace(f'{file_extension}', 'md')

        input_doc_path = get_file_from_s3(bucket_name, object_key)
        markdown_text = extract_document_to_markdown(input_doc_path)

        # Upload the markdown file back to S3
        output_doc_path = input_doc_path.with_suffix('.md')
        with open(output_doc_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        logger.info(f"uploading file at location {output_doc_path}")
        s3_client.upload_file(str(output_doc_path), bucket_name, output_key)

        # Cleanup temporary files
        output_doc_path.unlink(missing_ok=True)
        input_doc_path.unlink(missing_ok=True)

        return {'statusCode': 200, 'body': {"message": "markdown successfully uploaded!!", "filePath":f"{str(output_doc_path)}/{output_key}"}}
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {'statusCode': 400, 'body': {'error': str(e)}}