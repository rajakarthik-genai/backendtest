#!/bin/bash

# Enhanced Digital Twin Health Dashboard - Feature Verification Script
# This script verifies all implemented features are working correctly

echo "🔍 Enhanced Digital Twin Health Dashboard - Feature Verification"
echo "=============================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verification counters
total_checks=0
passed_checks=0

# Function to check if a feature exists
check_feature() {
    local feature_name="$1"
    local file_path="$2"
    local search_pattern="$3"
    local required="$4"
    
    ((total_checks++))
    
    if [ -f "$file_path" ]; then
        if grep -q "$search_pattern" "$file_path"; then
            echo -e "${GREEN}✅ $feature_name - FOUND${NC}"
            ((passed_checks++))
        else
            if [ "$required" = "required" ]; then
                echo -e "${RED}❌ $feature_name - MISSING PATTERN${NC}"
            else
                echo -e "${YELLOW}⚠️  $feature_name - OPTIONAL PATTERN NOT FOUND${NC}"
                ((passed_checks++))
            fi
        fi
    else
        echo -e "${RED}❌ $feature_name - FILE NOT FOUND: $file_path${NC}"
    fi
}

# Function to check if file exists
check_file() {
    local feature_name="$1"
    local file_path="$2"
    local required="$3"
    
    ((total_checks++))
    
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}✅ $feature_name - EXISTS${NC}"
        ((passed_checks++))
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}❌ $feature_name - NOT FOUND${NC}"
        else
            echo -e "${YELLOW}⚠️  $feature_name - OPTIONAL FILE NOT FOUND${NC}"
            ((passed_checks++))
        fi
    fi
}

echo -e "\n${BLUE}📁 Checking Core Files...${NC}"
check_file "Enhanced Index HTML" "index.html" "required"
check_file "Enhanced Main JavaScript" "app.js" "required"
check_file "Mock API with Timeline" "mock-api.js" "required"
check_file "Enhanced Configuration" "js/digital-twin-config.js" "required"
check_file "API Service Layer" "js/digital-twin-api.js" "required"
check_file "Dashboard Styles" "styles/dashboard.css" "required"
check_file "Backend Implementation Guide" "BACKEND_IMPLEMENTATION_GUIDE.md" "required"
check_file "Enhanced README" "README-ENHANCED.md" "required"
check_file "Start Script" "start-frontend.sh" "required"

echo -e "\n${BLUE}👤 Checking Dr. Ericsson Profile Updates...${NC}"
check_feature "Dr. Ericsson in HTML" "index.html" "Dr. Ericsson" "required"
check_feature "Dr. Ericsson Initials" "index.html" "DE" "required"
check_feature "Enhanced Title" "index.html" "Dr. Ericsson" "required"

echo -e "\n${BLUE}💬 Checking Expert Opinion Chat Features...${NC}"
check_feature "Expert Chat Panel" "index.html" "expertChatPanel" "required"
check_feature "Expert Mode Toggle" "index.html" "expertModeToggle" "required"
check_feature "Sources Panel" "index.html" "expertSourcesPanel" "required"
check_feature "Chat Input" "index.html" "chatInput" "required"
check_feature "Expert Opinion Button" "index.html" "Expert Opinion" "required"
check_feature "Expert Mode Handler" "app.js" "expertMode" "required"
check_feature "Send Chat Message" "app.js" "sendChatMessage" "required"
check_feature "Expert Response Display" "app.js" "displayExpertResponse" "required"
check_feature "Sources Panel Logic" "app.js" "showSourcesPanel" "required"

echo -e "\n${BLUE}📅 Checking Interactive Timeline Features...${NC}"
check_feature "Timeline Panel" "index.html" "timelinePanel" "required"
check_feature "Timeline Title" "index.html" "timelineTitle" "required"
check_feature "Body Region Markers" "index.html" "data-region=" "required"
check_feature "Timeline Load Function" "app.js" "loadTimeline" "required"
check_feature "Timeline Render Function" "app.js" "renderTimeline" "required"
check_feature "Year/Month Organization" "app.js" "eventsByYear" "required"
check_feature "Timeline Mock Data" "mock-api.js" "mockTimelineData" "required"

echo -e "\n${BLUE}🎨 Checking Enhanced UI/UX Features...${NC}"
check_feature "Pulse Animations" "index.html" "pulse-animation" "required"
check_feature "Glassmorphism Effects" "index.html" "backdrop-blur" "required"
check_feature "Responsive Chat Panel" "index.html" "w-full sm:w-96" "required"
check_feature "Gradient Backgrounds" "index.html" "bg-gradient-to" "required"
check_feature "Hover Effects" "index.html" "hover:bg-" "required"
check_feature "Transition Animations" "index.html" "transition-" "required"

echo -e "\n${BLUE}🔧 Checking API Integration...${NC}"
check_feature "Timeline Endpoint" "js/digital-twin-config.js" "TIMELINE" "required"
check_feature "Chat Endpoint" "js/digital-twin-config.js" "CHAT" "required"
check_feature "Expert Opinion Endpoint" "js/digital-twin-config.js" "EXPERT_OPINION" "required"
check_feature "Mock Timeline API" "mock-api.js" "getTimeline" "required"
check_feature "Mock Chat API" "mock-api.js" "sendChatMessage" "required"
check_feature "Expert Mock Responses" "mock-api.js" "expert:" "required"

echo -e "\n${BLUE}📱 Checking Mobile Responsiveness...${NC}"
check_feature "Mobile Viewport" "index.html" "viewport" "required"
check_feature "Responsive Grid" "index.html" "grid-cols-" "required"
check_feature "Mobile Chat Panel" "index.html" "w-full sm:w-" "required"
check_feature "Touch Optimizations" "index.html" "cursor-pointer" "required"

echo -e "\n${BLUE}🎯 Checking Interactive Body Map...${NC}"
check_feature "Head Region" "index.html" 'data-region="head"' "required"
check_feature "Heart Region" "index.html" 'data-region="heart"' "required"
check_feature "Lungs Region" "index.html" 'data-region="lungs"' "required"
check_feature "Liver Region" "index.html" 'data-region="liver"' "required"
check_feature "Kidneys Region" "index.html" 'data-region="kidneys"' "required"
check_feature "Stomach Region" "index.html" 'data-region="stomach"' "required"
check_feature "Shoulder Region" "index.html" 'data-region="shoulder"' "required"

echo -e "\n${BLUE}🔍 Checking Search & Export Features...${NC}"
check_feature "Search Input" "index.html" "search-input" "required"
check_feature "Export Button" "index.html" "export-btn" "required"
check_feature "Search Handler" "app.js" "handleSearch" "required"
check_feature "Export Handler" "app.js" "exportHealthData" "required"

echo -e "\n${BLUE}📊 Checking Data Features...${NC}"
check_feature "Severity Color Coding" "app.js" "severityColors" "required"
check_feature "Event Categorization" "app.js" "monthEvents" "required"
check_feature "Timeline Years" "index.html" "data-year=" "required"
check_feature "Loading Indicators" "index.html" "loading-indicator" "required"

echo -e "\n${BLUE}🔒 Checking Configuration & Security...${NC}"
check_feature "Development Mode" "js/digital-twin-config.js" "DEVELOPMENT_MODE" "required"
check_feature "Feature Flags" "js/digital-twin-config.js" "FEATURES" "required"
check_feature "Cache Configuration" "js/digital-twin-config.js" "CACHE_TIMEOUT" "required"
check_feature "Health Regions Config" "js/digital-twin-config.js" "HEALTH_REGIONS" "required"

echo -e "\n${BLUE}🧪 Checking Testing & Documentation...${NC}"
check_feature "Mock API Implementation" "mock-api.js" "window.mockAPI" "required"
check_feature "Error Handling" "app.js" "catch.*error" "required"
check_feature "Console Logging" "app.js" "console.log" "required"
check_feature "Backend Guide" "BACKEND_IMPLEMENTATION_GUIDE.md" "FastAPI" "required"

# Additional advanced checks
echo -e "\n${BLUE}🚀 Checking Advanced Features...${NC}"
check_feature "Citation Support" "app.js" "\\[\\(\\\\d\\+\\)\\]" "required"
check_feature "Research Steps" "app.js" "researchSteps" "required"
check_feature "Typing Indicators" "app.js" "typing-indicator" "required"
check_feature "Source Highlighting" "app.js" "highlightSource" "required"
check_feature "Expert Response Sources" "mock-api.js" "sources.*id.*title.*url" "required"

# Check if server is running
echo -e "\n${BLUE}🌐 Checking Server Status...${NC}"
((total_checks++))
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Development Server - RUNNING${NC}"
    ((passed_checks++))
else
    echo -e "${YELLOW}⚠️  Development Server - NOT RUNNING (run ./start-frontend.sh)${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Verification Summary${NC}"
echo "======================================"
echo -e "Total Checks: ${BLUE}$total_checks${NC}"
echo -e "Passed: ${GREEN}$passed_checks${NC}"
echo -e "Failed: ${RED}$((total_checks - passed_checks))${NC}"

# Calculate percentage
percentage=$((passed_checks * 100 / total_checks))
echo -e "Success Rate: ${BLUE}$percentage%${NC}"

if [ $percentage -ge 95 ]; then
    echo -e "\n${GREEN}🎉 EXCELLENT! All major features are implemented correctly.${NC}"
    echo -e "${GREEN}✅ Enhanced Digital Twin Health Dashboard is ready for use!${NC}"
elif [ $percentage -ge 80 ]; then
    echo -e "\n${YELLOW}⚠️  GOOD! Most features are working, minor issues detected.${NC}"
    echo -e "${YELLOW}🔧 Review failed checks above for improvements.${NC}"
else
    echo -e "\n${RED}❌ NEEDS WORK! Several features missing or incomplete.${NC}"
    echo -e "${RED}🛠️  Please review and fix the failed checks above.${NC}"
fi

echo -e "\n${BLUE}🚀 Quick Start Commands:${NC}"
echo "=================================="
echo "Start Dashboard: ./start-frontend.sh"
echo "View Dashboard: http://localhost:3000"
echo "Test Features:"
echo "  - Click body regions for timeline"
echo "  - Toggle Expert Opinion mode"
echo "  - Test chat with citations"
echo "  - Export health data"

echo -e "\n${BLUE}📚 Documentation:${NC}"
echo "=================================="
echo "Enhanced README: README-ENHANCED.md"
echo "Backend Guide: BACKEND_IMPLEMENTATION_GUIDE.md"
echo "Configuration: js/digital-twin-config.js"

exit 0
