#!/usr/bin/env python3
"""
Fashion Stylist Backend - FastAPI Server
Handles AI styling logic, tool execution, S3 integration, and image upload
IMPROVED: Clean streaming with dedicated preview endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import boto3
import sys
import io
import base64
import time
import uuid
from PIL import Image
from strands import Agent, tool

# ===========================================
# GLOBAL CONFIGURATION
# ===========================================
VECTOR_BUCKET_NAME = "fashion-demo-bucket1"
VECTOR_INDEX_NAME = "fashion-trends-index1"
TRYON_RESULTS_BUCKET = "tryon-results-bucket"  # Bucket for virtual try-on results
USER_PHOTOS_BUCKET = "fashion-catalog"  # Bucket for uploaded user photos
AWS_REGION = "us-east-1"

# Status message configuration
TECHNICAL_MODE = False  # Set to True for technical messages, False for business-friendly messages

# ===========================================
# STREAMING HELPER FOR REAL-TIME UPDATES
# ===========================================

def stream_print(message: str, message_type: str = "debug"):
    """Print that immediately streams to frontend with business/technical mode support"""
    if TECHNICAL_MODE:
        # Technical mode - show all debug messages
        print(message)
    else:
        # Business mode - show only user-friendly messages
        if message_type in ["business", "status", "progress"]:
            print(message)
        # Skip technical debug messages in business mode
    
    sys.stdout.flush()
    time.sleep(0.1)

def business_print(message: str):
    """Print business-friendly status updates"""
    stream_print(message, "business")

def status_print(message: str):
    """Print status updates visible in both modes"""
    stream_print(message, "status")

def debug_print(message: str):
    """Print technical debug messages (only in technical mode)"""
    stream_print(message, "debug")

# IMPROVED: Signal functions for frontend integration
def signal_products_found(product_data: dict):
    """Signal to frontend that products were found"""
    business_print(f"📋 PRODUCTS_FOUND: {json.dumps(product_data)}")

def signal_tryon_ready(s3_path: str, product_index: int):
    """Signal to frontend that a try-on is ready"""
    business_print(f"🖼️ TRYON_READY: {json.dumps({'s3_path': s3_path, 'product_index': product_index})}")

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def load_image_from_s3_as_base64(s3_path: str) -> str:
    """
    Load image from S3 and convert to base64.
    
    Args:
        s3_path (str): S3 path like 's3://bucket/key'
        
    Returns:
        str: Base64 encoded image
    """
    try:
        # Parse S3 path
        if not s3_path.startswith('s3://'):
            raise ValueError("Invalid S3 path format")
        
        path_parts = s3_path[5:].split('/', 1)
        bucket_name = path_parts[0]
        object_key = path_parts[1] if len(path_parts) > 1 else ''
        
        debug_print(f"📥 [DEBUG] Loading image from S3: bucket={bucket_name}, key={object_key}")
        
        # Download from S3
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        image_bytes = response['Body'].read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        debug_print(f"✅ [DEBUG] Image loaded and encoded to base64 ({len(image_base64)} chars)")
        
        return image_base64
        
    except Exception as e:
        debug_print(f"❌ [DEBUG] Error loading image from S3: {str(e)}")
        raise Exception(f"Failed to load image from S3: {str(e)}")

def save_image_to_s3(image_base64: str, bucket_name: str, object_key: str) -> str:
    """
    Save base64 image to S3 bucket.
    
    Args:
        image_base64 (str): Base64 encoded image
        bucket_name (str): S3 bucket name
        object_key (str): S3 object key
        
    Returns:
        str: S3 path of saved image
    """
    try:
        debug_print(f"💾 [DEBUG] Saving image to S3: bucket={bucket_name}, key={object_key}")
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=image_bytes,
            ContentType='image/png'
        )
        
        s3_path = f"s3://{bucket_name}/{object_key}"
        debug_print(f"✅ [DEBUG] Image saved to: {s3_path}")
        
        return s3_path
        
    except Exception as e:
        debug_print(f"❌ [DEBUG] Error saving image to S3: {str(e)}")
        raise Exception(f"Failed to save image to S3: {str(e)}")

def cleanup_tryon_bucket():
    """Clean up old virtual try-on images from S3 bucket"""
    try:
        debug_print("🧹 [DEBUG] Cleaning up old virtual try-on images...")
        business_print("🧹 Preparing fresh workspace for your virtual try-ons...")
        
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # List all objects with tryon_ prefix
        response = s3_client.list_objects_v2(
            Bucket=TRYON_RESULTS_BUCKET,
            Prefix="tryon_"
        )
        
        if 'Contents' in response:
            # Delete all old try-on images
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            if objects_to_delete:
                s3_client.delete_objects(
                    Bucket=TRYON_RESULTS_BUCKET,
                    Delete={'Objects': objects_to_delete}
                )
                debug_print(f"🗑️ [DEBUG] Deleted {len(objects_to_delete)} old try-on images")
                business_print(f"🗑️ Cleared {len(objects_to_delete)} previous try-on images")
            else:
                debug_print("✨ [DEBUG] No old images to clean up")
                business_print("✨ Workspace is already clean!")
        else:
            debug_print("✨ [DEBUG] No old images found")
            business_print("✨ Starting with a clean workspace!")
            
    except Exception as e:
        debug_print(f"⚠️ [DEBUG] Error cleaning bucket: {str(e)}")
        business_print("⚠️ Minor issue cleaning workspace, but continuing with your try-ons...")

# ===========================================
# FASHION TOOLS WITH IMPROVED SIGNALING
# ===========================================

@tool
def search_fashion_trends(user_request: str) -> str:
    """
    Search fashion trends database using semantic understanding to find relevant styling insights.
    
    Connects to a comprehensive vector database of fashion trends, seasonal styles, and occasion-based 
    recommendations. Uses machine learning embeddings for semantic search beyond keyword matching.
    
    Args:
        user_request (str): Natural language fashion query describing needs, preferences, occasion, 
                           or styling goals (e.g., "professional interview outfit", "casual summer look")
    
    Returns:
        str: JSON with occasion category, trending keywords, and status
    """
    business_print(f"🔍 Analyzing your style request: '{user_request}'")
    debug_print(f"🔍 [TOOL INPUT] search_fashion_trends called with: '{user_request}'")
    
    try:
        business_print("🎯 Searching our fashion trends database...")
        debug_print(f"🔍 [DEBUG] Searching trends for: '{user_request}'")
        
        bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        s3vectors = boto3.client('s3vectors', region_name=AWS_REGION)
        
        # Create embedding
        embedding_request = json.dumps({"inputText": user_request})
        embedding_response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0", 
            body=embedding_request
        )
        embedding = json.loads(embedding_response["body"].read())["embedding"]
        debug_print("✅ [DEBUG] Embedding created")
        
        # Search S3 Vectors
        results = s3vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            queryVector={"float32": embedding},
            topK=3,
            returnDistance=True,
            returnMetadata=True
        )
        debug_print(f"✅ [DEBUG] Found {len(results.get('vectors', []))} results")
        
        # Extract keywords and occasions
        trending_keywords = []
        occasions = []
        
        for result in results.get("vectors", []):
            metadata = result["metadata"]
            keywords = metadata.get("keywords", "").split(",")
            trending_keywords.extend([k.strip() for k in keywords if k.strip()])
            
            if metadata.get("occasion"):
                occasions.append(metadata.get("occasion"))
        
        main_occasion = max(set(occasions), key=occasions.count) if occasions else "casual"
        unique_keywords = list(set(trending_keywords))[:7]
        
        business_print(f"✨ Perfect! Found trending styles for {main_occasion} occasions")
        business_print(f"🏷️ Key style trends: {', '.join(unique_keywords[:3])}...")
        
        result = json.dumps({
            "user_request": user_request,
            "occasion": main_occasion,
            "trending_keywords": unique_keywords,
            "status": "success"
        })
        
        debug_print(f"🔍 [TOOL OUTPUT] search_fashion_trends returning: {result}")
        return result
        
    except Exception as e:
        business_print("❌ Having trouble accessing our trends database. Let me try a different approach...")
        debug_print(f"❌ [DEBUG] Error: {str(e)}")
        return json.dumps({"error": str(e), "status": "failed"})

@tool
def find_products(trend_data: str) -> str:
    """
    Search product catalog to find fashion items matching trend insights and user preferences.
    
    Queries comprehensive product database using trend analysis to locate clothing items and 
    accessories. Filters by occasion, style keywords, and body part categories for virtual try-on.
    
    Args:
        trend_data (str): JSON from search_fashion_trends containing occasion and trending keywords
    
    Returns:
        str: JSON with s3_image_paths, body_parts (garment classes), and product count
    """
    business_print("🛍️ Searching our curated collection for perfect matches...")
    debug_print(f"🛍️ [TOOL INPUT] find_products called with: {trend_data}")
    
    try:
        debug_print(f"🛍️ [DEBUG] Finding products from trend data")
        
        # Parse trend data
        trends = json.loads(trend_data)
        occasion = trends.get("occasion", "casual")
        
        business_print(f"👔 Looking for {occasion} pieces that match your style...")
        
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        table = dynamodb.Table('fashion-products')
        
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('occasion').eq(occasion)
        )
        
        # Extract just S3 image paths and body parts for virtual try-on
        s3_image_paths = []
        body_parts = []
        
        for item in response.get('Items', []):
            s3_image_paths.append(item['s3_image_path'])
            # Get body_part from DynamoDB, default to UPPER_BODY if not specified
            body_part = item.get('body_part', 'UPPER_BODY')
            body_parts.append(body_part)
            debug_print(f"🛍️ [DEBUG] Product: {item.get('name', 'Unknown')} - Body part: {body_part}")
        
        business_print(f"🎉 Found {len(s3_image_paths)} amazing pieces for you!")
        
        # IMPROVED: Signal to frontend with proper data structure
        product_data = {
            's3_image_paths': s3_image_paths,
            'count': len(s3_image_paths),
            'occasion': occasion
        }
        signal_products_found(product_data)
        
        # Clean up old try-on images before starting new ones
        cleanup_tryon_bucket()
        
        debug_print(f"✅ [DEBUG] Found {len(s3_image_paths)} product images")
        
        result = json.dumps({
            "occasion": occasion,
            "s3_image_paths": s3_image_paths,
            "body_parts": body_parts,  # Include body parts for virtual try-on
            "count": len(s3_image_paths)
        })
        
        debug_print(f"🛍️ [TOOL OUTPUT] find_products returning: {result}")
        return result
        
    except Exception as e:
        business_print("❌ Having trouble accessing our product catalog. Trying alternative search...")
        debug_print(f"❌ [DEBUG] Error: {str(e)}")
        return json.dumps({"error": str(e)})

@tool
def create_single_virtual_tryon(user_image_path: str, product_path: str, garment_class: str, product_index: int) -> str:
    """
    Generate a single virtual try-on image using Amazon Nova Canvas AI technology.
    
    Args:
        user_image_path (str): S3 path to user's photo for virtual try-on
        product_path (str): S3 path to single product image
        garment_class (str): Garment classification (UPPER_BODY, LOWER_BODY, etc.)
        product_index (int): Index of the product being processed
    
    Returns:
        str: JSON with virtual try-on result
    """
    business_print(f"✨ Creating virtual try-on #{product_index} - this is where the magic happens!")
    debug_print(f"🎨 [TOOL INPUT] create_single_virtual_tryon called for product {product_index}")
    debug_print(f"   Product: {product_path}")
    debug_print(f"   Garment class: {garment_class}")
    
    try:
        business_print(f"📸 Preparing your photo and the selected garment...")
        debug_print(f"🎨 [DEBUG] Creating virtual try-on for product {product_index}")
        
        # Load user image from S3
        debug_print(f"📥 [DEBUG] Loading user image from: {user_image_path}")
        user_image_base64 = load_image_from_s3_as_base64(user_image_path)
        
        # Load product image from S3
        debug_print(f"📥 [DEBUG] Loading product image from: {product_path}")
        product_image_base64 = load_image_from_s3_as_base64(product_path)
        
        debug_print(f"👕 [DEBUG] Using garment class: {garment_class}")
        
        # Prepare Nova Canvas inference parameters
        inference_params = {
            "taskType": "VIRTUAL_TRY_ON",
            "virtualTryOnParams": {
                "sourceImage": user_image_base64,
                "referenceImage": product_image_base64,
                "maskType": "GARMENT",
                "garmentBasedMask": {
                    "garmentClass": garment_class
                }
            }
        }
        
        business_print(f"🤖 Our AI is now creating your virtual try-on (this may take a moment)...")
        debug_print(f"🎯 [DEBUG] Calling Nova Canvas for product {product_index} (may take 5-15 seconds)...")
        
        # Initialize Bedrock client for Nova Canvas
        bedrock = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION)
        
        # Invoke Nova Canvas
        body_json = json.dumps(inference_params)
        response = bedrock.invoke_model(
            body=body_json,
            modelId="amazon.nova-canvas-v1:0",
            accept="application/json",
            contentType="application/json"
        )
        
        business_print(f"🎉 Virtual try-on #{product_index} complete! Processing results...")
        debug_print(f"✅ [DEBUG] Nova Canvas completed for product {product_index}!")
        
        # Extract the images from the response
        response_body_json = json.loads(response.get("body").read())
        images = response_body_json.get("images", [])
        
        debug_print(f"🖼️ [DEBUG] Nova Canvas returned {len(images)} images for product {product_index}")
        
        # Check for errors
        if response_body_json.get("error"):
            business_print(f"⚠️ Oops! Had some trouble with try-on #{product_index}. Continuing with next item...")
            debug_print(f"❌ [DEBUG] Nova Canvas error for product {product_index}: {response_body_json.get('error')}")
            return json.dumps({"error": response_body_json.get("error"), "product_index": product_index})
        
        generated_images = []
        
        # Process each generated image
        for img_idx, image_base64 in enumerate(images):
            # Generate unique filename with regular timestamp
            timestamp = int(time.time() * 1000)  # Millisecond timestamp
            object_key = f"tryon_{timestamp}_{product_index}_{img_idx+1}.png"
            
            business_print(f"💾 Saving your virtual try-on image...")
            debug_print(f"💾 [DEBUG] Saving generated image to S3: {object_key}")
            
            # Save image to S3
            generated_s3_path = save_image_to_s3(
                image_base64, 
                TRYON_RESULTS_BUCKET, 
                object_key
            )
            
            generated_images.append({
                'product_image': product_path,
                'user_image': user_image_path,
                'generated_image': generated_s3_path,
                'garment_class': garment_class,
                'product_index': product_index,
                'status': '✨ Virtual try-on created with Nova Canvas!'
            })
            
            business_print(f"✅ Perfect! Virtual try-on #{product_index} is ready to view!")
            
            # IMPROVED: Signal to frontend that try-on is ready
            signal_tryon_ready(generated_s3_path, product_index)
            
            debug_print(f"🎉 [DEBUG] Try-on saved: {generated_s3_path}")
        
        debug_print(f"✨ [DEBUG] Completed processing product {product_index}")
        
        result = json.dumps({
            "virtual_tryons": generated_images,
            "product_index": product_index,
            "total_created": len(generated_images),
            "message": f"🎉 Product {product_index} virtual try-on created successfully!"
        })
        
        debug_print(f"🎨 [TOOL OUTPUT] create_single_virtual_tryon returning: {result}")
        return result
        
    except Exception as e:
        business_print(f"❌ Encountered an issue with virtual try-on #{product_index}. Moving to next item...")
        debug_print(f"❌ [DEBUG] Error in create_single_virtual_tryon for product {product_index}: {str(e)}")
        return json.dumps({"error": str(e), "product_index": product_index})

# ===========================================
# FASHION AGENT
# ===========================================

fashion_agent = Agent(
    system_prompt="""You are an AI Fashion Stylist that helps users discover their perfect style through personalized recommendations and virtual try-on experiences.

Use your available tools intelligently to understand user preferences, find relevant products, and create realistic virtual try-ons. 

IMPORTANT: For virtual try-ons, process ONE product at a time using create_single_virtual_tryon tool. This allows for real-time streaming of progress.

Be enthusiastic, knowledgeable, and focus on providing complete styling solutions.""",
    
    tools=[search_fashion_trends, find_products, create_single_virtual_tryon],
    callback_handler=None  # Important for streaming
)

# ===========================================
# FASTAPI APPLICATION
# ===========================================

app = FastAPI(title="AI Fashion Stylist Backend", description="Virtual Try-On AI Backend")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FashionRequest(BaseModel):
    prompt: str
    user_image: str = "s3://user-photos/demo.jpg"

class ToggleModeRequest(BaseModel):
    technical: bool = False

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Fashion Stylist Backend"}

@app.post("/toggle-mode")
async def toggle_mode(request: ToggleModeRequest):
    """Toggle between business-friendly and technical status messages"""
    global TECHNICAL_MODE
    TECHNICAL_MODE = request.technical
    mode_name = "Technical" if request.technical else "Business"
    print(f"🔄 Mode switched to: {mode_name} (TECHNICAL_MODE={TECHNICAL_MODE})")
    return {
        "mode": mode_name,
        "technical_mode": TECHNICAL_MODE,
        "message": f"Switched to {mode_name} mode"
    }

@app.get("/get-mode")
async def get_mode():
    """Get current mode setting"""
    mode_name = "Technical" if TECHNICAL_MODE else "Business"
    return {
        "mode": mode_name,
        "technical_mode": TECHNICAL_MODE
    }

@app.get("/test-mode")
async def test_mode():
    """Test current mode by generating sample messages"""
    business_print("📝 This is a BUSINESS message - you should see this in business mode")
    debug_print("🔧 This is a DEBUG message - you should only see this in technical mode")
    
    return {
        "current_mode": "Technical" if TECHNICAL_MODE else "Business",
        "technical_mode": TECHNICAL_MODE,
        "test_completed": True
    }

@app.post("/get-upload-url")
async def get_upload_url(filename: str, content_type: str):
    """Generate pre-signed URL for direct S3 upload"""
    try:
        debug_print(f"📝 [DEBUG] Generating upload URL for: {filename}")
        
        # Validate content type
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time())
        
        # Get file extension
        file_extension = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
        if file_extension == 'jpeg':
            file_extension = 'jpg'
        
        object_key = f"user-uploads/{timestamp}_{unique_id}.{file_extension}"
        
        # Generate pre-signed URL
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': USER_PHOTOS_BUCKET,
                'Key': object_key,
                'ContentType': content_type
            },
            ExpiresIn=3600  # 1 hour
        )
        
        s3_path = f"s3://{USER_PHOTOS_BUCKET}/{object_key}"
        
        debug_print(f"✅ [DEBUG] Generated upload URL for: {s3_path}")
        
        return {
            "upload_url": presigned_url,
            "s3_path": s3_path,
            "object_key": object_key,
            "bucket": USER_PHOTOS_BUCKET,
            "expires_in": 3600
        }
        
    except Exception as e:
        debug_print(f"❌ [DEBUG] Error generating upload URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

@app.post("/upload-image-fallback")
async def upload_image_fallback(file: UploadFile = File(...)):
    """Fallback: Upload image through backend if S3 CORS fails"""
    try:
        debug_print(f"📤 [DEBUG] Fallback upload for: {file.filename}")
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time())
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
        if file_extension == 'jpeg':
            file_extension = 'jpg'
        
        object_key = f"user-uploads/{timestamp}_{unique_id}.{file_extension}"
        
        # Upload to S3
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        s3_client.put_object(
            Bucket=USER_PHOTOS_BUCKET,
            Key=object_key,
            Body=file_content,
            ContentType=file.content_type
        )
        
        s3_path = f"s3://{USER_PHOTOS_BUCKET}/{object_key}"
        
        debug_print(f"✅ [DEBUG] Fallback upload completed: {s3_path}")
        
        return {
            "success": True,
            "s3_path": s3_path,
            "message": "Image uploaded successfully via backend!",
            "method": "fallback",
            "file_size": len(file_content)
        }
        
    except Exception as e:
        debug_print(f"❌ [DEBUG] Error in fallback upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@app.get("/get-single-tryon-preview")
async def get_single_tryon_preview(s3_path: str):
    """Generate presigned URL for a single try-on image preview"""
    try:
        debug_print(f"🖼️ [DEBUG] Generating single try-on preview URL for: {s3_path}")
        
        # Parse S3 path
        if not s3_path.startswith('s3://'):
            return {"error": "Invalid S3 path format"}
            
        path_parts = s3_path[5:].split('/', 1)
        bucket_name = path_parts[0]
        object_key = path_parts[1] if len(path_parts) > 1 else ''
        
        # Generate presigned URL for viewing
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=3600  # 1 hour
        )
        
        debug_print(f"✅ [DEBUG] Generated single try-on preview URL")
        
        return {
            "s3_path": s3_path,
            "preview_url": presigned_url,
            "filename": object_key.split('/')[-1]
        }
        
    except Exception as e:
        debug_print(f"❌ [DEBUG] Error generating single try-on preview: {str(e)}")
        return {"error": str(e)}

@app.get("/get-product-previews")
async def get_product_previews(s3_paths: str):
    """Generate presigned URLs for product images to show as previews"""
    try:
        debug_print(f"🖼️ [DEBUG] Generating product preview URLs")
        
        # Parse the comma-separated S3 paths
        paths = [path.strip() for path in s3_paths.split(',') if path.strip()]
        
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        preview_images = []
        
        for s3_path in paths:
            try:
                # Parse S3 path
                if not s3_path.startswith('s3://'):
                    continue
                    
                path_parts = s3_path[5:].split('/', 1)
                bucket_name = path_parts[0]
                object_key = path_parts[1] if len(path_parts) > 1 else ''
                
                # Generate presigned URL for viewing
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_key},
                    ExpiresIn=3600  # 1 hour
                )
                
                preview_images.append({
                    's3_path': s3_path,
                    'preview_url': presigned_url,
                    'filename': object_key.split('/')[-1]
                })
                
                debug_print(f"✅ [DEBUG] Generated preview URL for: {object_key}")
                
            except Exception as e:
                debug_print(f"❌ [DEBUG] Error generating preview for {s3_path}: {str(e)}")
                continue
        
        return {
            "preview_images": preview_images,
            "total": len(preview_images)
        }
        
    except Exception as e:
        debug_print(f"❌ [DEBUG] Error in get_product_previews: {str(e)}")
        return {"error": str(e), "preview_images": []}

@app.post("/stream")
async def stream_fashion_advice(request: FashionRequest):
    """IMPROVED: Stream fashion advice with clean streaming and dedicated preview handling"""
    
    async def generate():
        try:
            # Create the full prompt with user image
            full_prompt = f"{request.prompt}. My photo is at {request.user_image}"
            
            current_tool = None
            
            # Redirect print statements to capture debug output
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            try:
                async for event in fashion_agent.stream_async(full_prompt):
                    
                    # Check for captured print statements from tools
                    captured = captured_output.getvalue()
                    if captured:
                        lines = captured.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                # Send debug output character by character for realistic effect
                                for char in f"{line}\n":
                                    yield char
                                    await asyncio.sleep(0.005)  # Faster output for debug
                        captured_output.truncate(0)
                        captured_output.seek(0)
                    
                    if "data" in event:
                        # Send each character immediately with no buffering
                        text_data = event["data"]
                        for char in text_data:
                            yield char
                            # Add tiny delay for realistic typing effect
                            await asyncio.sleep(0.02)  # 20ms per character
                            
                    elif "current_tool_use" in event:
                        # Show tool usage only once per tool
                        tool_info = event["current_tool_use"]
                        tool_name = tool_info.get('name', 'Unknown')
                        
                        if current_tool != tool_name:
                            current_tool = tool_name
                            tool_message = f"\n\n🔧 [STARTING TOOL] {tool_name}\n"
                            # Send tool message character by character
                            for char in tool_message:
                                yield char
                                await asyncio.sleep(0.015)  # Slightly faster for tool messages
                            
                    elif "result" in event:
                        # Send completion message character by character
                        completion_message = f"\n\n✅ [COMPLETED] Fashion styling complete!\n"
                        for char in completion_message:
                            yield char
                            await asyncio.sleep(0.015)
                
                # Send any final captured output
                final_captured = captured_output.getvalue()
                if final_captured:
                    lines = final_captured.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            for char in f"{line}\n":
                                yield char
                                await asyncio.sleep(0.005)
                            
            finally:
                sys.stdout = old_stdout
                        
        except Exception as e:
            error_message = f"\n❌ [ERROR] {str(e)}\n"
            for char in error_message:
                yield char
                await asyncio.sleep(0.01)
    
    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )

@app.get("/get-tryon-images")
async def get_tryon_images():
    """Fetch virtual try-on images from S3 bucket (for final gallery)"""
    try:
        # Configure S3 client
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # List objects in the bucket
        response = s3_client.list_objects_v2(
            Bucket=TRYON_RESULTS_BUCKET,
            Prefix="tryon_"  # Filter for try-on result images
        )
        
        images = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # Generate presigned URL for each image (valid for 1 hour)
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': TRYON_RESULTS_BUCKET, 'Key': obj['Key']},
                    ExpiresIn=3600  # 1 hour
                )
                
                images.append({
                    'key': obj['Key'],
                    'url': presigned_url,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
        
        return {
            "images": images,
            "source": "s3_bucket", 
            "bucket": TRYON_RESULTS_BUCKET,
            "total": len(images)
        }
        
    except Exception as e:
        debug_print(f"❌ Error fetching virtual try-on images: {str(e)}")
        return {"error": str(e), "images": []}

# ===========================================
# RUN THE APPLICATION
# ===========================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Fashion Stylist Backend...")
    print("📡 Backend running on: http://localhost:8000")
    print("📱 Make sure to start the frontend separately!")
    uvicorn.run(app, host="0.0.0.0", port=8000)