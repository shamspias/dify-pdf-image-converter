# PDF to Image Converter Plugin for Dify

A powerful PDF to image conversion plugin for Dify that converts PDF pages into high-quality images with customizable settings.

![Plugin Icon](./_assets/pdf2image.png)

## 🚀 Features

- **📄 → 🖼️ PDF to Image Conversion**: Convert any PDF document into individual page images
- **🎨 Multiple Format Support**: Export as PNG (lossless) or JPEG (compressed)
- **📐 Adjustable Resolution**: Choose from 72 to 600 DPI for different use cases
- **✂️ Page Splitting**: Each page as a separate image file
- **🎯 Quality Control**: Adjustable JPEG compression quality (1-100)
- **🔍 Transparency Support**: Optional alpha channel for PNG format
- **📊 Batch Processing**: Handle multiple PDF files simultaneously
- **🔧 Robust File Handling**: Supports both direct file uploads and URL-based file references

## 📦 Installation

1. Navigate to the Plugin section in your Dify application
2. Click "Add Plugin"
3. Search for "PDF to Image Converter" or upload this plugin package
4. Follow the installation wizard

## 🛠️ Configuration Options

### Image Format
- **PNG**: Best for quality, supports transparency
- **JPEG/JPG**: Smaller file size, adjustable quality

### Resolution (DPI)
- **72 DPI**: Screen viewing, web use
- **150 DPI**: Standard quality, documents
- **300 DPI**: High quality, professional use
- **600 DPI**: Print quality, archival

### Additional Options
- **Split Pages**: Create individual images for each page
- **JPEG Quality**: 1-100 (higher = better quality, larger size)
- **Transparency**: Include alpha channel (PNG only)

## 📝 Usage Example

1. Upload one or more PDF files
2. Select your preferred image format (PNG/JPEG)
3. Choose resolution (DPI) based on your needs
4. Adjust quality settings if using JPEG
5. Process and download converted images

## 🔄 Output

The plugin returns:
- Individual image files for each PDF page
- Detailed JSON metadata including:
  - Page dimensions
  - File sizes
  - Conversion settings
  - Processing statistics
- Summary report of the conversion process

## 🔧 Troubleshooting

### File Access Issues
If you encounter "Error accessing file" messages:
1. Ensure the plugin has proper permissions
2. Check that the FILES_URL environment variable is set if using URL-based files
3. Verify the file format is PDF

### Environment Variables (Optional)
```bash
# Base URL for file fetching (if needed)
FILES_URL=http://your-dify-instance:5001
DIFY_API_URL=https://api.dify.ai
```

## 🔒 Privacy & Security

- No data collection or storage
- All processing happens locally
- No external API calls
- Files are processed in memory only
- Compliant with data protection regulations

## 📋 Requirements

- PyMuPDF library (included)
- Pillow for image processing (included)
- Requests for URL file handling (included)
- Compatible with Dify plugin system

## 🤝 Support

For issues, feature requests, or questions:
- GitHub: [shamspias/pdf-to-image-plugin](https://github.com/shamspias/pdf-to-image-plugin)
- Email: info@shamspias.com

## 📄 License

This plugin is licensed under the [MIT License](LICENSE).

## 🙏 Credits

- Built with PyMuPDF and Pillow
- Developed for the Dify platform
- Robust file handling for various Dify configurations