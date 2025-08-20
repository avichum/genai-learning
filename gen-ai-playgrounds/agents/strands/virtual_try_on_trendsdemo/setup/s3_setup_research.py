#!/usr/bin/env python3
"""
S3 Vectors Setup for Fashion Research Agent
Creates S3 vector bucket, index, and adds 5 fashion trends
"""

import boto3
import json
import time

# ===========================================
# GLOBAL CONFIGURATION
# ===========================================
VECTOR_BUCKET_NAME = "fashion-demo-bucket1"
VECTOR_INDEX_NAME = "fashion-trends-index1"
AWS_REGION = "us-east-1"

def setup_s3_vectors():
    print("🚀 Setting up S3 Vectors for Fashion Research Agent...")
    
    # Initialize clients
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    s3vectors = boto3.client("s3vectors", region_name=AWS_REGION)
    
    trends = [
            # PROFESSIONAL OCCASIONS
            {
                "text": "job interview professional blazer navy structured confidence corporate formal business suit",
                "occasion": "professional",
                "keywords": "professional,blazer,navy,structured,confidence,corporate,formal,business,suit,interview"
            },
            {
                "text": "business meeting office work professional shirt formal smart casual workplace conservative",
                "occasion": "professional", 
                "keywords": "business,meeting,office,work,professional,shirt,formal,smart,casual,workplace"
            },
            {
                "text": "presentation conference professional polished sophisticated tailored executive boardroom",
                "occasion": "professional",
                "keywords": "presentation,conference,professional,polished,sophisticated,tailored,executive"
            },
            {
                "text": "networking event professional approachable smart business casual minggling colleagues",
                "occasion": "professional",
                "keywords": "networking,professional,approachable,smart,business,casual,colleagues"
            },
            
            # CASUAL OCCASIONS
            {
                "text": "casual weekend coffee comfortable jeans relaxed friendly approachable laid back denim",
                "occasion": "casual",
                "keywords": "casual,weekend,coffee,comfortable,jeans,relaxed,friendly,laid,back,denim"
            },
            {
                "text": "movie theater friends casual fun comfortable sneakers relaxed entertainment popcorn",
                "occasion": "casual",
                "keywords": "movie,theater,friends,casual,fun,comfortable,sneakers,relaxed,entertainment"
            },
            {
                "text": "shopping mall casual comfortable walking shoes browse stores weekend leisure",
                "occasion": "casual",
                "keywords": "shopping,mall,casual,comfortable,walking,shoes,browse,stores,weekend,leisure"
            },
            {
                "text": "brunch friends casual chic effortless weekend morning relaxed socializing",
                "occasion": "casual",
                "keywords": "brunch,friends,casual,chic,effortless,weekend,morning,relaxed,socializing"
            },
            {
                "text": "park picnic outdoor casual comfortable practical breathable natural relaxed",
                "occasion": "casual",
                "keywords": "park,picnic,outdoor,casual,comfortable,practical,breathable,natural,relaxed"
            },
            {
                "text": "studying library casual comfortable focus practical layers cozy concentration",
                "occasion": "casual",
                "keywords": "studying,library,casual,comfortable,focus,practical,layers,cozy,concentration"
            },
            {
                "text": "gym workout athletic sporty comfortable performance activewear fitness exercise",
                "occasion": "casual",
                "keywords": "gym,workout,athletic,sporty,comfortable,performance,activewear,fitness,exercise"
            },
            {
                "text": "beach vacation casual airy lightweight breathable summer relaxed tropical",
                "occasion": "casual",
                "keywords": "beach,vacation,casual,airy,lightweight,breathable,summer,relaxed,tropical"
            },
            
            # ELEGANT OCCASIONS
            {
                "text": "romantic dinner date elegant black dress sophisticated glamorous intimate fine dining",
                "occasion": "elegant",
                "keywords": "romantic,dinner,date,elegant,black,dress,sophisticated,glamorous,intimate,dining"
            },
            {
                "text": "wedding guest floral midi dress appropriate elegant respectful celebratory formal",
                "occasion": "elegant",
                "keywords": "wedding,guest,floral,midi,dress,appropriate,elegant,respectful,celebratory"
            },
            {
                "text": "cocktail party elegant sophisticated chic stylish evening glamorous social",
                "occasion": "elegant",
                "keywords": "cocktail,party,elegant,sophisticated,chic,stylish,evening,glamorous,social"
            },
            {
                "text": "theater opera elegant formal cultural sophisticated refined artistic classy",
                "occasion": "elegant",
                "keywords": "theater,opera,elegant,formal,cultural,sophisticated,refined,artistic,classy"
            },
            {
                "text": "graduation ceremony elegant proud milestone celebration formal family important",
                "occasion": "elegant",
                "keywords": "graduation,ceremony,elegant,proud,milestone,celebration,formal,family,important"
            },
            {
                "text": "anniversary celebration elegant romantic special memorable sophisticated couple",
                "occasion": "elegant",
                "keywords": "anniversary,celebration,elegant,romantic,special,memorable,sophisticated,couple"
            },
            {
                "text": "art gallery opening elegant cultured sophisticated creative artistic refined",
                "occasion": "elegant",
                "keywords": "art,gallery,opening,elegant,cultured,sophisticated,creative,artistic,refined"
            },
            {
                "text": "charity gala elegant formal sophisticated giving philanthropic black tie",
                "occasion": "elegant",
                "keywords": "charity,gala,elegant,formal,sophisticated,giving,philanthropic,black,tie"
            }
        ]
    
    # Step 1: Create vector bucket
    print("📦 Creating S3 vector bucket...")
    bucket_response = None
    try:
        bucket_response = s3vectors.create_vector_bucket(
            vectorBucketName=VECTOR_BUCKET_NAME
            # No encryption configuration (skipping as requested)
        )
        print(f"✅ Created bucket: {VECTOR_BUCKET_NAME}")
        print(f"📋 Bucket ARN: {bucket_response.get('vectorBucketArn', 'N/A')}")
    except Exception as e:
        print(f"⚠️ Bucket might exist: {e}")
        # If bucket exists, we need to get its ARN
        try:
            # You might need to list buckets or use describe to get ARN
            # For now, construct the ARN (typical format)
            sts = boto3.client('sts', region_name=AWS_REGION)
            account_id = sts.get_caller_identity()['Account']
            bucket_arn = f"arn:aws:s3vectors:{AWS_REGION}:{account_id}:vector-bucket/{VECTOR_BUCKET_NAME}"
            print(f"📋 Using constructed ARN: {bucket_arn}")
        except Exception as arn_error:
            print(f"❌ Could not determine bucket ARN: {arn_error}")
            bucket_arn = None
    
    # Get bucket ARN for index creation
    if bucket_response:
        bucket_arn = bucket_response.get('vectorBucketArn')
    else:
        # Construct ARN if bucket already exists
        try:
            sts = boto3.client('sts', region_name=AWS_REGION)
            account_id = sts.get_caller_identity()['Account']
            bucket_arn = f"arn:aws:s3vectors:{AWS_REGION}:{account_id}:vector-bucket/{VECTOR_BUCKET_NAME}"
        except:
            bucket_arn = None
    
    # Step 2: Create vector index
    print("📊 Creating vector index...")
    try:
        index_params = {
            "vectorBucketName": VECTOR_BUCKET_NAME,
            "indexName": VECTOR_INDEX_NAME,
            "dataType": "float32",
            "dimension": 1024,  # Titan Text Embeddings V2 outputs 1024 dimensions
            "distanceMetric": "cosine"
        }
        
        # Add vectorBucketArn if we have it
        if bucket_arn:
            index_params["vectorBucketArn"] = bucket_arn
            
        response = s3vectors.create_index(**index_params)
        print(f"✅ Created index: {VECTOR_INDEX_NAME}")
        print("⏳ Waiting for index to be ready...")
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ Index might exist: {e}")
    
    # Step 3: Generate embeddings
    print("🧠 Generating embeddings for fashion trends...")
    embeddings = []
    
    for i, trend in enumerate(trends):
        print(f"  Processing {i+1}/5: {trend['occasion']}")
        
        # Create embedding using correct format
        response = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps({"inputText": trend["text"]})
        )
        # Extract embedding from response
        response_body = json.loads(response["body"].read())
        embeddings.append(response_body["embedding"])
    
    print("✅ Generated embeddings")
    
    # Step 4: Insert vectors using correct format
    print("📤 Inserting vectors into S3...")
    
    s3vectors.put_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        vectors=[
            {
                "key": f"trend_{i+1}",
                "data": {"float32": embeddings[i]},
                "metadata": {
                    "source_text": trend["text"],
                    "occasion": trend["occasion"],
                    "keywords": trend["keywords"]
                }
            }
            for i, trend in enumerate(trends)
        ]
    )
    
    print(f"✅ Inserted {len(trends)} fashion trends")
    
    # Step 5: Test the setup
    print("\n🧪 Testing vector search...")
    test_search()
    
    print("\n🎉 S3 Vectors setup complete!")
    print("💡 You can now run: python research_agent_app.py")

def test_search():
    """Test the vector search functionality"""
    
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    s3vectors = boto3.client("s3vectors", region_name=AWS_REGION)
    
    # Test query
    test_query = "I need professional attire for work"
    print(f"🔍 Test query: '{test_query}'")
    
    # Generate the vector embedding
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": test_query})
    )
    # Extract embedding from response
    model_response = json.loads(response["body"].read())
    embedding = model_response["embedding"]
    
    # Query vector index
    results = s3vectors.query_vectors(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
        queryVector={"float32": embedding},
        topK=2,
        returnDistance=True,
        returnMetadata=True
    )
    
    print("📊 Top results:")
    for i, result in enumerate(results["vectors"], 1):
        metadata = result["metadata"]
        similarity = 1 - result.get("distance", 0)
        print(f"  {i}. {metadata['occasion']} - {metadata['keywords'][:30]}... (similarity: {similarity:.3f})")

if __name__ == "__main__":
    setup_s3_vectors()