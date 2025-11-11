"""
Example usage of the AI Opportunity Bot
Demonstrates crawler, parser, and matcher working together
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.crawlers.linkedin_crawler import LinkedInCrawler
from backend.crawlers.indeed_crawler import IndeedCrawler
from backend.crawlers.internshala_crawler import InternShalaCrawler
from backend.ai.parser import OpportunityParser
from backend.ai.matcher import MatchingEngine
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run complete opportunity discovery pipeline"""
    
    print("🤖 AI Opportunity Bot - Example Usage\n")
    
    # ============================================
    # Step 1: Crawl opportunities from multiple sources
    # ============================================
    print("📡 Step 1: Crawling opportunities...\n")
    
    search_queries = ["python developer", "machine learning internship"]
    all_opportunities = []
    
    # LinkedIn
    print("Crawling LinkedIn...")
    linkedin = LinkedInCrawler()
    linkedin_opps = linkedin.crawl(search_queries, max_pages=2)
    all_opportunities.extend(linkedin_opps)
    
    # Indeed
    print("\nCrawling Indeed...")
    indeed = IndeedCrawler()
    indeed_opps = indeed.crawl(search_queries, max_pages=2)
    all_opportunities.extend(indeed_opps)
    
    # Internshala
    print("\nCrawling Internshala...")
    internshala = InternShalaCrawler()
    internshala_opps = internshala.crawl(search_queries, max_pages=2)
    all_opportunities.extend(internshala_opps)
    
    print(f"\n✅ Crawled {len(all_opportunities)} opportunities total\n")
    
    # ============================================
    # Step 2: Parse opportunities with AI
    # ============================================
    print("🤖 Step 2: Parsing with GPT-4...\n")
    
    parser = OpportunityParser()
    parsed_opportunities = []
    
    for i, opp in enumerate(all_opportunities[:10], 1):  # Limit to 10 for demo
        print(f"Parsing {i}/{min(10, len(all_opportunities))}: {opp.get('title', 'Unknown')}")
        
        # Simulate HTML content (in real usage, you'd have the actual HTML)
        mock_html = f"""
        <html>
            <h1>{opp.get('title')}</h1>
            <div class="company">{opp.get('company')}</div>
            <div class="location">{opp.get('location')}</div>
            <div class="description">{opp.get('description')}</div>
        </html>
        """
        
        parsed = parser.parse_opportunity(mock_html, opp.get('url', ''))
        if parsed:
            parsed_opportunities.append(parsed)
    
    print(f"\n✅ Successfully parsed {len(parsed_opportunities)} opportunities\n")
    
    # ============================================
    # Step 3: Match opportunities to user profile
    # ============================================
    print("🎯 Step 3: Matching to user profile...\n")
    
    # Example user profile
    user_profile = {
        'skills': ['Python', 'Machine Learning', 'TensorFlow', 'Data Analysis'],
        'interests': ['AI', 'Computer Vision', 'NLP'],
        'education': 'bachelor',
        'experience': 1,
        'locations': ['Remote', 'San Francisco', 'New York'],
        'types': ['internship', 'job'],
        'remote_only': False,
        'companies': ['Google', 'Microsoft', 'OpenAI'],
        'salary_min': 50000,
        'keywords': ['artificial intelligence', 'deep learning']
    }
    
    # Create matcher and user profile
    matcher = MatchingEngine()
    profile = matcher.create_user_profile(user_profile)
    
    # Rank opportunities
    ranked_opportunities = matcher.rank_opportunities(parsed_opportunities, profile)
    
    # Filter top matches
    top_matches = matcher.filter_opportunities(ranked_opportunities, min_score=60, max_results=10)
    
    print(f"✅ Found {len(top_matches)} high-quality matches\n")
    
    # ============================================
    # Step 4: Display results
    # ============================================
    print("🏆 Top Matches:\n")
    print("=" * 80)
    
    for i, opp in enumerate(top_matches, 1):
        print(f"\n{i}. {opp['title']} @ {opp['company']}")
        print(f"   Match Score: {opp['match_score']:.1f}/100")
        print(f"   Location: {opp.get('location', 'Not specified')}")
        print(f"   Type: {opp.get('type', 'job').title()}")
        print(f"   Skills: {', '.join(opp.get('skills', [])[:5])}")
        print(f"   URL: {opp['apply_url']}")
    
    print("\n" + "=" * 80)
    
    # Save results to JSON
    output_file = "matched_opportunities.json"
    with open(output_file, 'w') as f:
        json.dump(top_matches, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    print("\n✅ Pipeline complete!")


if __name__ == "__main__":
    main()
