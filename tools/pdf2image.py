import logging
from collections.abc import Generator
from typing import Any
import io
import base64
from pathlib import Path
import os
import requests

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.file.file import File
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ToolParameters(BaseModel):
    files: list[File]
    image_format: str = "png"  # png, jpeg, jpg
    dpi: int = 150  # Resolution: 72, 150, 300, 600
    quality: int = 95  # JPEG quality (1-100)
    split_pages: bool = True  # If True, each page as separate image
    alpha_channel: bool = False  # Include transparency for PNG


class Pdf2imageTool(Tool):
    """
    A tool for converting PDF pages to images using PyMuPDF
    """

    def _get_file_content(self, file: File) -> bytes:
        """
        Get file content either from blob or by fetching from URL
        """
        # First, try to get the blob directly
        if hasattr(file, 'blob') and file.blob:
            logger.info(f"Using direct blob for {file.filename}")
            return file.blob

        # If no blob, try to fetch from URL
        if hasattr(file, 'remote_url') and file.remote_url:
            logger.info(f"Fetching file from URL for {file.filename}")

            # Check if it's a relative URL that needs a base URL
            url = file.remote_url
            if url.startswith('/'):
                # Try to get base URL from environment or use default
                base_url = os.getenv('FILES_URL', '')
                if not base_url:
                    # Try common Dify URLs
                    possible_bases = [
                        os.getenv('DIFY_API_URL', ''),
                        'http://localhost:5001',
                        'https://api.dify.ai'
                    ]
                    for base in possible_bases:
                        if base:
                            base_url = base.rstrip('/')
                            break

                if base_url:
                    url = base_url + url
                    logger.info(f"Constructed full URL: {url}")
                else:
                    raise ValueError(f"Cannot construct full URL from relative path: {file.remote_url}")

            # Fetch the file
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                logger.error(f"Failed to fetch file from {url}: {e}")
                raise ValueError(f"Failed to fetch file from URL: {e}")

        # If file has a _blob attribute (alternative naming)
        if hasattr(file, '_blob') and file._blob:
            return file._blob

        # Try to read file data if it's a file-like object
        if hasattr(file, 'read'):
            content = file.read()
            if hasattr(file, 'seek'):
                file.seek(0)  # Reset file pointer
            return content

        # Last resort: try to access raw file data
        if hasattr(file, 'data') and file.data:
            return file.data

        raise ValueError(f"Unable to get file content for {file.filename}. File might not be properly loaded.")

    def _invoke(
            self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:

        if tool_parameters.get("files") is None:
            yield self.create_text_message("No files provided. Please upload PDF files for conversion.")
            return

        params = ToolParameters(**tool_parameters)
        files = params.files

        # Validate parameters
        if params.dpi < 72 or params.dpi > 600:
            params.dpi = 150

        if params.quality < 1 or params.quality > 100:
            params.quality = 95

        if params.image_format not in ["png", "jpeg", "jpg"]:
            params.image_format = "png"

        try:
            # Import PyMuPDF
            try:
                import pymupdf
                fitz_module = pymupdf
            except ImportError:
                import fitz
                fitz_module = fitz

            # Import PIL for additional image processing
            from PIL import Image

            total_images_created = 0
            all_conversions = {}

            for file in files:
                try:
                    logger.info(f"Processing PDF file: {file.filename}")

                    # Get file content (handles both blob and URL cases)
                    try:
                        file_content = self._get_file_content(file)
                    except Exception as e:
                        error_msg = f"❌ Error accessing file {file.filename}: {str(e)}"
                        logger.error(error_msg)
                        yield self.create_text_message(error_msg)
                        all_conversions[file.filename] = {"error": f"File access error: {str(e)}"}
                        continue

                    # Open PDF file
                    file_bytes = io.BytesIO(file_content)
                    doc = fitz_module.open(stream=file_bytes, filetype="pdf")

                    page_count = doc.page_count
                    file_base_name = Path(file.filename).stem
                    images_info = []

                    # Calculate zoom factor based on DPI
                    # Standard PDF is 72 DPI, so zoom = desired_dpi / 72
                    zoom = params.dpi / 72.0
                    mat = fitz_module.Matrix(zoom, zoom)

                    for page_num in range(page_count):
                        try:
                            page = doc.load_page(page_num)

                            # Render page to pixmap
                            if params.alpha_channel and params.image_format == "png":
                                pix = page.get_pixmap(matrix=mat, alpha=True)
                            else:
                                pix = page.get_pixmap(matrix=mat, alpha=False)

                            # Convert to PIL Image
                            img_data = pix.tobytes("png")
                            img = Image.open(io.BytesIO(img_data))

                            # Convert to RGB if saving as JPEG
                            if params.image_format in ["jpeg", "jpg"]:
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    # Create white background
                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode == 'P':
                                        img = img.convert('RGBA')
                                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                    img = background

                            # Save image to bytes
                            img_buffer = io.BytesIO()
                            if params.image_format in ["jpeg", "jpg"]:
                                img.save(img_buffer, format="JPEG", quality=params.quality, optimize=True)
                                mime_type = "image/jpeg"
                                ext = "jpg"
                            else:
                                img.save(img_buffer, format="PNG", optimize=True)
                                mime_type = "image/png"
                                ext = "png"

                            img_bytes = img_buffer.getvalue()

                            # Generate filename for this page
                            if params.split_pages:
                                image_filename = f"{file_base_name}_page_{page_num + 1:03d}.{ext}"
                            else:
                                image_filename = f"{file_base_name}.{ext}"

                            # Store image info
                            image_info = {
                                "filename": image_filename,
                                "page": page_num + 1,
                                "width": img.width,
                                "height": img.height,
                                "format": params.image_format,
                                "dpi": params.dpi,
                                "size_bytes": len(img_bytes)
                            }
                            images_info.append(image_info)

                            # Yield image as blob message
                            yield self.create_blob_message(
                                img_bytes,
                                meta={
                                    "mime_type": mime_type,
                                    "filename": image_filename,
                                    "page_number": page_num + 1,
                                    "total_pages": page_count,
                                    "source_pdf": file.filename
                                }
                            )

                            # For debugging/preview, also send base64 encoded version in JSON
                            # (limited to first few pages to avoid memory issues)
                            if page_num < 3:  # Only first 3 pages for preview
                                image_info["preview_base64"] = base64.b64encode(img_bytes).decode('utf-8')[
                                                               :1000] + "..."

                            total_images_created += 1

                            # Clean up
                            pix = None
                            img.close()

                        except Exception as e:
                            error_msg = f"Error converting page {page_num + 1} of {file.filename}: {str(e)}"
                            logger.error(error_msg)
                            images_info.append({
                                "page": page_num + 1,
                                "error": str(e)
                            })

                    # Close the document
                    doc.close()

                    # Store conversion info
                    all_conversions[file.filename] = {
                        "total_pages": page_count,
                        "images_created": len([i for i in images_info if "error" not in i]),
                        "format": params.image_format,
                        "dpi": params.dpi,
                        "images": images_info
                    }

                    # Send success message for this file
                    success_msg = f"✅ Successfully converted {file.filename}: {page_count} pages → {len([i for i in images_info if 'error' not in i])} images"
                    yield self.create_text_message(success_msg)

                except Exception as e:
                    error_msg = f"❌ Error processing {file.filename}: {str(e)}"
                    logger.error(error_msg)
                    yield self.create_text_message(error_msg)
                    all_conversions[file.filename] = {"error": str(e)}

            # Send summary JSON message
            summary = {
                "total_files_processed": len(files),
                "total_images_created": total_images_created,
                "settings": {
                    "format": params.image_format,
                    "dpi": params.dpi,
                    "quality": params.quality if params.image_format in ["jpeg", "jpg"] else "N/A",
                    "split_pages": params.split_pages,
                    "alpha_channel": params.alpha_channel
                },
                "conversions": all_conversions
            }

            yield self.create_json_message(summary)

            # Final summary text
            final_msg = f"\n📊 Conversion Complete!\n" \
                        f"• Files processed: {len(files)}\n" \
                        f"• Total images created: {total_images_created}\n" \
                        f"• Format: {params.image_format.upper()}\n" \
                        f"• Resolution: {params.dpi} DPI"
            yield self.create_text_message(final_msg)

        except ImportError as e:
            error_msg = f"Error: Required libraries not installed. {str(e)}"
            logger.error(error_msg)
            yield self.create_text_message(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            yield self.create_text_message(error_msg)
