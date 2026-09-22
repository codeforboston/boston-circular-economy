"""
    Organization-specific OpenStreetMap query definitions.
    
"""
CLOTHING_FILTERS = [
    # Resale (buy/sell secondhand clothing)
    '["shop"="second_hand"]',
    '["shop"="clothes"]["second_hand"="yes"]',
    # Repair / alter
    '["shop"="tailor"]',
    '["craft"="tailor"]',
    '["repair"="clothes"]',
    # Donation (drop-off)
    '["shop"="charity"]',
    '["charity"="yes"]',
    '["amenity"="recycling"]["recycling:clothes"="yes"]',
]