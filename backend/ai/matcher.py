"""
AI-Powered Matching Engine
Matches opportunities to user profiles using semantic similarity
"""
import logging
from typing import Dict, List
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Semantic matching engine that scores opportunities against user profiles.
    Uses AI embeddings for intelligent skill and interest matching.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the matching engine.
        
        Args:
            model_name: Sentence transformer model name
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("✅ Matching engine ready")
        
    def create_user_profile(self, user_data: Dict) -> Dict:
        """
        Build comprehensive user profile from user data.
        
        Args:
            user_data: Raw user data
            
        Returns:
            Structured user profile
        """
        profile = {
            'skills': user_data.get('skills', []),
            'interests': user_data.get('interests', []),
            'education_level': user_data.get('education', 'bachelor'),
            'experience_years': user_data.get('experience', 0),
            'preferred_locations': user_data.get('locations', []),
            'preferred_types': user_data.get('types', ['job', 'internship']),
            'remote_only': user_data.get('remote_only', False),
            'target_companies': user_data.get('companies', []),
            'salary_min': user_data.get('salary_min', 0),
            'keywords': user_data.get('keywords', []),
        }
        
        # Create embeddings for skills and interests
        if profile['skills']:
            profile['skills_text'] = ', '.join(profile['skills'])
            profile['skills_embedding'] = self.model.encode(profile['skills_text'])
        
        if profile['interests']:
            profile['interests_text'] = ', '.join(profile['interests'])
            profile['interests_embedding'] = self.model.encode(profile['interests_text'])
        
        return profile
    
    def calculate_match_score(self, opportunity: Dict, user_profile: Dict) -> float:
        """
        Calculate match score between opportunity and user profile (0-100).
        
        Uses weighted scoring across multiple factors:
        - Skills similarity (40%)
        - Location match (20%)
        - Type match (15%)
        - Experience level (10%)
        - Company preference (10%)
        - Keywords (5%)
        
        Args:
            opportunity: Opportunity dictionary
            user_profile: User profile dictionary
            
        Returns:
            Match score between 0 and 100
        """
        scores = []
        weights = []
        
        # 1. Skills Matching (40% weight) - Semantic similarity
        if opportunity.get('skills') and user_profile.get('skills_embedding') is not None:
            opp_skills_text = ', '.join(opportunity['skills'])
            opp_embedding = self.model.encode(opp_skills_text)
            
            # Cosine similarity
            similarity = self._cosine_similarity(
                opp_embedding, 
                user_profile['skills_embedding']
            )
            
            skill_score = max(0, similarity * 100)  # Convert to 0-100
            scores.append(skill_score)
            weights.append(0.40)
        
        # 2. Location Matching (20% weight)
        location_score = self._match_location(opportunity, user_profile)
        scores.append(location_score)
        weights.append(0.20)
        
        # 3. Type Matching (15% weight)
        type_score = self._match_type(opportunity, user_profile)
        scores.append(type_score)
        weights.append(0.15)
        
        # 4. Experience Level (10% weight)
        experience_score = self._match_experience(opportunity, user_profile)
        scores.append(experience_score)
        weights.append(0.10)
        
        # 5. Company Preference (10% weight)
        company_score = self._match_company(opportunity, user_profile)
        scores.append(company_score)
        weights.append(0.10)
        
        # 6. Keywords (5% weight)
        keyword_score = self._match_keywords(opportunity, user_profile)
        scores.append(keyword_score)
        weights.append(0.05)
        
        # Calculate weighted average
        total_score = sum(s * w for s, w in zip(scores, weights))
        
        # Apply bonus/penalty factors
        total_score = self._apply_modifiers(total_score, opportunity, user_profile)
        
        # Ensure score is between 0 and 100
        return max(0, min(100, total_score))
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def _match_location(self, opportunity: Dict, user_profile: Dict) -> float:
        """Score location match"""
        # Remote is always a match for remote-only users
        if user_profile['remote_only'] and opportunity.get('remote'):
            return 100.0
        
        # Check if location is in preferred list
        opp_location = (opportunity.get('location') or '').lower()
        preferred = [loc.lower() for loc in user_profile['preferred_locations']]
        
        for pref in preferred:
            if pref in opp_location:
                return 100.0
        
        # Partial credit for remote opportunities
        if opportunity.get('remote'):
            return 70.0
        
        return 0.0
    
    def _match_type(self, opportunity: Dict, user_profile: Dict) -> float:
        """Score opportunity type match"""
        opp_type = (opportunity.get('type') or 'job').lower()
        if opp_type in user_profile['preferred_types']:
            return 100.0
        return 0.0
    
    def _match_experience(self, opportunity: Dict, user_profile: Dict) -> float:
        """Score experience level match"""
        # Simple heuristic based on keywords in description
        description = (opportunity.get('description') or '').lower()
        requirements = ' '.join(opportunity.get('requirements', [])).lower()
        combined = description + ' ' + requirements
        
        user_exp = user_profile['experience_years']
        
        # Check for experience indicators
        if any(word in combined for word in ['entry level', 'junior', 'internship', 'graduate']):
            return 100.0 if user_exp <= 2 else 50.0
        
        if any(word in combined for word in ['mid level', '2-5 years', '3+ years']):
            return 100.0 if 2 <= user_exp <= 5 else 50.0
        
        if any(word in combined for word in ['senior', '5+ years', 'lead', 'principal']):
            return 100.0 if user_exp >= 5 else 30.0
        
        # Default: moderate match
        return 50.0
    
    def _match_company(self, opportunity: Dict, user_profile: Dict) -> float:
        """Score company preference match"""
        if not user_profile['target_companies']:
            return 50.0  # Neutral if no preference
        
        opp_company = (opportunity.get('company') or '').lower()
        target_companies = [c.lower() for c in user_profile['target_companies']]
        
        for target in target_companies:
            if target in opp_company:
                return 100.0
        
        return 0.0
    
    def _match_keywords(self, opportunity: Dict, user_profile: Dict) -> float:
        """Score keyword match"""
        if not user_profile['keywords']:
            return 50.0  # Neutral
        
        opp_text = ' '.join([
            opportunity.get('title', ''),
            opportunity.get('description', ''),
            ' '.join(opportunity.get('skills', [])),
        ]).lower()
        
        keywords = [kw.lower() for kw in user_profile['keywords']]
        matches = sum(1 for kw in keywords if kw in opp_text)
        
        if not keywords:
            return 50.0
        
        return (matches / len(keywords)) * 100
    
    def _apply_modifiers(self, base_score: float, opportunity: Dict, user_profile: Dict) -> float:
        """Apply bonus/penalty modifiers to base score"""
        score = base_score
        
        # Bonus for recent postings
        # (Would need posted_date in opportunity dict)
        
        # Penalty for closed opportunities
        if not opportunity.get('is_still_open', True):
            score *= 0.5
        
        # Bonus for compensation match
        if opportunity.get('compensation') and user_profile.get('salary_min'):
            # Simple check if compensation mentions a high number
            # (More sophisticated parsing would be better)
            pass
        
        return score
    
    def rank_opportunities(self, opportunities: List[Dict], user_profile: Dict) -> List[Dict]:
        """
        Rank all opportunities by match score.
        
        Args:
            opportunities: List of opportunity dictionaries
            user_profile: User profile dictionary
            
        Returns:
            Sorted list of opportunities with match_score added
        """
        logger.info(f"Ranking {len(opportunities)} opportunities for user")
        
        # Calculate match scores
        for opp in opportunities:
            opp['match_score'] = self.calculate_match_score(opp, user_profile)
        
        # Sort by score (descending)
        ranked = sorted(opportunities, key=lambda x: x['match_score'], reverse=True)
        
        logger.info(f"✅ Ranking complete. Top score: {ranked[0]['match_score']:.1f}")
        
        return ranked
    
    def filter_opportunities(
        self, 
        opportunities: List[Dict], 
        min_score: float = 70.0,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Filter opportunities by minimum score and limit results.
        
        Args:
            opportunities: List of opportunities with match_score
            min_score: Minimum match score threshold
            max_results: Maximum number of results to return
            
        Returns:
            Filtered list of opportunities
        """
        filtered = [opp for opp in opportunities if opp.get('match_score', 0) >= min_score]
        return filtered[:max_results]
