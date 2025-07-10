import os
import io
import logging
import mimetypes
from typing import Optional, Tuple
import PyPDF2
import json
import csv
import xml.etree.ElementTree as ET
import yaml
import requests
from bs4 import BeautifulSoup
from config import Config

logger = logging.getLogger(__name__)

class FileProcessor:
    """File processing utilities for different file types"""
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get file information"""
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'mime_type': mime_type,
                'extension': os.path.splitext(file_path)[1].lower()[1:]
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    @staticmethod
    def is_supported_file(filename: str) -> bool:
        """Check if file type is supported"""
        extension = os.path.splitext(filename)[1].lower()[1:]
        return extension in Config.SUPPORTED_FILE_TYPES
    
    @staticmethod
    def is_supported_image(filename: str) -> bool:
        """Check if image type is supported"""
        extension = os.path.splitext(filename)[1].lower()[1:]
        return extension in Config.SUPPORTED_IMAGE_TYPES
    
    @staticmethod
    def extract_pdf_content(file_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            content = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text = page.extract_text()
                        if text.strip():
                            content.append(f"=== Page {page_num + 1} ===\n{text}\n")
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        content.append(f"=== Page {page_num + 1} ===\n[Error extracting content]\n")
                
                return "\n".join(content) if content else "No readable text found in PDF"
                
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            return f"Error reading PDF: {str(e)}"
    
    @staticmethod
    def extract_html_content(file_path: str) -> str:
        """Extract content from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Also include some structure information
            title = soup.title.string if soup.title else "No title"
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_desc = meta_tag.get("content", "")
            
            result = f"HTML Document Analysis\n"
            result += f"Title: {title}\n"
            if meta_desc:
                result += f"Description: {meta_desc}\n"
            result += f"\nContent:\n{text}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting HTML content: {e}")
            return f"Error reading HTML: {str(e)}"
    
    @staticmethod
    def extract_json_content(file_path: str) -> str:
        """Extract and format JSON content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Format JSON nicely
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Add analysis
            result = f"JSON Document Analysis\n"
            result += f"Structure: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                result += f"Keys: {list(data.keys())}\n"
            elif isinstance(data, list):
                result += f"Items: {len(data)}\n"
            
            result += f"\nFormatted Content:\n{formatted_json}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting JSON content: {e}")
            return f"Error reading JSON: {str(e)}"
    
    @staticmethod
    def extract_csv_content(file_path: str) -> str:
        """Extract and analyze CSV content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.reader(file, delimiter=delimiter)
                rows = list(reader)
            
            if not rows:
                return "Empty CSV file"
            
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            result = f"CSV Document Analysis\n"
            result += f"Columns: {len(headers)}\n"
            result += f"Rows: {len(data_rows)}\n"
            result += f"Headers: {', '.join(headers)}\n\n"
            
            # Show first few rows
            result += "Sample Data:\n"
            for i, row in enumerate(rows[:6]):  # Show header + 5 data rows
                result += f"Row {i}: {', '.join(row)}\n"
            
            if len(rows) > 6:
                result += f"... and {len(rows) - 6} more rows"
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting CSV content: {e}")
            return f"Error reading CSV: {str(e)}"
    
    @staticmethod
    def extract_xml_content(file_path: str) -> str:
        """Extract and analyze XML content"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            def xml_to_text(element, level=0):
                indent = "  " * level
                text = f"{indent}<{element.tag}"
                
                if element.attrib:
                    attrs = " ".join(f'{k}="{v}"' for k, v in element.attrib.items())
                    text += f" {attrs}"
                
                if element.text and element.text.strip():
                    text += f">{element.text.strip()}"
                    if list(element):
                        text += "\n"
                        for child in element:
                            text += xml_to_text(child, level + 1)
                        text += f"{indent}</{element.tag}>\n"
                    else:
                        text += f"</{element.tag}>\n"
                else:
                    if list(element):
                        text += ">\n"
                        for child in element:
                            text += xml_to_text(child, level + 1)
                        text += f"{indent}</{element.tag}>\n"
                    else:
                        text += " />\n"
                
                return text
            
            result = f"XML Document Analysis\n"
            result += f"Root Element: {root.tag}\n"
            result += f"Namespace: {root.tag.split('}')[0] + '}' if '}' in root.tag else 'None'}\n"
            result += f"Children: {len(list(root))}\n\n"
            result += "Structure:\n"
            result += xml_to_text(root)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting XML content: {e}")
            return f"Error reading XML: {str(e)}"
    
    @staticmethod
    def extract_yaml_content(file_path: str) -> str:
        """Extract and analyze YAML content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            # Format YAML nicely
            formatted_yaml = yaml.dump(data, default_flow_style=False, indent=2)
            
            result = f"YAML Document Analysis\n"
            result += f"Structure: {type(data).__name__}\n"
            
            if isinstance(data, dict):
                result += f"Keys: {list(data.keys())}\n"
            elif isinstance(data, list):
                result += f"Items: {len(data)}\n"
            
            result += f"\nFormatted Content:\n{formatted_yaml}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting YAML content: {e}")
            return f"Error reading YAML: {str(e)}"
    
    @staticmethod
    def extract_text_content(file_path: str) -> str:
        """Extract content from text files"""
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                    
                    # Add file analysis
                    lines = content.split('\n')
                    words = len(content.split())
                    chars = len(content)
                    
                    result = f"Text Document Analysis\n"
                    result += f"Lines: {len(lines)}\n"
                    result += f"Words: {words}\n"
                    result += f"Characters: {chars}\n\n"
                    result += f"Content:\n{content}"
                    
                    return result
                    
                except UnicodeDecodeError:
                    continue
            
            return "Unable to decode file with common encodings"
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return f"Error reading text file: {str(e)}"
    
    @staticmethod
    def process_file(file_path: str) -> Tuple[str, dict]:
        """Process file and extract content based on type"""
        try:
            file_info = FileProcessor.get_file_info(file_path)
            extension = file_info.get('extension', '').lower()
            
            if not FileProcessor.is_supported_file(file_info.get('filename', '')):
                return f"❌ Unsupported file type: {extension}", file_info
            
            # Check file size
            if file_info.get('size', 0) > Config.MAX_FILE_SIZE:
                return "❌ File too large. Maximum size is 16MB.", file_info
            
            # Extract content based on file type
            if extension == 'pdf':
                content = FileProcessor.extract_pdf_content(file_path)
            elif extension in ['html', 'htm']:
                content = FileProcessor.extract_html_content(file_path)
            elif extension == 'json':
                content = FileProcessor.extract_json_content(file_path)
            elif extension == 'csv':
                content = FileProcessor.extract_csv_content(file_path)
            elif extension == 'xml':
                content = FileProcessor.extract_xml_content(file_path)
            elif extension in ['yaml', 'yml']:
                content = FileProcessor.extract_yaml_content(file_path)
            else:
                # Default to text extraction for code files and other text files
                content = FileProcessor.extract_text_content(file_path)
            
            return content, file_info
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return f"❌ Error processing file: {str(e)}", {}
    
    @staticmethod
    def download_whatsapp_media(media_url: str, access_token: str) -> Optional[bytes]:
        """Download media file from WhatsApp"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'WhatsApp-Bot/1.0'
            }
            
            response = requests.get(media_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
