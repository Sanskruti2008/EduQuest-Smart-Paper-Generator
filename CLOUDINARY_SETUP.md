# Cloudinary Setup Guide

## Overview
Images extracted from question papers are now stored in Cloudinary cloud storage instead of local files. This provides better scalability, CDN delivery, and eliminates the need to manage local image storage.

## Setup Instructions

### 1. Create a Cloudinary Account
1. Visit [https://cloudinary.com](https://cloudinary.com)
2. Sign up for a free account (includes 25GB storage and 25GB bandwidth/month)
3. After signup, you'll be redirected to your Console Dashboard

### 2. Get Your Credentials
From your Cloudinary Console Dashboard, you'll see:
- **Cloud Name**: Your unique cloud name (e.g., `dxxxxxxx`)
- **API Key**: Your API key (e.g., `123456789012345`)
- **API Secret**: Your API secret (keep this secure!)

### 3. Configure Environment Variables
1. Open `backend/.env` file
2. Update the following variables:
```env
CLOUDINARY_CLOUD_NAME=your_actual_cloud_name
CLOUDINARY_API_KEY=your_actual_api_key
CLOUDINARY_API_SECRET=your_actual_api_secret
```

### 4. Test the Integration
1. Restart the backend server (it should already be running)
2. Upload a question paper PDF through the application
3. Check the logs for "Uploaded image to Cloudinary: [URL]"
4. Visit your Cloudinary Media Library to see uploaded images

## Features

### Image Upload
- Images are uploaded to `eduquest/question_images/` folder in your Cloudinary account
- Each image is named: `eduquest_page_{page_num}_image_{idx+1}`
- Images are tagged with page number and position metadata

### Automatic Fallback
If Cloudinary upload fails (network issues, invalid credentials, etc.), the system automatically:
- Falls back to local storage in `extracted_images/` folder
- Adds `local_fallback: true` flag to the image data
- Continues processing without errors

### Image Data Structure
Each extracted image includes:
```json
{
  "filename": "page_1_image_1.png",
  "url": "https://res.cloudinary.com/...",
  "public_id": "eduquest/question_images/eduquest_page_1_image_1",
  "cloudinary_url": "https://res.cloudinary.com/...",
  "width": 800,
  "height": 600,
  "bbox": [x1, y1, x2, y2],
  "page": 1
}
```

## Benefits

1. **Scalability**: No disk space limitations
2. **CDN Delivery**: Fast image loading worldwide
3. **Transformations**: Can resize/optimize images on-the-fly
4. **Accessibility**: Images accessible from any device
5. **No Backup Needed**: Cloudinary handles redundancy

## Troubleshooting

### Upload Fails
- **Check credentials**: Ensure `.env` has correct Cloudinary credentials
- **Network**: Verify internet connectivity
- **Quotas**: Check if you've exceeded free tier limits (25GB/month)

### Images Not Appearing
- **Check Console**: Look for "Uploaded to Cloudinary" messages in backend logs
- **Media Library**: Visit Cloudinary dashboard to see uploaded images
- **Public ID**: Verify images are in `eduquest/question_images/` folder

### Want to Use Local Storage Instead?
If you prefer local storage, simply don't configure Cloudinary credentials. The system will automatically use local fallback.

## Free Tier Limits
- Storage: 25 GB
- Bandwidth: 25 GB/month
- Transformations: 25 credits/month
- More than enough for typical usage!

## Need Help?
- Cloudinary Documentation: [https://cloudinary.com/documentation](https://cloudinary.com/documentation)
- API Reference: [https://cloudinary.com/documentation/image_upload_api_reference](https://cloudinary.com/documentation/image_upload_api_reference)
