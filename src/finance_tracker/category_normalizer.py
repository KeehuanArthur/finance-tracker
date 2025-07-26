import pandas as pd
import json
import os
from typing import Dict, List, Optional

class CategoryNormalizer:
    def __init__(self, mapping_file: str = "configs/category_mapping.json"):
        self.mapping_file = mapping_file
        self.category_mapping = self.load_mapping()
        
    def load_mapping(self) -> Dict[str, str]:
        """Load category mapping from JSON file and create reverse mapping."""
        try:
            with open(self.mapping_file, 'r') as f:
                target_to_sources = json.load(f)
            
            # Create reverse mapping: source -> target
            reverse_mapping = {}
            for target, sources in target_to_sources.items():
                for source in sources:
                    reverse_mapping[source.lower()] = target.lower()
            
            return reverse_mapping
        except FileNotFoundError:
            print(f"Warning: {self.mapping_file} not found. Creating default mapping.")
            self.create_default_mapping()
            return self.load_mapping()
    
    def create_default_mapping(self):
        """Create default category mapping file."""
        os.makedirs(os.path.dirname(self.mapping_file), exist_ok=True)
        
        default_mapping = {
            "dining": ["restaurant", "restaurants", "food", "dining", "cafe", "fast food", "takeout"],
            "groceries": ["grocery", "groceries", "supermarket", "market", "food store"],
            "transportation": ["gas", "fuel", "uber", "lyft", "taxi", "bus", "train", "parking"],
            "shopping": ["amazon", "walmart", "target", "store", "retail", "purchase"],
            "entertainment": ["netflix", "spotify", "hulu", "movies", "games", "subscription"],
            "income": ["salary", "paycheck", "deposit", "income", "wages", "bonus"],
            "housing": ["rent", "mortgage", "property", "home", "apartment"],
            "utilities": ["electric", "water", "internet", "phone", "cable", "utilities"],
            "healthcare": ["medical", "doctor", "pharmacy", "hospital", "health", "dental"],
            "insurance": ["insurance", "coverage", "policy", "premium"],
            "fees": ["atm", "fee", "charge", "penalty", "service fee"],
            "transfer": ["transfer", "payment", "wire", "check", "deposit"]
        }
        
        with open(self.mapping_file, 'w') as f:
            json.dump(default_mapping, f, indent=2)
    
    def normalize_category(self, category: str) -> str:
        """Normalize a single category."""
        if pd.isna(category):
            return "other"
        
        category_lower = str(category).lower().strip()
        
        # Check for exact matches first
        if category_lower in self.category_mapping:
            return self.category_mapping[category_lower]
        
        # Check for partial matches
        for key, value in self.category_mapping.items():
            if key in category_lower:
                return value
        
        return "other"
    
    def normalize_dataframe(self, df: pd.DataFrame, category_column: str = 'category') -> pd.DataFrame:
        """Normalize categories in a DataFrame."""
        if category_column not in df.columns:
            print(f"Warning: Column '{category_column}' not found in DataFrame")
            return df
        
        df = df.copy()
        df['normalized_category'] = df[category_column].apply(self.normalize_category)
        return df
    
    def get_unique_categories(self, df: pd.DataFrame, category_column: str = 'category') -> List[str]:
        """Get unique categories from DataFrame."""
        if category_column not in df.columns:
            return []
        
        return df[category_column].dropna().unique().tolist()
    
    def get_unmapped_categories(self, df: pd.DataFrame, category_column: str = 'category') -> List[str]:
        """Get categories that would be mapped to 'other'."""
        if category_column not in df.columns:
            return []
        
        unique_categories = self.get_unique_categories(df, category_column)
        unmapped = []
        
        for category in unique_categories:
            if self.normalize_category(category) == "other":
                unmapped.append(category)
                
        return unmapped