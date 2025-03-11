#!/usr/bin/env python
"""
Setup script to create a test SQLite database with dolphin species information.
This database will be stored at ~/.dolphin/dolphin.db and includes information about
different dolphin species, their characteristics, and evolutionary relationships.
"""

import os
import sqlite3
import pathlib

def create_dolphin_database():
    """Create a SQLite database with dolphin species information."""
    # Create directory if it doesn't exist
    db_dir = os.path.expanduser("~/.dolphin")
    os.makedirs(db_dir, exist_ok=True)
    
    # Database path
    db_path = os.path.join(db_dir, "dolphin.db")
    
    # Check if database already exists
    db_exists = os.path.exists(db_path)
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dolphin_species (
        id INTEGER PRIMARY KEY,
        common_name TEXT NOT NULL,
        scientific_name TEXT NOT NULL,
        family TEXT NOT NULL,
        habitat TEXT NOT NULL,
        average_length_meters REAL,
        average_weight_kg REAL,
        average_lifespan_years INTEGER,
        conservation_status TEXT,
        population_estimate TEXT,
        evolutionary_ancestor TEXT,
        description TEXT
    )
    ''')
    
    # Create a separate table for evolutionary relationships
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evolutionary_relationships (
        id INTEGER PRIMARY KEY,
        species_id INTEGER,
        related_species_id INTEGER,
        relationship_type TEXT NOT NULL,
        divergence_mya REAL,
        FOREIGN KEY (species_id) REFERENCES dolphin_species(id),
        FOREIGN KEY (related_species_id) REFERENCES dolphin_species(id)
    )
    ''')
    
    # Check if we already have data
    cursor.execute("SELECT COUNT(*) FROM dolphin_species")
    count = cursor.fetchone()[0]
    
    # Only insert data if the table is empty
    if count == 0:
        # Insert dolphin species data
        dolphin_species = [
            (1, "Common Bottlenose Dolphin", "Tursiops truncatus", "Delphinidae", "Coastal & Oceanic", 2.5, 300, 45, "Least Concern", "600,000+", "Kentriodontids", "One of the most well-known dolphin species, highly intelligent with complex social structures."),
            (2, "Indo-Pacific Bottlenose Dolphin", "Tursiops aduncus", "Delphinidae", "Coastal", 2.6, 230, 40, "Near Threatened", "Unknown", "Kentriodontids", "Slightly smaller than common bottlenose dolphins with a more slender body."),
            (3, "Common Dolphin", "Delphinus delphis", "Delphinidae", "Oceanic", 2.3, 110, 35, "Least Concern", "Unknown", "Kentriodontids", "Known for their distinctive colorful pattern and hourglass pattern on their sides."),
            (4, "Spinner Dolphin", "Stenella longirostris", "Delphinidae", "Oceanic", 2.0, 80, 25, "Least Concern", "Unknown", "Kentriodontids", "Famous for their acrobatic displays, spinning multiple times along their longitudinal axis."),
            (5, "Pantropical Spotted Dolphin", "Stenella attenuata", "Delphinidae", "Oceanic", 2.1, 120, 40, "Least Concern", "3,000,000+", "Kentriodontids", "Born without spots and develop them as they age."),
            (6, "Atlantic Spotted Dolphin", "Stenella frontalis", "Delphinidae", "Coastal & Oceanic", 2.3, 140, 35, "Least Concern", "Unknown", "Kentriodontids", "Closely related to pantropical spotted dolphins but with different spotting patterns."),
            (7, "Striped Dolphin", "Stenella coeruleoalba", "Delphinidae", "Oceanic", 2.4, 150, 40, "Least Concern", "2,000,000+", "Kentriodontids", "Distinctive blue and white stripes along their sides."),
            (8, "Rough-toothed Dolphin", "Steno bredanensis", "Delphinidae", "Oceanic", 2.5, 150, 35, "Least Concern", "Unknown", "Kentriodontids", "Distinctive conical head without a clear melon-forehead division."),
            (9, "Risso's Dolphin", "Grampus griseus", "Delphinidae", "Oceanic", 3.8, 500, 35, "Least Concern", "Unknown", "Kentriodontids", "Distinctive appearance with extensive scarring on adults."),
            (10, "Fraser's Dolphin", "Lagenodelphis hosei", "Delphinidae", "Oceanic", 2.5, 210, 25, "Least Concern", "Unknown", "Kentriodontids", "Stocky body with small appendages and distinctive lateral stripe."),
            (11, "Hector's Dolphin", "Cephalorhynchus hectori", "Delphinidae", "Coastal", 1.4, 50, 20, "Endangered", "<7,000", "Kentriodontids", "One of the smallest dolphin species and endemic to New Zealand."),
            (12, "Maui Dolphin", "Cephalorhynchus hectori maui", "Delphinidae", "Coastal", 1.4, 50, 20, "Critically Endangered", "<50", "Kentriodontids", "Subspecies of Hector's dolphin, one of the rarest and most endangered dolphins."),
            (13, "Amazon River Dolphin", "Inia geoffrensis", "Iniidae", "Freshwater", 2.5, 185, 30, "Endangered", "Unknown", "Platanistoidea", "Also known as the pink river dolphin, largest freshwater dolphin species."),
            (14, "Ganges River Dolphin", "Platanista gangetica", "Platanistidae", "Freshwater", 2.2, 85, 30, "Endangered", "<2,000", "Platanistoidea", "Nearly blind, uses echolocation to navigate muddy river waters."),
            (15, "Irrawaddy Dolphin", "Orcaella brevirostris", "Delphinidae", "Coastal & Freshwater", 2.3, 130, 30, "Endangered", "<7,000", "Kentriodontids", "Found in coastal areas and three rivers in Southeast Asia."),
            (16, "Orca (Killer Whale)", "Orcinus orca", "Delphinidae", "Oceanic & Coastal", 7.0, 5600, 50, "Data Deficient", "50,000+", "Kentriodontids", "Largest dolphin species, apex predator with complex social structures."),
            (17, "False Killer Whale", "Pseudorca crassidens", "Delphinidae", "Oceanic", 5.5, 1500, 60, "Near Threatened", "Unknown", "Kentriodontids", "Despite the name, more closely related to dolphins like Risso's and pilot whales."),
            (18, "Long-finned Pilot Whale", "Globicephala melas", "Delphinidae", "Oceanic", 6.5, 2500, 45, "Least Concern", "200,000+", "Kentriodontids", "Actually a large dolphin, forms strong social bonds and large pods."),
            (19, "Short-finned Pilot Whale", "Globicephala macrorhynchus", "Delphinidae", "Oceanic", 5.5, 2200, 45, "Least Concern", "Unknown", "Kentriodontids", "Similar to long-finned pilot whales but with genetic and morphological differences."),
            (20, "Commerson's Dolphin", "Cephalorhynchus commersonii", "Delphinidae", "Coastal", 1.5, 60, 18, "Least Concern", "Unknown", "Kentriodontids", "Distinctive black and white patterning, one of the smallest dolphin species.")
        ]
        
        cursor.executemany('''
        INSERT INTO dolphin_species (
            id, common_name, scientific_name, family, habitat, 
            average_length_meters, average_weight_kg, average_lifespan_years, 
            conservation_status, population_estimate, evolutionary_ancestor, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', dolphin_species)
        
        # Insert evolutionary relationships data
        # This is a simplified representation of some key relationships
        relationships = [
            (1, 1, 2, "Sister Species", 2.5),  # Bottlenose dolphin species split
            (2, 1, 3, "Same Family", 10),      # Bottlenose and Common dolphins
            (3, 3, 4, "Same Genus", 5),        # Within Stenella genus
            (4, 4, 5, "Sister Species", 3),    # Spinner and Spotted dolphins
            (5, 5, 6, "Sister Species", 2),    # Spotted dolphin species
            (6, 7, 5, "Same Genus", 4),        # Striped and Spotted dolphins
            (7, 16, 17, "Evolutionary Cousins", 15), # Orca and False Killer Whale
            (8, 18, 19, "Sister Species", 3.5), # Pilot whale species
            (9, 16, 18, "Same Family", 12),    # Orca and Pilot whales
            (10, 11, 12, "Subspecies", 0.8),   # Hector's and Maui dolphins
            (11, 11, 20, "Same Genus", 4),     # Hector's and Commerson's dolphins
            (12, 13, 14, "Different Families", 25), # River dolphin species
            (13, 1, 13, "Distant Relatives", 35), # Oceanic and river dolphins split
            (14, 15, 16, "Same Family", 18),   # Irrawaddy and Orca
            (15, 9, 18, "Evolutionary Branch", 14)  # Risso's and Pilot whales
        ]
        
        cursor.executemany('''
        INSERT INTO evolutionary_relationships (
            id, species_id, related_species_id, relationship_type, divergence_mya
        ) VALUES (?, ?, ?, ?, ?)
        ''', relationships)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    # Report status
    if db_exists:
        print(f"Database already existed at {db_path}")
        if count > 0:
            print(f"Database contains {count} dolphin species records")
        else:
            print(f"Added {len(dolphin_species)} dolphin species to the database")
    else:
        print(f"Created new database at {db_path}")
        print(f"Added {len(dolphin_species)} dolphin species to the database")
        print(f"Added {len(relationships)} evolutionary relationships to the database")
    
    print("\nDatabase Schema:")
    print("- Table: dolphin_species")
    print("  Columns: id, common_name, scientific_name, family, habitat, average_length_meters,")
    print("           average_weight_kg, average_lifespan_years, conservation_status,")
    print("           population_estimate, evolutionary_ancestor, description")
    print("- Table: evolutionary_relationships")
    print("  Columns: id, species_id, related_species_id, relationship_type, divergence_mya")
    
    return db_path

if __name__ == "__main__":
    db_path = create_dolphin_database()
    
    # Show sample queries that can be run against this database
    print("\nSample queries you can run:")
    print("1. List all dolphin species:")
    print("   SELECT common_name, scientific_name FROM dolphin_species")
    print("2. Find endangered species:")
    print("   SELECT common_name FROM dolphin_species WHERE conservation_status LIKE '%Endangered%'")
    print("3. Find evolutionary relationships:")
    print("   SELECT d1.common_name, d2.common_name, r.relationship_type, r.divergence_mya")
    print("   FROM evolutionary_relationships r")
    print("   JOIN dolphin_species d1 ON r.species_id = d1.id")
    print("   JOIN dolphin_species d2 ON r.related_species_id = d2.id")