/**
 * @file EventBufferTests.cpp
 * 
 * @brief Unit Tests for EventBuffer class.
 * 
 * @ingroup Testing/Core
 * 
 */


#include "EventBuffer.h"
#include "gtest/gtest.h"

TEST(EventBuffer, ConstructAndResize)
{
    EventBuffer emtpy_eb;
    emtpy_eb.resize(10);
}