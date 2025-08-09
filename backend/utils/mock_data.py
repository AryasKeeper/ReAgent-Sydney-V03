"""Mock property data for fallback when APIs fail"""
import random
from typing import List, Dict

def get_mock_properties(suburb: str = "Marrickville", bedrooms: int = 3, max_price: int = 2500000) -> List[Dict]:
    """Generate realistic mock property data"""
    
    streets = [
        "Victoria Street", "Illawarra Road", "Marrickville Road", 
        "Livingstone Road", "Addison Road", "Silver Street",
        "Petersham Road", "Wardell Road", "Premier Street"
    ]
    
    properties = []
    for i in range(5):
        street = random.choice(streets)
        price = random.randint(1200000, min(max_price, 2500000))
        
        properties.append({
            "address": f"{random.randint(1, 200)} {street}, {suburb} NSW 2204",
            "price": f"${price:,}",
            "bedrooms": bedrooms,
            "bathrooms": random.randint(1, 3),
            "property_type": random.choice(["House", "Terrace", "Semi"]),
            "url": f"https://www.domain.com.au/property/{i+1}"
        })
    
    return properties

def format_properties_text(properties: List[Dict]) -> str:
    """Format properties as readable text"""
    if not properties:
        return "No properties found matching your criteria."
    
    result = f"I found {len(properties)} properties matching your criteria:\n\n"
    
    for i, prop in enumerate(properties[:5], 1):
        result += f"{i}. {prop['address']}\n"
        result += f"   Price: {prop['price']}\n"
        result += f"   {prop['bedrooms']} bed, {prop['bathrooms']} bath\n"
        result += f"   Type: {prop['property_type']}\n\n"
    
    result += "Note: These are example properties. For current listings, check Domain.com.au or RealEstate.com.au"
    
    return result