#!/bin/bash

# Phase 5 Test Runner
# Runs all RBAC tests: setup, functional, security

set -e

echo "=========================================="
echo "PHASE 5: RBAC TESTING SUITE"
echo "=========================================="
echo ""

# Change to services directory
cd "$(dirname "$0")/services"

# Step 1: Setup test data
echo "Step 1: Setting up test data..."
python setup_phase5_test_data.py
echo ""

# Step 2: Run functional tests
echo "Step 2: Running functional tests..."
python test_phase5_functional.py
FUNCTIONAL_EXIT=$?
echo ""

# Step 3: Run security tests
echo "Step 3: Running security tests..."
python test_phase5_security.py
SECURITY_EXIT=$?
echo ""

# Summary
echo "=========================================="
echo "TEST EXECUTION SUMMARY"
echo "=========================================="
echo "Functional Tests: $([ $FUNCTIONAL_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo "Security Tests:   $([ $SECURITY_EXIT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
echo ""

if [ $FUNCTIONAL_EXIT -eq 0 ] && [ $SECURITY_EXIT -eq 0 ]; then
    echo "✅ ALL TESTS PASSED!"
    echo "   System is ready for deployment."
    exit 0
elif [ $SECURITY_EXIT -eq 2 ]; then
    echo "🚨 CRITICAL SECURITY FAILURES!"
    echo "   DO NOT DEPLOY TO PRODUCTION!"
    exit 2
else
    echo "❌ SOME TESTS FAILED"
    echo "   Review failures before deploying."
    exit 1
fi

