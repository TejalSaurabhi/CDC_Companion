# Uploaded Resumes Directory

This directory stores uploaded CV/Resume PDF files.

## Structure
- PDF files are uploaded here by users
- Files are named using Roll Numbers (e.g., `23MT10001.pdf`)
- This directory should be writable by the web application

## Deployment Notes
- Ensure this directory has proper write permissions: `chmod 755 Uploaded_Resumes/`
- PDF files are not committed to git (see .gitignore)
- On production, you may want to use cloud storage (S3) for scalability 