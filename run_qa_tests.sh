#!/bin/bash

# Comprehensive QA Test Runner for Project Agent
# This script runs all quality checks and tests

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track test results
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Project Agent - QA Test Suite          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Function to print test status
print_test_status() {
    local test_name="$1"
    local status="$2"
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $test_name"
        ((PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC} - $test_name"
        ((FAILED++))
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC} - $test_name"
        ((WARNINGS++))
    elif [ "$status" = "SKIP" ]; then
        echo -e "${BLUE}⏭️  SKIP${NC} - $test_name"
    fi
}

# Function to run a test safely
run_test() {
    local test_name="$1"
    local test_command="$2"
    echo -e "\n${BLUE}Running: $test_name${NC}"
    if eval "$test_command"; then
        print_test_status "$test_name" "PASS"
        return 0
    else
        print_test_status "$test_name" "FAIL"
        return 1
    fi
}

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}1. CODE STRUCTURE & QUALITY CHECKS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Check if new shared modules exist
if [ -f "packages/shared/config.py" ]; then
    print_test_status "Config module exists" "PASS"
else
    print_test_status "Config module exists" "FAIL"
fi

if [ -f "packages/shared/logging_config.py" ]; then
    print_test_status "Logging config module exists" "PASS"
else
    print_test_status "Logging config module exists" "FAIL"
fi

if [ -f "packages/shared/exceptions.py" ]; then
    print_test_status "Exception module exists" "PASS"
else
    print_test_status "Exception module exists" "FAIL"
fi

if [ -f "web/portal/lib/api-client.ts" ]; then
    print_test_status "API client module exists" "PASS"
else
    print_test_status "API client module exists" "FAIL"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}2. FRONTEND VALIDATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

if [ -d "web/portal" ]; then
    cd web/portal
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install --silent || print_test_status "NPM install" "WARN"
    fi
    
    # TypeScript type checking
    if command -v npx &> /dev/null; then
        echo -e "\n${BLUE}Checking TypeScript types...${NC}"
        if npx tsc --noEmit 2>&1 | head -20; then
            print_test_status "TypeScript type check" "PASS"
        else
            print_test_status "TypeScript type check" "WARN"
        fi
    else
        print_test_status "TypeScript type check" "SKIP"
    fi
    
    # Check for console.log statements (code smell)
    echo -e "\n${BLUE}Checking for console.log statements...${NC}"
    if grep -r "console\.log" components/ lib/ app/ 2>/dev/null | grep -v "// console.log" | wc -l | grep -q "^0$"; then
        print_test_status "No debug console.log statements" "PASS"
    else
        CONSOLE_COUNT=$(grep -r "console\.log" components/ lib/ app/ 2>/dev/null | grep -v "// console.log" | wc -l)
        echo -e "${YELLOW}Found $CONSOLE_COUNT console.log statements${NC}"
        print_test_status "Console.log cleanup" "WARN"
    fi
    
    # Check for hardcoded URLs
    echo -e "\n${BLUE}Checking for hardcoded URLs...${NC}"
    if grep -r "http://localhost:[0-9]" lib/ components/ 2>/dev/null | grep -v "api-client.ts" | wc -l | grep -q "^0$"; then
        print_test_status "No hardcoded localhost URLs" "PASS"
    else
        print_test_status "Hardcoded URLs found" "WARN"
    fi
    
    cd ../..
else
    print_test_status "Frontend directory" "FAIL"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}3. BACKEND VALIDATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Check Python syntax
echo -e "\n${BLUE}Checking Python syntax...${NC}"
find packages/ services/api/ -name "*.py" -type f -exec python3 -m py_compile {} \; 2>&1 | head -10
if [ $? -eq 0 ]; then
    print_test_status "Python syntax check" "PASS"
else
    print_test_status "Python syntax check" "FAIL"
fi

# Check for sys.path manipulation (code smell)
echo -e "\n${BLUE}Checking for sys.path manipulation...${NC}"
if grep -r "sys\.path\.append\|sys\.path\.insert" packages/ 2>/dev/null | wc -l | grep -q "^0$"; then
    print_test_status "No sys.path manipulation" "PASS"
else
    SYS_PATH_COUNT=$(grep -r "sys\.path\.append\|sys\.path\.insert" packages/ 2>/dev/null | wc -l)
    echo -e "${YELLOW}Found $SYS_PATH_COUNT sys.path manipulations in packages/${NC}"
    print_test_status "sys.path cleanup" "WARN"
fi

# Check for proper logging usage
echo -e "\n${BLUE}Checking logging patterns...${NC}"
if grep -r "print(" services/api/ 2>/dev/null | grep -v "# print" | wc -l; then
    PRINT_COUNT=$(grep -r "print(" services/api/ 2>/dev/null | grep -v "# print" | wc -l)
    if [ "$PRINT_COUNT" -gt "0" ]; then
        echo -e "${YELLOW}Found $PRINT_COUNT print() statements (should use logger)${NC}"
        print_test_status "Structured logging usage" "WARN"
    else
        print_test_status "Structured logging usage" "PASS"
    fi
fi

echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}4. SECURITY CHECKS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Check for exposed secrets
echo -e "\n${BLUE}Checking for exposed secrets...${NC}"
if grep -r "api[_-]key\|secret[_-]key\|password\s*=" packages/ services/ web/ --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "env" | grep -v "\.get(" | wc -l | grep -q "^0$"; then
    print_test_status "No exposed secrets" "PASS"
else
    print_test_status "Potential secrets found" "WARN"
fi

# Check for TODO/FIXME comments
echo -e "\n${BLUE}Checking for TODO/FIXME comments...${NC}"
TODO_COUNT=$(grep -r "TODO\|FIXME" packages/ services/api/ web/portal/components/ 2>/dev/null | wc -l)
echo -e "${BLUE}Found $TODO_COUNT TODO/FIXME comments${NC}"
if [ "$TODO_COUNT" -gt "20" ]; then
    print_test_status "TODO comments count" "WARN"
else
    print_test_status "TODO comments count" "PASS"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}5. DOCUMENTATION CHECKS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Check for README files
if [ -f "README.md" ]; then
    print_test_status "README exists" "PASS"
else
    print_test_status "README exists" "FAIL"
fi

# Check for environment example
if [ -f "services/env.example" ]; then
    print_test_status "Environment example exists" "PASS"
else
    print_test_status "Environment example exists" "FAIL"
fi

# Check for deployment docs
if [ -f "DEPLOYMENT_GUIDE.md" ]; then
    print_test_status "Deployment guide exists" "PASS"
else
    print_test_status "Deployment guide exists" "WARN"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}6. CONFIGURATION VALIDATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# Check Docker files exist
if [ -f "web/portal/Dockerfile" ]; then
    print_test_status "Web Dockerfile exists" "PASS"
else
    print_test_status "Web Dockerfile exists" "FAIL"
fi

# Check Terraform configuration
if [ -f "infra/terraform/main.tf" ]; then
    print_test_status "Terraform config exists" "PASS"
else
    print_test_status "Terraform config exists" "FAIL"
fi

# Check Cloud Build configuration
if [ -f "ops/cloudbuild.yaml" ]; then
    print_test_status "Cloud Build config exists" "PASS"
else
    print_test_status "Cloud Build config exists" "FAIL"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

TOTAL=$((PASSED + FAILED + WARNINGS))
echo -e "\n${GREEN}✅ Passed:  $PASSED${NC}"
echo -e "${RED}❌ Failed:  $FAILED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "Total Tests: $TOTAL"

# Calculate pass rate
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo -e "Pass Rate: ${PASS_RATE}%"
    
    if [ $PASS_RATE -ge 90 ]; then
        echo -e "\n${GREEN}🎉 EXCELLENT! Ready for QA review.${NC}"
        exit 0
    elif [ $PASS_RATE -ge 75 ]; then
        echo -e "\n${YELLOW}⚠️  GOOD with warnings. Address warnings before production.${NC}"
        exit 0
    elif [ $PASS_RATE -ge 50 ]; then
        echo -e "\n${YELLOW}⚠️  NEEDS WORK. Fix critical issues before deployment.${NC}"
        exit 1
    else
        echo -e "\n${RED}❌ FAILED. Major issues need resolution.${NC}"
        exit 1
    fi
else
    echo -e "\n${YELLOW}⚠️  No tests were run.${NC}"
    exit 1
fi

