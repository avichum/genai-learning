#!/usr/bin/env python3
"""
DynamoDB Setup for Fashion Agent with Body Part Mapping
Creates table and inserts fashion products with Nova Canvas body part classification
"""

import boto3
from decimal import Decimal

# ===========================================
# GLOBAL CONFIGURATION
# ===========================================
TABLE_NAME = "fashion-products"
AWS_REGION = "us-east-1"  # DynamoDB region

def setup_dynamodb():
    print("🚀 Setting up DynamoDB for Fashion Agent with Body Part Mapping...")
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    
    # Step 1: Create table
    print(f"📊 Creating DynamoDB table: {TABLE_NAME}")
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'product_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print("⏳ Waiting for table creation...")
        table.wait_until_exists()
        print(f"✅ Created table: {TABLE_NAME}")
        
    except Exception as e:
        table = dynamodb.Table(TABLE_NAME)
        print(f"⚠️ Table might already exist: {e}")
    
    # Step 2: Insert sample products
    print("📤 Inserting sample fashion products with body part mapping...")
    insert_sample_products(dynamodb)
    
    # Step 3: Test the setup
    print("🧪 Testing product lookup...")
    test_product_lookup(dynamodb)
    
    print("🎉 DynamoDB setup complete!")

def insert_sample_products(dynamodb):
    """Insert sample fashion products with Nova Canvas body part mapping"""
    
    table = dynamodb.Table(TABLE_NAME)
    
    # 7 Simple fashion products matching our occasions with body_part field
    products = [
        # Professional Items
        {
            'product_id': 'blazer-navy-001',
            'name': 'Navy Blazer',
            'type': 'top',
            'body_part': 'UPPER_BODY',  # Nova Canvas garment class
            'occasion': 'professional',
            's3_image_path': 's3://fashion-catalog/blazer-navy.jpg',
            'price': Decimal('89.99'),
            'description': 'Classic navy blazer for professional settings'
        },
        {
            'product_id': 'shirt-white-001',
            'name': 'White Shirt',
            'type': 'top',
            'body_part': 'UPPER_BODY',
            'occasion': 'professional',
            's3_image_path': 's3://fashion-catalog/shirt-white.jpg',
            'price': Decimal('45.00'),
            'description': 'Crisp white button-down shirt'
        },
        {
            'product_id': 'pants-black-001',
            'name': 'Black Pants',
            'type': 'bottom',
            'body_part': 'LOWER_BODY',
            'occasion': 'professional',
            's3_image_path': 's3://fashion-catalog/pants-black.jpg',
            'price': Decimal('65.00'),
            'description': 'Classic black tailored pants'
        },
        
        # Elegant Items
        {
            'product_id': 'dress-black-001',
            'name': 'Black Dress',
            'type': 'dress',
            'body_part': 'FULL_BODY',
            'occasion': 'elegant',
            's3_image_path': 's3://fashion-catalog/dress-black.jpg',
            'price': Decimal('120.00'),
            'description': 'Elegant black dress for special occasions'
        },
        {
            'product_id': 'dress-floral-001',
            'name': 'Floral Dress',
            'type': 'dress',
            'body_part': 'FULL_BODY',
            'occasion': 'elegant',
            's3_image_path': 's3://fashion-catalog/dress-floral.jpg',
            'price': Decimal('95.00'),
            'description': 'Beautiful floral midi dress'
        },
        
        # Casual Items
        {
            'product_id': 'jeans-blue-001',
            'name': 'Blue Jeans',
            'type': 'bottom',
            'body_part': 'LOWER_BODY',
            'occasion': 'casual',
            's3_image_path': 's3://fashion-catalog/jeans-blue.jpg',
            'price': Decimal('75.00'),
            'description': 'Comfortable blue jeans for casual wear'
        },
        {
            'product_id': 'cardigan-beige-001',
            'name': 'Beige Cardigan',
            'type': 'top',
            'body_part': 'UPPER_BODY',
            'occasion': 'casual',
            's3_image_path': 's3://fashion-catalog/cardigan-beige.jpg',
            'price': Decimal('55.00'),
            'description': 'Soft beige cardigan for layering'
        }
    ]
    
    # Insert products
    with table.batch_writer() as batch:
        for product in products:
            batch.put_item(Item=product)
            print(f"  ✅ Added: {product['name']} - {product['body_part']} (${product['price']})")
    
    print(f"🎉 Inserted {len(products)} products")

def test_product_lookup(dynamodb):
    """Test product lookup functionality"""
    
    table = dynamodb.Table(TABLE_NAME)
    
    # Test occasions
    occasions = ['professional', 'elegant', 'casual']
    
    for occasion in occasions:
        print(f"\n🔍 Testing products for: {occasion}")
        
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('occasion').eq(occasion)
        )
        
        products = response.get('Items', [])
        print(f"  Found {len(products)} products:")
        
        for product in products:
            print(f"    - {product['name']} ({product['body_part']}) - ${product['price']}")

def test_body_part_lookup(dynamodb):
    """Test body part lookup functionality"""
    
    table = dynamodb.Table(TABLE_NAME)
    
    # Test the 3 main body parts (no FOOTWEAR in our 7 examples)
    body_parts = ['UPPER_BODY', 'LOWER_BODY', 'FULL_BODY']
    
    print("\n" + "="*60)
    print("🎯 TESTING BODY PART MAPPING FOR NOVA CANVAS")
    print("="*60)
    
    for body_part in body_parts:
        print(f"\n👕 Products for: {body_part}")
        
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('body_part').eq(body_part)
        )
        
        products = response.get('Items', [])
        print(f"  Found {len(products)} products:")
        
        for product in products:
            print(f"    - {product['name']} ({product['type']}) - {product['occasion']}")

def show_table_info():
    """Show table information"""
    
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        # Get table info using correct method
        response = table.meta.client.describe_table(TableName=TABLE_NAME)
        table_info = response['Table']
        
        print(f"\n📊 Table Information:")
        print(f"  Table Name: {table_info['TableName']}")
        print(f"  Status: {table_info['TableStatus']}")
        print(f"  Item Count: {table_info.get('ItemCount', 'N/A')}")
        print(f"  Region: {AWS_REGION}")
        
        # Show schema
        print(f"\n📋 Product Schema:")
        print(f"  - product_id (Primary Key)")
        print(f"  - name")
        print(f"  - type") 
        print(f"  - body_part (UPPER_BODY | LOWER_BODY | FULL_BODY)")
        print(f"  - occasion")
        print(f"  - s3_image_path")
        print(f"  - price")
        print(f"  - description")
        
    except Exception as e:
        print(f"❌ Error getting table info: {e}")

if __name__ == "__main__":
    print("🚀 DynamoDB Setup for Fashion Agent with Body Part Mapping")
    
    # Setup DynamoDB
    setup_dynamodb()
    
    # Test body part lookup
    dynamodb_resource = boto3.resource('dynamodb', region_name=AWS_REGION)
    test_body_part_lookup(dynamodb_resource)
    test_product_lookup(dynamodb_resource)
    
    # Show table information
    show_table_info()
    
    print(f"\n💡 Table '{TABLE_NAME}' is ready with body part mapping!")
    print("💡 Nova Canvas garment classes: UPPER_BODY, LOWER_BODY, FULL_BODY")
    print("💡 You can now run: python fashion_backend.py")