#!/bin/bash
# setup.sh - Quick setup script for job scraper project

set -e

echo "========================================"
echo "🚀 Job Scraper Setup Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create a .env file first."
    exit 1
fi

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check pip
echo -e "${YELLOW}Checking pip...${NC}"
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip found${NC}"

# Install Python dependencies
echo ""
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip3 install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Install Playwright browsers
echo ""
echo -e "${YELLOW}Installing Playwright browsers...${NC}"
playwright install chromium
echo -e "${GREEN}✓ Playwright browsers installed${NC}"

# Check MongoDB connection
echo ""
echo -e "${YELLOW}Testing MongoDB connection...${NC}"
python3 -c "from db_mongo import init_db; init_db(); print('✓ MongoDB connection successful')" || {
    echo -e "${RED}❌ MongoDB connection failed${NC}"
    echo "Please check your MONGO_URI in .env file"
    exit 1
}

# Check for user profile
echo ""
if [ ! -f user_profile.md ] && [ ! -f user_profile.txt ]; then
    echo -e "${YELLOW}⚠️  user_profile.md not customized yet${NC}"
    echo "   Please edit user_profile.md with your information"
else
    echo -e "${GREEN}✓ user_profile found${NC}"
fi

# Check for matching criteria
if [ ! -f matching_criteria.txt ]; then
    echo -e "${YELLOW}⚠️  matching_criteria.txt not customized yet${NC}"
    echo "   Please edit matching_criteria.txt with your criteria"
else
    echo -e "${GREEN}✓ matching_criteria.txt exists${NC}"
fi

# Check for OpenAI API key
echo ""
echo -e "${YELLOW}Checking OpenAI API key...${NC}"
if grep -q "your_openai_api_key_here" .env 2>/dev/null; then
    echo -e "${RED}❌ OpenAI API key not configured${NC}"
    echo "   Please add your API key to .env file"
    echo "   Get it from: https://platform.openai.com/api-keys"
else
    echo -e "${GREEN}✓ API key configured${NC}"
fi

# Make scripts executable
echo ""
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x run_task.sh
chmod +x view_matches.py
echo -e "${GREEN}✓ Scripts are executable${NC}"

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit your profile and criteria:"
echo "   - user_profile.md (or user_profile.txt)"
echo "   - matching_criteria.txt"
echo ""
echo "2. Test the scraper:"
echo "   python3 indeed_scraper.py -k \"frontend\" -p 1"
echo ""
echo "3. Test AI matching:"
echo "   python3 ai_matcher.py -l 3"
echo ""
echo "4. Set up daily automation:"
echo "   cp com.user.job_scraper.plist ~/Library/LaunchAgents/"
echo "   launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist"
echo ""
echo "📖 Read QUICKSTART.md for detailed instructions"
echo ""
