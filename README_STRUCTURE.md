# SDX Project Manager - Folder Structure

## 📁 Project Organization

### Core Application
- `app/` - Main application entry point
- `modules/` - Business logic modules  
- `config/` - Configuration files
- `utils/` - Utility functions

### Static Assets (for UI)
- `static/css/` - Stylesheets
- `static/js/` - JavaScript files
- `static/images/logos/` - Company logos
- `static/images/slides/` - Login page slideshow
- `static/images/icons/` - UI icons
- `static/fonts/` - Custom fonts

### Data Storage (File-based to save DB space)
- `data/uploads/documents/` - PDF, Word, Excel files
- `data/uploads/images/` - User uploaded images  
- `data/uploads/avatars/` - Profile pictures
- `data/exports/` - Generated reports (CSV, PDF)
- `data/backups/` - Database backups
- `data/temp/` - Temporary processing files
- `data/cache/` - Application cache

### Logs & Monitoring  
- `logs/app/` - Application logs
- `logs/database/` - Database operation logs
- `logs/errors/` - Error logs
- `logs/performance/` - Performance monitoring

### Development & Deployment
- `tests/` - Unit and integration tests
- `docker/` - Docker configurations
- `scripts/` - Deployment and utility scripts
- `docs/` - Documentation

## 🎯 Space Optimization Strategy

### Database (10GB Limit)
- **Store in DB**: Small files < 1MB, metadata, structured data
- **Store as Files**: Large documents, images, exports
- **Compression**: JSON data, logs, backups
- **Auto-cleanup**: Temp files, old logs, cached data

### File Storage Guidelines
- **Images**: Always store as files, auto-optimize, create thumbnails
- **Documents**: Store large files (>1MB) as files, small files in DB
- **Exports**: Generate as files, auto-cleanup after 30 days
- **Logs**: Compress and rotate, keep 3 months max

### Best Practices
- Use file deduplication (MD5 hashes)
- Implement auto-cleanup routines
- Compress backups
- Monitor disk usage
- Regular maintenance tasks

## 🔧 Configuration Files
- `config/file_config.yaml` - File upload settings
- `config/database_config.yaml` - DB optimization settings
- `static/config.json` - Static file settings
- `utils/file_manager.py` - File management utilities